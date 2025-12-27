import random

async def get_funding_rates():
    # Псевдо API, замінити на реальне
    return [
        {"symbol": "BTCUSDT", "rate": round(random.uniform(-0.05, 0.05), 3)},
        {"symbol": "ETHUSDT", "rate": round(random.uniform(-0.05, 0.05), 3)},
    ]
