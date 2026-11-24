# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"

async def main():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    bot = await client.get_entity("@txkmrobot")

    # Reset conversation first
    await client.send_message(bot, "/reset")
    await asyncio.sleep(2)

    scenarios = [
        # Scenario 1: User gives FM, bot says toza and asks for INN, user says "hozir tashlayman"
        ("LG420230624507 mana shumi", 5),
        ("hozir tashlayman", 5),
        # Scenario 2: IKPU error test
        ("aparatim ikpu diyabdi", 6)
    ]

    for text, wait_sec in scenarios:
        print(f"\n--- [MIJOZ YUBORDI]: {text} ---")
        sent = await client.send_message(bot, text)
        sent_id = sent.id
        await asyncio.sleep(wait_sec)

        responses = []
        async for msg in client.iter_messages(bot, limit=5):
            if msg.id > sent_id and msg.sender_id != sent.sender_id:
                responses.append(msg)

        responses.reverse()
        if not responses:
            print("[BOT JAVOB BERMADI]")
        for r in responses:
            txt = r.text or ""
            media_info = ""
            if r.media:
                media_info = f" [MEDIA: {type(r.media).__name__}]"
                if hasattr(r, 'fwd_from') and r.fwd_from:
                    media_info += f" (Forwarded from channel, post_id: {r.fwd_from.channel_post})"
            print(f"[BOT JAVOBI]{media_info}:\n{txt}\n")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
