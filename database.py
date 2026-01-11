import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # === OBUNALAR ===
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id BIGINT PRIMARY KEY,
        status TEXT,
        paid_until DATE,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)

    # === USER PROFILE ===
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)

    # === AUTH USERS ===
    cur.execute("""
    CREATE TABLE IF NOT EXISTS authorized_users (
        user_id BIGINT PRIMARY KEY,
        phone TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)

    # === SAVED GROUPS ===
    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_groups (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        group_id BIGINT,
        name TEXT,
        type TEXT,
        saved_at BIGINT
    );
    """)

    # === PAYMENTS (agar ishlatyapsan) ===
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        amount BIGINT,
        created_at BIGINT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()






