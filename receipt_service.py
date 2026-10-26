"""
MARS ELEKTRON TEXNIKA MCHJ - To'lov kvitansiyalarini tahlil qilish va o'qish xizmati.
- Rasm (JPG, PNG) va PDF hujjatlardan matnlarni o'qiydi (RapidOCR va pypdf).
- Kvitansiya ekanligini aniqlaydi (Click, Payme, bank to'lov topshirig'nomasi, va h.k.).
- Kvitansiyadagi To'lov maqsadi, Yuboruvchi va STIR/JSHSHIR ma'lumotlaridan tashkilotni aniqlaydi.
- Tashkilotning oylik abonent to'lovi holatini tekshiradi.
"""
import os
import re
from typing import Dict, Any, Optional

import config
from excel_service import excel_service

_ocr_instance = None

def get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_instance = RapidOCR()
        except Exception as e:
            print(f"[RECEIPT_OCR] RapidOCR yuklashda xatolik: {e}")
            _ocr_instance = False
    return _ocr_instance


class ReceiptService:
    def __init__(self):
        # Mars Elektron Texnika MCHJ ning o'z rekvizitlari (ularni mijozniki deb adashtirmaslik uchun)
        self.mars_inns = {"302568138"}
        self.mars_accounts = {"20208000800208044003"}

    def extract_text_from_file(self, file_path: str) -> str:
        """PDF yoki Rasm fayldan barcha matnlarni ajratib oladi"""
        if not os.path.exists(file_path):
            return ""

        ext = os.path.splitext(file_path)[1].lower()

        # 1. PDF fayl bo'lsa
        if ext == ".pdf":
            extracted = self._extract_text_from_pdf(file_path)
            if len(extracted.strip()) >= 20:
                return extracted
            # Agar raqamli matn bo'lmasa (skaner qilingan rasm bo'lsa), rasmlarni OCR qilamiz
            ocr_text = self._ocr_pdf_images(file_path)
            return (extracted + "\n" + ocr_text).strip()

        # 2. Rasm fayl bo'lsa (JPG, PNG, WEBP, BMP, va h.k.)
        return self._extract_text_from_image(file_path)

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text_parts = []
            for page in reader.pages:
                pt = page.extract_text()
                if pt:
                    text_parts.append(pt)
            return "\n".join(text_parts)
        except Exception as e:
            print(f"[RECEIPT] PDF o'qishda xatolik: {e}")
            return ""

    def _ocr_pdf_images(self, pdf_path: str) -> str:
        ocr = get_ocr()
        if not ocr:
            return ""
        text_parts = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            for page_idx, page in enumerate(reader.pages):
                for img_idx, img_obj in enumerate(page.images):
                    temp_img = os.path.join(config.DATA_DIR, f"temp_pdf_{page_idx}_{img_idx}.png")
                    try:
                        with open(temp_img, "wb") as f_img:
                            f_img.write(img_obj.data)
                        ocr_res, _ = ocr(temp_img)
                        if ocr_res:
                            text_parts.extend([item[1] for item in ocr_res])
                    finally:
                        if os.path.exists(temp_img):
                            try:
                                os.remove(temp_img)
                            except Exception:
                                pass
        except Exception as e:
            print(f"[RECEIPT] PDF ichidagi rasmlarni OCR qilishda xatolik: {e}")
        return "\n".join(text_parts)

    def _extract_text_from_image(self, image_path: str) -> str:
        ocr = get_ocr()
        if not ocr:
            return ""
        try:
            ocr_res, _ = ocr(image_path)
            if not ocr_res:
                return ""
            return "\n".join([item[1] for item in ocr_res])
        except Exception as e:
            print(f"[RECEIPT] Rasmni OCR qilishda xatolik: {e}")
            return ""

    def is_payment_receipt(self, text: str) -> bool:
        """Matn to'lov kvitansiyasiga tegishli ekanligini aniqlash"""
        if not text:
            return False

        t = text.lower()

        # Asosiy to'lov va kvitansiya belgilari
        primary_markers = [
            "kvitansiya", "квитанция", "chek", "чек", "to'lov", "tulov", "оплата", "платеж",
            "to'lov topshirig'nomasi", "to'lov kvitansiyasi", "elektron chek",
            "to'lov maqsadi", "tulov maqsadi", "назначение платежа", "to'lov ma'lumoti", "tulov malumoti",
            "yuboruvchi", "отправитель", "to'lovchi", "плательщик",
            "qabul qiluvchi", "получатель", "oluvchi",
            "tranzaksiya", "транзакция", "o'tkazma", "перевод",
            "click", "payme", "uzum", "anor", "apelsin", "paynet", "munis",
            "mars elektron", "mars electron", "302568138", "20208000800208044003",
            "merchant", "terminal", "operator", "chek raqami", "chek no", "чек no",
            "amaliyot muvaffaqiyatli", "операция успешна", "o'tkazma muvaffaqiyatli",
            "xizmat turi", "komissiya", "комиссия", "talaba", "talaba id"
        ]

        found_count = 0
        for m in primary_markers:
            if m in t:
                found_count += 1

        # Agar to'lov maqsadi yoki yuboruvchi yoki Mars rekviziti bo'lsa, bu deyarli 100% kvitansiya
        has_strong_field = any(sf in t for sf in [
            "to'lov maqsadi", "tulov maqsadi", "назначение платежа",
            "to'lov ma'lumoti", "tulov malumotlari",
            "yuboruvchi", "to'lovchi", "отправитель", "плательщик",
            "qabul qiluvchi", "получатель", "oluvchi",
            "mars elektron", "mars electron", "302568138",
            "merchant", "terminal", "operator", "chek raqami",
            "amaliyot muvaffaqiyatli", "talaba id"
        ])

        # Summa va to'lov indikatorlari
        has_amount = any(w in t for w in ["so'm", "som", "сум", "uzs", "summa", "сумма", "jami", "итог"])
        has_pay_word = any(w in t for w in ["to'lov", "tulov", "chek", "чек", "kvitansiya", "квитанция", "оплата", "платеж", "click", "payme", "uzum", "terminal", "merchant", "operator"])

        if has_strong_field and (has_amount or has_pay_word or found_count >= 2):
            return True

        if found_count >= 2:
            return True

        return False

    def check_receipt_recipient(self, text: str) -> Dict[str, Any]:
        """Kvitansiya qabul qiluvchisini aniqlaydi: Mars, Yangi Texnologiyalar, yoki Begona tashkilot"""
        t = text.lower() if text else ""
        
        # 1. Mars Elektron Texnika
        if any(k in t for k in ["302568138", "20208000800208044003", "mars elektron", "mars electron"]):
            return {"belongs_to": "MARS"}
            
        # 2. Yangi Texnologiyalar DUK (Fiskal modul)
        if any(k in t for k in ["yangi texnologiyalar", "янги технологиялар", "20210000100431200010", "23402000", "fiskal modul"]):
            return {"belongs_to": "OFD_YILLIK"}
            
        # 3. Begona tashkilot (masalan ISFT Instituti, maktab, universitet, boshqa xizmat)
        receiver = None
        m_rec = re.search(r"(?:operator|qabul\s*qiluvchi|получатель|kompaniya|muassasa|tashkilot|oluvchi)[\s:\-_]*([^\n\r,]+)", text, re.IGNORECASE)
        if m_rec:
            receiver = m_rec.group(1).strip()
            receiver = re.split(r"[\t;]", receiver)[0].strip()
        if not receiver:
            for line in text.split("\n"):
                l_strip = line.strip()
                if any(w in l_strip.lower() for w in ["institut", "universitet", "kollej", "maktab", "bank", "mchj", "ooo", "yatt", "holding", "cargo", "clinic", "isft"]):
                    receiver = l_strip
                    break

        amount = None
        m_amt = re.search(r"(?:summa|сумма|to[\'\`\‘\’]?lov|jami|итог|miqdor|qiymat)[\s:\-_]*([0-9]{1,3}(?:[.,\s][0-9]{3})+(?:\.[0-9]{2})?\s*(?:so[\'\`\‘\’]?m|som|сум|uzs)?)", text, re.IGNORECASE)
        if m_amt:
            amount = m_amt.group(1).strip()
        else:
            m_amt_curr = re.search(r"([0-9]{1,3}(?:[.,\s][0-9]{3})+(?:\.[0-9]{2})?\s*(?:so[\'\`\‘\’]?m|som|сум|uzs))", text, re.IGNORECASE)
            if m_amt_curr:
                amount = m_amt_curr.group(1).strip()

        if amount and not any(c in amount.lower() for c in ["so'm", "som", "сум", "uzs"]):
            amount += " so'm"

        return {
            "belongs_to": "OTHER",
            "receiver": receiver or "Begona tashkilot",
            "amount": amount or "Ko'rsatilmagan"
        }

    def is_transfer_screenshot(self, text: str) -> bool:
        """Foydalanuvchi rasmiy kvitansiya o'rniga mobil ilovaning o'tkazma/hisobot skrinshotini yuborganini aniqlash"""
        if not text:
            return False
        t = text.lower()

        # Rasmiy kvitansiya sarlavhalari bo'lsa, bu skrinshot emas, rasmiy hujjat:
        official_headers = [
            "patta", "патт", "мемориальный ордер", "платежное поручение",
            "to'lov topshirig'nomasi", "tolov topshirignomasi", "электронная квитанция"
        ]
        if any(h in t for h in official_headers):
            return False

        app_screen_markers = [
            "hisobotlar", "muvaffaqiyatli", "yechiladigan summa", "pul yechish",
            "takrorlash", "to'lovni saqlash", "tolovni saqlash", "to'lovlar tarixi", "tolovlar tarixi",
            "xarid cheki", "kvitansiya yukl", "kvitansiyani yukl", "скачать чек", "скачать квитанцию",
            "повторить", "сохранить платеж", "история платежей", "rekvizitlar bo'yicha to'lov",
            "rekvizitlar boyicha tolov", "rekvizitlar boyicha", "to'lov raqami", "tolov raqami",
            "qabul qiluvchining hisob raqami", "qabul qiluvchining hisobraqami",
            "o'tkazma muvaffaqiyatli", "otkazma muvaffaqiyatli", "muvaffaqiyatli to'landi",
            "muvaffaqiyatli tolandi", "karta uzcard", "karta humo", "kapta uzcard", "kapta humo"
        ]
        matches = [m for m in app_screen_markers if m in t]
        if len(matches) >= 2 or any(m in t for m in ["hisobotlar", "kvitansiya yukl", "xarid cheki", "takrorlash"]):
            return True
        return False

    def identify_organization(self, text: str, session=None) -> Dict[str, Any]:
        """
        Kvitansiya matnidan tashkilotni (INN / JSHSHIR / Nomi) aniqlash va bazadan tekshirish.
        Natija:
        {
            "found": True | False,
            "org_name": str,
            "inn": str,
            "id_type": str,
            "has_debt": bool,
            "debt_amount": float,
            "balance_str": str,
            "excel_info": dict or None
        }
        """
        t = text.lower() if text else ""

        # 1. Matndan 9 xonali (STIR) yoki 14 xonali (JSHSHIR) raqamlarni qidirish
        # Marsning o'z INNsi (302568138) ni chetlab o'tamiz!
        candidates = []

        # A) "To'lov maqsadi", "To'lov ma'lumoti" yoki "Yuboruvchi / To'lovchi" qismlarini aniqlash
        priority_sections = []
        priority_patterns = [
            r"(?:to[\'\`\‘\’]?lov|tulov|tolov)[\s\-_]*(?:maqsadi|tafsilot|malumot|nomi)",
            r"(?:ha3ha|назнач)",
            r"(?:yuboruvchi|to[\'\`\‘\’]?lovchi|tashkilot|korxona|отправитель|плательщик)",
            r"(?:jshsh[i]?r|жшшир|stir|inn|инн|пинфл|pinfl)"
        ]
        for pat in priority_patterns:
            for m in re.finditer(pat, t):
                chunk = t[m.start():m.start() + 450]
                priority_sections.append(chunk)

        priority_text = " ".join(priority_sections)

        # B) Maxsus yorliqlar (INN / STIR / JSHSHIR / JSHSHR) yonidagi raqamlar:
        for m in re.findall(r"(?:jshsh[i]?r|жшшир|stir|inn|инн|пинфл|pinfl)[\s:\-_№#]*(\d{9}|\d{14})", t):
            if m not in self.mars_inns and m not in candidates:
                candidates.append(m)

        # C) Ustuvor (To'lov maqsadi / Yuboruvchi) qismidagi 14 va 9 xonali raqamlar (harflarga yopishgan bo'lsa ham)
        prio_14 = re.findall(r"(?<!\d)(\d{14})(?!\d)", priority_text)
        prio_9 = re.findall(r"(?<!\d)(\d{9})(?!\d)", priority_text)
        for num in prio_14 + prio_9:
            if num not in self.mars_inns and num not in candidates:
                candidates.append(num)

        # D) Butun kvitansiya matnidagi 14 va 9 xonali raqamlar (harflarga yopishgan bo'lsa ham: inn123456789, jshshr12345678901234)
        gen_14 = re.findall(r"(?<!\d)(\d{14})(?!\d)", text)
        gen_9 = re.findall(r"(?<!\d)(\d{9})(?!\d)", text)
        for num in gen_14 + gen_9:
            if num not in self.mars_inns and num not in candidates:
                candidates.append(num)

        # E) Bo'sh joyli yoki chiziqchali raqamlar (masalan: 311 790 999 yoki 314 038 855 900 11)
        for chunk in [priority_text, text]:
            for m in re.findall(r"(?<!\d)(\d{3}[\s\.\-]\d{3}[\s\.\-]\d{3})(?!\d)", chunk):
                clean_m = re.sub(r"\D", "", m)
                if len(clean_m) == 9 and clean_m not in self.mars_inns and clean_m not in candidates:
                    candidates.append(clean_m)
            for m in re.findall(r"(?<!\d)(\d{1,4}[\s\.\-]\d{2,4}[\s\.\-]\d{2,4}[\s\.\-]\d{2,4})(?!\d)", chunk):
                clean_m = re.sub(r"\D", "", m)
                if len(clean_m) == 14 and clean_m not in self.mars_inns and clean_m not in candidates:
                    candidates.append(clean_m)

        # 2. Har bir nomzod raqamni Excel bazadan tekshiramiz
        for num in candidates:
            info = excel_service.find_by_identifier(num)
            if info:
                return self._format_result(info)

        # 3. Agar raqam topilmagan bo'lsa, "To'lov maqsadi" va "Yuboruvchi" matnidagi tashkilot nomini bazadan izlaymiz
        excel_service.load_data()
        clean_text_letters = re.sub(r"[^A-Za-z0-9]", "", text).upper()
        clean_text_upper = text.upper()
        best_org_info = None

        # Bazadagi barcha tashkilotlar bo'yicha nom qidirish
        for stir_key, p_list in excel_service.cache_by_inn.items():
            if not p_list:
                continue
            org_candidate = p_list[0].get("org_name", "").strip()
            if not org_candidate or len(org_candidate) < 4:
                continue

            # Masalan: "ALISHER BOBO", "UCHQO'RG'ON TTB"
            org_upper = org_candidate.upper()
            clean_org_name = re.sub(r"\b(MCHJ|МЧЖ|OOO|ООО|QK|XK|ХК|YATT|ЯТТ|OK|ОК|FERMER XO'JALIGI|FERMER|KX)\b", "", org_upper).strip()
            clean_org_name = re.sub(r"[`'\"«»]", "", clean_org_name).strip()

            if len(clean_org_name) >= 5:
                if clean_org_name in clean_text_upper:
                    info = excel_service.find_by_identifier(stir_key)
                    if info:
                        best_org_info = info
                        break
                clean_org_compact = re.sub(r"[^A-Za-z0-9]", "", clean_org_name)
                if len(clean_org_compact) >= 6 and clean_org_compact in clean_text_letters:
                    info = excel_service.find_by_identifier(stir_key)
                    if info:
                        best_org_info = info
                        break

        if best_org_info:
            return self._format_result(best_org_info)

        # 4. Kvitansiyaning o'zidan tashkilot aniqlanmadi (yoki Excelda yo'q)
        return {
            "found": False,
            "org_name": None,
            "inn": None,
            "id_type": "STIR / INN",
            "has_debt": False,
            "debt_amount": 0.0,
            "balance_str": None,
            "excel_info": None
        }

    def _format_result(self, info: Dict[str, Any], note: Optional[str] = None) -> Dict[str, Any]:
        """Tashkilot natijasini qulay formatga solish"""
        org_name = info.get("org_name", "Noma'lum")
        inn = info.get("query", "")
        id_type = info.get("id_type", "STIR / INN")
        has_debt = info.get("has_debt", False)
        total_debt = info.get("total_debt", 0.0)
        has_advance = info.get("has_advance", False)
        advance_amount = info.get("advance_amount", 0.0)

        if has_debt and total_debt > 0:
            balance_str = f"⚠️ Qarzdorlik: *{total_debt:,.0f} so'm*".replace(",", " ")
        elif has_advance and advance_amount > 0:
            balance_str = f"💰 Ortiqcha to'lov (avans): *{advance_amount:,.0f} so'm*".replace(",", " ")
        else:
            balance_str = "✅ Qarzdorlik yo'q (0 so'm)"

        return {
            "found": True,
            "org_name": org_name,
            "inn": inn,
            "id_type": id_type,
            "has_debt": has_debt,
            "debt_amount": total_debt,
            "balance_str": balance_str,
            "excel_info": info,
            "note": note
        }

    def process_file(self, file_path: str, session=None) -> Dict[str, Any]:
        """
        Faylni to'liq tekshirish: matnni olish, kvitansiya ekanligini tasdiqlash va tashkilotni aniqlash
        """
        text = self.extract_text_from_file(file_path)

        # 1. Mobil ilova o'tkazma ekrani (skrinshot) bo'lsa - rasmiy kvitansiya emas:
        if self.is_transfer_screenshot(text):
            return {
                "is_receipt": False,
                "is_transfer_screen": True,
                "text": text,
                "org_info": None
            }

        is_rec = self.is_payment_receipt(text)
        if not is_rec:
            return {
                "is_receipt": False,
                "is_transfer_screen": False,
                "text": text,
                "org_info": None
            }

        rec_info = self.check_receipt_recipient(text)
        if rec_info.get("belongs_to") == "OTHER":
            return {
                "is_receipt": True,
                "is_foreign_receipt": True,
                "foreign_info": rec_info,
                "text": text,
                "org_info": None
            }

        org_info = self.identify_organization(text, session=session)
        return {
            "is_receipt": True,
            "is_foreign_receipt": False,
            "foreign_info": rec_info,
            "text": text,
            "org_info": org_info
        }

receipt_service = ReceiptService()
