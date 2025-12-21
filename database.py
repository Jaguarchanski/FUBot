# database.py
import sqlite3
from datetime import datetime

DB_FILE = "bot.db"


def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'uk',
            plan TEXT DEFAULT 'FREE',
            plan_expires TEXT,
            interval INTEGER DEFAULT 5,
            threshold REAL DEFAULT 1.5,
            exchange TEXT DEFAULT 'BingX',
            timezone TEXT DEFAULT 'UTC'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        INSERT OR IGNORE INTO stats (key, value)
        VALUES ('early_bird', 0)
    """)

    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "user_id": row[0],
        "language": row[1],
        "plan": row[2],
        "plan_expires": datetime.fromisoformat(row[3]) if row[3] else None,
        "interval": row[4],
        "threshold": row[5],
        "exchange": row[6],
        "timezone": row[7],
    }


def add_or_update_user(user_id: int, data: dict):
    user = get_user(user_id)

    payload = {
        "language": data.get("language", user["language"] if user else "uk"),
        "plan": data.get("plan", user["plan"] if user else "FREE"),
        "plan_expires": data.get("plan_expires"),
        "interval": data.get("interval", user["interval"] if user else 5),
        "threshold": data.get("threshold", user["threshold"] if user else 1.5),
        "exchange": data.get("exchange", user["exchange"] if user else "BingX"),
        "timezone": data.get("timezone", user["timezone"] if user else "UTC"),
    }

    expires = payload["plan_expires"].isoformat() if payload["plan_expires"] else None

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO users (
            user_id, language, plan, plan_expires,
            interval, threshold, exchange, timezone
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            language = excluded.language,
            plan = excluded.plan,
            plan_expires = excluded.plan_expires,
            interval = excluded.interval,
            threshold = excluded.threshold,
            exchange = excluded.exchange,
            timezone = excluded.timezone
    """, (
        user_id,
        payload["language"],
        payload["plan"],
        expires,
        payload["interval"],
        payload["threshold"],
        payload["exchange"],
        payload["timezone"],
    ))

    conn.commit()
    conn.close()


def get_plan(user_id: int):
    user = get_user(user_id)
    if not user:
        return "FREE"

    if user["plan"] == "PRO" and user["plan_expires"]:
        if user["plan_expires"] < datetime.utcnow():
            add_or_update_user(user_id, {"plan": "FREE", "plan_expires": None})
            return "FREE"

    return user["plan"]


def increment_early_bird():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE stats
        SET value = value + 1
        WHERE key = 'early_bird'
    """)

    conn.commit()
    conn.close()


def get_early_bird_count():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT value FROM stats WHERE key = 'early_bird'")
    row = c.fetchone()
    conn.close()

    return row[0] if row else 0
