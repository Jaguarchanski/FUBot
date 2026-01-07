import aiosqlite
import os

DB_PATH = "database/funding_bot.db"

async def init_db():
    # Створюємо папку, якщо її немає
    if not os.path.exists("database"):
        os.makedirs("database")
        
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблиця користувачів згідно з твоїм ТЗ
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                plan TEXT DEFAULT 'Free',
                threshold REAL DEFAULT 1.5,
                timezone INTEGER DEFAULT 0,
                alert_time_before TEXT DEFAULT '15m',
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_date TIMESTAMP
            )
        ''')
        
        # Глобальні налаштування для лічильника Early Bird
        await db.execute('''
            CREATE TABLE IF NOT EXISTS global_settings (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
        ''')
        
        # Встановлюємо 500 місць для Early Bird, якщо ще не встановлено
        await db.execute('''
            INSERT OR IGNORE INTO global_settings (key, value) 
            VALUES ('promo_left', 500)
        ''')
        await db.commit()

async def get_promo_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM global_settings WHERE key = 'promo_left'") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def register_user(user_id, username):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as cursor:
            existing_user = await cursor.fetchone()
            if existing_user:
                return existing_user[0]
        
        promo_left = await get_promo_count()
        plan = "Premium" if promo_left > 0 else "Free"
        
        if plan == "Premium":
            await db.execute("UPDATE global_settings SET value = value - 1 WHERE key = 'promo_left'")
        
        await db.execute(
            "INSERT INTO users (user_id, username, plan) VALUES (?, ?, ?)",
            (user_id, username, plan)
        )
        await db.commit()
        return plan
