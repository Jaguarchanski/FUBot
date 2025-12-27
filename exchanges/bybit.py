import random

async def get_funding_rates():
    return [
        {"symbol": "BTCUSD", "rate": round(random.uniform(-0.05, 0.05), 3)},
        {"symbol": "ETHUSD", "rate": round(random.uniform(-0.05, 0.05), 3)},
    ]
