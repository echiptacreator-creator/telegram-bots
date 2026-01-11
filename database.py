import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("postgresql://postgres:FMGmkhnZAhcDMkFfLYVBwsGBcrLGEffF@nozomi.proxy.rlwy.net:49721/railway")

def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # 🔐 authorized_users (JSON o‘rniga)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS authorized_users (
        user_id INTEGER PRIMARY KEY,
        phone TEXT,
        created_at INTEGER
    )
    """)
    
    # saved_groups
    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_groups (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        group_id BIGINT,
        name TEXT,
        type TEXT,
        saved_at BIGINT,
        UNIQUE (user_id, group_id)
    )
    """)

    # 👤 user_profiles (phone bilan)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        phone TEXT,
        created_at INTEGER
    )
    """)

    # 📦 subscriptions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER PRIMARY KEY,
        status TEXT,
        expires_at INTEGER
    )
    """)

    # 💳 payments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        created_at INTEGER
    )
    """)

    # 📊 stats
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        key TEXT PRIMARY KEY,
        value INTEGER
    )
    """)

    conn.commit()
    cur.close()
    conn.close()





