import aiosqlite
import os

DB_PATH = "database/funding_bot.db"

async def init_db():
    if not os.path.exists("database"):
        os.makedirs("database")
        
    async with aiosqlite.connect(DB_PATH) as db:
        # Основна таблиця користувачів
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                plan TEXT DEFAULT 'Free',
                threshold REAL DEFAULT 1.5,
                timezone REAL DEFAULT 0.0,
                alert_lead_time INTEGER DEFAULT 15,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Таблиця обраних бірж
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_exchanges (
                user_id INTEGER,
                exchange_name TEXT,
                is_enabled INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, exchange_name)
            )
        ''')
        await db.commit()

async def register_user(user_id, username):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as cursor:
            existing = await cursor.fetchone()
            if existing: return existing[0]
        
        # Реєстрація юзера
        await db.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        
        # Додавання всіх 9 бірж за замовчуванням
        exchanges = ["Bybit", "BingX", "Binance", "MEXC", "KuCoin", "Huobi", "Gate.io", "OKX", "Bitget"]
        for ex in exchanges:
            await db.execute("INSERT OR IGNORE INTO user_exchanges (user_id, exchange_name) VALUES (?, ?)", (user_id, ex))
            
        await db.commit()
        return "Free"
