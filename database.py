import os
import psycopg2


def get_db():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(database_url)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS authorized_users (
        user_id TEXT PRIMARY KEY,
        phone TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id TEXT PRIMARY KEY,
        status TEXT,
        paid_until TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        phone TEXT,
        created_at INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_groups (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        group_id BIGINT,
        name TEXT,
        type TEXT,
        saved_at INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        user_id TEXT PRIMARY KEY,
        posts INTEGER DEFAULT 0,
        groups INTEGER DEFAULT 0
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
