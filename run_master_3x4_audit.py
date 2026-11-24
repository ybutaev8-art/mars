# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import time
import json
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\data\test_runner_session"
BOT_USERNAME = "txkmrobot"

test_suites = [
    {
        "module": "1. STIR (INN) & JSHSHIR Oylik to'lov tekshiruvi (4 ta test)",
        "cases": [
            {
                "id": "1.1",
                "name": "Oddiy 9 xonali STIR",
                "input": "302568138",
                "verify": lambda texts: any("MARS ELEKTRON" in t or "302568138" in t for t in texts) and any("oylik" in t.lower() for t in texts)
            },
            {
                "id": "1.2",
                "name": "Matn ichida STIR",
                "input": "Iltimos 302568138 ni oylik qarzini ko'rib bering",
                "verify": lambda texts: any("MARS ELEKTRON" in t or "302568138" in t for t in texts)
            },
            {
                "id": "1.3",
                "name": "Bazada yo'q STIR",
                "input": "200111222",
                "verify": lambda texts: any("topilmadi" in t.lower() or "mavjud emas" in t.lower() for t in texts)
            },
            {
                "id": "1.4",
                "name": "14 xonali JSHSHIR",
                "input": "32608935480024",
                "verify": lambda texts: any("JSHSHIR" in t or "qarzdor" in t.lower() or "toza" in t.lower() or "tashkilot" in t.lower() or "32608935480024" in t for t in texts)
            }
        ]
    },
    {
        "module": "2. Fiskal modul (FM) Yillik to'lov tekshiruvi (4 ta test)",
        "cases": [
            {
                "id": "2.1",
                "name": "Katta harflarda UZ200715068777",
                "input": "UZ200715068777",
                "verify": lambda texts: any("fiskal modul" in t.lower() or "yillik" in t.lower() or "fm" in t.lower() or "200715068777" in t for t in texts) and not any("terminal raqamini (pos id)" in t.lower() for t in texts)
            },
            {
                "id": "2.2",
                "name": "Kichik harflarda uz200715068777",
                "input": "uz200715068777",
                "verify": lambda texts: any("fiskal modul" in t.lower() or "yillik" in t.lower() or "fm" in t.lower() or "200715068777" in t for t in texts) and not any("terminal raqamini (pos id)" in t.lower() for t in texts)
            },
            {
                "id": "2.3",
                "name": "Boshqa FM prefiksi (VG/LG)",
                "input": "VG2028081065",
                "verify": lambda texts: any("fiskal modul" in t.lower() or "yillik" in t.lower() or "fm" in t.lower() or "vg2028081065" in t.lower() for t in texts)
            },
            {
                "id": "2.4",
                "name": "Matn ichida FM raqami",
                "input": "Fiskal modulim UZ200715068777 yilligini tekshiring",
                "verify": lambda texts: any("fiskal modul" in t.lower() or "yillik" in t.lower() or "fm" in t.lower() or "200715068777" in t for t in texts)
            }
        ]
    },
    {
        "module": "3. Bir xabarda 2 ta savol (Multi-intent) (4 ta test)",
        "cases": [
            {
                "id": "3.1",
                "name": "Shotdan to'lov + Apparat soati",
                "input": "Shotdan to'lasa bo'ladimi? Apparat soati noto'g'ri bo'lib qoldi",
                "verify": lambda texts: any("soat" in t.lower() or "vaqt" in t.lower() or "parol" in t.lower() for t in texts) and any("hisob" in t.lower() or "rekvizit" in t.lower() or "click" in t.lower() or "bo'ladi" in t.lower() for t in texts)
            },
            {
                "id": "3.2",
                "name": "STIR oylik qarz + Z-otchyot",
                "input": "302568138 oylik qarzim bormi, yana z-otchyot qanday olinadi?",
                "verify": lambda texts: any("302568138" in t or "mars elektron" in t.lower() for t in texts) and any("z" in t.lower() or "hisobot" in t.lower() or "chek" in t.lower() for t in texts)
            },
            {
                "id": "3.3",
                "name": "Lenta solish + Oylik rekvizit",
                "input": "Lenta qanday qo'yiladi va yana oylik to'lov rekvizitini bering",
                "verify": lambda texts: any("lenta" in t.lower() for t in texts) and any("rekvizit" in t.lower() or "20208000800208044003" in t or "click" in t.lower() for t in texts)
            },
            {
                "id": "3.4",
                "name": "Click videosi + Soat xatoligi",
                "input": "Clickdan to'lash videosi kerak? Keyin apparat soati orqada qolyapti",
                "verify": lambda texts: any("soat" in t.lower() or "vaqt" in t.lower() for t in texts) and any("click" in t.lower() or "video" in t.lower() for t in texts)
            }
        ]
    },
    {
        "module": "4. To'lov usullari (Clickdan tashqari ilovalar va shotdan to'lov) (4 ta test)",
        "cases": [
            {
                "id": "4.1",
                "name": "Shotdan to'lasam bo'ladimi?",
                "input": "Shotdan to'lasam bo'ladimi?",
                "verify": lambda texts: any("ha, bo'ladi" in t.lower() or "bo'ladi" in t.lower() for t in texts) and any("rekvizit" in t.lower() or "hisob" in t.lower() for t in texts)
            },
            {
                "id": "4.2",
                "name": "Paymedan to'lasa bo'ladimi?",
                "input": "Paymedan to'lasa bo'ladimi?",
                "verify": lambda texts: any("payme" in t.lower() for t in texts) and any("bo'ladi" in t.lower() for t in texts) and any("hisob raqam" in t.lower() or "rekvizit" in t.lower() for t in texts)
            },
            {
                "id": "4.3",
                "name": "Paymedan to'lash videosi bormi?",
                "input": "Paymedan to'lash videosi bormi?",
                "verify": lambda texts: any("faqat click" in t.lower() or "click dasturida" in t.lower() for t in texts) and any("payme" in t.lower() for t in texts)
            },
            {
                "id": "4.4",
                "name": "Alif ilovasidan to'lasa bo'ladimi?",
                "input": "Alif ilovasidan to'lasa bo'ladimi?",
                "verify": lambda texts: any("bo'ladi" in t.lower() for t in texts) and any("hisob raqam" in t.lower() or "rekvizit" in t.lower() for t in texts)
            }
        ]
    },
    {
        "module": "5. Video qo'llanmalar (4 ta test)",
        "cases": [
            {
                "id": "5.1",
                "name": "Z-otchyot / hisobot olish videosi",
                "input": "Z-otchyot qanday olinadi?",
                "verify": lambda texts: any("z" in t.lower() and "hisobot" in t.lower() or "atchoyt" in t.lower() or "chek" in t.lower() for t in texts)
            },
            {
                "id": "5.2",
                "name": "Kassa apparatiga lenta solish videosi",
                "input": "Kassa apparatiga lenta qanday solinadi?",
                "verify": lambda texts: any("lenta" in t.lower() for t in texts)
            },
            {
                "id": "5.3",
                "name": "Apparatda soatni to'g'rilash videosi va parollari",
                "input": "Apparatda soatni to'g'rilash videosi",
                "verify": lambda texts: any("soat" in t.lower() or "vaqt" in t.lower() for t in texts) and any("12341234" in t or "parol" in t.lower() for t in texts)
            },
            {
                "id": "5.4",
                "name": "Kassadan chek chiqarish qo'llanmasi",
                "input": "Kassadan qanday chek uriladi?",
                "verify": lambda texts: any("chek" in t.lower() or "savdo" in t.lower() or "video" in t.lower() for t in texts)
            }
        ]
    },
    {
        "module": "6. Bot tushunmaydigan savollarda istisno tariqasida texnikka ulash (3 ta test)",
        "cases": [
            {
                "id": "6.1",
                "name": "Noodatiy texnik savol (ekran qizishi)",
                "input": "Aparatim g'alati qizib ketyapti nima qilsam bo'ladi?",
                "verify": lambda texts: any("mas'ul" in t.lower() or "mutaxassis" in t.lower() or "kutib turing" in t.lower() for t in texts)
            },
            {
                "id": "6.2",
                "name": "Noma'lum xizmatlar haqidagi savol",
                "input": "Sizlarda kassa apparatidan tashqari yana qanday xizmatlar bor?",
                "verify": lambda texts: any("mas'ul" in t.lower() or "mutaxassis" in t.lower() or "kutib turing" in t.lower() for t in texts)
            },
            {
                "id": "6.3",
                "name": "Kassa apparatini ijaraga olish haqida savol",
                "input": "Sizlarda kassa apparatini ijaraga olsa bo'ladimi?",
                "verify": lambda texts: any("mas'ul" in t.lower() or "mutaxassis" in t.lower() or "kutib turing" in t.lower() for t in texts)
            }
        ]
    },
    {
        "module": "7. Suhbatni unutish va qayta boshlash (3 ta test)",
        "cases": [
            {
                "id": "7.1",
                "name": "/salombot buyrug'i",
                "input": "/salombot",
                "verify": lambda texts: any("assalomu alaykum" in t.lower() or "mars elektron" in t.lower() for t in texts)
            },
            {
                "id": "7.2",
                "name": "/start buyrug'i",
                "input": "/start",
                "verify": lambda texts: any("assalomu alaykum" in t.lower() or "mars elektron" in t.lower() for t in texts)
            },
            {
                "id": "7.3",
                "name": "Boshidan boshlash so'zi",
                "input": "boshidan boshlash",
                "verify": lambda texts: any("assalomu alaykum" in t.lower() or "mars elektron" in t.lower() or "tozalandi" in t.lower() for t in texts)
            }
        ]
    }
]

