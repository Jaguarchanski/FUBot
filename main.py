import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

from bot import start, set_threshold
from notifier import notify_loop
from config import BOT_TOKEN, WEBHOOK_URL, PROXY_URL

app = FastAPI()

application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set_threshold", set_threshold))

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# запуск funding loop у background
async def main():
    asyncio.create_task(notify_loop(application))
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.updater.start_polling()  # FastAPI буде отримувати webhook, polling тут можна вимкнути
    await application.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
