# database.py
import sqlite3
from datetime import datetime, timedelta

DB_FILE = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY,
                 language TEXT DEFAULT 'uk',
                 plan TEXT DEFAULT 'FREE',
                 plan_expires TEXT,
                 interval INTEGER DEFAULT 5,
                 threshold REAL DEFAULT 1.5,
                 exchange TEXT DEFAULT 'Bybit',
                 timezone TEXT DEFAULT 'UTC')''')
    c.execute('CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER)')
    c.execute('INSERT OR IGNORE INTO stats (key, value) VALUES ("early_bird", 0)')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "language": row[1],
            "plan": row[2],
            "plan_expires": datetime.fromisoformat(row[3]) if row[3] else None,
            "interval": row[4],
            "threshold": row[5],
            "exchange": row[6],
            "timezone": row[7]
        }
    return None

def add_or_update_user(user_id, data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    expires = data['plan_expires'].isoformat() if data.get('plan_expires') else None
    c.execute("""INSERT OR REPLACE INTO users 
                 (user_id, language, plan, plan_expires, interval, threshold, exchange, timezone)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (user_id, data.get('language','uk'), data.get('plan','FREE'), expires,
               data.get('interval',5), data.get('threshold',1.5),
               data.get('exchange','Bybit'), data.get('timezone','UTC')))
    conn.commit()
    conn.close()

def get_plan(user_id):
    user = get_user(user_id)
    if user and user['plan'] == 'PRO' and user['plan_expires'] and user['plan_expires'] < datetime.now():
        add_or_update_user(user_id, {"plan": "FREE", "plan_expires": None})
        return "FREE"
    return user['plan'] if user else "FREE"

def increment_early_bird():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE stats SET value = value + 1 WHERE key = "early_bird"')
    conn.commit()
    conn.close()

def get_early_bird_count():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT value FROM stats WHERE key = "early_bird"')
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0
