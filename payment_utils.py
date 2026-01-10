import json
import os
import time
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAYMENTS_FILE = os.path.join(BASE_DIR, "payments.json")


def load_payments():
    if not os.path.exists(PAYMENTS_FILE):
        return {}
    try:
        with open(PAYMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_payments(data):
    with open(PAYMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_payment(user_id: int, amount: int, days: int, approved_by: int):
    payments = load_payments()

    payment_id = str(uuid.uuid4())

    payments[payment_id] = {
        "user_id": user_id,
        "amount": amount,
        "period_days": days,
        "approved_at": int(time.time()),
        "approved_by": approved_by,
        "status": "approved"
    }

    save_payments(payments)

    return payment_id
