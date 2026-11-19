# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"
LOG_FILE = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\video_tests_results.txt"

def log_test(text):
    print(text, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

async def send_and_wait(client, bot_entity, text, wait_sec=6):
    log_test(f"\n[MIJOZ]: {text}")
    sent = await client.send_message(bot_entity, text)
    sent_id = sent.id

    responses = []
    start_time = time.time()
    while time.time() - start_time < wait_sec:
        await asyncio.sleep(1.5)
        async for msg in client.iter_messages(bot_entity, limit=6):
            if msg.id > sent_id and msg.sender_id != sent.sender_id:
                if msg.id not in [r.id for r in responses]:
                    responses.append(msg)
        if responses:
            await asyncio.sleep(1.5)
            async for msg in client.iter_messages(bot_entity, limit=6):
                if msg.id > sent_id and msg.sender_id != sent.sender_id:
                    if msg.id not in [r.id for r in responses]:
                        responses.append(msg)
            break

    if responses:
        for r in sorted(responses, key=lambda x: x.id):
            media_info = f" [MEDIA: {type(r.media).__name__}]" if r.media else ""
            fwd_info = ""
            if r.fwd_from:
                fwd_info = f" [FORWARDED: {getattr(r.fwd_from, 'channel_post', '')}]"
            log_test(f"[BOT JAVOBI]{media_info}{fwd_info}:\n{r.text or '[Media fayl / Video]'}")
    else:
        log_test("[BOT JAVOBI]: (Javob kelmadi!)")

    return responses

async def main():
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except Exception:
            pass

    log_test("==================================================")
    log_test("🎥 BARCHA VIDEO DARSLIKLARNI BIRMA-BIR TEKSHIRISH")
    log_test(f"Boshlangan vaqt: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_test("==================================================")

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        log_test("XATOLIK: User avtorizatsiyadan o'tmagan!")
        return

    bot = await client.get_entity("@txkmrobot")
    log_test(f"Ulandi: @{bot.username} ({bot.first_name})")

    # Suhbatni toza boshlash
    await send_and_wait(client, bot, "/salombot", wait_sec=4)
    await asyncio.sleep(2)

    tests = [
        ("1. Oylik to'lov videosi (Post 148)", "oylik abonent to'lovini qanday to'layman video qo'llanmasi bormi"),
        ("2. Kvitansiya yuklab olish videosi (Post 151)", "clickdan kvitansiya yuklab olish videosini tashlang"),
        ("3. Yillik to'lov videosi (Post 145)", "yillik to'lovni clickdan to'lash videosi bormi"),
        ("4. Kassa soatini to'g'rilash videosi (Post 141)", "kassaning soatini to'g'rilash videosi bormi"),
        ("5. IKPU kodini to'g'rilash videosi (Post 126)", "ikpu xatoligini to'g'rilash videosi kerak"),
        ("6. Ma'lumotlarni yuklash videosi (Post 138)", "malumotlarni yuklash vediosi bormi"),
        ("7. Tovar qo'shish videosi (Post 15)", "qanday tavar qushiladi bunga tovar qo'shish videosi"),
        ("8. Tovar narxini o'zgartirish videosi (Post 140)", "tovar narxini o'zgartirish videosini tashlang"),
        ("9. Tovarni atkaz qilish videosi (Post 53)", "tovarni atkaz qilish bekor qilish videosi bormi"),
        ("10. Chek urish va Z hisobot videosi (Post 2)", "chek urish va z hisobot olish videosi"),
        ("11. Kassa dasturini yangilash videosi (Post 142)", "kassa dasturini yangilash videosi bormi"),
        ("12. 2D skaner ishlatish videosi (Post 27)", "2d skaner ishlatish videosi"),
        ("13. Markirovkani o'chirish videosi (Post 139)", "markirovkani o'chirish videosini tashlang"),
        ("14. Barcha videolar ro'yxati", "barcha video darsliklar ro'yxatini tashlang"),
    ]

    for title, query in tests:
        log_test(f"\n--- {title} ---")
        await send_and_wait(client, bot, query, wait_sec=7)
        await asyncio.sleep(2)

    log_test("\n==================================================")
    log_test("✅ BARCHA VIDEO DARSLIKLARNI TEKSHIRISH TUGADI!")
    log_test("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
