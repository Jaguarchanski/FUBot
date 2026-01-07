import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from database.db import init_db, register_user, get_promo_count
import telegram_bot.bot as bot_logic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tg_app
    await init_db()
    
    tg_app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot_logic.start_threshold_input, pattern="^set_threshold$")],
        states={bot_logic.WAITING_THRESHOLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_logic.save_threshold)]},
        fallbacks=[CallbackQueryHandler(bot_logic.handle_callbacks, pattern="^main_menu$")]
    )
    
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(conv_handler)
    tg_app.add_handler(CallbackQueryHandler(bot_logic.handle_callbacks))
    
    await tg_app.initialize()
    webhook_url = os.getenv("WEBHOOK_URL")
    final_url = f"{webhook_url.rstrip('/')}/webhook"
    await tg_app.bot.set_webhook(url=final_url)
    
    await tg_app.start()
    yield
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)
tg_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = await register_user(update.effective_user.id, update.effective_user.username)
    promo = await get_promo_count()
    text = (f"🚀 **Early Bird Premium Active!**\nSpots left: {promo}/500" if plan == "Premium" 
            else "👋 **Welcome!** Free Plan active.")
    await update.message.reply_text(text, reply_markup=await bot_logic.get_settings_keyboard(update.effective_user.id), parse_mode="Markdown")

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    await tg_app.process_update(Update.de_json(data, tg_app.bot))
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
