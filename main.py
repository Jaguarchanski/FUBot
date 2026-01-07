import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
# ДОДАНО ContextTypes ТА ІНШІ НЕОБХІДНІ ІМПОРТИ ТУТ:
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ConversationHandler, 
    MessageHandler, 
    filters,
    ContextTypes  # Оце те, чого не вистачало
)
from database.db import init_db, register_user, get_promo_count
import telegram_bot.bot as bot_logic

# Налаштування логів
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tg_app
    await init_db()
    
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found in environment variables!")

    tg_app = Application.builder().token(token).build()
    
    # Реєстрація ConversationHandler для вводу Threshold
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot_logic.start_threshold_input, pattern="^set_threshold$")],
        states={
            bot_logic.WAITING_THRESHOLD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot_logic.save_threshold)
            ]
        },
        fallbacks=[CallbackQueryHandler(bot_logic.handle_callbacks, pattern="^main_menu$")]
    )
    
    # Додаємо обробники
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(conv_handler)
    tg_app.add_handler(CallbackQueryHandler(bot_logic.handle_callbacks))
    
    await tg_app.initialize()
    
    # Налаштування Webhook
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        final_url = f"{webhook_url.rstrip('/')}/webhook"
        await tg_app.bot.set_webhook(url=final_url)
        logger.info(f"Webhook set to {final_url}")
    
    await tg_app.start()
    yield
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)
tg_app = None

# Функція Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plan = await register_user(user.id, user.username)
    promo = await get_promo_count()
    
    text = (
        f"🚀 **Early Bird Premium Active!**\nSpots left: {promo}/500" 
        if plan == "Premium" 
        else "👋 **Welcome!** Free Plan active."
    )
    
    await update.message.reply_text(
        text, 
        reply_markup=await bot_logic.get_settings_keyboard(user.id), 
        parse_mode="Markdown"
    )

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    try:
        await tg_app.process_update(Update.de_json(data, tg_app.bot))
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return {"ok": True}

if __name__ == "__main__":
    # Render використовує змінну оточення PORT
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
