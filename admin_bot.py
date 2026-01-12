import asyncio
import time
from datetime import date, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from subscription_db import get_all_subs, update_subscription
from payment_db import add_payment, load_payments
from stats_db import load_stats
from database import init_db
from config import PRICE
from database import get_db
from subscription_db import get_all_subs, update_subscription
from subscription_db import activate_subscription




init_db()

def days_left(user):
    if not user.get("paid_until"):
        return None
    end = date.fromisoformat(user["paid_until"])
    return (end - date.today()).days


ADMIN_ID = 515902673        # 👈 o‘zingni ID
ADMIN_BOT_TOKEN = "8455652640:AAE0Mf0haSpP_8yCjZTCKAqGQAcVF4kf02s"
SERVICE_BOT_TOKEN = "8485200508:AAEIwbb9HpGBUX_mWPGVplpxNRoXXnlSOrU"
service_bot = Bot(SERVICE_BOT_TOKEN)

bot = Bot(ADMIN_BOT_TOKEN)
dp = Dispatcher()

def is_logged_in_user(user_id: str) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM authorized_users WHERE user_id = %s",
        (user_id,)
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID


@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name

    # 1️⃣ ADMIN
    if message.from_user.id == ADMIN_ID:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🧾 Kutilayotgan to‘lovlar")],
                [KeyboardButton(text="🟢 Faol obunalar")],
                [KeyboardButton(text="🔴 Bloklangan obunalar")],
                [KeyboardButton(text="📊 Hisobotlar")],
            ],
            resize_keyboard=True
        )
        await message.answer(
            f"👋 Assalomu alaykum, {username}!\n\n"
            "Admin panelga xush kelibsiz.",
            reply_markup=kb
        )
        return

    # 2️⃣ LOGIN QILMAGAN FOYDALANUVCHI
    if not is_logged_in_user(user_id):
        await message.answer(
            "❌ Siz hali xizmat botdan login qilmagansiz.\n\n"
            "👉 Avval xizmat botga kirib login qiling."
        )
        return

    # 3️⃣ LOGIN QILGAN, LEKIN OBUNA YO‘Q
    subs = get_all_subs()
    if user_id not in subs:
        await message.answer(
            f"👋 Assalomu alaykum, {username}!\n\n"
            "💳 Siz bu bot orqali tizimga to‘lovni amalga oshirasiz.\n"
            "Iltimos, to‘lov chekini rasm sifatida yuboring."
        )
        return

    # 4️⃣ LOGIN + OBUNA BOR
    await message.answer(
        f"👋 Assalomu alaykum, {username}!\n\n"
        "📌 Sizda faol obuna mavjud."
    )


# 📸 FOYDALANUVCHI CHEK YUBORSA
@dp.message(F.photo)
async def receive_receipt(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name

    # ADMIN rasm yuborsa — o‘tkazib yuboramiz
    if message.from_user.id == ADMIN_ID:
        return

    # LOGIN QILMAGAN USER
    if not is_logged_in_user(user_id):
        await message.answer(
            "❌ Siz hali xizmat botdan login qilmagansiz."
        )
        return

    # ADMIN UCHUN TUGMALAR
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"approve:{user_id}"
            ),
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=f"reject:{user_id}"
            )
        ]
    ])

    caption = (
        "🧾 Yangi to‘lov cheki\n\n"
        f"👤 User ID: {user_id}\n"
        f"👤 Ism: {username}"
    )

    await bot.send_photo(
        ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=caption,
        reply_markup=keyboard
    )

    await message.answer(
        "✅ Chekingiz qabul qilindi.\n"
        "Admin tekshiruvdan so‘ng sizga xabar beradi."
    )


# ✅ TO‘LOVNI TASDIQLASH
@dp.callback_query(F.data.startswith("approve:"))
async def approve_payment(call: CallbackQuery):
    user_id = call.data.split(":")[1]

    activate_subscription(user_id)

    # 2️⃣ USERGA XABAR
    await bot.send_message(
        chat_id=int(user_id),
        text="✅ To‘lovingiz tasdiqlandi. Obunangiz faollashtirildi 🎉"
    )

    # 3️⃣ ADMIN CHAT
    await call.message.answer("✅ To‘lov tasdiqlandi")

    await call.answer()


    from datetime import date, timedelta

