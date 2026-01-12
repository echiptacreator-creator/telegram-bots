import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from subscription_db import get_all_subs, update_subscription
from datetime import date, timedelta
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from stats_db import load_stats
from aiogram.filters import CommandStart
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery
from aiogram import F
import time
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from payment_db import add_payment, load_payments
from database import init_db
from config import PRICE
init_db()

from datetime import date

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


def is_admin(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID


@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name
    subs = get_all_subs()

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

    # 3️⃣ BEGONA
    await message.answer(
        "❌ Siz ro‘yxatdan o‘tmagansiz.\n\n"
        "👉 Avval xizmat botga kirib /start bosing."
    )
            return


# 📸 FOYDALANUVCHI CHEK YUBORSA
@dp.message(F.photo)
async def receive_receipt(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    first_name = message.from_user.first_name

    subs = get_all_subs()
    # 1️⃣ ADMIN rasm yuborsa — e’tiborsiz qoldiramiz
    if message.from_user.id == ADMIN_ID:
        return

    # 2️⃣ BEGONA foydalanuvchi
    if user_id not in subs:
        await message.answer(
            "❌ Siz ro‘yxatdan o‘tmagansiz.\n\n"
            "👉 Avval xizmat botga /start bosing."
        )
        return

    # 3️⃣ MIJOZ — CHEKNI ADMINGA YUBORAMIZ
    caption = (
        "📥 Yangi to‘lov cheki\n\n"
        f"👤 ID: {user_id}\n"
        f"👤 Ism: {first_name}\n"
        + (f"👤 Username: @{username}\n" if username else "")
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ 30 kun tasdiqlash",
                    callback_data=f"approve_30_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject_{user_id}"
                )
            ]
        ]
    )

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption,
        reply_markup=keyboard
    )

    # 4️⃣ MIJOZGA JAVOB
    await message.answer(
        "✅ Chekingiz qabul qilindi.\n"
        "Tekshiruvdan so‘ng sizga xabar beriladi."
    )


# ✅ TO‘LOVNI TASDIQLASH
@dp.callback_query(F.data.startswith("approve_30_"))
async def approve_30(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Ruxsat yo‘q", show_alert=True)
        return

    user_id = cb.data.split("_")[2]

    subs = get_all_subs()
    if user_id not in subs:
        await cb.answer("Foydalanuvchi topilmadi", show_alert=True)
        return

    # ❗ AGAR ALLAQACHON TASDIQLANGAN BO‘LSA
    if subs[user_id]["status"] == "active":
        await cb.answer("Bu to‘lov allaqachon tasdiqlangan", show_alert=True)
        return


    from datetime import date, timedelta
    paid_until = date.today() + timedelta(days=30)

    subs[user_id]["status"] = "active"
    subs[user_id]["paid_until"] = str(paid_until)
    update_subscription(user_id, "active", str(paid_until))



    # 💰 TO‘LOVNI TARIXGA YOZAMIZ
    add_payment(
        user_id=int(user_id),
        amount=PRICE,
        days=30,
        approved_by=ADMIN_ID
        
    )
    # 1️⃣ ADMIN UCHUN – STATUS XABARI (YANGI)
    await cb.message.answer(
        "✅ TO‘LOV TASDIQLANDI\n\n"
        f"👤 User ID: {user_id}\n"
        f"📅 Tugash sanasi: {paid_until}"
    )

    # 2️⃣ MIJOZGA – ADMIN BOTDAN
    await bot.send_message(
        int(user_id),
        "✅ To‘lovingiz tasdiqlandi!\n\n"
        f"📅 Obuna muddati: {paid_until}\n"
        "🚀 Endi xizmatdan foydalanishingiz mumkin."
    )

    # 3️⃣ MIJOZGA – XIZMAT BOTDAN
    await service_bot.send_message(   # 👈 pastda tushuntiraman
        int(user_id),
        "🎉 To‘lovingiz tasdiqlandi!\n\n"
        "Endi bot funksiyalaridan foydalanishingiz mumkin."
    )

    await cb.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Ruxsat yo‘q", show_alert=True)
        return

    user_id = cb.data.split("_")[1]

    # 1️⃣ ADMIN UCHUN
    await cb.message.answer(
        "❌ TO‘LOV RAD ETILDI\n\n"
        f"👤 User ID: {user_id}"
    )

    # 2️⃣ MIJOZGA – ADMIN BOTDAN
    await bot.send_message(
        int(user_id),
        "❌ To‘lovingiz rad etildi.\n\n"
        "Iltimos, to‘lovni tekshirib qayta yuboring."
    )

    # 3️⃣ MIJOZGA – XIZMAT BOTDAN
    await service_bot.send_message(
        int(user_id),
        "⛔ To‘lov tasdiqlanmadi.\n\n"
        "Xizmatdan foydalanish vaqtincha bloklandi."
    )

    await cb.answer("Rad etildi")

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
    update_subscription(user_id, "blocked", None)




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

