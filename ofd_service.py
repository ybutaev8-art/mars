"""
Fiskal Modul va OFD Tekshirish Servisi (@ofd943_bot jonli integratsiyasi)
Fiskal modul raqami (FM) bo'yicha yillik to'lov muddatini aniqlash.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import re
import config
from excel_service import excel_service
from ofd_bridge import ofd_bridge

class OFDService:
    def __init__(self):
        pass

    def check_fm(self, fm_number, session=None):
        """
        Fiskal modul raqamini tekshirish:
        1. @ofd943_bot orqali Telegram user sessiyasi orqali to'g'ridan-to'g'ri (real-time) tekshiradi.
        2. Agar OFD boti faol / to'langan desa -> status: toza
        3. Agar muddati tugagan / to'lov kerak desa -> status: qarzdor (rekvizit va video yuboriladi)
        4. Agar topilmasa -> status: topilmadi
        5. Zaxira sifatida lokal hisob-kitob bazasidan ham tekshiradi.
        """
        raw_fm = re.sub(r"[^A-Za-z0-9]", "", str(fm_number)).upper()

        # Excel bazadan tekshiramiz (tashkilot nomini ko'rsatish uchun)
        excel_info = excel_service.find_by_fm(raw_fm)
        if not excel_info and session and session.inn:
            inn_info = excel_service.find_by_inn(session.inn)
            if inn_info and inn_info.get("fm_number") and str(inn_info.get("fm_number")).strip().upper() == raw_fm:
                excel_info = inn_info

        org_name = excel_info.get("org_name") if excel_info else None
        org_line = f"🏢 *Tashkilot:* {org_name}\n" if org_name else ""

        # 1. Real-time @ofd943_bot dan tekshirish
        live_result = ofd_bridge.query_bot(raw_fm)
        # Agar oddiy 12 xonali raqam yuborilgan bo'lsa va topilmasa, "LG" qo'shib ham tekshirib ko'ramiz
        if not live_result or "mavjud emas" in (live_result or "").lower():
            if len(raw_fm) == 12 and raw_fm.isdigit():
                alt_res = ofd_bridge.query_bot("LG" + raw_fm)
                if alt_res and "mavjud emas" not in alt_res.lower():
                    live_result = alt_res
                    raw_fm = "LG" + raw_fm

        if live_result:
            live_clean = live_result.strip()
            live_lower = live_clean.lower()
            print(f"[OFD SERVICE] @ofd943_bot jonli javobi ({raw_fm}): {live_clean}")

            # 1. Qarzdorlik / VMQ-943 / To'lov muddati kelgan bo'lsa
            # (OFD boti 'Fiskal modul faol holatda. Lekin, VMQ-943 ga ko'ra FMO dan qarzdorlik mavjud...' deb yozishi mumkin)
            if any(w in live_lower for w in ["qarzdorlik", "vmq-943", "vmq 943", "fmo dan qarzdorlik", "to'lov qilish muddati", "tulov qilish muddati"]):
                res_text = (
                    f"🔍 *Davlat Soliq Qo'mitasi OFD tizimi (@ofd943_bot) ma'lumoti:*\n\n"
                    f"📟 *Fiskal Modul raqami:* `{raw_fm}`\n"
                    f"{org_line}"
                    f"⚠️ *OFD xabari:*\n{live_clean}\n\n"
                    f"📌 *Aparatingiz fiskal moduli 1 yillik fiskal modul to'loviga kelgan.*\n"
                    f"Yillik fiskal modul to'lov rekviziti va video qo'llanmasi quyida yuborildi 👇"
                )
                return {
                    "status": "qarzdor",
                    "text": res_text,
                    "fm": raw_fm,
                    "live_response": live_clean
                }

            # 2. Tadbirkorlik subyekti nofaol bo'lsa
            elif any(w in live_lower for w in ["nofaol", "subyekti holati nofaol", "tadbirkorlik subyekti nofaol"]):
                res_text = (
                    f"🔍 *Davlat Soliq Qo'mitasi OFD tizimi (@ofd943_bot) ma'lumoti:*\n\n"
                    f"📟 *Fiskal Modul raqami:* `{raw_fm}`\n"
                    f"{org_line}"
                    f"⚠️ *OFD xabari:*\n{live_clean}\n\n"
                    f"🏛 *Tadbirkorlik guvohnomangizning muddati tugagan yoki to'xtatilgan bo'lishi mumkin. Buni Davlat xizmatlari markazi (Yagona darcha) orqali aniqlashtiring.*"
                )
                return {
                    "status": "nofaol",
                    "text": res_text,
                    "fm": raw_fm,
                    "live_response": live_clean
                }

            # 2.5. Fiskal modul ro'yxatdan chiqarilgan bo'lsa
            elif any(w in live_lower for w in ["chiqarilgan", "ro'yxatdan chiqarilgan", "ro‘yxatdan chiqarilgan", "ruyxatdan chiqarilgan"]):
                res_text = (
                    f"🔍 *Davlat Soliq Qo'mitasi OFD tizimi (@ofd943_bot) ma'lumoti:*\n\n"
                    f"📟 *Fiskal Modul raqami:* `{raw_fm}`\n"
                    f"⚠️ *OFD xabari:*\n{live_clean}"
                )
                return {
                    "status": "royxatdan_chiqarilgan",
                    "text": res_text,
                    "fm": raw_fm,
                    "live_response": live_clean
                }

            # 3. Bunday fiskal modul mavjud emas bo'lsa
            elif any(w in live_lower for w in ["mavjud emas", "topilmadi", "bunday fiskal modul"]):
                res_text = (
                    f"🔍 *Davlat Soliq Qo'mitasi OFD tizimi (@ofd943_bot) ma'lumoti:*\n\n"
                    f"📟 *Fiskal Modul raqami:* `{raw_fm}`\n\n"
                    f"⚠️ *Iltimos, fiskal modul raqami bazada topilmadi. Fiskal modul raqamini tekshirib, to'g'ri yozib yuboring.*\n\n"
                    f"ℹ️ *Ma'lumot uchun:* Fiskal modul raqami aparatingiz chiqargan chekning pastki qismida *FM raqami* deb yozilgan bo'limda ko'rsatiladi."
                )
                return {
                    "status": "topilmadi",
                    "text": res_text,
                    "fm": raw_fm,
                    "live_response": live_clean
                }

            # 4. Haqiqiy toza faol holatda (qarzdorliksiz)
            elif "faol" in live_lower:
                has_photo = bool(session and getattr(session, "last_photo_file_id", None))
                photo_prompt = ""
                if not has_photo:
                    photo_prompt = "\n\nAgar aparatingiz baribir ishlamayotgan bo'lsa, aparat ekrani to'liq ko'ringan holda rasm olib tashlang men sizni masul texnik bilan bog'layman."

                res_text = (
                    f"🔍 *Davlat Soliq Qo'mitasi OFD tizimi (@ofd943_bot) ma'lumoti:*\n\n"
                    f"📟 *Fiskal Modul raqami:* `{raw_fm}`\n"
                    f"{org_line}"
                    f"✅ *Fiskal modul to'lovi faol holatda!* Yillik to'lovdan qarzdorlik mavjud emas.\n\n"
                    f"Agar aparatingiz baribir ishlamayotgan bo'lsa, quyidagilarni tekshiring:\n"
                    f"1. Internet aloqasi (Wi-Fi yoki SIM-karta balansi)\n"
                    f"2. Aparatdagi sana va vaqt to'g'riligi\n"
                    f"3. Aparatni o'chirib qayta yoqing (perezagruzka){photo_prompt}"
                )
                return {
                    "status": "toza",
                    "text": res_text,
                    "fm": raw_fm,
                    "live_response": live_clean
                }

            # Boshqa noaniq javob bo'lsa (ehtiyot shart qarzdor deb yuboriladi)
            else:
                res_text = (
                    f"🔍 *Davlat Soliq Qo'mitasi OFD tizimi (@ofd943_bot) ma'lumoti:*\n\n"
                    f"📟 *Fiskal Modul raqami:* `{raw_fm}`\n"
                    f"{org_line}"
                    f"⚠️ *OFD xabari:*\n{live_clean}\n\n"
                    f"📌 *Aparatingiz fiskal moduli 1 yillik fiskal modul to'loviga kelgan bo'lishi mumkin.*\n"
                    f"Yillik fiskal modul to'lov rekviziti va video qo'llanmasi quyida yuborildi 👇"
                )
                return {
                    "status": "qarzdor",
                    "text": res_text,
                    "fm": raw_fm,
                    "live_response": live_clean
                }

        # 2. Agar jonli bot vaqtincha javob bermasa (Fallback - lokal baza)
        if excel_info and excel_info.get("muddat"):
            muddat = excel_info["muddat"]
            res_text = (
                f"🔍 *Fiskal Modul ma'lumotlari:*\n\n"
                f"📟 *Fiskal Modul:* `{raw_fm}`\n"
                f"{org_line}"
                f"📅 *Yillik to'lov amal qilish muddati:* {muddat}\n\n"
            )
            is_expired = False
            try:
                from datetime import datetime
                for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]:
                    try:
                        exp_date = datetime.strptime(muddat.strip(), fmt)
                        if exp_date < datetime.now():
                            is_expired = True
                        break
                    except ValueError:
                        pass
            except Exception:
                pass

            if is_expired:
                res_text += (
                    f"⚠️ *DIQQAT:* Yillik fiskal modul xizmati muddati tugagan!\n"
                    f"Aparatingiz to'xtab qolmasligi uchun to'lovni amalga oshirishingiz lozim.\n\n"
                    f"To'lov rekviziti va video qo'llanmasi quyida yuborildi 👇"
                )
                status = "qarzdor"
            else:
                has_photo = bool(session and getattr(session, "last_photo_file_id", None))
                photo_prompt = ""
                if not has_photo:
                    photo_prompt = "\n\nAgar aparatingiz baribir ishlamayotgan bo'lsa, aparat ekrani to'liq ko'ringan holda rasm olib tashlang men sizni masul texnik bilan bog'layman."

                res_text += (
                    f"✅ *Fiskal modul to'lovi faol holatda!* Yillik to'lovdan qarzdorlik yo'q.\n\n"
                    f"Agar aparatingiz baribir ishlamayotgan bo'lsa, quyidagilarni tekshiring:\n"
                    f"1. Internet aloqasi (Wi-Fi yoki SIM-karta balansi)\n"
                    f"2. Aparatdagi sana va vaqt to'g'riligi\n"
                    f"3. Aparatni o'chirib qayta yoqing (perezagruzka){photo_prompt}"
                )
                status = "toza"
        else:
            res_text = (
                f"🔍 *OFD tekshiruvi:*\n\n"
                f"📟 *Fiskal Modul raqami:* `{raw_fm}` qabul qilindi.\n\n"
                f"Rasmiy Davlat Soliq Qo'mitasi OFD tizimi orqali to'lov holatini tekshirish mumkin:\n"
                f"👉 [OFD Botida tekshirish (bosing)](https://t.me/ofd943_bot?start={raw_fm})\n\n"
                f"📌 *Agar yillik to'lov muddati tugagan bo'lsa yoki to'lamoqchi bo'lsangiz, quyida to'lov rekviziti va video qo'llanmasi yuborildi 👇*"
            )
            status = "tekshirildi"

        return {
            "status": status,
            "text": res_text,
            "fm": raw_fm
        }

# Global servis
ofd_service = OFDService()
