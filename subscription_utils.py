import json
import os
import time
from datetime import date


# 🔥 ANIQ: avtobot.py turgan papka
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBS_FILE = os.path.join(BASE_DIR, "subscriptions.json")

PRICE = 30000


def load_subs():
    if not os.path.exists(SUBS_FILE):
        return {}
    try:
        with open(SUBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_subs(data):
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_user(user_id: int, username: str | None):
    subs = load_subs()
    uid = str(user_id)

    if uid not in subs:
        subs[uid] = {
            "username": username,
            "status": "pending",
            "paid_until": None,
            "created_at": int(time.time())
        }
        save_subs(subs)
        return True   # 👈 YANGI USER

    return False      # 👈 OLDIN BOR


def has_access(user_id: int) -> bool:
    subs = load_subs()
    user = subs.get(str(user_id))
    return bool(user and user["status"] == "active")

    from datetime import date

def days_left(user: dict) -> int | None:
    if not user.get("paid_until"):
        return None

    end = date.fromisoformat(user["paid_until"])
    return (end - date.today()).days
