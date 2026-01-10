from db.database import get_conn
from datetime import date
from aiogram import Bot
import asyncio

bot = Bot("BOT_TOKEN")

async def subscription_watcher():
    while True:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, paid_until FROM subscriptions
            WHERE status = 'active'
        """)

        rows = cur.fetchall()

        for user_id, paid_until in rows:
            if not paid_until:
                continue

            left = (date.fromisoformat(paid_until) - date.today()).days

            if left == 1:
                await bot.send_message(user_id, "⚠️ Obuna 1 kun qoldi")

            if left < 0:
                cur.execute("""
                    UPDATE subscriptions
                    SET status='blocked'
                    WHERE user_id=?
                """, (user_id,))

        conn.commit()
        conn.close()

        await asyncio.sleep(86400)
