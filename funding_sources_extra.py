# funding_sources_extra.py
import os
import aiohttp
import asyncio

# Проксі береться зі змінних середовища
PROXY = os.getenv("PROXY_URL")  # формат: http://user:pass@ip:port
TIMEOUT = aiohttp.ClientTimeout(total=10)

async def fetch_url(url):
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        try:
            async with session.get(url, proxy=PROXY) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"{response.status} {response.reason}"}
        except Exception as e:
            return {"error": str(e)}

# Bybit
async def get_bybit_funding():
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    return await fetch_url(url)

# Binance
async def get_binance_funding():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    return await fetch_url(url)

# Bitget
async def get_bitget_funding():
    url = "https://api.bitget.com/api/v2/mix/market/funding-rate?productType=USDT-FUTURES"
    return await fetch_url(url)

# OKX
async def get_okx_funding():
    url = "https://www.okx.com/api/v5/public/funding-rate-all"
    return await fetch_url(url)

# KuCoin
async def get_kucoin_funding():
    url = "https://api-futures.kucoin.com/api/v1/funding-rate"
    return await fetch_url(url)

# Gate.io
async def get_gate_funding():
    url = "https://api.gateio.ws/api/v4/futures/usdt/funding_rate"
    return await fetch_url(url)

# HTX
async def get_htx_funding():
    url = "https://api.htx.com/linear-swap-api/v1/swap_funding_rate"
    return await fetch_url(url)

# Функція для одночасного отримання всіх бірж
async def get_all_funding():
    tasks = [
        get_bybit_funding(),
        get_binance_funding(),
        get_bitget_funding(),
        get_okx_funding(),
        get_kucoin_funding(),
        get_gate_funding(),
        get_htx_funding()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        "Bybit": results[0],
        "Binance": results[1],
        "Bitget": results[2],
        "OKX": results[3],
        "KuCoin": results[4],
        "Gate": results[5],
        "HTX": results[6],
    }

# Для тесту файлу
if __name__ == "__main__":
    data = asyncio.run(get_all_funding())
    for exchange, result in data.items():
        print(f"{exchange}: {result}\n")
