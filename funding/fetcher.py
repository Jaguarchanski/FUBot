import ccxt.async_support as ccxt
import asyncio
import logging
import os

PROXY_URL = os.getenv("PROXY_URL")

async def fetch_exchange_data(exchange_id):
    ex = None
    try:
        conf = {
            'options': {'defaultType': 'swap'},
            'timeout': 20000,
            'enableRateLimit': True
        }
        if PROXY_URL:
            conf['aiohttp_proxy'] = PROXY_URL
            
        ex_class = getattr(ccxt, exchange_id)
        ex = ex_class(conf)
        
        # Спроба отримати всі фандинги
        try:
            rates = await ex.fetch_funding_rates()
            return [
                {'exchange': exchange_id.upper(), 'symbol': s, 'rate': i['fundingRate'] * 100}
                for s, i in rates.items() if i.get('fundingRate') is not None
            ]
        except:
            # Якщо масовий запит не підтримується, беремо лише BTC
            # Пробуємо різні формати символів
            for sym in ['BTC/USDT:USDT', 'BTC/USDT', 'BTC-USDT']:
                try:
                    r = await ex.fetch_funding_rate(sym)
                    return [{'exchange': exchange_id.upper(), 'symbol': sym, 'rate': r['fundingRate'] * 100}]
                except:
                    continue
            return []

    except Exception as e:
        logging.error(f"Error {exchange_id}: {str(e)[:50]}")
        return []
    finally:
        if ex:
            await ex.close() # Це прибере помилки "Unclosed client session"

async def fetch_all_funding_rates():
    # Список бірж з конфігу
    from config import config
    tasks = [fetch_exchange_data(ex_id) for ex_id in config.EXCHANGES]
    results = await asyncio.gather(*tasks)
    return [item for sublist in results for item in sublist]
