from exchanges import binance, bybit, okx, ftx, huobi, kucoin, gateio, bitget, bitmart

EXCHANGES = [binance, bybit, okx, ftx, huobi, kucoin, gateio, bitget, bitmart]

async def fetch_all():
    results = {}
    for exchange in EXCHANGES:
        # Припустимо лише BTCUSDT для MVP
        rate = await exchange.get_funding_rate("BTCUSDT")
        results[exchange.__name__] = rate
    return results
