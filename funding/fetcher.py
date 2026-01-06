import ccxt.async_support as ccxt
import asyncio
import logging
from config import config

async def fetch_all_funding_rates():
    tasks = []
    for ex_id in config.EXCHANGES:
        tasks.append(fetch_exchange_data(ex_id))
    
    results = await asyncio.gather(*tasks)
    # Збираємо все в один плаский список
    return [item for sublist in results for item in sublist]

async def fetch_exchange_data(exchange_id):
    try:
        ex_class = getattr(ccxt, exchange_id)
        # Використовуємо свопи (perpetual)
        ex = ex_class({'options': {'defaultType': 'swap'}})
        rates = await ex.fetch_funding_rates()
        data = []
        for symbol, info in rates.items():
            if 'USDT' in symbol:
                data.append({
                    'exchange': exchange_id.upper(),
                    'symbol': symbol,
                    'rate': info['fundingRate'] * 100
                })
        await ex.close()
        return data
    except Exception as e:
        logging.error(f"Error fetching {exchange_id}: {e}")
        return []
