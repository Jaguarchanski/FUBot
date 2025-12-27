import random

async def get_funding_rates():
    return [
        {"symbol": "BTC-USDT", "rate": round(random.uniform(-0.05, 0.05), 3)},
        {"symbol": "ETH-USDT", "rate": round(random.uniform(-0.05, 0.05), 3)},
    ]
