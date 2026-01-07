import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database.db import init_db, register_user, get_promo_count

# Налаштування логів
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("WEBHOOK_URL")

# Використовуємо Lifespan замість on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    global tg_app
    await init_db()
    
    tg_app = Application.builder().token(TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    
    await tg_app.initialize()
    
    # Корекція Webhook
    final_webhook_url = BASE_URL if BASE_URL.endswith("/webhook") else f"{BASE_URL}/webhook"
    await tg_app.bot.set_webhook(url=final_webhook_url)
    
    logger.info(f"🚀 Webhook set to: {final_webhook_url}")
    await tg_app.start()
    
    yield
    
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)
tg_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    plan = await register_user(user_id, username)
    promo_left = await get_promo_count()
    
    if plan == "Premium":
        text = (
            f"Hi! You are an **Early Bird**! 🏃‍♂️\n"
            f"You've received **Premium Access** (1 month) for free.\n"
            f"Spots left: {promo_left}/500\n\n"
            "Use Settings to configure your Timezone and Threshold."
        )
    else:
        text = (
            "Welcome! You are on the **Free Plan**.\n"
            "Bybit only, 1.5% threshold, hidden coins.\n\n"
            "Upgrade to Premium for $50/month to unlock everything."
        )
    await update.message.reply_text(text, parse_mode="Markdown")

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "running"}

if __name__ == "__main__":
    # Render передає порт через змінну оточення PORT
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
