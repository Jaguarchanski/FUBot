# database.py
import sqlite3
from datetime import datetime

DB_FILE = "bot.db"


def _connect():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    conn = _connect()
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


def get_user(user_id: int) -> dict:
    conn = _connect()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    if not row:
        # 🔑 АВТОСТВОРЕННЯ КОРИСТУВАЧА
        c.execute("""
            INSERT INTO users (
                user_id, language, plan, plan_expires,
                interval, threshold, exchange, timezone
            ) VALUES (?, 'uk', 'FREE', NULL, 5, 1.5, 'BingX', 'UTC')
        """, (user_id,))
        conn.commit()

        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()

    conn.close()

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


def add_or_update_user(user_id: int, **fields):
    user = get_user(user_id)

    data = {
        "language": fields.get("language", user["language"]),
        "plan": fields.get("plan", user["plan"]),
        "plan_expires": (
            fields["plan_expires"].isoformat()
            if fields.get("plan_expires")
            else user["plan_expires"].isoformat()
            if user["plan_expires"]
            else None
        ),
        "interval": fields.get("interval", user["interval"]),
        "threshold": fields.get("threshold", user["threshold"]),
        "exchange": fields.get("exchange", user["exchange"]),
        "timezone": fields.get("timezone", user["timezone"]),
    }

    conn = _connect()
    c = conn.cursor()

    c.execute("""
        UPDATE users SET
            language = ?,
            plan = ?,
            plan_expires = ?,
            interval = ?,
            threshold = ?,
            exchange = ?,
            timezone = ?
        WHERE user_id = ?
    """, (
        data["language"],
        data["plan"],
        data["plan_expires"],
        data["interval"],
        data["threshold"],
        data["exchange"],
        data["timezone"],
        user_id
    ))

    conn.commit()
    conn.close()


def get_plan(user_id: int) -> str:
    user = get_user(user_id)

    if (
        user["plan"] == "PRO"
        and user["plan_expires"]
        and user["plan_expires"] < datetime.utcnow()
    ):
        add_or_update_user(user_id, plan="FREE", plan_expires=None)
        return "FREE"

    return user["plan"]


def increment_early_bird():
    conn = _connect()
    c = conn.cursor()

    c.execute("""
        UPDATE stats
        SET value = value + 1
        WHERE key = 'early_bird'
    """)

    conn.commit()
    conn.close()


def get_early_bird_count() -> int:
    conn = _connect()
    c = conn.cursor()

    c.execute("SELECT value FROM stats WHERE key = 'early_bird'")
    row = c.fetchone()

    conn.close()
    return row[0] if row else 0
