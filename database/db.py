import aiosqlite
import datetime

DB_PATH = 'database/funding_bot.db'

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            plan TEXT DEFAULT 'Free',
            expiry_date TEXT,
            threshold REAL DEFAULT 1.0,
            timezone REAL DEFAULT 0.0,
            selected_exchanges TEXT DEFAULT 'binance,bybit,okx'
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS fundings (
            exchange TEXT,
            symbol TEXT,
            rate REAL,
            next_funding_time TEXT,
            PRIMARY KEY (exchange, symbol)
        )''')
        await db.commit()

async def register_user(user_id, username):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
            if row: return row[0]
            
        # Early Bird: перші 500 користувачів
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            count = (await c.fetchone())[0]
        
        if count < 500:
            plan = "Premium"
            expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
        else:
            plan = "Free"
            expiry = None
            
        await db.execute("INSERT INTO users (user_id, username, plan, expiry_date) VALUES (?, ?, ?, ?)",
                         (user_id, username, plan, expiry))
        await db.commit()
        return plan
