# main.py
import os
import asyncio
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from bot import bot, setup_handlers
from notifier import notify_loop

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()

# Налаштовуємо хендлери Telegram бота
setup_handlers(bot)

# Фоновий таск для сповіщень
@app.on_event("startup")
async def startup_event():
    # Запускаємо Telegram бота
    asyncio.create_task(bot.initialize())
    # Запускаємо notify loop
    asyncio.create_task(notify_loop(bot))

# Webhook endpoint
@app.post(f"/webhook/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = bot.types.Update.de_json(data)
    await bot.update_queue.put(update)
    return {"ok": True}

# Точка для локального запуску (тільки для дебагу)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
