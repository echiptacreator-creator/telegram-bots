import sqlite3

DB_NAME = "bot.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS / SUBSCRIPTIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        status TEXT,
        paid_until TEXT,
        created_at INTEGER
    )
    """)

    # PAYMENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        period_days INTEGER,
        approved_at INTEGER,
        approved_by INTEGER,
        status TEXT
    )
    """)

    # USER STATS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id INTEGER PRIMARY KEY,
        total_payments INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0,
        posts_sent INTEGER DEFAULT 0,
        groups_used INTEGER DEFAULT 0,
        last_active INTEGER
    )
    """)

    # SAVED GROUPS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        group_id INTEGER,
        name TEXT,
        type TEXT,
        saved_at INTEGER
    )
    """)

    # USER PROFILES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        phone TEXT,
        cars TEXT,
        created_at INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS authorized_users (
        user_id TEXT PRIMARY KEY,
        phone TEXT
    )
    """)


    conn.commit()
    conn.close()
