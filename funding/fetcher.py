from exchanges import bybit, binance, okx, ftx, huobi, kucoin, gateio, bitget, bitmart

EXCHANGE_MODULES = [bybit, binance, okx, ftx, huobi, kucoin, gateio, bitget, bitmart]

async def fetch_all():
    results = []
    for module in EXCHANGE_MODULES:
        data = await module.fetch_funding()
        results.extend(data)
    return results
