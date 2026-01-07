import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database.db import init_db, register_user, get_promo_count

# Логування для відстеження помилок у консолі Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Твої ENV змінні
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("WEBHOOK_URL") 

app = FastAPI()
tg_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Логіка реєстрації: Free або Premium (Early Bird)
    plan = await register_user(user_id, username)
    promo_left = await get_promo_count()
    
    if plan == "Premium":
        text = (
            f"Hi! You are an **Early Bird**! 🏃‍♂️\n"
            f"You've received **Premium Access** (1 month) for free.\n"
            f"Spots left: {promo_left}/500\n\n"
            "Go to Settings to configure your Timezone and Threshold."
        )
    else:
        text = (
            "Welcome! You are on the **Free Plan**.\n"
            "Bybit only, 1.5% threshold, hidden coin names.\n\n"
            "Upgrade to Premium ($50/month) to unlock all exchanges and data."
        )
    
    await update.message.reply_text(text, parse_mode="Markdown")

@app.on_event("startup")
async def startup():
    global tg_app
    await init_db() # Запуск бази даних
    
    tg_app = Application.builder().token(TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    
    await tg_app.initialize()
    
    # Корекція шляху вебхука (щоб уникнути 404)
    final_webhook_url = BASE_URL if BASE_URL.endswith("/webhook") else f"{BASE_URL}/webhook"
    
    await tg_app.bot.set_webhook(url=final_webhook_url)
    logger.info(f"🚀 Webhook address: {final_webhook_url}")
    await tg_app.start()

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "active", "early_bird_left": await get_promo_count()}
