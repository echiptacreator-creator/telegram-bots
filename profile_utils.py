# profile_utils.py
import json
import os
import time

FILE = "user_profiles.json"

def load_profiles():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_profile(user_id, username):
    profiles = load_profiles()
    if user_id not in profiles:
        profiles[user_id] = {
            "username": username,
            "created_at": int(time.time()),
            "phone": None,
            "cars": []
        }
        save_profiles(profiles)
    return profiles[user_id]
