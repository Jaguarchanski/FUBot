# database.py
import sqlite3
from datetime import datetime

DB_FILE = "bot.db"

DEFAULT_USER = {
    "language": "uk",
    "plan": "FREE",
    "plan_expires": None,
    "interval": 5,
    "threshold": 1.5,
    "exchange": "BingX",
    "timezone": "UTC"
}


def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT NOT NULL DEFAULT 'uk',
            plan TEXT NOT NULL DEFAULT 'FREE',
            plan_expires TEXT,
            interval INTEGER NOT NULL DEFAULT 5,
            threshold REAL NOT NULL DEFAULT 1.5,
            exchange TEXT NOT NULL DEFAULT 'BingX',
            timezone TEXT NOT NULL DEFAULT 'UTC'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
    """)

    c.execute("""
        INSERT OR IGNORE INTO stats (key, value)
        VALUES ('early_bird', 0)
    """)

    conn.commit()
    conn.close()


def create_user_if_not_exists(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = c.fetchone()

    if not exists:
        c.execute("""
            INSERT INTO users (
                user_id, language, plan, plan_expires,
                interval, threshold, exchange, timezone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            DEFAULT_USER["language"],
            DEFAULT_USER["plan"],
            None,
            DEFAULT_USER["interval"],
            DEFAULT_USER["threshold"],
            DEFAULT_USER["exchange"],
            DEFAULT_USER["timezone"]
        ))
        conn.commit()

    conn.close()


def get_user(user_id):
    create_user_if_not_exists(user_id)

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT language, plan, plan_expires, interval, threshold, exchange, timezone
        FROM users WHERE user_id = ?
    """, (user_id,))

    row = c.fetchone()
    conn.close()

    return {
        "language": row[0],
        "plan": row[1],
        "plan_expires": datetime.fromisoformat(row[2]) if row[2] else None,
        "interval": row[3],
        "threshold": row[4],
        "exchange": row[5],
        "timezone": row[6]
    }


def update_user(user_id, **kwargs):
    if not kwargs:
        return

    create_user_if_not_exists(user_id)

    fields = []
    values = []

    for key, value in kwargs.items():
        if key == "plan_expires" and value:
            value = value.isoformat()
        fields.append(f"{key} = ?")
        values.append(value)

    values.append(user_id)

    query = f"""
        UPDATE users SET {', '.join(fields)}
        WHERE user_id = ?
    """

    conn = get_connection()
    c = conn.cursor()
    c.execute(query, values)
    conn.commit()
    conn.close()


def get_plan(user_id):
    user = get_user(user_id)

    if user["plan"] == "PRO" and user["plan_expires"]:
        if user["plan_expires"] < datetime.utcnow():
            update_user(user_id, plan="FREE", plan_expires=None)
            return "FREE"

    return user["plan"]


def increment_early_bird():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE stats SET value = value + 1
        WHERE key = 'early_bird'
    """)
    conn.commit()
    conn.close()


def get_early_bird_count():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT value FROM stats WHERE key = 'early_bird'
    """)
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0
