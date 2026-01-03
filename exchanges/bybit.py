async def get_funding_rate(symbol="BTCUSDT"):
    # Поки скелет, для тесту повертаємо випадкове значення
    import random
    return round(random.uniform(-0.01, 0.02), 4)  # від -1% до 2%
