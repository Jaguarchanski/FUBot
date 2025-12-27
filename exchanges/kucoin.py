import random

async def get_funding_rates():
    return [
        {"symbol": "BTCUSDTM", "rate": round(random.uniform(-0.05, 0.05), 3)},
        {"symbol": "ETHUSDTM", "rate": round(random.uniform(-0.05, 0.05), 3)},
    ]
