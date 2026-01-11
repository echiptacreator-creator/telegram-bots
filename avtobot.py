import asyncio
import os
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    WebAppInfo
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from telethon import TelegramClient
from aiogram import Bot
from stats_db import add_post_stat, add_group_stat
from payment_db import load_payments
import time
from profile_utils import ensure_profile, load_profiles
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from collections import defaultdict
from subscription_db import get_all_subs
from config import PRICE
from database import get_db
from database import init_db
import sqlite3

init_db()

car_states = defaultdict(dict)


# ================= CONFIG =================

BOT_TOKEN = "8485200508:AAEIwbb9HpGBUX_mWPGVplpxNRoXXnlSOrU"
LOGIN_WEBAPP_URL = "https://hyperactive-lorean-zoologically.ngrok-free.dev"

API_ID = 25780325
API_HASH = "2c4cb6eee01a46dc648114813042c453"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")

ADMIN_ID = 515902673
ADMIN_BOT_TOKEN = "8455652640:AAE0Mf0haSpP_8yCjZTCKAqGQAcVF4kf02s"
admin_bot = Bot(ADMIN_BOT_TOKEN)

# ================= GURUH SAQLASH ================

def save_group(user_id, dialog, username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO saved_groups
        (user_id, group_id, name, type, saved_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        dialog.id,
        dialog.name,
        "supergroup" if dialog.is_channel else "group",
        int(time.time())
    ))
    conn.commit()
    conn.close()


# ================= GLOBAL =================

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_state = {}
user_campaigns = {}
user_clients = {}

GROUP_CACHE = {}
GROUP_CACHE_TIME = {}
CACHE_TTL = 300  # 5 daqiqa

PAGE_SIZE = 20

# ================= HELPERS =================

