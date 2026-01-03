import asyncio
from bot import bot
from funding import fetcher, analyzer

async def notify_loop():
    while True:
        funding_data = await fetcher.fetch_all()
        alerts = analyzer.filter_alerts(funding_data)
        for chat_id, exchange, rate in alerts:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"📢 Funding alert on {exchange}: {rate*100:.2f}%"
                )
            except Exception as e:
                print(f"Failed to send message to {chat_id}: {e}")
        await asyncio.sleep(60)  # перевірка кожну хвилину
