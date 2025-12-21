import aiohttp
import asyncio
from proxy import get_proxy

EXCHANGES = {
    "Binance": "https://fapi.binance.com/fapi/v1/premiumIndex",
    "Bybit": "https://api.bybit.com/v5/market/funding/history?category=linear&limit=50",
    "OKX": "https://www.okx.com/api/v5/public/funding-rate",
}

async def fetch(session, name, url):
    try:
        async with session.get(url, timeout=10) as r:
            data = await r.json()
            return name, data
    except Exception as e:
        return name, {"error": str(e)}

async def get_all_funding():
    proxy = get_proxy()

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            fetch(session, name, url)
            for name, url in EXCHANGES.items()
        ]
        results = await asyncio.gather(*tasks)

    return results

def format_funding_message(results, lang="ua"):
    lines = ["🔥 Топ funding rate:\n"]

    for name, data in results:
        if "error" in data:
            lines.append(f"❌ {name}: error")
        else:
            lines.append(f"✅ {name}: data received")

    return "\n".join(lines)
