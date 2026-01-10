# db/database.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        status TEXT,
        paid_until TEXT,
        created_at INTEGER
    )
    """)

    conn.commit()
    conn.close()
