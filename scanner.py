import asyncio
import ccxt.async_support as ccxt
import aiosqlite
import logging
import os
from database.db import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scanner")

# Список всіх бірж
EXCHANGE_IDS = ["binance", "bybit", "okx", "gateio", "bitget", "bingx", "huobi"]

async def fetch_funding_rates(exchange_id):
    ex = None
    proxy = os.getenv("PROXY_URL") # Формат: http://user:pass@host:port
    
    try:
        exchange_class = getattr(ccxt, exchange_id)
        config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        }
        if proxy:
            config['proxies'] = {'http': proxy, 'https': proxy}
            
        ex = exchange_class(config)
        logger.info(f"🔄 Fetching {exchange_id}...")
        
        rates = await ex.fetch_funding_rates()
        
        async with aiosqlite.connect(DB_PATH) as db:
            for symbol, data in rates.items():
                rate_val = data.get('fundingRate')
                if rate_val is None: continue
                    
                rate = rate_val * 100
                # Зберігаємо також час наступного фандингу
                await db.execute('''
                    INSERT OR REPLACE INTO fundings (exchange, symbol, rate, next_funding_time)
                    VALUES (?, ?, ?, ?)
                ''', (exchange_id.capitalize(), symbol, rate, data.get('datetime')))
            await db.commit()
        logger.info(f"✅ Updated {exchange_id}")
        
    except Exception as e:
        logger.error(f"❌ Error {exchange_id}: {str(e)[:100]}")
    finally:
        if ex: await ex.close()

async def run_scanner():
    while True:
        logger.info("🚀 Starting scan cycle...")
        for ex_id in EXCHANGE_IDS:
            await fetch_funding_rates(ex_id)
            await asyncio.sleep(2) # Пауза щоб не отримати бан по IP навіть з проксі
        logger.info("💤 Cycle finished. Waiting 5 min...")
        await asyncio.sleep(300)
