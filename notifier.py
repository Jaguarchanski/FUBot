import asyncio
from exchanges import fetch_funding

async def notify_loop(app):
    while True:
        data = fetch_funding()
        for d in data:
            if d["funding"] >= 1.5:
                await app.bot.send_message(
                    chat_id=app.bot_data["admin"],
                    text=f"{d['exchange']} | {d['symbol']} | {d['funding']}%"
                )
        await asyncio.sleep(300)
