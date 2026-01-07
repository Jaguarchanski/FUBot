import ccxt.pro as ccxt
import asyncio
import aiosqlite
import os
from database.db import DB_PATH

EXCHANGES = ['binance', 'bybit', 'okx', 'gateio', 'bitget', 'bingx', 'kucoin', 'mexc', 'htx']
PROXY = os.getenv("PROXY_URL")

async def fetch_exchange(ex_id):
    try:
        conf = {
            'proxies': {'http': PROXY, 'https': PROXY} if PROXY else {},
            'timeout': 30000,
            'enableRateLimit': True
        }
        ex_instance = getattr(ccxt, ex_id)(conf)
        await ex_instance.load_markets()
        rates = await ex_instance.fetch_funding_rates()
        
        async with aiosqlite.connect(DB_PATH) as db:
            for symbol, data in rates.items():
                if not data or 'fundingRate' not in data: continue
                rate_val = data['fundingRate'] * 100
                await db.execute("INSERT OR REPLACE INTO fundings (exchange, symbol, rate, next_funding_time) VALUES (?, ?, ?, ?)",
                                 (ex_id, symbol, rate_val, str(data.get('timestamp'))))
            await db.commit()
        await ex_instance.close()
    except Exception as e:
        print(f"Scanner Error on {ex_id}: {e}")

async def run_scanner():
    while True:
        tasks = [fetch_exchange(ex) for ex in EXCHANGES]
        await asyncio.gather(*tasks)
        await asyncio.sleep(60)
