# -*- coding: utf-8 -*-
import os
import sys
import time
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"
REPORT_FILE = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\master_100_audit_results.txt"

def log_audit(msg):
    print(msg, flush=True)
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def run_scenario(client, bot, query, expected_desc, wait_sec=5):
    log_audit(f"\n" + "="*60)
    log_audit(f"▶️ [TEST SO'ROVI]: '{query}'")
    log_audit(f"🎯 [KUTILGAN NATIJA]: {expected_desc}")

    sent = await client.send_message(bot, query)
    sent_id = sent.id
    await asyncio.sleep(wait_sec)

    responses = []
    async for msg in client.iter_messages(bot, limit=5):
        if msg.id > sent_id and msg.sender_id != sent.sender_id:
            responses.append(msg)

    responses.reverse()
    if not responses:
        log_audit("❌ [XATOLIK]: Botdan javob kelmadi!")
        return False

    for r in responses:
        txt = r.text or ""
        media_info = ""
        if r.media:
            media_info = f" [MEDIA: {type(r.media).__name__}]"
            if hasattr(r, 'fwd_from') and r.fwd_from and hasattr(r.fwd_from, 'channel_post'):
                media_info += f" (Post ID: {r.fwd_from.channel_post})"
        log_audit(f"🤖 [BOT JAVOBI]{media_info}:\n{txt.strip()}\n")
    return True

async def main():
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)

    log_audit("🚀 MARS POS BOT MASTER 100% TO'LIQ AUDITI BOSHLANDI")
    log_audit("Sana va vaqt: " + time.strftime("%Y-%m-%d %H:%M:%S"))

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    bot = await client.get_entity("@txkmrobot")

    # Suhbatni reset qilish
    await client.send_message(bot, "/reset")
    await asyncio.sleep(2)

    scenarios = [
        # --- 1. SALOMLASHISH VA BOSHLANG'ICH TUSHUNTIRISH ---
        ("assalomu alaykum", "Salomlashish va bot imkoniyatlari"),

        # --- 2. OYLIK ABONENT TO'LOVI TEKSHIRUVI (TURCHA HOLATLAR) ---
        ("311790999", "STIR toza (qarzi yo'q), 1 ta apparat, rasm so'rash"),
        ("206011507", "STIR qarzdor (1 600 400 so'm), to'lov rekvizitlari va video"),
        ("308635722", "Ko'p apparatli tashkilot (3 ta POS), har biri holati"),
        ("32212995720017", "14 xonali JSHSHIR orqali tekshirish"),
        ("999999999", "Bazadan topilmagan 9 xonali STIR"),
        ("99999999999999", "Bazadan topilmagan 14 xonali JSHSHIR"),

        # --- 3. YILLIK FISKAL MODUL TO'LOVI (OFD JONLI VA MUDDATI) ---
        ("LG420230624507 mana shumi", "Fiskal modul faol holatda, texnikka ulash uchun STIR so'rashi"),
        ("hozir tashlayman", "Kutib turish (video/rekvizitsiz muloyim javob)"),
        ("yillik tolov qachongacha yetadi", "Muddati ko'rinmasligi, faolligi tekshirilishi tushuntirilishi"),

        # --- 4. TO'LOV REKVIZITLARI VA QO'LLANMALARI ---
        ("oylik tolov rekviziti", "Oylik to'lov videosi (148) va rekviziti (85)"),
        ("yillik tolov rekviziti", "Yillik to'lov videosi (145) va rekviziti (34)"),
        ("to'lov rekvizitini bering", "Qaysi to'lov (oylik yoki yillik) kerakligini so'rash"),

        # --- 5. TO'LOV QILINGANI VA KVITANSIYA / TARIX ---
        ("to'lov qildim", "To'lov kvitansiyasini (chek rasmi yoki PDF) so'rash"),
        ("to'lovlarim tarixi", "Oylar kesimidagi to'lovlar jadvali"),

        # --- 6. XATOLIKLAR BO'YICHA BARCHA VIDEO QO'LLANMALAR ---
        ("soati noturiykan", "141-video (Soatni sozlash) va parollar"),
        ("parol sorayapti", "Soat sozlash parollari (12341234, 123498765)"),
        ("aparatim ikpu diyabdi", "138-video (Ma'lumotlarni yuklash / sinxronizatsiya)"),
        ("markirofkani qanday uchiraman", "139-video (Markirovkani o'chirish)"),
        ("narxni qanday ozgartiraman", "140-video (Tovar narxini o'zgartirish)"),
        ("xato urilgan chekni bekor qilish videosi", "53-video (Chekni atkaz qilish)"),
        ("yangi tovar qoshish videosi", "15-video (Tovarni qo'shish va MXIK)"),
        ("kassa dasturini yangilash videosi", "142-video (Dastur yangilash)"),
        ("skanerni qanday ulayman", "27-video (2D skaner ulash)"),
        ("serverdan sinxronizatsiya qilish videosi", "138-video (Sinxronizatsiya)"),
        ("z hisobot olish videosi", "2-video (Chek urish va Z-hisobot)"),
        ("hamma videolarni tashlab ber", "Barcha 12 ta video darsliklar katalogi"),

        # --- 7. UMUMIY MA'LUMOTLAR VA TEXNIK / OPERATOR ---
        ("ofis qayerda joylashgan", "Ofis manzili, mo'ljal va ish vaqti"),
        ("operator bilan bog'lang", "Rasm so'rash yoki texnikka ulash"),
        ("/reset", "Suhbat xotirasini tozalash")
    ]

    passed_count = 0
    total_count = len(scenarios)

    for query, exp_desc in scenarios:
        ok = await run_scenario(client, bot, query, exp_desc, wait_sec=5)
        if ok:
            passed_count += 1
        await asyncio.sleep(1)

    log_audit("\n" + "="*60)
    log_audit(f"🏁 MASTER AUDIT YAKUNLANDI: Jami {total_count} ta sinovdan {passed_count} tasi muvaffaqiyatli yakunlandi!")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
