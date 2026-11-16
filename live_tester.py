# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\ofd_user_session"
DESKTOP_DIR = r"C:\Users\YASHNARBEK\Desktop\1"
LOG_FILE = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\live_test_results.txt"

def log_test(text):
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

async def send_and_wait(client, bot_entity, text=None, file_path=None, caption=None, wait_sec=8):
    if text:
        log_test(f"\n[MIJOZ (Sizning nomingizdan)]: {text}")
        sent = await client.send_message(bot_entity, text)
    elif file_path:
        fname = os.path.basename(file_path)
        log_test(f"\n[MIJOZ (Rasm tashladi)]: {fname} (Caption: {caption or ''})")
        sent = await client.send_file(bot_entity, file_path, caption=caption or "")
    else:
        return []

    # Wait for bot to process and respond
    sent_id = sent.id
    log_test(f"  ... Bot javobini kutmoqda ({wait_sec}s) ...")
    
    responses = []
    start_time = time.time()
    while time.time() - start_time < wait_sec:
        await asyncio.sleep(2)
        async for msg in client.iter_messages(bot_entity, limit=5):
            if msg.id > sent_id and msg.sender_id != sent.sender_id:
                if msg.id not in [r.id for r in responses]:
                    responses.append(msg)
        if responses:
            # wait a small moment in case multiple messages are sent (e.g. text + video)
            await asyncio.sleep(2)
            async for msg in client.iter_messages(bot_entity, limit=5):
                if msg.id > sent_id and msg.sender_id != sent.sender_id:
                    if msg.id not in [r.id for r in responses]:
                        responses.append(msg)
            break

    if responses:
        for r in sorted(responses, key=lambda x: x.id):
            media_info = f" [MEDIA: {type(r.media).__name__}]" if r.media else ""
            log_test(f"[BOT JAVOBI]:{media_info}\n{r.text or '[Media xabar]'}")
    else:
        log_test("[BOT JAVOBI]: (Javob kelmadi yoki kechikdi!)")

    return responses

async def run_live_tests():
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except Exception:
            pass

    log_test("==================================================")
    log_test("🚀 JONLI TEST BOSHLANDI (Quvonchbek akkauntidan)")
    log_test(f"Vaqt: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_test("==================================================")

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        log_test("XATOLIK: User avtorizatsiyadan o'tmagan!")
        return

    bot = await client.get_entity("@txkmrobot")
    log_test(f"Bot topildi: {bot.first_name} (@{bot.username})")

    # ====================================================
    # SCENARIO 1: Foydalanuvchi so'ragan test:
    # 1. "salom aparatim ishlamayabdi"
    # 2. Soati ko'rinmagan rasm
    # 3. Bot soatli rasm so'raydi -> To'liq rasm tashlanadi
    # 4. "yillikni tekshirib ber"
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 TEST 1: SALOM APARATIM ISHLAMAYABDI + RASMLAR + YILLIK TEKSHIRUV")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="salom aparatim ishlamayabdi", wait_sec=6)
    await asyncio.sleep(2)

    # Soati ko'rinmagan rasm (image_2026-10-17_20-41-02.png)
    bad_img = os.path.join(DESKTOP_DIR, "image_2026-10-17_20-41-02.png")
    if os.path.exists(bad_img):
        await send_and_wait(client, bot, file_path=bad_img, caption="mana rasmi", wait_sec=6)
        await asyncio.sleep(2)

    # To'liq rasm (photo_1_2026-11-13_14-31-54.jpg)
    good_img = os.path.join(DESKTOP_DIR, "photo_1_2026-11-13_14-31-54.jpg")
    if os.path.exists(good_img):
        await send_and_wait(client, bot, file_path=good_img, caption="mana ekrani soati bilan", wait_sec=6)
        await asyncio.sleep(2)

    # Yillikni tekshirish
    await send_and_wait(client, bot, text="yillikni tekshirib ber", wait_sec=6)
    await asyncio.sleep(2)

    # FM raqami yuboriladi
    await send_and_wait(client, bot, text="VG298430008670", wait_sec=6)
    await asyncio.sleep(3)

    # ====================================================
    # SCENARIO 2: Dialekt: "aparatimni qushib beriyla urommayabmiz"
    # 1. /salombot
    # 2. "aparatimni qushib beriyla urommayabmiz"
    # 3. INN yuboriladi (311790999)
    # 4. Oshibka rasmi yuboriladi (photo_5)
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 TEST 2: SHEVADA: 'aparatimni qushib beriyla urommayabmiz'")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="aparatimni qushib beriyla urommayabmiz", wait_sec=6)
    await asyncio.sleep(2)

    # INN yuboriladi
    await send_and_wait(client, bot, text="311790999", wait_sec=6)
    await asyncio.sleep(2)

    # Oshibka rasmi yuboriladi
    p5_img = os.path.join(DESKTOP_DIR, "photo_5_2026-11-13_14-31-54.jpg")
    if os.path.exists(p5_img):
        await send_and_wait(client, bot, file_path=p5_img, caption="ashebka chiqaryapti chek urib bomayapti", wait_sec=7)
        await asyncio.sleep(3)

    # ====================================================
    # SCENARIO 3: To'lov tarixi va hisoboti
    # 1. /salombot
    # 2. "tulovlarim tarixini tashavoringlar qani qancha qarzim bor"
    # 3. JSHSHIR yuboriladi
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 TEST 3: SHEVADA: 'tulovlarim tarixini tashavoringlar qani qancha qarzim bor'")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="tulovlarim tarixini tashavoringlar qani qancha qarzim bor", wait_sec=6)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="40305805740011", wait_sec=6)
    await asyncio.sleep(3)

    # ====================================================
    # SCENARIO 4: Kvitansiya yuklash videosi (151-post)
    # 1. /salombot
    # 2. "clickdan kvitansani qanaqa qilib yuklaymiz video bormi"
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 TEST 4: SHEVADA: 'clickdan kvitansani qanaqa qilib yuklaymiz video bormi'")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="clickdan kvitansani qanaqa qilib yuklaymiz video bormi", wait_sec=7)
    await asyncio.sleep(3)

    # ====================================================
    # SCENARIO 5: Soat va vaqt nosozligi
    # 1. /salombot
    # 2. "aparat soati orqada qopti togirlashga parol beringlar"
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 TEST 5: SHEVADA: 'aparat soati orqada qopti togirlashga parol beringlar'")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="aparat soati orqada qopti togirlashga parol beringlar", wait_sec=6)
    await asyncio.sleep(2)

    log_test("\n" + "="*50)
    log_test("🏁 BARCHA TESTLAR YAKUNLANDI!")
    log_test("="*50)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run_live_tests())
