# -*- coding: utf-8 -*-
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"

async def main():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    bot = await client.get_entity("@txkmrobot")

    # Step 1: User asks general requisites
    sent1 = await client.send_message(bot, "to'lov rekvizitini bering")
    await asyncio.sleep(4)
    async for msg in client.iter_messages(bot, limit=2):
        if msg.id > sent1.id:
            print("[BOT JAVOBI 1 (rekvizit so'rovi)]:\n", msg.text)

    # Step 2: User says "to'lov qildim"
    sent2 = await client.send_message(bot, "to'lov qildim")
    await asyncio.sleep(4)
    async for msg in client.iter_messages(bot, limit=2):
        if msg.id > sent2.id:
            print("[BOT JAVOBI 2 (to'lov qildim)]:\n", msg.text)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
