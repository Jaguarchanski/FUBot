import os
import logging
import uvicorn
import asyncio
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from database.db import init_db, register_user
import telegram_bot.bot as bot_logic
from scanner import run_scanner

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tg_app
    # 1. Ініціалізація БД
    await init_db()
    
    # 2. Запуск сканера фандингу у фоні
    asyncio.create_task(run_scanner())
    
    # 3. Налаштування Telegram бота
    token = os.getenv("BOT_TOKEN")
    tg_app = Application.builder().token(token).build()
    
    # Налаштування розмови для введення даних (Threshold та UTC)
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(bot_logic.start_threshold_input, pattern="^set_threshold$"),
            CallbackQueryHandler(bot_logic.start_utc_input, pattern="^set_tz_manual$")
        ],
        states={
            bot_logic.WAITING_THRESHOLD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot_logic.save_threshold)
            ],
            bot_logic.WAITING_UTC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot_logic.save_utc)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(bot_logic.handle_callbacks, pattern="^main_menu$")
        ],
        per_message=False
    )
    
    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(conv_handler)
    tg_app.add_handler(CallbackQueryHandler(bot_logic.handle_callbacks))
    
    # 4. Запуск Webhook
    await tg_app.initialize()
    webhook_url = os.getenv("WEBHOOK_URL").rstrip('/')
    await tg_app.bot.set_webhook(url=f"{webhook_url}/webhook")
    await tg_app.start()
    
    logger.info("Application started successfully")
    yield
    # Зупинка
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)
tg_app = None

async def start_command(update: Update, context):
    user = update.effective_user
    # Реєстрація (перевірка на 500 місць Early Bird всередині)
    plan = await register_user(user.id, user.username)
    
    welcome_text = (
        f"🚀 **FUBot: Funding Arbitrage Scanner**\n\n"
        f"Вітаємо, {user.first_name}!\n"
        f"Ваш статус: **{plan}**\n\n"
        f"Я відстежую фандинг на 9 біржах у реальному часі."
    )
    
    reply_markup = await bot_logic.get_settings_keyboard(user.id)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def health_check():
    return {"status": "online", "timestamp": datetime.datetime.now().isoformat()}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