def get_user_phone(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT phone FROM authorized_users WHERE user_id = ?",
        (str(user_id),)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

async def main():
    print("🤖 Avtobot ishga tushdi")

    # dispatcher, router, startup ishlari
    await dp.start_polling(bot)


# 🚗 MASHINA RUSUMLARI (MASHHUR MODELLAR)

BRANDS = {
    "uz": [
        "Cobalt",
        "Spark",
        "Onix",
        "Tracker",
        "Lacetti (Gentra)",
        "Nexia 3",
        "Malibu",
        "Equinox",
        "Captiva"
    ],

    "jp": [
        "Toyota Camry",
        "Toyota Corolla",
        "Toyota Land Cruiser",
        "Lexus RX",
        "Lexus LX",
        "Nissan X-Trail",
        "Honda Accord",
        "Mazda 6",
        "Subaru Forester"
    ],

    "de": [
        "BMW 3 Series",
        "BMW 5 Series",
        "Mercedes C-Class",
        "Mercedes E-Class",
        "Audi A4",
        "Audi A6",
        "Volkswagen Passat",
        "Volkswagen Tiguan"
    ],

    "kr": [
        "Hyundai Sonata",
        "Hyundai Elantra",
        "Hyundai Tucson",
        "Kia K5",
        "Kia Sportage",
        "Kia Sorento"
    ],

    "us": [
        "Tesla Model 3",
        "Tesla Model Y",
        "Ford Mustang",
        "Ford Explorer",
        "Jeep Grand Cherokee",
        "Chevrolet Tahoe"
    ],

    "cn": [
        "Chery Tiggo 7",
        "Chery Tiggo 8",
        "Haval Jolion",
        "Geely Monjaro",
        "BYD Song Plus",
        "Jetour X70",
        "Exeed TXL"
    ]
}



def is_logged_in(user_id: int) -> bool:
    return get_user_phone(user_id) is not None


async def get_client(user_id: int) -> TelegramClient:
    if user_id in user_clients:
        return user_clients[user_id]

    phone = get_user_phone(user_id)
    if not phone:
        raise RuntimeError("User not authorized")

    session_path = os.path.join(SESSIONS_DIR, phone.replace("+", ""))
    client = TelegramClient(session_path, API_ID, API_HASH)

    await client.start()   # 🔥 MUHIM

    user_clients[user_id] = client
    return client

#================== JSONDAN GURUH OQISH ================

def load_saved_groups():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT group_id, name FROM saved_groups
    """)
    rows = cur.fetchall()
    conn.close()

    groups = []
    for gid, name in rows:
        groups.append({
            "group_id": gid,
            "name": name
        })
    
    # duplicate bo‘lsa — olib tashlaymiz
    unique = {str(g["group_id"]): g for g in groups}
    return list(unique.values())


# ================= KEYBOARDS =================

def login_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            text="🔐 Telegram login",
            web_app=WebAppInfo(url=LOGIN_WEBAPP_URL)
        )]],
        resize_keyboard=True
    )

def check_login_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Loginni tekshirish")],
            [KeyboardButton(
                text="🔐 Telegram login",
                web_app=WebAppInfo(url=LOGIN_WEBAPP_URL)
            )]
        ],
        resize_keyboard=True
    )

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Xabar yuborish")],
            [KeyboardButton(text="📂 Guruhlar katalogi")],
            [KeyboardButton(text="👤 Profil")],
            [KeyboardButton(text="🚪 Chiqish")]
        ],
        resize_keyboard=True
    )


# ================= LOGIN (TEGILMADI) =================

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    subs = get_all_subs()
    is_new = str(message.from_user.id) not in subs


    if is_new:
        if message.from_user.username:
            text = (
                "🆕 Yangi foydalanuvchi xizmat botga kirdi\n\n"
                f"👤 ID: {message.from_user.id}\n"
                f"👤 Username: @{message.from_user.username}"
            )
        else:
            text = (
                "🆕 Yangi foydalanuvchi xizmat botga kirdi\n\n"
                f"👤 ID: {message.from_user.id}\n"
                "👤 Username: yo‘q"
            )

        await admin_bot.send_message(ADMIN_ID, text)

    # 👇 pastdagi eski logika o‘zgarishsiz
    if is_logged_in(message.from_user.id):
        await message.answer(
            "✅ Tabriklayman! tizimga kirdingiz.",
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            "🔐 Avval Telegram login qiling.",
            reply_markup=check_login_menu()
        )



@dp.message(F.text.startswith("🔄"))
async def check_login_handler(message: Message):
    if is_logged_in(message.from_user.id):
        await message.answer("✅ Login tasdiqlandi!", reply_markup=main_menu())
    else:
        await message.answer("❌ Login qilinmagan.", reply_markup=login_menu())

# ================= POST JOYLASH =================

@dp.message(F.text == "➕ Xabar yuborish")
async def post_start(message: Message):

     # 🔐 OBUNA TEKSHIRUV (YANGI)
   
    subs = get_all_subs()
    user = subs.get(str(message.from_user.id))

    if not user or user["status"] != "active":

        await message.answer(
            "❌ Xizmatdan foydalanish uchun obuna kerak.\n\n"
            f"💰 Narx: {PRICE} so‘m\n"
            "💳 Karta: 9860260107680035 I. Ibrohimov"

            "👉 To‘lov chekini @shafyoradminbot ga yuboring."
        )
        return
    # 🔐 OBUNA TEKSHIRUV TUGADI

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Bitta guruhga")],
            [KeyboardButton(text="📍 Ko‘p guruhlarga")],
            [KeyboardButton(text="⬅️ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    user_state[message.from_user.id] = {"step": "choose_mode"}
    await message.answer("Rejimni tanlang:", reply_markup=keyboard)



@dp.message(F.text == "⬅️ Bekor qilish")
async def cancel_handler(message: Message):
    user_state.pop(message.from_user.id, None)

    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data.startswith("pause_"))
async def pause_campaign(cb: CallbackQuery):
    cid = int(cb.data.split("_")[1])
    campaign = user_campaigns[cb.from_user.id][cid]
    campaign["paused"] = True
    await cb.answer("⏸ Kampaniya to‘xtatildi")


@dp.callback_query(F.data.startswith("resume_"))
async def resume_campaign(cb: CallbackQuery):
    cid = int(cb.data.split("_")[1])
    campaign = user_campaigns[cb.from_user.id][cid]
    campaign["paused"] = False
    await cb.answer("▶ Kampaniya davom etmoqda")


@dp.callback_query(F.data.startswith("stop_"))
async def stop_campaign(cb: CallbackQuery):
    cid = int(cb.data.split("_")[1])
    campaign = user_campaigns[cb.from_user.id][cid]
    campaign["active"] = False
    await cb.answer("🛑 Kampaniya to‘liq to‘xtatildi")

@dp.message(F.text.in_(["📍 Bitta guruhga", "📍 Ko‘p guruhlarga"]))
async def choose_mode(message: Message):
    user_id = message.from_user.id
    now = time.time()

    loading_msg = await message.answer(
        "⏳ Guruhlar yuklanmoqda, iltimos kuting..."
    )

    client = await get_client(user_id)

    dialogs = []  # 🔥 ASOSIY RO‘YXAT

    if (
        user_id in GROUP_CACHE and
        user_id in GROUP_CACHE_TIME and
        now - GROUP_CACHE_TIME[user_id] < CACHE_TTL
    ):
        dialogs = GROUP_CACHE[user_id]
    else:
        async for d in client.iter_dialogs(limit=500):
            # eski botdagi kabi: faqat guruh va supergroup
            if d.is_group or (d.is_channel and getattr(d.entity, "megagroup", False)):
                dialogs.append(d)


        GROUP_CACHE[user_id] = dialogs
        GROUP_CACHE_TIME[user_id] = now

    if not dialogs:
        await loading_msg.edit_text("❌ Sizda guruhlar topilmadi.")
        return

    user_state[user_id] = {
        "step": "choose_channel_inline",
        "mode": "single" if "Bitta" in message.text else "multi",
        "channels": {str(d.id): d for d in dialogs},
        "selected_ids": [],
        "selected_names": []
    }

    # 🔥 pagination uchun
    user_state[user_id]["dialogs"] = dialogs
    user_state[user_id]["page"] = 0
    user_state[user_id]["_offset"] = 0

    page = dialogs[:20]   # 🔥 SHU QATOR YETISHMAYOTGAN EDI

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d.name, callback_data=f"pick_{d.id}")]
            for d in page
        ]
    )

    # 🔥 INLINE OLDINGI / KEYINGI
    if len(dialogs) > 20:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data="__prev"),
            InlineKeyboardButton(text="➡️ Keyingi", callback_data="__next")
        ])

    # 🔥 KO‘P GURUH UCHUN
    if "Ko‘p" in message.text:
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="✅ Tayyor", callback_data="done")]
        )

    # ❗ FAQAT BITTA MARTA edit_text
    await loading_msg.edit_text(
        "Guruhni tanlang:",
        reply_markup=keyboard
    )

#=============== tugma KEYINGI VA OLDNGI=========

@dp.callback_query(F.data.in_(["__prev", "__next"]))
async def inline_pages(cb: CallbackQuery):
    state = user_state.get(cb.from_user.id)
    if not state:
        await cb.answer()
        return

    dialogs = list(state["channels"].values())
    offset = state.get("_offset", 0)

    if cb.data == "__next":
        offset += 20
    else:
        offset -= 20

    if offset < 0:
        offset = 0
    if offset >= len(dialogs):
        offset = state.get("_offset", 0)

    state["_offset"] = offset
    page = dialogs[offset:offset + 20]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d.name, callback_data=f"pick_{d.id}")]
            for d in page
        ]
    )

    if len(dialogs) > 20:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data="__prev"),
            InlineKeyboardButton(text="➡️ Keyingi", callback_data="__next")
        ])

    if state["mode"] == "multi":
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="✅ Tayyor", callback_data="done")]
        )

    await cb.message.edit_reply_markup(reply_markup=keyboard)
    await cb.answer()

#====================================================================

@dp.callback_query(F.data.startswith("pick_"))
async def pick_group(cb: CallbackQuery):
    await cb.answer()  # 🔥 SHART
    user_id = str(cb.from_user.id)
    group_id = int(cb.data.split("_")[1])

    state = user_state.get(cb.from_user.id)
    if not state:
        await cb.answer()
        return

    dialog = state["channels"].get(str(group_id))

    # BITTA GURUH SAQLASH UCHUN
    if state["mode"] == "single":
        save_group(cb.from_user.id, dialog, cb.from_user.username)

  # 👈 QO‘SHILADI
    # ==============

    # KOP GURUH SAQLASH UCHUN
    if dialog.id not in state["selected_ids"]:
        state["selected_ids"].append(dialog.id)
        state["selected_names"].append(dialog.name)

        save_group(cb.from_user.id, dialog, cb.from_user.username)
          # 👈 QO‘SHILADI
    # ======================

    if not dialog:
        await cb.answer("❌ Guruh topilmadi", show_alert=True)
        return

    
    # ---- OLDINGI LOGIKA DAVOM ETADI ----
    if state["mode"] == "single":
        state["selected_ids"] = [dialog.id]
        state["selected_names"] = [dialog.name]
        state["step"] = "enter_text"

        await cb.message.edit_text(
            f"✅ Tanlandi: {dialog.name}\n\nMatnni kiriting:"
        )
        return

    if dialog.id not in state["selected_ids"]:
        state["selected_ids"].append(dialog.id)
        state["selected_names"].append(dialog.name)

    await cb.answer(f"➕ {dialog.name} qo‘shildi")


@dp.callback_query(F.data == "done")
async def done_picking(cb: CallbackQuery):
    state = user_state.get(cb.from_user.id)
    if not state or state.get("step") != "choose_channel_inline":
        await cb.answer()
        return

    if not state["selected_ids"]:
        await cb.answer("❌ Hech narsa tanlanmadi", show_alert=True)
        return

    state["step"] = "enter_text"
    await cb.message.edit_text(
        "Matnni kiriting:"
    )


@dp.message(F.text.in_(["⬅️ Oldingi", "➡️ Keyingi"]))
async def navigate(message: Message):
    state = user_state.get(message.from_user.id)
    if not state:
        return
    state["page"] += -1 if "Oldingi" in message.text else 1
    await show_page(message)

async def show_page(message: Message):
    state = user_state[message.from_user.id]
    page = state["page"]
    channels = state["channels"]

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    keyboard = [[KeyboardButton(text=ch.name)] for ch in channels[start:end]]

    if state["mode"] == "multi":
        keyboard.append([KeyboardButton(text="✅ Tayyor")])

    nav = []
    if start > 0:
        nav.append(KeyboardButton(text="⬅️ Oldingi"))
    if end < len(channels):
        nav.append(KeyboardButton(text="➡️ Keyingi"))
    if nav:
        keyboard.append(nav)

    await message.answer(
        "Kanal/guruhni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )

@dp.message(lambda m: m.from_user.id in user_state and user_state[m.from_user.id].get("step") in {
    "enter_text", "enter_interval", "enter_duration"
})
async def steps(message: Message):
    state = user_state.get(message.from_user.id)
    if not state:
        return

    step = state.get("step")

    # 1️⃣ GURUH TANLASH
    #if step == "choose_channel":
    if state["mode"] == "multi" and message.text == "✅ Tayyor":
        state["step"] = "enter_text"
        await message.answer("Matnni kiriting:", reply_markup=ReplyKeyboardRemove())
        return

        ch = next((c for c in state["channels"] if c.name == message.text), None)
        if not ch:
            return

        if state["mode"] == "single":
            state["selected_ids"] = [ch.id]
            state["selected_names"] = [ch.name]
            state["step"] = "enter_text"
            await message.answer("Matnni kiriting:", reply_markup=ReplyKeyboardRemove())
        else:
            if ch.id not in state["selected_ids"]:
                state["selected_ids"].append(ch.id)
                state["selected_names"].append(ch.name)
            await message.answer(f"✅ {ch.name} qo‘shildi")
        return

    # 2️⃣ MATN KIRITISH
    if step == "enter_text":
        state["text"] = message.text
        state["step"] = "enter_interval"
        await message.answer("Qanchada bir yuborilsin (daqiqada):")
        return

    # 3️⃣ INTERVAL
    if step == "enter_interval":
        if not message.text.isdigit():
            await message.answer("❌ Faqat raqam kiriting")
            return

        state["interval"] = int(message.text)
        state["step"] = "enter_duration"
        await message.answer("Qancha vaqt davom etsin (daqiqada):")
        return

    # 4️⃣ DAVOMIYLIK + KAMPANIYA BOSHLASH
    if step == "enter_duration":
        if not message.text.isdigit():
            await message.answer("❌ Faqat raqam kiriting")
            return

        state["duration"] = int(message.text)

        campaign = {
            "id": len(user_campaigns.get(message.from_user.id, [])),
            "channels": state["selected_ids"],
            "text": state["text"],
            "interval": state["interval"],
            "duration": state["duration"],
            "start": time.time(),
            "sent_count": 0,
            "active": True,
            "paused": False,
            "status_message_id": None,
            "chat_id": message.chat.id
        }

        # 📊 STATISTIKA — GURUHLAR SONI
        for _ in state["selected_ids"]:
            add_group_stat(message.from_user.id)

        user_campaigns.setdefault(message.from_user.id, []).append(campaign)
        asyncio.create_task(run_campaign(message.from_user.id, campaign))

        buttons = InlineKeyboardMarkup(inline_keyboard=[
    [
            InlineKeyboardButton(
                text="⏸ To‘xtatish",
                callback_data=f"pause_{campaign['id']}"
            ),
            InlineKeyboardButton(
                text="▶ Davom ettirish",
                callback_data=f"resume_{campaign['id']}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🛑 To‘liq to‘xtatish",
                callback_data=f"stop_{campaign['id']}"
            )
        ]
    ])

        campaign["buttons"] = buttons  # 🔥 ENG MUHIM QATOR


        msg = await message.answer(
            f"🚀 Kampaniya boshlandi!\n\n"
            f"💬 Xabar:\n{campaign['text']}\n"
            f"⏱ Interval: {campaign['interval']} daqiqa\n"
            f"🕒 Boshlangan: hozir\n"
            f"📊 Yuborildi: 0",
            reply_markup=buttons
        )

        campaign["status_message_id"] = msg.message_id

        await message.answer(
            "📋 Asosiy menyu:",
            reply_markup=main_menu()
        )

        user_state.pop(message.from_user.id)
        return

async def run_campaign(user_id: int, campaign: dict):
    client = await get_client(user_id)

    end_time = campaign["start"] + campaign["duration"] * 60

    while campaign["active"] and time.time() < end_time:
        if campaign["paused"]:
            await asyncio.sleep(3)
            continue

        for ch in campaign["channels"]:
            if not campaign["active"]:
                break

            await client.send_message(ch, campaign["text"])
            campaign["sent_count"] += 1
            
            # 📊 STATISTIKA — POST YUBORILDI
            add_post_stat(user_id)

            # status yangilash
            if campaign.get("status_message_id"):
                await bot.edit_message_text(
                    chat_id=campaign["chat_id"],
                    message_id=campaign["status_message_id"],
                    text=(
                        f"🚀 Kampaniya ishlayapti\n\n"
                        f"💬 Xabar:\n{campaign['text']}\n"
                        f"⏱ Interval: {campaign['interval']} daqiqa\n"
                        f"🕒 Boshlangan: {int((time.time() - campaign['start']) // 60)} daqiqa oldin\n"
                        f"📊 Yuborildi: {campaign['sent_count']}"
                    ),
                    reply_markup=campaign["buttons"]
                )

        # 🔥 MANA SHU QATOR YETISHMAYOTGANDI
        await asyncio.sleep(campaign["interval"] * 60)

    campaign["active"] = False

# ======== GURUHLAR KATALOGI ==============

@dp.message(F.text == "📂 Guruhlar katalogi")
async def show_group_catalog(message: Message):

     # 🔐 OBUNA TEKSHIRUV (YANGI)
    
    subs = get_all_subs()
    user = subs.get(str(message.from_user.id))

    if not user or user["status"] != "active":
        await message.answer(
            "❌ Xizmatdan foydalanish uchun obuna kerak.\n\n"
            f"💰 Narx: {PRICE} so‘m\n"
            "👉 To‘lov chekini @shafyoradminbot ga yuboring."
        )
        return

        await message.answer(
            "❌ Xizmatdan foydalanish uchun obuna kerak.\n\n"
            f"💰 Narx: {PRICE} so‘m\n"
            "💳 Karta: 9860260107680035 I. Ibrohimov"
            
            "👉 To‘lov chekini @shafyoradminbot ga yuboring."
        )
        return
    # 🔐 OBUNA TEKSHIRUV TUGADI

    groups = load_saved_groups()

    if not groups:
        await message.answer("📭 Hozircha katalog bo‘sh.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=g["name"],
                    callback_data=f"catalog_{g['group_id']}"
                )
            ]
            for g in groups[:20]
        ]
    )

    await message.answer(
        "📂 Tavsiya etiladigan guruhlar:",
        reply_markup=keyboard
    )

#============ GURUHLAR CALLBACKI =================

@dp.callback_query(F.data.startswith("catalog_"))
async def join_catalog_group(cb: CallbackQuery):
    group_id = int(cb.data.split("_")[1])
    client = await get_client(cb.from_user.id)

    try:
        entity = await client.get_entity(group_id)
    except Exception:
        await cb.answer("❌ Guruh topilmadi", show_alert=True)
        return

    # 1️⃣ Agar public bo‘lsa — username orqali
    if getattr(entity, "username", None):
        link = f"https://t.me/{entity.username}"
        await cb.message.answer(f"🔗 Guruhga qo‘shilish havolasi:\n{link}")
        await cb.answer()
        return

    # 2️⃣ Aks holda invite link olishga urinamiz
    try:
        invite = await client.export_chat_invite_link(entity)
        await cb.message.answer(
            f"🔗 Guruhga qo‘shilish havolasi:\n{invite}"
        )
        await cb.answer()
        return
    except Exception:
        # kim saqlaganini topamiz
        saved_by = None
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id FROM saved_groups
                WHERE group_id = ?
                LIMIT 1
            """, (group_id,))
            row = cur.fetchone()
            conn.close()

            saved_by = row[0] if row else None

        except Exception:
            pass

        if saved_by:
            contact = f"Telegram ID: {saved_by}"
            await cb.message.answer(
                "🔒 Bu guruh yopiq (private).\n\n"
                "👉 Ushbu guruhni katalogga qo‘shgan foydalanuvchidan "
                "taklif havolasini so‘rashingiz mumkin:\n\n"
                f"👤 {contact}"
            )
        else:
            await cb.message.answer(
                "🔒 Bu guruh yopiq (private).\n"
                "Taklif havolasi topilmadi."
            )



