async def get_funding_rate():
    """
    Повертає funding rate у %
    Для тесту повертаємо випадкове значення
    """
    import random
    return round(random.uniform(0, 2), 2)
