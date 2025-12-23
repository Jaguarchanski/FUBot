import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

# Фільтри
FREE_MAX_FUNDING = 1.5  # %
DEFAULT_FREE_EXCHANGE = "Bybit"
ALL_EXCHANGES = ["Bybit", "Binance", "FTX", "Huobi", "OKX", "KuCoin", "BingX", "Kraken", "Bitget"]

# Early bird
EARLY_BIRD_TOTAL = 500
EARLY_BIRD_DURATION_DAYS = 30