def approve_subscription(user_id: str, amount: int, period_days: int):
    start = date.today()
    end = start + timedelta(days=period_days)

    conn = get_db()
    cur = conn.cursor()

    # 1️⃣ payment tarixi
    cur.execute("""
        INSERT INTO payments (user_id, amount, period_days, approved)
        VALUES (%s, %s, %s, TRUE)
    """, (user_id, amount, period_days))

    # 2️⃣ subscription (FAOLLASHTIRISH)
    cur.execute("""
        UPDATE subscriptions
        SET status=%s, paid_until=%s
        WHERE user_id=%s
    """, ("active", end, user_id))

    conn.commit()
    conn.close()

@dp.callback_query(F.data.startswith("reject:"))
async def reject_payment(call: CallbackQuery):
    user_id = call.data.split(":")[1]

    # 1️⃣ USERGA XABAR
    await bot.send_message(
        chat_id=int(user_id),
        text="❌ Siz yuborgan to‘lov cheki rad etildi.\nIltimos, to‘g‘ri chek yuboring."
    )

    # 2️⃣ ADMIN CHATGA JAVOB
    await call.message.answer("❌ To‘lov rad etildi")

    await call.answer()


@dp.message(F.text == "📊 Hisobotlar")
async def open_stats_from_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Bugungi tushum", callback_data="stats_today")],
            [InlineKeyboardButton(text="📅 Oylik tushum", callback_data="stats_month")],
            [InlineKeyboardButton(text="👥 TOP foydalanuvchilar", callback_data="stats_top")],
            [InlineKeyboardButton(text="⏰ Muddati yaqinlar", callback_data="stats_expiring")]
        ]
    )
    await message.answer("📊 Hisobotlar bo‘limi:", reply_markup=kb)

@dp.callback_query(F.data == "stats_today")
async def stats_today(cb: CallbackQuery):
    payments = load_payments()
    today = time.strftime("%Y-%m-%d")

    total = 0
    for p in payments.values():
        day = time.strftime("%Y-%m-%d", time.localtime(p["approved_at"]))
        if day == today:
            total += p["amount"]

    await cb.message.edit_text(
        f"💰 Bugungi tushum:\n\n"
        f"Jami: {total} so‘m"
    )
    await cb.answer()

@dp.callback_query(F.data == "stats_month")
async def stats_month(cb: CallbackQuery):
    payments = load_payments()
    now = time.localtime()
    total = 0

    for p in payments.values():
        t = time.localtime(p["approved_at"])
        if t.tm_year == now.tm_year and t.tm_mon == now.tm_mon:
            total += p["amount"]

    await cb.message.edit_text(
        f"📅 Oylik tushum:\n\n"
        f"Jami: {total} so‘m"
    )
    await cb.answer()


@dp.callback_query(F.data == "stats_top")
async def stats_top(cb: CallbackQuery):
    stats = load_stats()

    top = sorted(
        stats.items(),
        key=lambda x: x[1]["total_spent"],
        reverse=True
    )[:5]

    if not top:
        await cb.message.edit_text("👥 Hozircha statistika yo‘q.")
        await cb.answer()
        return

    text = "👥 TOP foydalanuvchilar:\n\n"
    for i, (uid, s) in enumerate(top, 1):
        text += (
            f"{i}. ID: {uid}\n"
            f"   💰 {s['total_spent']} so‘m | "
            f"📨 {s['posts_sent']} post\n\n"
        )

    await cb.message.edit_text(text)
    await cb.answer()

@dp.callback_query(F.data == "stats_expiring")
async def stats_expiring(cb: CallbackQuery):
    subs = get_all_subs()
    text = "⏰ Muddati yaqin obunachilar:\n\n"
    found = False

    for uid, user in subs.items():
        if user["status"] != "active":
            continue

        left = days_left(user)
        if left is not None and left <= 3:
            found = True
            text += f"ID: {uid} — {left} kun qoldi\n"

    if not found:
        text += "Yaqin tugaydigan obuna yo‘q."

    await cb.message.edit_text(text)
    await cb.answer()

@dp.message(F.text == "🧾 Kutilayotgan to‘lovlar")
async def pending_payments(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    subs = get_all_subs()
    pending = {uid: u for uid, u in subs.items() if u["status"] == "pending"}


    if not pending:
        await message.answer("🧾 Kutilayotgan to‘lovlar yo‘q.")
        return

    for uid, user in pending.items():
        username = user.get("username", "—")

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ 30 kun tasdiqlash",
                        callback_data=f"approve_30_{uid}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Rad etish",
                        callback_data=f"reject_{uid}"
                    )
                ]
            ]
        )

        await message.answer(
            f"👤 ID: {uid}\n"
            f"👤 Username: @{username}\n"
            f"🕒 Holat: kutilmoqda",
            reply_markup=kb
        )


