import asyncio
import ccxt.async_support as ccxt
import aiosqlite
import logging
import os
from database.db import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scanner")

EXCHANGE_IDS = ["binance", "bybit", "okx", "gateio", "bitget", "bingx"]

async def fetch_funding_rates(exchange_id):
    ex = None
    raw_proxy = os.getenv("PROXY_URL") 
    
    # Формуємо правильний URL для проксі (додаємо http:// якщо немає)
    proxy_url = None
    if raw_proxy:
        proxy_url = raw_proxy if raw_proxy.startswith("http") else f"http://{raw_proxy}"

    try:
        exchange_class = getattr(ccxt, exchange_id)
        config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        }
        
        # Налаштування проксі для aiohttp (двигуна CCXT)
        if proxy_url:
            config['aiohttp_proxy'] = proxy_url
            
        ex = exchange_class(config)
        logger.info(f"🔄 Fetching {exchange_id} (Proxy: {'Active' if proxy_url else 'No'})...")
        
        rates = await ex.fetch_funding_rates()
        
        async with aiosqlite.connect(DB_PATH) as db:
            for symbol, data in rates.items():
                rate_val = data.get('fundingRate')
                if rate_val is None: continue
                
                # Зберігаємо raw час (може бути ISO рядок або timestamp)
                raw_time = data.get('datetime') or data.get('timestamp')
                
                await db.execute('''
                    INSERT OR REPLACE INTO fundings (exchange, symbol, rate, next_funding_time)
                    VALUES (?, ?, ?, ?)
                ''', (exchange_id.capitalize(), symbol, rate_val * 100, str(raw_time)))
            await db.commit()
        logger.info(f"✅ Updated {exchange_id}")
            
    except Exception as e:
        logger.error(f"❌ Error {exchange_id}: {str(e)[:100]}")
    finally:
        if ex:
            await ex.close()

async def run_scanner():
    while True:
        for ex_id in EXCHANGE_IDS:
            await fetch_funding_rates(ex_id)
            await asyncio.sleep(2) # Маленька пауза між біржами
        logger.info("💤 Cycle finished. Waiting 5 min...")
        await asyncio.sleep(300)
