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
LOG_FILE = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\live_test_advanced_results.txt"

def log_test(text):
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

async def send_and_wait(client, bot_entity, text=None, file_path=None, caption=None, wait_sec=9):
    if text:
        log_test(f"\n[MIJOZ]: {text}")
        sent = await client.send_message(bot_entity, text)
    elif file_path:
        fname = os.path.basename(file_path)
        log_test(f"\n[MIJOZ (Rasm tashladi)]: {fname} (Caption: {caption or ''})")
        sent = await client.send_file(bot_entity, file_path, caption=caption or "")
    else:
        return []

    sent_id = sent.id
    log_test(f"  ... Bot javobini kutmoqda ({wait_sec}s) ...")

    responses = []
    start_time = time.time()
    while time.time() - start_time < wait_sec:
        await asyncio.sleep(2)
        async for msg in client.iter_messages(bot_entity, limit=6):
            if msg.id > sent_id and msg.sender_id != sent.sender_id:
                if msg.id not in [r.id for r in responses]:
                    responses.append(msg)
        if responses:
            await asyncio.sleep(2)
            async for msg in client.iter_messages(bot_entity, limit=6):
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

async def run_advanced_tests():
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except Exception:
            pass

    log_test("==================================================")
    log_test("🚀 CHUQUR VA TURLI XIL VAZIYATLAR TESTI BOSHLANDI")
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
    # SSENARIY 1: Shoshilinch / Asabiy murojaat + Rasm + Texnikka ulash
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 SSENARIY 1: ASABIY / SHOSHILINCH: 'savdo toxtab qoldi odamlar navbatda turibdi'")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="e nega ishlamayapti kassa nima qildilaring savdo toxtab qoldi odamlar navbatda turibdi tez ulab berilar", wait_sec=7)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="40305805740011", wait_sec=7)
    await asyncio.sleep(2)

    # photo_2: 36889 xatolik rasmi
    p2_img = os.path.join(DESKTOP_DIR, "photo_2_2026-11-13_14-31-54.jpg")
    if os.path.exists(p2_img):
        await send_and_wait(client, bot, file_path=p2_img, caption="mana ekrandagi xatosi tez korilar", wait_sec=8)
        await asyncio.sleep(3)

    # ====================================================
    # SSENARIY 2: Aralash til (Surzhyk): 'kassa apparat zablokirovalsya oshibka bervotti'
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 SSENARIY 2: ARALASH TIL: 'kassa apparat zablokirovalsya oshibka bervotti chek urib bomayapti'")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="kassa apparat zablokirovalsya oshibka bervotti chek urib bomayapti", wait_sec=7)
    await asyncio.sleep(2)

    # ====================================================
    # SSENARIY 3: Umumiy rekvizit so'rovi -> Oylik tanlash -> Yillik so'rash
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 SSENARIY 3: UMUMIY REKVIZIT SO'ROVI -> OYLIK TANLASH -> YILLIK SO'RASH")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="menga to'lov rekvizit tashlanglar", wait_sec=7)
    await asyncio.sleep(2)

    # Oylik to'lov rekvizitini so'rash
    await send_and_wait(client, bot, text="oylik to'lov rekviziti", wait_sec=7)
    await asyncio.sleep(2)

    # Keyin yillikni so'rash
    await send_and_wait(client, bot, text="yillik to'lov rekviziti", wait_sec=7)
    await asyncio.sleep(2)

    # ====================================================
    # SSENARIY 4: IKPU xatoligi -> Video yuborilishi -> "Baribir ishlamadi" -> Darhol texnikka ulash
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 SSENARIY 4: IKPU XATOSI -> VIDEO -> 'FOYDASI BO'LMADI' -> DARHOL TEXNIKKA ULASH")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="aparatda ikpu xatosi beryapti tovar kodi chiqmayapti", wait_sec=8)
    await asyncio.sleep(3)

    await send_and_wait(client, bot, text="videoni kordim baribir ishlamayapti foydasi bolmadi", wait_sec=8)
    await asyncio.sleep(2)

    # ====================================================
    # SSENARIY 5: To'lov amalga oshirilganligi bildirilganda kvitansiya so'rash
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 SSENARIY 5: TO'LOV QILINGANLIGI HAQIDA XABAR: 'pul tashladim 100 ming'")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="pul tashladim 100 ming o'tkazdim", wait_sec=7)
    await asyncio.sleep(2)

    # ====================================================
    # SSENARIY 6: Kompaniya manzili, aloqa telefonlari va minnatdorchilik
    # ====================================================
    log_test("\n" + "="*50)
    log_test("👉 SSENARIY 6: OFIS MANZILI, TELEFONLAR VA MINNATDORCHILIK")
    log_test("="*50)

    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="ofisingiz qayerda telefon nomeringizni bering", wait_sec=7)
    await asyncio.sleep(2)

    await send_and_wait(client, bot, text="rahmat katta ishlarizga omad", wait_sec=7)
    await asyncio.sleep(2)

    log_test("\n" + "="*50)
    log_test("🏁 CHUQUR TESTLARNING BARCHASI YAKUNLANDI!")
    log_test("="*50)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run_advanced_tests())
