import json
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(BASE_DIR, "users_stats.json")


def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_user_stats(user_id: int):
    stats = load_stats()
    uid = str(user_id)

    if uid not in stats:
        stats[uid] = {
            "total_payments": 0,
            "total_spent": 0,
            "posts_sent": 0,
            "groups_used": 0,
            "last_active": int(time.time())
        }
        save_stats(stats)

    return stats[uid]


def add_payment_stat(user_id: int, amount: int):
    stats = load_stats()
    uid = str(user_id)

    ensure_user_stats(user_id)

    stats[uid]["total_payments"] += 1
    stats[uid]["total_spent"] += amount
    stats[uid]["last_active"] = int(time.time())

    save_stats(stats)


def add_post_stat(user_id: int):
    stats = load_stats()
    uid = str(user_id)

    ensure_user_stats(user_id)

    stats[uid]["posts_sent"] += 1
    stats[uid]["last_active"] = int(time.time())

    save_stats(stats)


def add_group_stat(user_id: int):
    stats = load_stats()
    uid = str(user_id)

    ensure_user_stats(user_id)

    stats[uid]["groups_used"] += 1
    stats[uid]["last_active"] = int(time.time())

    save_stats(stats)
