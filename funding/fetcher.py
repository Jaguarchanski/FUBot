import ccxt.async_support as ccxt
import asyncio
import logging
from config import config

async def fetch_exchange_data(exchange_id):
    ex = None
    try:
        ex_class = getattr(ccxt, exchange_id)
        ex = ex_class({'options': {'defaultType': 'swap'}, 'timeout': 20000})
        
        # Спеціальна обробка для бірж, де fetchFundingRates не працює
        if exchange_id in ['kucoin', 'mexc', 'huobi']:
            # Для простоти беремо основні пари, якщо масовий запит не підтримується
            ticker = await ex.fetch_funding_rate('BTC/USDT:USDT')
            return [{
                'exchange': exchange_id.upper(),
                'symbol': ticker['symbol'],
                'rate': ticker['fundingRate'] * 100
            }]
        
        rates = await ex.fetch_funding_rates()
        return [
            {'exchange': exchange_id.upper(), 'symbol': s, 'rate': i['fundingRate'] * 100}
            for s, i in rates.items() if 'USDT' in s and i.get('fundingRate') is not None
        ]
    except Exception as e:
        logging.error(f"Error fetching {exchange_id}: {str(e)[:100]}")
        return []
    finally:
        if ex:
            await ex.close() # Важливо: завжди закриваємо з'єднання

async def fetch_all_funding_rates():
    # Запускаємо запити паралельно, але з контролем
    tasks = [fetch_exchange_data(ex_id) for ex_id in config.EXCHANGES]
    results = await asyncio.gather(*tasks)
    return [item for sublist in results for item in sublist]
