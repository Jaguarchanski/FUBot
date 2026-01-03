import asyncio
from telegram.ext import Application
from storage import get_users
from funding import fetcher, analyzer
from config import FUNDING_THRESHOLD_FREE

async def notify_loop(app: Application):
    while True:
        users = get_users()
        if not users:
            await asyncio.sleep(5)
            continue

        data = await fetcher.fetch_all()
        for chat_id, settings in users.items():
            threshold = settings.get("threshold", FUNDING_THRESHOLD_FREE)
            messages = []
            for ex_name, rate in data.items():
                if analyzer.check_threshold(rate, threshold):
                    messages.append(f"{ex_name}: {rate}%")
            if messages:
                text = "\n".join(messages)
                try:
                    await app.bot.send_message(chat_id=chat_id, text=text)
                except:
                    pass
        await asyncio.sleep(60)  # перевірка кожну хвилину
