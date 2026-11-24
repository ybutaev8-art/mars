# -*- coding: utf-8 -*-
import asyncio
from telethon import TelegramClient

async def get_recent():
    client = TelegramClient(r"data\test_runner_session", 2040, "b18441a1ff607e10a989891a5462e627")
    await client.connect()
    bot = await client.get_entity("@txkmrobot")
    msgs = []
    async for msg in client.iter_messages(bot, limit=25):
        msgs.append(msg)
    for msg in reversed(msgs):
        sender = "BOT" if msg.sender_id == bot.id else "USER"
        media = f"[MEDIA: {type(msg.media).__name__}]" if msg.media else ""
        fwd_post = getattr(msg.fwd_from, "channel_post", None) if msg.fwd_from else None
        fwd = f"[FWD post {fwd_post}]" if fwd_post else ""
        text = (msg.text or "").replace("\n", " ")
        print(f"{sender}: {text} {media} {fwd}".strip())
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(get_recent())
