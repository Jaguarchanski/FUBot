import aiosqlite
import datetime
import os

DB_PATH = 'database/funding_bot.db'

async def init_db():
    os.makedirs('database', exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            plan TEXT DEFAULT 'FREE',
            expiry_date TEXT,
            threshold REAL DEFAULT 0.1,
            timezone REAL DEFAULT 0.0,
            alert_time INTEGER DEFAULT 15,
            selected_exchanges TEXT DEFAULT 'bybit'
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS fundings (
            exchange TEXT, symbol TEXT, rate REAL, next_funding_time TEXT,
            PRIMARY KEY (exchange, symbol)
        )''')
        await db.commit()

async def register_user(user_id, username):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
        
        if not row:
            async with db.execute("SELECT COUNT(*) FROM users") as c:
                count = (await c.fetchone())[0]
            
            # Early Bird: first 500 get PREMIUM
            plan = "PREMIUM" if count < 500 else "FREE"
            expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat() if plan == "PREMIUM" else None
            exchanges = "binance,bybit,okx,gateio,bitget,bingx,kucoin,mexc,htx" if plan == "PREMIUM" else "bybit"
            
            await db.execute("INSERT INTO users (user_id, username, plan, expiry_date, selected_exchanges) VALUES (?, ?, ?, ?, ?)",
                             (user_id, username, plan, expiry, exchanges))
            await db.commit()
            return plan
        return row[0]
