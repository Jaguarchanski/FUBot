import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

from storage import db_manager
from funding.fetcher import fetch_all_funding_rates
from config import config

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація об'єктів
tg_bot = Bot(token=config.BOT_TOKEN)
application = Application.builder().token(config.BOT_TOKEN).build()

# --- ОБРОБНИКИ КОМАНД ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        logger.info(f"Команда /start від {chat_id}")
        await db_manager.upsert_user(chat_id)
        await update.message.reply_text(
            "✅ Бот запущений!\n\n"
            "Я буду моніторити фандинг на 9 біржах.\n"
            "Встановіть поріг сповіщень: /threshold 0.1"
        )
    except Exception as e:
        logger.error(f"Помилка в start_cmd: {e}")

async def threshold_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(context.args[0])
        if val > config.FREE_LIMIT:
            await update.message.reply_text(f"❌ Ліміт для Free: {config.FREE_LIMIT}%")
            return
        await db_manager.update_threshold(update.effective_chat.id, val)
        await update.message.reply_text(f"🎯 Поріг встановлено: {val}%")
    except Exception:
        await update.message.reply_text("⚠️ Формат: /threshold 0.05")

# --- ФОНОВИЙ МОНІТОРИНГ ---
async def funding_monitoring_loop():
    while True:
        try:
            logger.info("Початок перевірки бірж...")
            rates = await fetch_all_funding_rates()
            users = await db_manager.get_active_users()
            
            for user in users:
                alerts = [
                    f"🔸 {r['exchange']} | {r['symbol']}: `{r['rate']:.4f}%`"
                    for r in rates if abs(r['rate']) >= user['threshold']
                ]
                if alerts:
                    text = "🚨 *FUNDING ALERT*\n\n" + "\n".join(alerts[:15])
                    try:
                        await tg_bot.send_message(user['chat_id'], text, parse_mode='Markdown')
                    except Exception as e:
                        logger.warning(f"Не вдалося надіслати повідомлення {user['chat_id']}: {e}")
            
            await asyncio.sleep(600) # 10 хвилин
        except Exception as e:
            logger.error(f"Помилка в циклі моніторингу: {e}")
            await asyncio.sleep(60)

# --- ЖИТТЄВИЙ ЦИКЛ ДОДАТКУ ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Дії при запуску
    await db_manager.init_db()
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("threshold", threshold_cmd))
    
    await application.initialize()
    await application.start()
    
    # Встановлення Вебхука (БЕЗ подвійних /webhook)
    webhook_url = f"{config.WEBHOOK_URL.rstrip('/')}/webhook"
    await tg_bot.set_webhook(webhook_url)
    logger.info(f"✅ Webhook встановлено: {webhook_url}")
    
    # Запуск фонового завдання
    monitor_task = asyncio.create_task(funding_monitoring_loop())
    
    yield
    # Дії при вимкненні
    monitor_task.cancel()
    await application.stop()
    await application.shutdown()

app = FastAPI(lifespan=lifespan)

# --- ЕНДПОІНТИ ---
@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        body = await request.json()
        update = Update.de_json(body, tg_bot)
        await application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Помилка обробки вебхука: {e}")
        return Response(status_code=500)

@app.get("/")
async def index():
    return {"status": "online", "message": "Funding Bot is running"}

if __name__ == "__main__":
    import uvicorn
    # Render передає порт через змінну оточення
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
