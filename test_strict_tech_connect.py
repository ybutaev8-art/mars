# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"

BOT_USERNAME = "txkmrobot"
CHANNEL_ID = -1004327901839

async def main():
    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        print("[1] Telethon client connected.")
        bot = await client.get_entity(BOT_USERNAME)
        channel = await client.get_entity(CHANNEL_ID)

        # 1-QADAM: IKPU so'rovi
        print("\n▶️ [QADAM 1]: 'aparatda ikpu chiqyapti'")
        sent1 = await client.send_message(bot, "aparatda ikpu chiqyapti")
        await asyncio.sleep(4)
        async for m in client.iter_messages(bot, limit=2):
            if m.id > sent1.id:
                print(f"   Bot javobi 1: {m.text[:100]}... (media: {bool(m.media)})")

        # 2-QADAM: Video foyda bermadi, ustaga ula
        print("\n▶️ [QADAM 2]: 'video boyicha qildim oxshamadi usta bilan boglang'")
        sent2 = await client.send_message(bot, "video boyicha qildim oxshamadi usta bilan boglang")
        await asyncio.sleep(4)
        resp2_text = ""
        async for m in client.iter_messages(bot, limit=2):
            if m.id > sent2.id:
                resp2_text = m.text or ""
                print(f"   Bot javobi 2: {resp2_text}")

        # Tekshiramiz: Bot INN so'radimi?
        if "STIR" in resp2_text or "JSHSHIR" in resp2_text or "oylik abonent to'lovini" in resp2_text:
            print("✅ [QADAM 2 TASDIQLANDI]: Bot to'g'ridan-to'g'ri ulamasdan, avval STIR/JSHSHIR va oylik to'lovni so'radi!")
        else:
            print("❌ [XATOLIK]: Bot STIR/JSHSHIR so'ramadi!")
            return False

        # 3-QADAM: Noto'g'ri/Mavjud bo'lmagan raqam yuboramiz (99999999999999)
        print("\n▶️ [QADAM 3]: '99999999999999' (Mavjud bo'lmagan raqam)")
        sent3 = await client.send_message(bot, "99999999999999")
        await asyncio.sleep(4)
        resp3_text = ""
        async for m in client.iter_messages(bot, limit=2):
            if m.id > sent3.id:
                resp3_text = m.text or ""
                print(f"   Bot javobi 3: {resp3_text}")

        if "topilmadi" in resp3_text:
            print("✅ [QADAM 3 TASDIQLANDI]: Noto'g'ri raqam bo'yicha ma'lumot topilmaganligi aytildi va texnikka ulanmadi!")
        else:
            print("❌ [XATOLIK]: Noto'g'ri raqamga to'g'ri javob berilmadi!")
            return False

        # 4-QADAM: To'g'ri va qarzdorligi yo'q STIR yuboramiz (311790999)
        print("\n▶️ [QADAM 4]: '311790999' (ALISHER BOBO QURILISH MOLLARI DOKONI - toza)")
        sent4 = await client.send_message(bot, "311790999")
        await asyncio.sleep(5)
        resp4_text = ""
        async for m in client.iter_messages(bot, limit=2):
            if m.id > sent4.id:
                resp4_text = m.text or ""
                print(f"   Bot javobi 4: {resp4_text}")

        if "mutaxassisimizga yetkazildi" in resp4_text or "o'rganib chiqib" in resp4_text or "texnik" in resp4_text:
            print("✅ [QADAM 4 TASDIQLANDI]: Ma'lumotlar aniqlangach, mas'ul texnik mutaxassisga yetkazildi!")
        else:
            print("❌ [XATOLIK]: Texnikka yetkazilmadi!")
            return False

        # 5-QADAM: Kanal postini tekshiramiz
        print("\n▶️ [QADAM 5]: MARS TEXNIKLAR kanalidagi yangi postni tekshiramiz...")
        channel_post_text = ""
        async for m in client.iter_messages(channel, limit=1):
            channel_post_text = m.text or ""
            print(f"   Kanaldagi post matni:\n{channel_post_text}")

        if "ALISHER BOBO" in channel_post_text and "311790999" in channel_post_text and "Mavjud emas" not in channel_post_text and "Tekshirilmagan" not in channel_post_text:
            print("\n🎉🎉🎉 [100% MUVAFFAQIYATLI NATIJA]: Tiket kartochkasida Tashkilot va INN to'liq aniqlandi, 'Mavjud emas' va 'Tekshirilmagan' so'zlari butunlay yo'q qilindi!")
            return True
        else:
            print("❌ [XATOLIK]: Kanal postida ma'lumotlar to'liq emas!")
            return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
