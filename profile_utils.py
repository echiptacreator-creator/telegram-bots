import json
import time
from database import get_db

def ensure_profile(user_id: str, username: str | None):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id, username, phone, cars FROM user_profiles WHERE user_id = %s",
        (user_id,)
    )
    row = cur.fetchone()

    if row:
        profile = {
            "user_id": row[0],
            "username": row[1],
            "phone": row[2],
            "cars": row[3] or []
        }
    else:
        profile = {
            "user_id": user_id,
            "username": username,
            "phone": None,
            "cars": []
        }

        cur.execute(
            """
            INSERT INTO user_profiles (user_id, username, phone, cars, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                username,
                None,
                json.dumps([]),
                int(time.time())
            )
        )
        conn.commit()

    cur.close()
    conn.close()
    return profile
