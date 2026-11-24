# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"
OUTPUT_REPORT = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\live_audit_report.txt"

def record_log(text):
    print(text, flush=True)
    with open(OUTPUT_REPORT, "a", encoding="utf-8") as f:
        f.write(text + "\n")

async def test_case(client, bot, text, expected_desc, wait_sec=6):
    record_log(f"\n==================================================")
    record_log(f"▶️ [MIJOZ SO'ROVI]: '{text}'")
    record_log(f"🎯 [KUTILGAN NATIJA]: {expected_desc}")
    
    sent = await client.send_message(bot, text)
    sent_id = sent.id
    await asyncio.sleep(wait_sec)

    responses = []
    async for msg in client.iter_messages(bot, limit=5):
        if msg.id > sent_id and msg.sender_id != sent.sender_id:
            responses.append(msg)

    responses.reverse()
    if not responses:
        record_log("❌ [XATOLIK]: Botdan javob kelmadi!")
        return False

    for r in responses:
        txt = r.text or ""
        media_info = ""
        if r.media:
            media_info = f" [MEDIA: {type(r.media).__name__}]"
            if hasattr(r, 'fwd_from') and r.fwd_from and hasattr(r.fwd_from, 'channel_post'):
                media_info += f" (Post ID: {r.fwd_from.channel_post})"
        record_log(f"🤖 [BOT JAVOBI]{media_info}:\n{txt.strip()}\n")
    return True

async def main():
    if os.path.exists(OUTPUT_REPORT):
        os.remove(OUTPUT_REPORT)

    record_log("🚀 JONLI TELEGRAM AUDITI BOSHLANDI (@txkmrobot)")
    record_log("Vaqt: " + time.strftime("%Y-%m-%d %H:%M:%S"))

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    bot = await client.get_entity("@txkmrobot")

    # Suhbatni reset qilish
    await client.send_message(bot, "/reset")
    await asyncio.sleep(2)

    # 1. Soat muammosi (soati noturiykan)
    await test_case(client, bot, "soati noturiykan", "141-video (Soatni sozlash videosi)")

    # 2. Soat muammosi boshqa shaklda (soatni qanday tugirlasam buladi)
    await test_case(client, bot, "soatni qanday tugirlasam buladi", "141-video (Soatni sozlash videosi)")

    # 3. Soat parolini so'rash
    await test_case(client, bot, "parol sorayapti", "Soat sozlash parollari (12341234, 123498765)")

    # 4. IKPU xatoligi (aparatim ikpu diyabdi)
    await test_case(client, bot, "aparatim ikpu diyabdi", "138-video (Ma'lumotlarni yuklash / sinxronizatsiya)")

    # 5. Markirovkani o'chirish
    await test_case(client, bot, "markirofkani qanday uchiraman", "139-video (Markirovkani o'chirish)")

    # 6. Narxni o'zgartirish
    await test_case(client, bot, "narxni qanday ozgartiraman", "140-video (Tovar narxini o'zgartirish)")

    # 7. Xato urilgan chekni bekor qilish
    await test_case(client, bot, "xato urilgan chekni bekor qilish videosi", "53-video (Chekni atkaz qilish)")

    # 8. Yillik to'lov muddati (qachongacha yetishi)
    await test_case(client, bot, "yillik tolov qachongacha yetadi", "Yillik to'lov muddati botda ko'rinmasligi, faqat toza/qarzdorlik tekshirilishi tushuntirilishi")

    # 9. Kontekst va xotira: FM to'lovini tekshirish -> toza -> INN so'rash -> hozir tashlayman -> INN yuborish
    await test_case(client, bot, "LG420230624507 mana shumi", "Fiskal modul toza deb, texnikka ulash uchun STIR so'rashi")
    await test_case(client, bot, "hozir tashlayman", "Kutib turaman deyishi (video yoki rekvizit tashlamasdan!)")
    await test_case(client, bot, "302568138", "Oylik abonent holatini to'g'ridan-to'g'ri tekshirib berishi (hech narsa so'ramasdan)")

    await client.disconnect()
    record_log("\n✅ JONLI AUDIT TO'LIQ YAKUNLANDI!")

if __name__ == "__main__":
    asyncio.run(main())
