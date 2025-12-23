import random
from config import EXCHANGES

def fetch_funding():
    data = []
    for ex in EXCHANGES:
        data.append({
            "exchange": ex,
            "symbol": "BTCUSDT",
            "funding": round(random.uniform(0.1, 3.5), 3),
            "next_funding_min": 60
        })
    return data
