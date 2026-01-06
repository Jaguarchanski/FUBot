import aiosqlite

class Storage:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    threshold REAL DEFAULT 0.1,
                    is_pro BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            await db.commit()

    async def upsert_user(self, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
            await db.execute("UPDATE users SET is_active = 1 WHERE chat_id = ?", (chat_id,))
            await db.commit()

    async def update_threshold(self, chat_id, threshold):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET threshold = ? WHERE chat_id = ?", (threshold, chat_id))
            await db.commit()

    async def get_active_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE is_active = 1") as cursor:
                return await cursor.fetchall()

db_manager = Storage()
