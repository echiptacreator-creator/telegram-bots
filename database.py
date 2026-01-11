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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id BIGINT PRIMARY KEY,
        status TEXT,
        paid_until TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        amount INT,
        created_at INT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS saved_groups (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        group_id BIGINT,
        name TEXT,
        type TEXT,
        saved_at INT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
