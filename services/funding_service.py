import ccxt.async_support as ccxt
import logging
import os

logger = logging.getLogger(__name__)

async def get_top_funding_rates(exchange_id: str, limit: int = 10):
    """
    Fetches funding rates using a proxy from environment variables 
    to bypass geo-restrictions on Render.
    """
    proxy_url = os.getenv("PROXY_URL")
    
    config = {
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    }

    # Add proxy if available in .env
    if proxy_url:
        config['aiohttp_proxy'] = proxy_url
        logger.info(f"Using proxy for {exchange_id}")

    # Special handling for Binance URL
    if exchange_id == 'binance':
        config['urls'] = {'api': {'fapi': 'https://fapi.binance.com/fapi/v1'}}

    exchange_class = getattr(ccxt, exchange_id, None)
    if not exchange_class:
        return f"❌ Exchange {exchange_id} not supported."

    exchange = exchange_class(config)
    
    try:
        if exchange_id == 'binance':
            rates_data = await exchange.fapiPublicGetPremiumIndex()
            valid_rates = [
                (item['symbol'], float(item['lastFundingRate'])) 
                for item in rates_data if 'lastFundingRate' in item
            ]
        else:
            await exchange.load_markets()
            if exchange.has.get('fetchFundingRates'):
                rates = await exchange.fetch_funding_rates()
                valid_rates = [
                    (symbol, data['fundingRate']) 
                    for symbol, data in rates.items() 
                    if data.get('fundingRate') is not None
                ]
            else:
                # Fallback for exchanges without bulk fetch
                return f"⚠️ {exchange_id.upper()} doesn't support bulk fetch."

        if not valid_rates:
            return f"😕 No data found for {exchange_id.upper()}."

        # Sort: Highest positive rates first
        sorted_rates = sorted(valid_rates, key=lambda x: x[1], reverse=True)

        report = f"📊 **TOP-{limit} Funding: {exchange_id.upper()}**\n"
        report += "*(Rates in % per 8h/1h)*\n\n"
        
        for i, (symbol, rate) in enumerate(sorted_rates[:limit], 1):
            emoji = "🔴" if rate > 0 else "🟢"
            clean_symbol = symbol.split(':')[0].split('/')[0]
            report += f"{i}. {emoji} `{clean_symbol}`: **{rate*100:.4f}%**\n"
            
        return report

    except Exception as e:
        logger.error(f"Error fetching from {exchange_id}: {e}")
        return f"❌ Connection error with {exchange_id.upper()}. Check proxy or API status."
    finally:
        await exchange.close()
