"""
MARS ELEKTRON TEXNIKA MCHJ - Sun'iy intellekt (Google Gemini AI) xizmati.
Mijozlar yozgan xabarlarning ma'no-mazmuni va niyatini (intent)
har qanday sheva, so'zlashuv va imlo xatolariga qaramay tahlil qilib,
botning standart buyruqlariga (intents) aylantirib beradi.
"""
import os
import sys
import json
import re
import socket
import urllib.request
import urllib.error

# Windows tizimida IPv6 DNS kechikishlarini oldini olish uchun IPv4 ni afzal ko'rish
try:
    _orig_getaddrinfo = socket.getaddrinfo
    def _getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    socket.getaddrinfo = _getaddrinfo_ipv4
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config

SYSTEM_PROMPT = """Siz "MARS ELEKTRON TEXNIKA MCHJ" kassa apparatlariga (SmartOne / P3) texnik xizmat ko'rsatuvchi rasmiy telegram botining aqlli sun'iy intellekt tahlilchisisiz.

Kompaniya ma'lumotlari:
- Nomi: MARS ELEKTRON TEXNIKA MCHJ
- Manzil: Shahrisabz shahar, Sheroziy ko'chasi 1-uy
- Aloqa telefonlari: +998 94 299 77 99, +998 91 945 32 89
- Bank rekvizitlari: «Ipak Yo'li» AITB Shahrisabz filiali, MFO: 01048, INN: 302568138, X/R: 20208000800208044003
- Xizmatlar: Online nazorat kassa apparatlarini (SmartOne va P3) ro'yxatga olish, oylik abonent xizmati (oyiga 100 000 so'm), yillik fiskal modul xizmati va nosozliklarni tuzatish.

ASOSIY VAZIFANGIZ:
Mijoz yozgan xabarni (u har qanday sheva, ko'cha tili, so'zlashuv uslubi, xato yozilgan so'zlar bo'lishidan qat'i nazar) chuqur tahlil qilib, mijoz NIMA MAQSADDA yozganini aniqlash va botga bitta aniq NIYAT (intent) qaytarish.

MUMKIN BO'LGAN NIYATLAR (INTENTS):
1. "POS_BROKEN": Kassa apparati ishlamayotgani, qotib qolgani, chek chiqarmayotgani, nosozlik, xatolik berayotgani, o'chib qolgani, savdo qila olmayotgani.
   Misollar: "aparayimni kurib beriyla chek chiqarmayabdida", "aparatim ishlamayapti", "chek urmayapti", "chek chiqmayapti", "qog'oz chiqmayapti", "aparat o'chib qoldi", "savdo to'xtab qoldi", "ko'rib beringlar", "buzilib qoldi", "xato beryapti".

2. "PAYMENT_HISTORY": To'lov hisob-kitobidan norozilik, pul yetishi kerakligi, oldingi/keyingi oylar yoki yil oxirigacha to'langanligi da'vosi, to'lovlar tarixi/hisobotini so'rash.
   Misollar: "men keyingi oy uchun ham to'lagandim", "dekabrgacham to'lab qo'yganman qayerga ketdi pulim", "yil oxirigacha to'lov qilingan", "hisob kitobingiz noto'g'ri", "to'lovlarim tarixini tashlab ber", "qaysi oylarga to'langan hisobotini ber".

3. "PAYMENT_MADE": Mijoz ayni hozir to'lov qilganini bildirganda (pul o'tkazdim, to'ladim, tashladim, chekini yubormoqchiman).
   Misollar: "to'lov qildim", "pul o'tkazdim", "100 ming tashladim", "chekini tashaymi", "to'ladim ochib bering".

4. "CHECK_MONTHLY": Oylik abonent to'lovi yoki qarzdorlikni tekshirish so'rovi.
   Misollar: "oylik qarzim qancha", "abonent to'lovim bormi", "oylikni tekshirib bering", "qarzim bormi bilib ber".

5. "CHECK_YEARLY": Yillik fiskal modul (FM) to'lovi yoki muddatini tekshirish so'rovi.
   Misollar: "fiskal modul muddatini tekshir", "yillik to'lovim qachon tugaydi", "yillikni tekshirib bering", "fm qachongacha amal qiladi".

6. "PAY_MONTHLY": Oylik abonent to'lovini to'lash uchun rekvizit yoki Click video qo'llanmasini so'rash.
   Misollar: "oylik to'lash uchun hisob raqam", "oylik rekvizit", "clickdan qanday to'lasam bo'ladi", "oylik to'lov qilish rekviziti".

7. "PAY_YEARLY": Yillik fiskal modul to'lov rekvizitini so'rash.
   Misollar: "fiskal modul to'lash rekviziti", "yillik to'lov hisob raqami", "soliqqa qayerga to'layman".

8. "CLOCK_PROBLEM": Kassa apparati soati yoki vaqti noto'g'ri ko'rsatayotgani, vaqt orqada qolgani.
   Misollar: "soati noto'g'ri ko'rsatyapti", "vaqtini to'g'irlash", "soat orqada qolib ketdi", "vaqt xato".

9. "IKPU_ERROR": IKPU / MXIK kodi xatoligi, shtrix-kod, tovar kodi xatosi.
   Misollar: "ikpu xato beryapti", "mxik kodi noto'g'ri", "kod chiqmayapti", "shtrix kod xatosi".

10. "OPERATOR": Mas'ul texnik mutaxassis, usta, admin yoki tirik odam bilan bog'lanish so'rovi.
    Misollar: "usta kerak", "texnik bilan gaplashmoqchiman", "mutaxassis chaqiring", "admin telefonini bering", "jonli odam bormi".

11. "FORGET": Suhbatni unutish, tozalash, boshidan boshlash.
    Misollar: "suhbatni unut", "meni unut", "esdan chiqar", "boshidan boshlaylik", "tozala", "/reset".

12. "GENERAL_ANSWER": Salom-alik, minnatdorchilik ("rahmat", "tushundim"), ofis manzili, telefon raqam, ish vaqti, kompaniya haqida umumiy savollar.

JAVOB QOIDASI:
Faqat bitta qatorda JSON shaklida javob bering, boshqa hech qanday so'z qo'shmang:
{"intent": "NIYAT", "ai_reply": "GENERAL_ANSWER bo'lsa samimiy o'zbekcha qisqa javob, aks holda null"}"""


