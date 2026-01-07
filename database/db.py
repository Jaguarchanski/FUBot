import aiosqlite
import datetime
import os

DB_PATH = 'database/funding_bot.db'

async def init_db():
    # Створюємо папку для бази, якщо її немає
    os.makedirs('database', exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблиця користувачів з усіма полями за ТЗ
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            plan TEXT DEFAULT 'Free',
            expiry_date TEXT,
            threshold REAL DEFAULT 1.0,
            timezone REAL DEFAULT 0.0,
            selected_exchanges TEXT DEFAULT 'binance,bybit,okx,gateio,bitget,bingx,kucoin,mexc,htx'
        )''')
        
        # Таблиця фандингів для збереження даних сканера
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
        # Перевіряємо, чи є вже такий юзер
        async with db.execute("SELECT plan, expiry_date FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
        
        # Рахуємо загальну кількість юзерів для Early Bird
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]

        # ЛОГІКА EARLY BIRD (500 місць)
        # Якщо юзер новий АБО він Free, але ліміт 500 ще не досягнуто — даємо Premium
        if not row or (row[0] == 'Free' and total_users < 500):
            plan = "Premium"
            # Даємо 30 днів безкоштовно
            expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            
            if not row:
                await db.execute('''INSERT INTO users (user_id, username, plan, expiry_date) 
                                 VALUES (?, ?, ?, ?)''', (user_id, username, plan, expiry))
            else:
                await db.execute("UPDATE users SET plan = ?, expiry_date = ? WHERE user_id = ?", 
                                 (plan, expiry, user_id))
            await db.commit()
            return plan
        
        # Перевірка на прострочений преміум (якщо вже не Early Bird)
        plan, expiry_date = row
        if plan == "Premium" and expiry_date:
            if datetime.datetime.fromisoformat(expiry_date) < datetime.datetime.now():
                await db.execute("UPDATE users SET plan = 'Free', expiry_date = NULL WHERE user_id = ?", (user_id,))
                await db.commit()
                return "Free"
                
        return plan

async def update_user_settings(user_id, **kwargs):
    """Універсальна функція для оновлення порогу, UTC або списку бірж"""
    if not kwargs: return
    cols = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    vals = list(kwargs.values()) + [user_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {cols} WHERE user_id = ?", vals)
        await db.commit()
