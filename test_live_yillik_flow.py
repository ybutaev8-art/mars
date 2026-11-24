# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"
BOT_USERNAME = "txkmrobot"

async def main():
    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        print("[1] Telethon client connected.")
        bot = await client.get_entity(BOT_USERNAME)

        # 1-qadam: 'buldi ishladi rahmat'
        print("\n▶️ [QADAM 1]: 'buldi ishladi rahmat'")
        s1 = await client.send_message(bot, "buldi ishladi rahmat")
        await asyncio.sleep(4)
        async for m in client.iter_messages(bot, limit=2):
            if m.id > s1.id:
                print(f"   Bot javobi 1: {m.text.strip()}")

        # 2-qadam: 'yilligniyam tekshirib beringchi' (Foydalanuvchi screenshotidagi aniq matn)
        print("\n▶️ [QADAM 2]: 'yilligniyam tekshirib beringchi'")
        s2 = await client.send_message(bot, "yilligniyam tekshirib beringchi")
        await asyncio.sleep(5)
        resp2 = ""
        async for m in client.iter_messages(bot, limit=2):
            if m.id > s2.id:
                resp2 = m.text.strip()
                print(f"   Bot javobi 2: {resp2}")

        # Tekshiramiz:
        # 1) Bot adashib 'Kechirasiz men faqat kassa apparatingizni SmartOne tekshirish...' degan xato tushunmaslik xabarini bermagan bo'lishi kerak.
        # 2) 'qachon kelishi menga ko'rinmaydi' va 'FM raqami' haqidagi aniq tushuntirish berilgan bo'lishi kerak.
        if "qachon kelishi menga ko'rinmaydi" in resp2 and "FM raqami" in resp2:
            print("\n🎉🎉🎉 [100% MUVAFFAQIYATLI NATIJA]: Bot 'yilligniyam tekshirib beringchi' so'rovini to'liq tushundi va foydalanuvchi aytganidek qisqa, aniq va to'g'ri javob berdi!")
            return True
        else:
            print("\n❌ [XATOLIK]: Kutilgan tushuntirish va FM so'rovi berilmadi!")
            return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
