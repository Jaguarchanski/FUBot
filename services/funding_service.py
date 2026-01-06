import ccxt.async_support as ccxt
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

# Налаштування проксі (якщо є)
PROXY_URL = os.getenv("PROXY_URL")

async def get_funding_rates(exchange_id: str):
    """
    Отримує ставки фінансування для конкретної біржі.
    """
    exchange_class = getattr(ccxt, exchange_id, None)
    if not exchange_class:
        logger.error(f"Біржа {exchange_id} не підтримується CCXT")
        return None

    # Ініціалізація біржі з проксі, якщо він вказаний
    config = {
        'enableRateLimit': True,
    }
    if PROXY_URL:
        config['proxies'] = {'http': PROXY_URL, 'https': PROXY_URL}
        logger.info(f"Використання проксі для {exchange_id}")

    exchange = exchange_class(config)
    
    try:
        # Спроба отримати всі ставки фінансування
        # Примітка: методи можуть відрізнятися залежно від біржі в CCXT
        funding_rates = {}
        
        if exchange_id == 'binance':
            markets = await exchange.fetch_premium_index()
            for symbol, data in markets.items():
                if 'lastFundingRate' in data:
                    funding_rates[symbol] = float(data['lastFundingRate']) * 100
        
        elif exchange_id == 'bybit':
            # Для Bybit використовуємо fetch_tickers або спеціальний метод
            tickers = await exchange.fetch_tickers()
            for symbol, ticker in tickers.items():
                if 'info' in ticker and 'fundingRate' in ticker['info']:
                    funding_rates[symbol] = float(ticker['info']['fundingRate']) * 100
        
        else:
            # Універсальний підхід для інших бірж (MEXC, Bitget тощо)
            # Багато бірж віддають фандинг через fetch_tickers в полі info
            tickers = await exchange.fetch_tickers()
            for symbol, ticker in tickers.items():
                info = ticker.get('info', {})
                # Різні біржі використовують різні назви полів
                rate = info.get('fundingRate') or info.get('funding_rate') or info.get('lastFundingRate')
                if rate is not None:
                    funding_rates[symbol] = float(rate) * 100

        return funding_rates

    except Exception as e:
        logger.error(f"Помилка при отриманні даних з {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

def get_all_exchanges():
    """Повертає список доступних бірж"""
    return ["binance", "bybit", "mexc", "bitget", "kucoin", "bingx", "gateio"]
