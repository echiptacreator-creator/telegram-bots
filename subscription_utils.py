from db.database import get_conn
import time

PRICE = 30000

def ensure_user(user_id: int, username: str | None):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM subscriptions WHERE user_id = ?", (user_id,))
    if cur.fetchone():
        return False

    cur.execute("""
        INSERT INTO subscriptions (user_id, username, status, paid_until, created_at)
        VALUES (?, ?, 'pending', NULL, ?)
    """, (user_id, username, int(time.time())))

    conn.commit()
    conn.close()
    return True


def has_access(user_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT status FROM subscriptions
        WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()
    return bool(row and row[0] == "active")
