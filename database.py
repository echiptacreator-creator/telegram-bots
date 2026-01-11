import sqlite3
from config import DB_PATH

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # 🔹 subscriptions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER PRIMARY KEY,
        status TEXT,
        expires_at INTEGER
    )
    """)

    # 🔹 user_profiles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        created_at INTEGER
    )
    """)

    # 🔹 payments (agar ishlatilsa)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        created_at INTEGER
    )
    """)

    # 🔹 stats (agar ishlatilsa)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        key TEXT PRIMARY KEY,
        value INTEGER
    )
    """)

    conn.commit()
    conn.close()

