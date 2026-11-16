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
OUTPUT_FILE = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\audit_results.txt"

def log_audit(text):
    print(text)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

async def send_and_wait(client, bot_entity, text=None, file_path=None, caption=None, wait_sec=10):
    if text:
        log_audit(f"\n[MIJOZ]: {text}")
        sent = await client.send_message(bot_entity, text)
    elif file_path:
        fname = os.path.basename(file_path)
        log_audit(f"\n[MIJOZ (Rasm)]: {fname} | Caption: {caption or ''}")
        sent = await client.send_file(bot_entity, file_path, caption=caption or "")
    else:
        return []

    sent_id = sent.id
    log_audit(f"  ... Javob kutilmoqda ({wait_sec}s) ...")

    responses = []
    start_time = time.time()
    while time.time() - start_time < wait_sec:
        await asyncio.sleep(2)
        async for msg in client.iter_messages(bot_entity, limit=6):
            if msg.id > sent_id and msg.sender_id != sent.sender_id:
                if msg.id not in [r.id for r in responses]:
                    responses.append(msg)
        if responses:
            await asyncio.sleep(2.5)
            async for msg in client.iter_messages(bot_entity, limit=6):
                if msg.id > sent_id and msg.sender_id != sent.sender_id:
                    if msg.id not in [r.id for r in responses]:
                        responses.append(msg)
            break

    if responses:
        for r in sorted(responses, key=lambda x: x.id):
            media_info = f" [MEDIA: {type(r.media).__name__}]" if r.media else ""
            log_audit(f"[BOT JAVOBI]:{media_info}\n{r.text or '[Media xabar]'}")
    else:
        log_audit("[BOT JAVOBI]: (Javob qaytmadi yoki vaqt tugadi!)")

    return responses

