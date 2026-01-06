import asyncio
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

from config import config
from storage import db_manager
from funding.fetcher import fetch_all_funding_rates

# Логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація
tg_bot = Bot(token=config.BOT_TOKEN)
application = Application.builder().token(config.BOT_TOKEN).build()
app = FastAPI()

# --- Команди бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await db_manager.upsert_user(update.effective_chat.id)
    await update.message.reply_text("✅ Бот активовано! Встановіть поріг: /threshold 0.1")

async def threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(context.args[0])
        if val > config.FREE_LIMIT:
            return await update.message.reply_text(f"❌ Ліміт Free: {config.FREE_LIMIT}%")
        await db_manager.update_threshold(update.effective_chat.id, val)
        await update.message.reply_text(f"🎯 Поріг встановлено: {val}%")
    except:
        await update.message.reply_text("⚠️ Формат: /threshold 0.05")

# --- Фоновий моніторинг ---
async def funding_monitoring():
    while True:
        logging.info("Checking exchanges...")
        rates = await fetch_all_funding_rates()
        users = await db_manager.get_active_users()
        
        for user in users:
            alerts = [
                f"🔥 {r['exchange']} | {r['symbol']}: `{r['rate']:.4f}%`"
                for r in rates if abs(r['rate']) >= user['threshold']
            ]
            if alerts:
                try:
                    text = "🚨 **FUNDING ALERT**\n\n" + "\n".join(alerts[:15])
                    await tg_bot.send_message(user['chat_id'], text, parse_mode='Markdown')
                except:
                    pass
        await asyncio.sleep(600) # 10 хвилин

# --- Webhook ---
@app.post("/webhook")
async def process_update(request: Request):
    update = Update.de_json(await request.json(), tg_bot)
    await application.process_update(update)
    return {"ok": True}

@app.on_event("startup")
async def startup():
    await db_manager.init_db()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("threshold", threshold))
    await application.initialize()
    await tg_bot.set_webhook(f"{config.WEBHOOK_URL}/webhook")
    asyncio.create_task(funding_monitoring())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