#============ PROFIL ================

@dp.message(F.text == "👤 Profil")
async def show_profile(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username

    # 🔽 PROFILNI TA’MINLAYMIZ (YANGI)
    profile = ensure_profile(user_id, username)

    # 📂 OBUNA MA’LUMOTI
    subs = get_all_subs()
    user_sub = subs.get(user_id)

    if not user_sub:
        sub_text = "❌ Obuna yo‘q"
    else:
        status = user_sub.get("status", "—")
        paid_until = user_sub.get("paid_until", "—")

        if status == "active":
            sub_text = f"🟢 Faol\n📅 {paid_until} gacha"
        elif status == "pending":
            sub_text = "🕒 To‘lov kutilmoqda"
        else:
            sub_text = "🔴 Bloklangan"

    # 💳 TO‘LOVLAR
    payments = load_payments()
    user_payments = [
        p for p in payments.values()
        if p["user_id"] == int(user_id)
    ]

    total_paid = sum(p["amount"] for p in user_payments)
    payments_count = len(user_payments)

    # 🚗 MASHINALAR (JSON'DAN O‘QIYMIZ)
    cars = profile.get("cars", [])

    if not cars:
        cars_text = "🚗 Mashinalar:\n\nHali mashina qo‘shilmagan."
    else:
        cars_text = "🚗 Mashinalaringiz:\n\n"
        for i, car in enumerate(cars, 1):
            cars_text += (
                f"   🚕 Rusum: {car['brand']}\n"
                f"   🎨 Rang: {car['color']}\n"
                f"   ⛽ Yoqilg‘i: {car['fuel']}\n"
                f"   🔢 Raqam: {car['plate']}\n\n"
        )



    # 📱 TELEFON (YANGI)
    phone = profile.get("phone")
    if phone:
        phone_text = f"📱 Telefon: {phone}"
        kb = None
    else:
        phone_text = "📱 Telefon: kiritilmagan"
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
                [KeyboardButton(text="⬅️ Ortga")]
            ],
            resize_keyboard=True
        )

    text = (
        "👤 *Sizning profilingiz*\n\n"
        f"{phone_text}\n\n"
        f"🧾 Obuna:\n{sub_text}\n\n"
        f"💳 To‘lovlar:\n"
        f"• Soni: {payments_count} ta\n"
        f"• Jami: {total_paid} so‘m\n\n"
        f"{cars_text}"
    )

    # ✅ MANA SHU YERDA TUGMA YARATILADI
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Mashina qo‘shish", callback_data="add_car")]
        ]
    )

    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.message(F.contact)
