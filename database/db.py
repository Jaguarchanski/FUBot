import aiosqlite
import logging

DB_PATH = "furate.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                threshold REAL DEFAULT 0.01
            )
        ''')
        await db.commit()
    logging.info("🗄 База даних FURate ініціалізована.")
