import ccxt.async_support as ccxt
import logging

logger = logging.getLogger(__name__)

async def get_top_funding_rates(exchange_id: str, limit: int = 10):
    """
    Отримує топ ставок фінансування для обраної біржі.
    """
    # Динамічно отримуємо клас біржі з ccxt
    exchange_class = getattr(ccxt, exchange_id, None)
    if not exchange_class:
        return "❌ Ця біржа поки не підтримується."

    exchange = exchange_class()
    try:
        await exchange.load_markets()
        
        # Перевіряємо, чи біржа підтримує отримання ставок фінансування
        if not exchange.has.get('fetchFundingRates', False):
            return f"⚠️ Біржа {exchange_id.capitalize()} не надає загальний список ставок через API."

        # Отримуємо ставки
        rates = await exchange.fetch_funding_rates()
        
        # Відфільтровуємо лише безстрокові ф'ючерси (Perpetual) та сортуємо
        # Беремо значення fundingRate, ігноруючи None
        valid_rates = [
            (symbol, data['fundingRate']) 
            for symbol, data in rates.items() 
            if data.get('fundingRate') is not None
        ]
        
        # Сортуємо: спочатку найбільші позитивні ставки
        sorted_rates = sorted(valid_rates, key=lambda x: x[1], reverse=True)

        if not sorted_rates:
            return f"😕 На даний момент не знайдено активних ставок на {exchange_id.capitalize()}."

        report = f"📊 **Топ-{limit} ставок на {exchange_id.capitalize()}**\n"
        report += "*(у відсотках за 8 годин)*\n\n"
        
        for i, (symbol, rate) in enumerate(sorted_rates[:limit], 1):
            emoji = "🔴" if rate > 0.0001 else "🟢" # Червоний, якщо платять лонгісти
            report += f"{i}. {emoji} `{symbol}`: **{rate*100:.4f}%**\n"
            
        return report

    except Exception as e:
        logger.error(f"CCXT Error for {exchange_id}: {e}")
        return f"❌ Помилка API {exchange_id.capitalize()}: {str(e)[:50]}..."
    finally:
        await exchange.close()