async def save_phone(message: Message):
    user_id = str(message.from_user.id)
    phone = message.contact.phone_number
    username = message.from_user.username

    profiles = load_profiles()
    profile = profiles.get(user_id)

    if not profile:
        profile = ensure_profile(user_id, username)
        profiles = load_profiles()

    profile["phone"] = phone
    save_profiles(profiles)

    await message.answer(
        "✅ Telefon raqamingiz saqlandi.\n"
        "Profilingiz yangilandi."
    )

@dp.callback_query(F.data == "add_car")
async def add_car_start(cb: CallbackQuery):
    await cb.message.edit_reply_markup(reply_markup=None)  # 👈 O‘CHDI
    car_states[cb.from_user.id] = {}

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 Ommabop", callback_data="brand_group_uz")],
            [InlineKeyboardButton(text="🇯🇵 Yapon", callback_data="brand_group_jp")],
            [InlineKeyboardButton(text="🇩🇪 Nemis", callback_data="brand_group_de")],
            [InlineKeyboardButton(text="🇰🇷 Koreys", callback_data="brand_group_kr")],
            [InlineKeyboardButton(text="🇺🇸 Amerika", callback_data="brand_group_us")],
            [InlineKeyboardButton(text="🇨🇳 Xitoy", callback_data="brand_group_cn")],
            [InlineKeyboardButton(text="➕ Boshqa", callback_data="brand_other")]
        ]
    )

    await cb.message.answer("🚗 Mashina rusumi guruhini tanlang:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("brand_group_"))
async def choose_brand(cb):
    await cb.message.edit_reply_markup(reply_markup=None)  # 👈 O‘CHDI

    group = cb.data.replace("brand_group_", "")

    if group == "other":
        await cb.message.answer("✍️ Mashina rusumini yozing:")
        car_states[cb.from_user.id]["awaiting_brand_text"] = True
        await cb.answer()
        return

    brands = BRANDS.get(group)
    if not brands:
        await cb.answer("Xatolik", show_alert=True)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=b, callback_data=f"brand_{b}")]
            for b in brands
        ]
    )

    await cb.message.answer("🚗 Mashina rusumini tanlang:", reply_markup=kb)
    await cb.answer()


