from exchanges import binance, bybit, okx, bitget, gateio, kucoin, mexc, huobi, bingx

EXCHANGES = [binance, bybit, okx, bitget, gateio, kucoin, mexc, huobi, bingx]

async def fetch_all():
    results = {}
    for ex in EXCHANGES:
        try:
            rate = await ex()
            results[ex.__name__] = rate
        except Exception as e:
            results[ex.__name__] = None
    return results
