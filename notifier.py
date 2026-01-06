import asyncio
from bot import application
from storage import get_active_users

async def fetch_funding():
    # Заглушка funding, тут пізніше підключимо API бірж
    return {"Binance": 0.7, "Bybit": 1.2}

async def start_notify_loop():
    while True:
        data = await fetch_funding()
        users = get_active_users()
        for chat_id in users:
            msg = "📊 Funding Rates:\n" + "\n".join([f"{ex}: {val}%" for ex, val in data.items()])
            try:
                await application.bot.send_message(chat_id=chat_id, text=msg)
            except Exception as e:
                print(f"❌ Cannot send to {chat_id}: {e}")
        await asyncio.sleep(60)  # Перевірка кожні 60 секунд
