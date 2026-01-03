import asyncio
from storage import storage
from funding import fetcher, analyzer

async def notify_loop(app):
    while True:
        for user in storage.users.values():
            funding_list = await fetcher.fetch_all()
            filtered = analyzer.filter_funding(user, funding_list)
            for f in filtered:
                message = f"{f['symbol']}: {f['rate']*100:.2f}%"
                try:
                    await app.bot.send_message(chat_id=user.chat_id, text=message)
                except Exception:
                    pass
        await asyncio.sleep(60)
