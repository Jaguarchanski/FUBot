import aiohttp

async def fetch_funding():
    url = "https://api.bybit.com/v2/public/funding/prev-funding-rate?symbol=BTCUSDT"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            # приклад: повертаємо словник з монетою і funding rate
            return [{"symbol": "BTCUSDT", "rate": float(data["result"]["funding_rate"])}]
