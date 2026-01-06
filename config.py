import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", 8000))
    
    # Ліміти за ТЗ
    FREE_LIMIT = 1.5
    PRO_LIMIT = 5.0
    
    # 9 Бірж з ТЗ
    EXCHANGES = [
        'binance', 'bybit', 'okx', 'bitget', 'gateio', 
        'kucoin', 'mexc', 'huobi', 'bingx'
    ]

config = Config()
