from database import get_db

def load_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_stats")
    rows = cur.fetchall()
    conn.close()

    stats = {}
    for r in rows:
        stats[str(r[0])] = {
            "total_payments": r[1],
            "total_spent": r[2],
            "posts_sent": r[3],
            "groups_used": r[4],
            "last_active": r[5]
        }
    return stats

def add_post_stat(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_stats (user_id, posts_sent)
        VALUES (%s, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET posts_sent = posts_sent + 1
    """, (user_id,))
    conn.commit()
    conn.close()


def add_group_stat(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_stats (user_id, groups_used)
        VALUES (?, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET groups_used = groups_used + 1
    """, (user_id,))
    conn.commit()
    conn.close()

