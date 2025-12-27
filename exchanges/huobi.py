import random

async def get_funding_rates():
    return [
        {"symbol": "BTC_CQ", "rate": round(random.uniform(-0.05, 0.05), 3)},
        {"symbol": "ETH_CQ", "rate": round(random.uniform(-0.05, 0.05), 3)},
    ]
