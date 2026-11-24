# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"

DISCUSSION_GROUP = -1004332222960
BOT_USERNAME = "txkmrobot"

async def test_bridge():
    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        print("[1] Telethon client connected.")
        bot_entity = await client.get_entity(BOT_USERNAME)
        group_entity = await client.get_entity(DISCUSSION_GROUP)

        # 1. Texnik sifatida guruhdagi 75-mavzuga reply yozamiz
        print("[2] Guruhdagi 75-xabarga texnik sifatida sharh yozamiz...")
        tech_msg = await client.send_message(
            group_entity,
            "Salom! Kassa apparatingizni qayta o'chirib yoqib ko'ring, ulanish tiklanadi.",
            reply_to=75
        )
        print(f"    Guruhga yuborildi: msg_id={tech_msg.id}")
        await asyncio.sleep(4)

        # 2. Botning shaxsiy chatiga kelgan javobni tekshiramiz
        print("[3] Botning shaxsiy chatida mijozga yetib kelgan xabarni tekshiramiz...")
        found_tech_reply = False
        async for m in client.iter_messages(bot_entity, limit=3):
            txt = m.text or ""
            print(f"    Bot xabari: {txt}")
            if "Mas'ul mutaxassis" in txt or "qayta o'chirib" in txt:
                found_tech_reply = True
                break

        if found_tech_reply:
            print("✅ [BRIDGE TEST] Texnik mutaxassisning guruhdagi javobi mijozga muvaffaqiyatli yetib bordi!")
        else:
            print("❌ [BRIDGE TEST] Texnik javobi mijozga yetib bormadi!")
            return False

        # 3. Texnik suhbatni yakunlaydi (/yakun)
        print("[4] Texnik /yakun yuboradi...")
        close_msg = await client.send_message(
            group_entity,
            "/yakun",
            reply_to=75
        )
        await asyncio.sleep(4)

        # 4. Mijozga suhbat yakunlanganligi haqida xabar borganini tekshiramiz
        found_close = False
        async for m in client.iter_messages(bot_entity, limit=3):
            txt = m.text or ""
            print(f"    Bot xabari: {txt}")
            if "suhbat yakunlandi" in txt or "yakunlandi" in txt:
                found_close = True
                break

        if found_close:
            print("✅ [CLOSE TEST] Murojaat muvaffaqiyatli yakunlandi va mijozga xabar berildi!")
        else:
            print("❌ [CLOSE TEST] Yakunlash xabari kelmadi!")
            return False

        return True

if __name__ == "__main__":
    success = asyncio.run(test_bridge())
    sys.exit(0 if success else 1)
