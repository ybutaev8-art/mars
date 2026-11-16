# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\tester_session"
LOG_FILE = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\test_identifier_results.txt"

def log_t(text):
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

async def send_and_wait(client, bot, text, wait_sec=8):
    log_t(f"\n[MIJOZ]: {text}")
    sent = await client.send_message(bot, text)
    sent_id = sent.id
    log_t(f"  ... Kutmoqda ({wait_sec}s) ...")

    responses = []
    start_time = time.time()
    while time.time() - start_time < wait_sec:
        await asyncio.sleep(2)
        async for msg in client.iter_messages(bot, limit=5):
            if msg.id > sent_id and msg.sender_id != sent.sender_id:
                if msg.id not in [r.id for r in responses]:
                    responses.append(msg)
        if responses:
            await asyncio.sleep(2)
            async for msg in client.iter_messages(bot, limit=5):
                if msg.id > sent_id and msg.sender_id != sent.sender_id:
                    if msg.id not in [r.id for r in responses]:
                        responses.append(msg)
            break

    if responses:
        for r in sorted(responses, key=lambda x: x.id):
            media_info = f" [MEDIA: {type(r.media).__name__}]" if r.media else ""
            log_t(f"[BOT JAVOBI]:{media_info}\n{r.text or '[Media xabar]'}")
    else:
        log_t("[BOT JAVOBI]: (Javob kelmadi!)")

    return responses

async def run_tests():
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except Exception:
            pass

    log_t("="*60)
    log_t("🚀 IDENTIFIKATORLAR (FM, INN, JSHSHIR, POS ID, X/R) TESTI")
    log_t("="*60)

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    bot = await client.get_entity("@txkmrobot")

    # 1. Reset
    await send_and_wait(client, bot, "/salombot", wait_sec=4)
    await asyncio.sleep(2)

    # 2. INN kiritish (311790999)
    log_t("\n>>> 1-QADAM: Toza INN kiritamiz")
    await send_and_wait(client, bot, "311790999", wait_sec=7)
    await asyncio.sleep(2)

    # 3. Yillik to'lovni tekshirishni so'raymiz (avvalgi 10-kamchilik: Exceldagi pos_id 2028081065 ni FM deb o'ylab xato beraverardi)
    log_t("\n>>> 2-QADAM: Yillik to'lovni so'raymiz (Apparat raqamini FM deb adashtirmasligi kerak)")
    await send_and_wait(client, bot, "yillik tolovimni tekshirib bering", wait_sec=7)
    await asyncio.sleep(2)

    # 4. Adashib yana STIR (9 xonali) yuborilsa
    log_t("\n>>> 3-QADAM: FM so'ralganda mijoz adashib yana 9 xonali INN yuborsa")
    await send_and_wait(client, bot, "311790999", wait_sec=7)
    await asyncio.sleep(2)

    # 5. Adashib UZ... terminal raqami yuborilsa
    log_t("\n>>> 4-QADAM: FM so'ralganda mijoz adashib POS ID (UZ...) yuborsa")
    await send_and_wait(client, bot, "UZ210317263622", wait_sec=7)
    await asyncio.sleep(2)

    # 6. Haqiqiy FM (VG298430008670) yuborilganda
    log_t("\n>>> 5-QADAM: Haqiqiy FM (VG298430008670) yuborilganda")
    await send_and_wait(client, bot, "VG298430008670", wait_sec=10)
    await asyncio.sleep(2)

    # 7. Bank hisob raqami (20 xonali X/R) yuborilganda
    log_t("\n>>> 6-QADAM: 20 xonali bank hisob raqami (X/R) yuborilganda")
    await send_and_wait(client, bot, "20208000800208044003", wait_sec=7)
    await asyncio.sleep(2)

    # 8. Ofis manzili va telefon so'ralganda
    log_t("\n>>> 7-QADAM: Ofis manzili va telefon so'ralganda")
    await send_and_wait(client, bot, "ofisingiz qayerda telefon nomeringizni bering", wait_sec=7)
    await asyncio.sleep(2)

    log_t("\n" + "="*60)
    log_t("🏁 TEST YAKUNLANDI!")
    log_t("="*60)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run_tests())
