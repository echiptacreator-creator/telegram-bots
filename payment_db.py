import time
from database import get_db

def add_payment(user_id, amount, days, approved_by):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO payments
    (user_id, amount, period_days, approved_at, approved_by, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        amount,
        days,
        int(time.time()),
        approved_by,
        "approved"
    ))
    conn.commit()
    conn.close()


def load_payments():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM payments")
    rows = cur.fetchall()
    conn.close()

    payments = {}
    for r in rows:
        payments[r[0]] = {
            "user_id": r[1],
            "amount": r[2],
            "period_days": r[3],
            "approved_at": r[4],
            "approved_by": r[5],
            "status": r[6]
        }
    return payments