@dp.message(F.text == "🟢 Faol obunalar")
async def active_subscriptions(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    subs = get_all_subs()
    active = {uid: u for uid, u in subs.items() if u["status"] == "active"}


    if not active:
        await message.answer("🟢 Hozircha faol obunalar yo‘q.")
        return

    for uid, user in active.items():
        username = user.get("username", "—")
        paid_until = user.get("paid_until", "—")
        left = days_left(user)

        if left is None:
            status = "⚪ noma’lum"
        elif left > 5:
            status = f"🟢 {left} kun qoldi"
        elif 2 <= left <= 5:
            status = f"🟡 {left} kun qoldi"
        else:
            status = f"🔴 {left} kun qoldi"

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
            [InlineKeyboardButton(text="📜 To‘lovlar tarixi", callback_data=f"payments_{uid}")],
            [InlineKeyboardButton(text="⛔ Bloklash", callback_data=f"block_{uid}")]
    ]
)

        await message.answer(
            f"🟢 FAOL OBUNA\n\n"
            f"👤 ID: {uid}\n"
            f"👤 Username: @{username}\n"
            f"📅 Tugash: {paid_until}\n"
            f"⏳ Holat: {status}",
            reply_markup=kb
        )

def activate_subscription(user_id: str, days: int = 30):
    from datetime import date, timedelta
    from database import get_db

    paid_until = date.today() + timedelta(days=days)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO subscriptions (user_id, paid_until, status)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            paid_until = EXCLUDED.paid_until,
            status = EXCLUDED.status
    """, (int(user_id), paid_until, "active"))

    conn.commit()
    conn.close()



@dp.callback_query(F.data.startswith("block_"))
async def block_subscription(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Ruxsat yo‘q", show_alert=True)
        return

    user_id = cb.data.split("_")[1]
    subs = get_all_subs()
    if user_id not in subs:
        await cb.answer("Foydalanuvchi topilmadi", show_alert=True)
        return

    subs[user_id]["status"] = "blocked"
    update_subscription(user_id, "rejected")




    # Admin uchun tasdiq
    await cb.message.edit_text(
        f"⛔ OBUNA BLOKLANDI\n\n"
        f"👤 User ID: {user_id}"
    )

    # Foydalanuvchiga xabar
    await bot.send_message(
        int(user_id),
        "⛔ Obunangiz admin tomonidan bloklandi.\n"
        "Agar xato bo‘lsa, admin bilan bog‘laning."
    )

    await cb.answer("Bloklandi")

@dp.message(F.text == "🔴 Bloklangan obunalar")
async def blocked_subscriptions(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    subs = get_all_subs()
    blocked = {uid: u for uid, u in subs.items() if u["status"] == "blocked"}


    if not blocked:
        await message.answer("🔴 Bloklangan obunalar yo‘q.")
        return

    for uid, user in blocked.items():
        username = user.get("username", "—")

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔓 Qayta faollashtirish", callback_data=f"unblock_{uid}")]
            ]
        )

        await message.answer(
            f"🔴 BLOKLANGAN OBUNA\n\n"
            f"👤 ID: {uid}\n"
            f"👤 Username: @{username}",
            reply_markup=kb
        )

@dp.callback_query(F.data.startswith("payments_"))
async def user_payments_history(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Ruxsat yo‘q", show_alert=True)
        return

    user_id = int(cb.data.split("_")[1])
    payments = load_payments()

    user_payments = [
        p for p in payments.values()
        if p["user_id"] == user_id
    ]

    if not user_payments:
        await cb.message.edit_text(
            f"📜 To‘lovlar tarixi\n\n"
            f"👤 User ID: {user_id}\n\n"
            "To‘lovlar topilmadi."
        )
        await cb.answer()
        return

    text = f"📜 To‘lovlar tarixi\n\n👤 User ID: {user_id}\n\n"
    total = 0

    for i, p in enumerate(user_payments, 1):
        date_str = time.strftime(
            "%Y-%m-%d",
            time.localtime(p["approved_at"])
        )

        text += (
            f"{i}️⃣ {p['amount']} so‘m\n"
            f"📅 {date_str}\n"
            f"📆 {p['period_days']} kun\n\n"
        )
        total += p["amount"]

    text += f"💰 Jami to‘langan: {total} so‘m"

    await cb.message.edit_text(text)
    await cb.answer()


#========= MAIN ===========
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



















