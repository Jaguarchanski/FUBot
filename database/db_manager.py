import aiosqlite
import logging

DB_PATH = "bot_database.db"

async def init_db():
    """Ініціалізація бази даних та створення таблиць, якщо вони відсутні"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблиця користувачів
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                plan TEXT DEFAULT 'free',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Таблиця підписок (якщо знадобиться для сповіщень)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                exchange TEXT,
                pair TEXT,
                threshold REAL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        await db.commit()
        logging.info("🗄 База даних та таблиці успішно ініціалізовані.")

async def get_db():
    """Повертає з'єднання з базою даних"""
    return await aiosqlite.connect(DB_PATH)
