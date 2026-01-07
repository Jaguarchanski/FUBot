import asyncio
import ccxt.async_support as ccxt
import aiosqlite
import logging
from database.db import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scanner")

EXCHANGE_IDS = ["binance", "bybit", "okx", "gateio", "mexc", "huobi", "kucoin", "bitget"]

async def fetch_funding_rates(exchange_id):
    ex = None
    try:
        exchange_class = getattr(ccxt, exchange_id)
        ex = exchange_class({'enableRateLimit': True})
        rates = await ex.fetch_funding_rates()
        
        async with aiosqlite.connect(DB_PATH) as db:
            for symbol, data in rates.items():
                rate = data.get('fundingRate', 0) * 100
                await db.execute('''
                    INSERT OR REPLACE INTO fundings (exchange, symbol, rate, next_funding_time)
                    VALUES (?, ?, ?, ?)
                ''', (exchange_id.capitalize(), symbol, rate, data.get('datetime')))
            await db.commit()
        logger.info(f"✅ Updated {exchange_id}")
    except Exception as e:
        logger.error(f"❌ Error {exchange_id}: {e}")
    finally:
        if ex: await ex.close()

async def run_scanner():
    while True:
        logger.info("🚀 Starting scan...")
        tasks = [fetch_funding_rates(ex_id) for ex_id in EXCHANGE_IDS]
        await asyncio.gather(*tasks)
        await asyncio.sleep(300) # Кожні 5 хвилин
