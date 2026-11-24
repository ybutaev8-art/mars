# -*- coding: utf-8 -*-
import os
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"
IMG_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\check_1792928519_1966874161.jpg"

async def main():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    bot = await client.get_entity("@txkmrobot")

    # Ensure in AWAITING_RECEIPT
    await client.send_message(bot, "to'lov qildim")
    await asyncio.sleep(2)

    # Send receipt photo
    sent = await client.send_file(bot, IMG_PATH, caption="Mana to'lov cheki")
    await asyncio.sleep(5)

    async for msg in client.iter_messages(bot, limit=3):
        if msg.id > sent.id:
            print("[BOT JAVOBI (Kvitansiya qabul qilindi)]:\n", msg.text)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
