import time
from database import get_db


def ensure_profile(user_id: str, username: str):
    conn = get_db()
    cur = conn.cursor()

    # profil bor-yo‘qligini tekshiramiz
    cur.execute(
        "SELECT user_id, username, phone FROM user_profiles WHERE user_id = %s",
        (user_id,)
    )
    row = cur.fetchone()

    if row:
        profile = {
            "user_id": row[0],
            "username": row[1],
            "phone": row[2],
        }
    else:
        # yangi profil yaratamiz
        cur.execute(
            """
            INSERT INTO user_profiles (user_id, username, phone, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                username,
                None,
                int(time.time())
            )
        )
        conn.commit()

        profile = {
            "user_id": user_id,
            "username": username,
            "phone": None,
        }

    cur.close()
    conn.close()
    return profile


def load_profiles():
    """
    DB versiyada bu funksiya endi kerak emas,
    lekin avtobot import qilayotgani uchun bo‘sh qoldiramiz
    """
    return {}
