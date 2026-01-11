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
