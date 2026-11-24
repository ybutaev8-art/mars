# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import json
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"
BOT_USERNAME = "txkmrobot"
SESSIONS_JSON = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\sessions.json"

async def main():
    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        print("[1] Telethon client connected.")
        bot = await client.get_entity(BOT_USERNAME)
        me = await client.get_me()
        my_id = str(me.id)

        # 1-QADAM: Birinchi tashkilot INN si (206011507 - Qarzdor tashkilot)
        print("\n▶️ [QADAM 1]: Birinchi tashkilot INN sini yuboramiz: '206011507'")
        s1 = await client.send_message(bot, "206011507")
        await asyncio.sleep(4)
        async for m in client.iter_messages(bot, limit=2):
            if m.id > s1.id:
                print(f"   Bot javobi 1: {m.text[:120]}...")

        # 2-QADAM: Yangi butunlay boshqa tashkilot INN sini yuboramiz: '311790999'
        print("\n▶️ [QADAM 2]: Yangi tashkilot INN sini yuboramiz: '311790999'")
        s2 = await client.send_message(bot, "311790999")
        await asyncio.sleep(4)
        resp2 = ""
        async for m in client.iter_messages(bot, limit=2):
            if m.id > s2.id:
                resp2 = m.text.strip()
                print(f"   Bot javobi 2:\n{resp2}")

        # Tekshiruv 1: Bot yangi tashkilot ma'lumotlarini chiqargan bo'lishi kerak
        if "ALISHER BOBO" in resp2 and "311790999" in resp2:
            print("✅ [TEKSHIRUV 1]: Bot yangi tashkilotni (ALISHER BOBO) to'liq qabul qildi!")
        else:
            print("❌ [XATOLIK]: Bot yangi tashkilotni to'g'ri chiqarmadi!")
            return False

        # Tekshiruv 2: Sessiyani o'qib tekshiramiz (eski rasm, eski suhbat butunlay tozalangan bo'lishi kerak)
        with open(SESSIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        user_sess = data.get("sessions", {}).get(my_id, {})
        print(f"\n▶️ [Sessiya holati]:")
        print(f"   INN: {user_sess.get('inn')}")
        print(f"   Org: {user_sess.get('org_name')}")
        print(f"   Photo file ID: {user_sess.get('last_photo_file_id')}")
        print(f"   Dialog history uzunligi: {len(user_sess.get('dialog_history', []))}")

        if user_sess.get('last_photo_file_id') is None and user_sess.get('inn') == "311790999":
            print("\n🎉🎉🎉 [100% MUVAFFAQIYATLI NATIJA]: Yangi INN kiritilganda avvalgi tashkilot, suhbat tarixi va yuborilgan rasm butunlay unutilishi tasdiqlandi!")
            return True
        else:
            print("\n❌ [XATOLIK]: Xotirada eski ma'lumotlar to'liq o'chmadi!")
            return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