COLORS = [
    "Oq", "Qora", "Kulrang", "Kumush", "Qizil",
    "Ko‘k", "Yashil", "Sariq", "Jigarrang", "Bej", "Boshqa"
]

@dp.callback_query(F.data.startswith("brand_"))
async def brand_selected(cb: CallbackQuery):
    await cb.message.edit_reply_markup(reply_markup=None)

    brand = cb.data.replace("brand_", "")
    car_states[cb.from_user.id]["brand"] = brand

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c, callback_data=f"color_{c}")]
            for c in COLORS
        ]
    )

    await cb.message.answer("🎨 Rangni tanlang:", reply_markup=kb)
    await cb.answer()

FUELS = ["Benzin","Metan","Propan","Elektr","Gibrid","Dizel"]

@dp.callback_query(F.data.startswith("color_"))
async def color_selected(cb: CallbackQuery):
    await cb.message.edit_reply_markup(reply_markup=None)

    color = cb.data.replace("color_", "")
    car_states[cb.from_user.id]["color"] = color

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f, callback_data=f"fuel_{f}")]
            for f in FUELS
        ]
    )

    await cb.message.answer("⛽ Yoqilg‘i turini tanlang:", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("fuel_"))
async def fuel_selected(cb: CallbackQuery):
    await cb.message.edit_reply_markup(reply_markup=None)

    fuel = cb.data.replace("fuel_", "")
    car_states[cb.from_user.id]["fuel"] = fuel

    await cb.message.answer(
        "🚘 Davlat raqamini kiriting\nMasalan: 01A123BC"
    )
    await cb.answer()