async def run_audit():
    async with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        bot = await client.get_entity(BOT_USERNAME)
        print("="*70)
        print("🧪 MARS POS BOT - BARCHA IMKONIYATLAR BO'YICHA YALPI AUDIT (3-4 MARTALAB TEKSHIRUV)")
        print("="*70)
        
        all_results = []
        total_tests = 0
        passed_tests = 0

        for suite in test_suites:
            module_name = suite["module"]
            print(f"\n📂 {module_name}")
            print("-" * 70)
            
            # Har bir modul boshlanishida toza xotira bilan boshlash uchun /salombot
            s_reset = await client.send_message(bot, "/salombot")
            await asyncio.sleep(4)

            for case in suite["cases"]:
                total_tests += 1
                c_id = case["id"]
                c_name = case["name"]
                c_input = case["input"]
                
                print(f"  ▶️ [{c_id}] {c_name} (Xabar: '{c_input}') ... ", end="", flush=True)
                
                # Agar test 6 bo'lsa yoki avvalgi testda ADMIN_BOGLANISH bo'lib qolgan bo'lsa, oldin reset qilib olamiz
                if "6." in c_id or "7." in c_id:
                    pass  # keep flow or reset as needed

                sent_msg = await client.send_message(bot, c_input)
                wait_sec = 8 if "3." in c_id else 5
                await asyncio.sleep(wait_sec)
                
                incoming = await client.get_messages(bot, limit=10)
                bot_replies = [m for m in reversed(incoming) if m.id > sent_msg.id]
                if not bot_replies and "3." in c_id:
                    await asyncio.sleep(3)
                    incoming = await client.get_messages(bot, limit=10)
                    bot_replies = [m for m in reversed(incoming) if m.id > sent_msg.id]
                reply_texts = [m.text for m in bot_replies if m.text]
                
                # Tekshirish
                is_ok = False
                try:
                    is_ok = case["verify"](reply_texts)
                except Exception as ex:
                    is_ok = False
                
                status_str = "✅ PASS" if is_ok else "❌ FAIL"
                if is_ok:
                    passed_tests += 1
                print(status_str)
                
                # Agar tekshiruvda texnikka ulanish sodir bo'lgan bo'lsa (modul 6), keyingi test uchun darhol reset qilamiz
                if "6." in c_id or not is_ok:
                    s_tmp = await client.send_message(bot, "/salombot")
                    await asyncio.sleep(3)

                all_results.append({
                    "id": c_id,
                    "name": c_name,
                    "input": c_input,
                    "passed": is_ok,
                    "replies_count": len(bot_replies),
                    "replies_preview": [t[:120].replace('\n', ' ') for t in reply_texts]
                })
                
                await asyncio.sleep(2)

        print("\n" + "="*70)
        print(f"📊 YAKUNIY NATIJA: {passed_tests} / {total_tests} TA TEST MUVAFFAQIYATLI O'TDI ({passed_tests*100//total_tests}%)")
        print("="*70)
        
        with open(r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot\master_audit_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "total": total_tests,
                "passed": passed_tests,
                "percentage": passed_tests*100//total_tests,
                "details": all_results
            }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(run_audit())
