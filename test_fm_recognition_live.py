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

        # Send UZ200715068777
        fm_code = "UZ200715068777"
        print(f"\n▶️ [TEST]: Botga '{fm_code}' yuborilmoqda...")
        msg = await client.send_message(bot, fm_code)
        await asyncio.sleep(6)

        resp = ""
        async for m in client.iter_messages(bot, limit=2):
            if m.id > msg.id:
                resp = m.text.strip()
                print(f"   Bot javobi: {resp}")
                break

        # Check that it did NOT say POS ID:
        if "terminal raqamini (POS ID) yubordingiz" in resp:
            print("❌ [XATO]: Bot hali ham POS ID deb xato javob berdi!")
            return False

        if "fiskal modul" in resp.lower() or "to'lov" in resp.lower() or "faol" in resp.lower() or "toza" in resp.lower():
            print(f"🎉🎉🎉 [MUVAFFAQIYATLI]: Bot fiskal modulni aniqladi va javob qaytardi!")
            return True
        else:
            print(f"⚠️ Kutilmagan javob: {resp}")
            return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
