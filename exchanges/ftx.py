import random

async def get_funding_rates():
    return [
        {"symbol": "BTC-PERP", "rate": round(random.uniform(-0.05, 0.05), 3)},
        {"symbol": "ETH-PERP", "rate": round(random.uniform(-0.05, 0.05), 3)},
    ]