@dp.message(F.text)
async def plate_entered(message: Message):
    state = car_states.get(message.from_user.id)

    if not state or "fuel" not in state:
        return

    plate = message.text.strip().upper()
    state["plate"] = plate

    text = (
        "🚗 Mashina ma’lumotlari:\n\n"
        f"Rusum: {state['brand']}\n"
        f"Rang: {state['color']}\n"
        f"Yoqilg‘i: {state['fuel']}\n"
        f"Davlat raqami: {state['plate']}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="save_car")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_car")]
        ]
    )

    await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "save_car")
async def save_car(cb: CallbackQuery):
    await cb.message.edit_reply_markup(reply_markup=None)

    user_id = str(cb.from_user.id)
    username = cb.from_user.username

    profiles = load_profiles()

    # agar profil yo‘q bo‘lsa — yaratamiz
    if user_id not in profiles:
        profiles[user_id] = {
            "username": username,
            "created_at": int(time.time()),
            "phone": None,
            "cars": []
        }

    car = car_states.get(cb.from_user.id)
    if not car:
        await cb.answer("Xatolik", show_alert=True)
        return

    car_data = {
        "id": f"car_{len(profiles[user_id]['cars']) + 1}",
        "brand": car["brand"],
        "color": car["color"],
        "fuel": car["fuel"],
        "plate": car["plate"],
        "added_at": int(time.time())
    }

    profiles[user_id]["cars"].append(car_data)

    save_profiles(profiles)  # 👈 ENDI ANIQ YOZILADI

    car_states.pop(cb.from_user.id, None)

    await cb.message.edit_text("✅ Mashina muvaffaqiyatli qo‘shildi!")
    await cb.answer()



# ================= RUN =================

#@dp.message()
#async def fallback_handler(message: Message):
#    await message.answer(
#        "📋 Asosiy menyu:",
#        reply_markup=main_menu()
#    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())








