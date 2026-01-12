from database import get_db

def get_all_subs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscriptions")
    rows = cur.fetchall()
    conn.close()

    subs = {}
    for r in rows:
        subs[str(r[0])] = {
            "username": r[1],
            "status": r[2],
            "paid_until": r[3],
            "created_at": r[4]
        }
    return subs


def update_subscription(user_id, status, paid_until=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    UPDATE subscriptions
    SET status=?, paid_until=?
    WHERE user_id=?
    """, (status, paid_until, user_id))
    conn.commit()
    conn.close()

def activate_subscription(user_id: str, days: int = 30):
    start = date.today()
    end = start + timedelta(days=days)

    conn = get_db()
    cur = conn.cursor()
    # agar oldin bo‘lmasa — qo‘shadi, bo‘lsa — yangilaydi
    cur.execute("""
        INSERT INTO subscriptions (user_id, status, paid_until)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            paid_until = EXCLUDED.paid_until
    """, ("active", end, user_id))

    conn.commit()
    conn.close()

