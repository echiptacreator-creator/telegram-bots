import json
import time
from database import get_db

def load_profiles():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profiles")
    rows = cur.fetchall()
    conn.close()

    profiles = {}
    for r in rows:
        profiles[r[0]] = {
            "username": r[1],
            "phone": r[2],
            "cars": json.loads(r[3]) if r[3] else [],
            "created_at": r[4]
        }
    return profiles


def ensure_profile(user_id, username=None):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute("""
            INSERT INTO user_profiles
            (user_id, username, phone, cars, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            username,
            None,
            json.dumps([]),
            int(time.time())
        ))
        conn.commit()

        profile = {
            "username": username,
            "phone": None,
            "cars": [],
            "created_at": int(time.time())
        }
    else:
        profile = {
            "username": row[1],
            "phone": row[2],
            "cars": json.loads(row[3]) if row[3] else [],
            "created_at": row[4]
        }

    conn.close()
    return profile


def save_profiles(profiles: dict):
    conn = get_db()
    cur = conn.cursor()

    for user_id, profile in profiles.items():
        cur.execute("""
            UPDATE user_profiles
            SET phone = ?, cars = ?
            WHERE user_id = ?
        """, (
            profile.get("phone"),
            json.dumps(profile.get("cars", [])),
            user_id
        ))

    conn.commit()
    conn.close()