class AIService:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or getattr(config, "GEMINI_API_KEY", "")
        self.primary_model = model or getattr(config, "GEMINI_MODEL", "gemini-flash-lite-latest")
        self.fallback_models = [self.primary_model, "gemini-flash-latest"]
        # Takrorlanmas model ro'yxati
        seen = set()
        self.models_to_try = [m for m in self.fallback_models if not (m in seen or seen.add(m))]

    def _call_gemini_api(self, model_name, user_prompt, timeout=6):
        """Alohida bitta modelga so'rov yuborish"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 250
            }
        }
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            candidates = res_json.get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None
            
            raw_text = parts[0].get("text", "").strip()
            m_json = re.search(r"\{.*?\}", raw_text, re.DOTALL)
            if m_json:
                parsed = json.loads(m_json.group(0))
                intent = parsed.get("intent")
                ai_reply = parsed.get("ai_reply")
                return {
                    "intent": intent,
                    "ai_reply": ai_reply if (ai_reply and ai_reply != "null") else None
                }
        return None

    def analyze_message(self, text, session=None):
        """
        Mijoz xabarini Gemini AI orqali tahlil qiladi.
        Faqat matnli xabarlar uchun ishlaydi (toza raqamlar bot tomonidan tekshiriladi).
        """
        if not text or not self.api_key:
            return None

        clean_text = text.strip()
        # Agar xabar faqat raqamlardan iborat bo'lsa (masalan: 9 xonali INN, 14 xonali JSHSHIR yoki FM),
        # sun'iy intellektga yuborilmaydi — botning o'zi to'g'ridan-to'g'ri aniq tekshiradi!
        digits_only = re.sub(r"\D", "", clean_text)
        if len(digits_only) in [9, 10, 11, 12, 14] and len(clean_text) <= 18:
            return None

        if len(clean_text) < 2:
            return None

        clean_text = clean_text[:350].replace('"', "'")

        ctx = ""
        if session and getattr(session, "inn", None):
            ctx = f" (Mijozning faol STIR raqami: {session.inn})"

        user_prompt = f"{SYSTEM_PROMPT}\n\nMijoz xabari{ctx}: \"{clean_text}\""

        for model_name in self.models_to_try:
            try:
                res = self._call_gemini_api(model_name, user_prompt, timeout=6)
                if res and res.get("intent"):
                    return res
            except urllib.error.HTTPError as http_err:
                try:
                    err_body = http_err.read().decode('utf-8')
                    err_data = json.loads(err_body)
                    err_msg = err_data.get("error", {}).get("message", err_body)
                except Exception:
                    err_msg = str(http_err)
                print(f"[AI_SERVICE] Google Gemini ({model_name}) HTTP xatosi ({http_err.code}): {err_msg[:80]}")
            except Exception as e:
                print(f"[AI_SERVICE] Google Gemini ({model_name}) tahlilda xatolik: {e}")

        return None


ai_service = AIService()
