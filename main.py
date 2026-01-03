from fastapi import FastAPI, Request
from telegram.ext import Application, CommandHandler
from bot import start, set_threshold
from config import BOT_TOKEN
from notifier import notify_loop
import asyncio

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# Telegram handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set_threshold", set_threshold))

# FastAPI webhook
@app.post("/webhook")
async def webhook(req: Request):
    update = await req.json()
    await application.update_queue.put(update)
    return {"ok": True}

# Background task
async def startup():
    asyncio.create_task(notify_loop(application))

@app.on_event("startup")
async def on_startup():
    await startup()