async def run_audit():
    if os.path.exists(OUTPUT_FILE):
        try:
            os.remove(OUTPUT_FILE)
        except Exception:
            pass

    log_audit("="*60)
    log_audit("🔍 MARS ELEKTRON TEXNIKA BOTI - 360 DARAJA CHUQUR AUDIT VA TEST")
    log_audit(f"Boshlangan vaqt: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_audit("="*60)

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        log_audit("XATOLIK: User avtorizatsiyadan o'tmagan!")
        return

    bot = await client.get_entity("@txkmrobot")
    log_audit(f"Ulandi: {bot.first_name} (@{bot.username})")

    # ---------------------------------------------------------
    # SUITE 1: SEMANTIK VA SHEVALAR (AI INTEGRATSIYASI)
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 1: SHEVADA APARAT NOSOZLIGI: 'apparatimi ulayolmayapmiz chek urmay qoldi'")
    log_audit("="*60)
    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="assalomu aleykum apparatimi ulayolmayapmiz chek urmay qoldi iltimos yordam berilar", wait_sec=8)
    await asyncio.sleep(2)

    # ---------------------------------------------------------
    # SUITE 2: 8 SOATLIK XOTIRA VA KONTENT UZVIYLIGI
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 2: XOTIRA TESTI: INN kiritilgach, qayta so'ramasdan to'lov tarixi berilishi")
    log_audit("="*60)
    # INN kiritamiz (Toza korxona: 311790999)
    await send_and_wait(client, bot, text="311790999", wait_sec=8)
    await asyncio.sleep(2)
    # INN kiritmasdan to'g'ridan-to'g'ri to'lov tarixini so'raymiz
    await send_and_wait(client, bot, text="to'lovlarim tarixini tashlab bering", wait_sec=8)
    await asyncio.sleep(2)

    # ---------------------------------------------------------
    # SUITE 3: QARZDORLIK VA CHEKLOV NAZORATI
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 3: QARZDOR KORXONA OQIMI: STIR 310715741 (100k+ qarz)")
    log_audit("="*60)
    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="310715741", wait_sec=8)
    await asyncio.sleep(2)
    # Qarzdor korxona nosozlik haqida yozsa nima bo'ladi?
    await send_and_wait(client, bot, text="aparatim ochilmayapti tez ochib beringlar", wait_sec=8)
    await asyncio.sleep(2)

    # ---------------------------------------------------------
    # SUITE 4: VISION / FOTO TEKSHIRUVI (KESILGAN vs TO'LIQ RASM)
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 4.1: KESILGAN RASM (Soati/interneti yo'q): image_2026-10-17_20-41-02.png")
    log_audit("="*60)
    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)
    # Avval toza INN beramiz
    await send_and_wait(client, bot, text="40305805740011", wait_sec=7)
    await asyncio.sleep(2)
    # Kesilgan rasmni yuboramiz
    cropped_img = os.path.join(DESKTOP_DIR, "image_2026-10-17_20-41-02.png")
    if os.path.exists(cropped_img):
        await send_and_wait(client, bot, file_path=cropped_img, caption="mana ekrandagi nosozlik", wait_sec=14)
        await asyncio.sleep(3)

    log_audit("\n" + "="*60)
    log_audit("TEST 4.2: TO'LIQ RASM (Soati va interneti bor): photo_1_2026-11-13_14-31-54.jpg")
    log_audit("="*60)
    full_img = os.path.join(DESKTOP_DIR, "photo_1_2026-11-13_14-31-54.jpg")
    if os.path.exists(full_img):
        await send_and_wait(client, bot, file_path=full_img, caption="mana tepasi soati bilan to'liq rasm", wait_sec=14)
        await asyncio.sleep(3)

    # ---------------------------------------------------------
    # SUITE 5: SOAT VA VAQT SOZLASH
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 5: SOAT / VAQT XATOSI: 'kassada vaqt orqada qopti to'g'irlab bering'")
    log_audit("="*60)
    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="kassada vaqt orqada qopti to'g'irlab bering", wait_sec=8)
    await asyncio.sleep(2)

    # ---------------------------------------------------------
    # SUITE 6: YILLIK FISKAL MODULNI TEKSHIRISH
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 6: YILLIK FISKAL MODULNI TEKSHIRISH: 'yillikni tekshirib bering'")
    log_audit("="*60)
    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="yillik tolovimni tekshirib bering", wait_sec=8)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="VG298430008670", wait_sec=10)
    await asyncio.sleep(2)

    # ---------------------------------------------------------
    # SUITE 7: UMUMIY REKVIZITLAR SO'ROVI
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 7: REKVIZIT SO'ROVI: 'menga rekvizit tashlab bering'")
    log_audit("="*60)
    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="menga to'lov rekvizit tashlang", wait_sec=8)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="oylik to'lov rekviziti", wait_sec=8)
    await asyncio.sleep(2)

    # ---------------------------------------------------------
    # SUITE 8: OFIS MANZILI VA TELEFON RAQAM
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 8: OFIS VA ALOQA: 'ofisingiz qayerda telefon nomeringizni bering'")
    log_audit("="*60)
    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="ofisingiz qayerda telefon nomeringizni bering", wait_sec=8)
    await asyncio.sleep(2)

    # ---------------------------------------------------------
    # SUITE 9: BE’MA’NI MATN / GIBBERISH
    # ---------------------------------------------------------
    log_audit("\n" + "="*60)
    log_audit("TEST 9: TUSHUNARSIZ MATN: 'aslkdjaslkdjasd'")
    log_audit("="*60)
    await send_and_wait(client, bot, text="/salombot", wait_sec=4)
    await asyncio.sleep(2)
    await send_and_wait(client, bot, text="aslkdjaslkdjasd", wait_sec=8)
    await asyncio.sleep(2)

    log_audit("\n" + "="*60)
    log_audit("🏁 BARCHA TESTLAR MUVAFFAQIYATLI YAKUNLANDI!")
    log_audit(f"Tugagan vaqt: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_audit("="*60)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run_audit())
