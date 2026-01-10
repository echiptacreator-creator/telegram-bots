import asyncio
from subscription_utils import load_subs, save_subs, days_left
from aiogram import Bot

SERVICE_BOT_TOKEN = "8485200508:AAEIwbb9HpGBUX_mWPGVplpxNRoXXnlSOrU"
bot = Bot(SERVICE_BOT_TOKEN)

async def subscription_watcher():
    while True:
        print("🔍 Subscription watcher tekshiruvdan o‘tyapti")
        subs = load_subs()

        for user_id, user in subs.items():
            if user["status"] != "active":
                continue

            left = days_left(user)
            if left is None:
                continue

            uid = int(user_id)

            # ⏳ 1 HAFTA QOLDI
            if left == 7:
                await bot.send_message(
                    uid,
                    "⏳ Obunangiz tugashiga 1 hafta qoldi.\n"
                    "Iltimos, to‘lovni oldindan amalga oshiring."
                )
                
            # ⏳ 5 KUN QOLDI
            if left == 5:
                await bot.send_message(
                    uid,
                    "⏳ Obunangiz tugashiga 5 kun qoldi.\n"
                    "Iltimos, to‘lovni oldindan amalga oshiring."
                )

            # ⏳ 3 KUN QOLDI
            if left == 3:
                await bot.send_message(
                    uid,
                    "⏳ Obunangiz tugashiga 3 kun qoldi.\n"
                    "Iltimos, to‘lovni oldindan amalga oshiring."
                )

            # ⏳ 1 KUN QOLDI
            elif left == 1:
                await bot.send_message(
                    uid,
                    "⚠️ Obunangiz tugashiga 1 kun qoldi!\n"
                    "Aks holda xizmat bloklanadi."
                )

            # ❌ MUDDAT TUGADI
            elif left < 0:
                user["status"] = "blocked"
                await bot.send_message(
                    uid,
                    "⛔ Obunangiz muddati tugadi.\n"
                    "Xizmat vaqtincha bloklandi."
                )

        save_subs(subs)

        # 🔁 HAR 24 SOATDA
        await asyncio.sleep(60 * 60 * 24)
