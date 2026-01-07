import os, logging, uvicorn, asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from database.db import init_db, register_user
import telegram_bot.bot as bot_logic
from scanner import run_scanner

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tg_app
    await init_db()
    asyncio.create_task(run_scanner()) # Запуск сканера
    
    tg_app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(bot_logic.start_threshold_input, pattern="^set_threshold$"),
            CallbackQueryHandler(bot_logic.start_utc_input, pattern="^set_tz_manual$")
        ],
        states={
            bot_logic.WAITING_THRESHOLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_logic.save_threshold)],
            bot_logic.WAITING_UTC: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_logic.save_utc)]
        },
        fallbacks=[CallbackQueryHandler(bot_logic.handle_callbacks, pattern="^main_menu$")]
    )
    
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(conv)
    tg_app.add_handler(CallbackQueryHandler(bot_logic.handle_callbacks))
    
    await tg_app.initialize()
    await tg_app.bot.set_webhook(url=f"{os.getenv('WEBHOOK_URL').rstrip('/')}/webhook")
    await tg_app.start()
    yield
    await tg_app.stop()

app = FastAPI(lifespan=lifespan)
tg_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plan = await register_user(user.id, user.username)
    await update.message.reply_text(f"🚀 **Funding Bot**\nPlan: {plan}", reply_markup=await bot_logic.get_settings_keyboard(user.id), parse_mode="Markdown")

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    await tg_app.process_update(Update.de_json(data, tg_app.bot))
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
