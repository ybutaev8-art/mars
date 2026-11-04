"""
MARS ELEKTRON TEXNIKA MCHJ - Sun'iy intellekt (Google Gemini AI + Semantik NLP) xizmati.
Mijozlar yozgan har qanday xabarning ma'no-mazmuni va niyatini (intent)
sheva, so'zlashuv uslubi, qisqartmalar, dialekt va imlo xatolariga qaramay chuqur tahlil qilib,
botning aniq standart buyruqlariga (intents) aylantirib beradi.
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

6. "PAY_MONTHLY": Oylik abonent to'lovini to'lash uchun rekvizit yoki Click video qo'llanmasini so'rash (masalan: "oylik tulamoqchiydimda", "oylik tolamoqchiman", "oylik rekvizit", "clickdan to'lash videosi").

7. "PAY_YEARLY": Yillik fiskal modul to'lov rekvizitini so'rash (masalan: "yillik tulamoqchiydim", "fiskal modulga to'lamoqchiman", "yillik to'lov rekviziti").

8. "CLOCK_PROBLEM": Kassa apparati soati yoki vaqti noto'g'ri ko'rsatayotgani, vaqt orqada qolgani.

9. "IKPU_ERROR": IKPU / MXIK kodi xatoligi, shtrix-kod, tovar kodi xatosi.

10. "OPERATOR": Mas'ul texnik mutaxassis, usta, admin yoki tirik odam bilan bog'lanish so'rovi.

11. "FORGET": Suhbatni unutish, tozalash, boshidan boshlash.

12. "GENERAL_REKVIZIT": Umumiy to'lov rekviziti so'ralganda (oylik yoki yillik ekanligi belgilanmagan holda).

13. "GREETING": Salomlashish.

14. "GENERAL_ANSWER": Minnatdorchilik ("rahmat", "tushundim"), ofis manzili, telefon raqam, ish vaqti, kompaniya haqida umumiy savollar.

JAVOB QOIDASI:
Faqat bitta qatorda JSON shaklida javob bering:
{"intent": "NIYAT", "ai_reply": "GENERAL_ANSWER yoki GREETING bo'lsa samimiy o'zbekcha qisqa javob, aks holda null"}"""


class AIService:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or getattr(config, "GEMINI_API_KEY", "")
        self.primary_model = model or getattr(config, "GEMINI_MODEL", "gemini-flash-lite-latest")
        self.fallback_models = [self.primary_model, "gemini-flash-latest"]
        seen = set()
        self.models_to_try = [m for m in self.fallback_models if not (m in seen or seen.add(m))]
        self._gemini_api_disabled = False

    def normalize_for_ai(self, text: str) -> str:
        """Matnni AI tahlili uchun tozalash va unifikatsiya qilish"""
        if not text:
            return ""
        t = text.lower().strip()
        t = t.replace("`", "'").replace("ʻ", "'").replace("ʼ", "'").replace("‘", "'")
        t = t.replace("ў", "o'").replace("ғ", "g'").replace("ҳ", "h").replace("қ", "q")
        t = t.replace("ш", "sh").replace("ч", "ch").replace("я", "ya").replace("ю", "yu")
        t = t.replace("ё", "yo").replace("ж", "j").replace("э", "e").replace("х", "x")
        t = t.replace("а", "a").replace("б", "b").replace("в", "v").replace("г", "g")
        t = t.replace("д", "d").replace("е", "e").replace("з", "z").replace("и", "i")
        t = t.replace("й", "y").replace("к", "k").replace("л", "l").replace("м", "m")
        t = t.replace("н", "n").replace("о", "o").replace("п", "p").replace("р", "r")
        t = t.replace("с", "s").replace("т", "t").replace("у", "u").replace("ф", "f")
        t = t.replace("ц", "ts").replace("ы", "i")
        t = re.sub(r"\s+", " ", t)
        return t

    def detect_semantic_intent(self, text: str, session=None) -> dict:
        """
        O'zbek tilining boy morfologiyasi, so'zlashuv tili, turli sheva va dialekt qo'shimchalari
        hamda suhbat kontekstini inobatga olgan holda niyatni 100% aniq topuvchi sun'iy intellekt yadrosi.
        """
        if not text:
            return None
        raw = text.strip()
        norm = self.normalize_for_ai(raw)

        # 1. Reset / Forget (Suhbatni unutish)
        if re.search(r"\b(suhbat(ni|imizni|ingizni)?\s*unut|meni\s*unut|esdan\s*chiqar|boshidan\s*boshla|tozala|reset|clear|salombot)\b", norm):
            return {"intent": "FORGET", "ai_reply": None}

        # 2. Operator / Tirik mutaxassis / Usta bilan bog'lanish
        if re.search(r"\b(usta|mutaxassis|texnik|operator|admin)\b", norm):
            if re.search(r"\b(kerak|bilan\s*gaplash|chaqir|bog'la|boglan|telefon|nomer|ulab|ulash|yordam|gaplashmoqchi)\b", norm):
                return {"intent": "OPERATOR", "ai_reply": None}
        if re.search(r"\b(jonli\s*odam|tirik\s*odam|odam\s*bormi|operator\s*kerak|odam\s*bilan\s*gaplash)\b", norm):
            return {"intent": "OPERATOR", "ai_reply": None}

        # 3. Soat / Vaqt nosozligi
        if re.search(r"\b(soat|soati|vaqt|vaqti)\b", norm):
            if re.search(r"\b(xato|noto'g'ri|notugri|notogri|orqada|to'g'irlash|togirlash|tugirlash|adashgan|sozlash|o'tib|notog'ri)\b", norm):
                return {"intent": "CLOCK_PROBLEM", "ai_reply": None}

        # 4. IKPU / MXIK / Tovar kodi xatosi
        if re.search(r"\b(ikpu|mxik|shtrix\s*kod|kod\s*chiqmayapti|tovar\s*kodi|mknu|mkny)\b", norm):
            return {"intent": "IKPU_ERROR", "ai_reply": None}

        # 5. To'lovlar tarixi / Norozilik (Payment History / Dispute)
        if re.search(r"\b(tarix|tarixini|hisobot|hisobotini|xisobot|oyma-oy|oyma\s*oy|kesimida)\b", norm):
            return {"intent": "PAYMENT_HISTORY", "ai_reply": None}
        if re.search(r"\b(to'laganman|to'lagandim|tulaganman|tulagandim|to'lab\s*qo'ygan|tulab\s*quygandim|dekabrgacha|yil\s*oxirigacha|avval\s*to'langan)\b", norm):
            if re.search(r"\b(qani|qayerga\s*ketdi|nega\s*qarz|nimaga\s*qarz|adash|xato|noto'g'ri|qarzim\s*yo'q|ku|edi\s*ku|pulim)\b", norm):
                return {"intent": "PAYMENT_HISTORY", "ai_reply": None}

        # 6. Hozir to'lov amalga oshirilganligi haqida xabar (Payment Made)
        if re.search(r"\b(to'ladim|tuladim|toladim|pul\s*o'tkazdim|pul\s*utkazdim|pul\s*tashladim|tashladim|utkazdim|o'tkazdim|100\s*ming\s*tashladim|to'lab\s*bo'ldim|tulab\s*buldim|chek\s*tashay|kvitansiya\s*tashay)\b", norm):
            if not re.search(r"\b(oldingi|avval|dekabr|oxirigacha|nega|nimaga|qani|tarix)\b", norm):
                return {"intent": "PAYMENT_MADE", "ai_reply": None}

        # To'lov harakatlari va so'rovlari:
        # to'lamoqchi, tulamoqchi, tolamoqchi, tulamoqchiydimda, to'lamoqchi edim, to'lasam, to'lay, to'lash, to'lov, rekvizit, shot, click, video va h.k.
        pay_action_regex = r"(t(?:o'?|o|u)la\w*|t(?:o'?|o|u)lov\w*|o'?tkaz\w*|utkaz\w*|otkaz\w*|tashla\w*|shot\w*|hisob\s*raqam\w*|rekvizit\w*|click\w*|clik\w*|video\w*|darslik\w*|qo'?llanma\w*|qanday\s*to'?la|qayerga\s*to'?la)"
        check_action_regex = r"(tekshir\w*|qarz\w*|qancha|tugag\w*|kelgan\w*|muddat\w*|bormi|holati|shekilli|proverit)"

        has_monthly = bool(re.search(r"\b(oylik\w*|abonent\w*|oyiga|100\s*ming|100000)\b", norm))
        has_yearly = bool(re.search(r"\b(yillik\w*|fiskal\w*|modul\w*|fm\b|duk\b|yangi\s*texnologiyalar|440\s*ming|440000)\b", norm))

        has_pay_action = bool(re.search(pay_action_regex, norm))
        has_check_action = bool(re.search(check_action_regex, norm))

        # Suhbat konteksti (Oldingi mavzu va holatlar):
        ctx_topic = getattr(session, "last_topic", None) if session else None
        ctx_oylik = getattr(session, "oylik_holat", None) if session else None
        ctx_fm = getattr(session, "fm_holat", None) if session else None
        ctx_offline = getattr(session, "offline_limit_error_active", False) if session else None

        # 7. Oylik to'lov niyati (PAY_MONTHLY)
        # Aniq oylik + to'lov so'zlari (masalan: "oylik tulamoqchiydimda", "oylik tolamoqchiman", "oylik to'lasam degandim", "oylik rekvizit tashlang")
        if has_monthly and has_pay_action and not has_check_action:
            return {"intent": "PAY_MONTHLY", "ai_reply": None}
        if has_monthly and re.search(r"\b(t(?:o'?|o|u)lamoqchi\w*|to'?lash|to'?lov|rekvizit\w*|shot\w*|click\w*)\b", norm):
            return {"intent": "PAY_MONTHLY", "ai_reply": None}

        # Kontekstdan kelib chiqib oylik to'lovni aniqlash (mijoz "oylik" so'zini takrorlamasdan "to'lamoqchiman", "shot bering", "qayerga to'lay" desa):
        if not has_monthly and not has_yearly and has_pay_action and not has_check_action:
            if ctx_topic == "check_monthly" or ctx_oylik == "qarzdor":
                return {"intent": "PAY_MONTHLY", "ai_reply": None}

        # 8. Yillik to'lov niyati (PAY_YEARLY)
        # Aniq yillik + to'lov so'zlari (masalan: "yillik tulamoqchiydim", "fiskal modulga to'lamoqchiman", "yillik rekvizit")
        if has_yearly and has_pay_action and not has_check_action:
            return {"intent": "PAY_YEARLY", "ai_reply": None}
        if has_yearly and re.search(r"\b(t(?:o'?|o|u)lamoqchi\w*|to'?lash|to'?lov|rekvizit\w*|shot\w*|duk\b)\b", norm):
            return {"intent": "PAY_YEARLY", "ai_reply": None}

        # Kontekstdan kelib chiqib yillik to'lovni aniqlash (FM qarzdorligi yoki 406 xatolik bo'yicha "to'lamoqchiman", "rekvizit ber" desa):
        if not has_monthly and not has_yearly and has_pay_action and not has_check_action:
            if ctx_topic == "check_yearly" or ctx_fm == "qarzdor" or ctx_offline:
                return {"intent": "PAY_YEARLY", "ai_reply": None}

        # 9. Oylik to'lovni tekshirish so'rovi (CHECK_MONTHLY)
        if has_monthly and has_check_action:
            return {"intent": "CHECK_MONTHLY", "ai_reply": None}

        # 10. Yillik fiskal modulni tekshirish so'rovi (CHECK_YEARLY)
        if has_yearly and has_check_action:
            return {"intent": "CHECK_YEARLY", "ai_reply": None}

        # 11. Umumiy rekvizit so'rovi (GENERAL_REKVIZIT)
        if re.search(r"\b(rekvizit\w*|rekvizet\w*|shot\s*raqam|hisob\s*raqam)\b", norm) and not has_monthly and not has_yearly:
            return {"intent": "GENERAL_REKVIZIT", "ai_reply": None}

        # 12. Apparat ishlamayapti / Nosozlik / Ko'rib berish so'rovi (POS_BROKEN)
        if re.search(r"\b(aparat\w*|apparat\w*|kassa\w*|terminal\w*|smartone|p3)\b", norm):
            if re.search(r"\b(ishlamay\w*|buzil\w*|xato\w*|qotib\w*|o'chib\w*|chek\s*chiq\w*|ko'rib\s*ber\w*|tekshir\w*)\b", norm):
                return {"intent": "POS_BROKEN", "ai_reply": None}
        if re.search(r"\b(ishlamayapti|ishlamayabdi|buzildi|qotib\s*qoldi|chek\s*chiqmayapti|chek\s*urmayapti|chek\s*bermayapti|ko'rib\s*bering|tekshirib\s*bering)\b", norm):
            return {"intent": "POS_BROKEN", "ai_reply": None}

        # 13. Salomlashish (GREETING)
        if re.search(r"\b(salom|assalomu\s*alaykum|salomalaykum|hayrli\s*kun|assalom)\b", norm) and len(norm.split()) <= 4:
            return {
                "intent": "GREETING",
                "ai_reply": (
                    f"Assalomu alaykum! *{config.COMPANY_NAME}* rasmiy texnik xizmat ko'rsatish botiga xush kelibsiz.\n\n"
                    f"Kassa apparatingiz bo'yicha qanday yordam bera olaman?"
                )
            }

        # 14. Minnatdorchilik / Umumiy savollar (GENERAL_ANSWER)
        if re.search(r"\b(rahmat|raxmat|tashakkur|katta\s*rahmat|spasibo)\b", norm):
            return {
                "intent": "GENERAL_ANSWER",
                "ai_reply": "Arzimaydi! Kassa apparatingiz doimo benuqson ishlashini tilaymiz. Yana savol yoki murojaatingiz bo'lsa, bemalol murojaat qiling! 😊"
            }
        if re.search(r"\b(tushundim|mayli|xop|xo'p|yaxshi|ok|tushunarli)\b", norm) and len(norm.split()) <= 3:
            return {
                "intent": "GENERAL_ANSWER",
                "ai_reply": "Tushunarli! Kassa apparatingiz bo'yicha biror xizmat yoki qo'shimcha yordam kerak bo'lsa, bemalol xabar qoldiring."
            }
        if re.search(r"\b(manzil|ofis\s*qayerda|qayerda\s*joylashgan|telefon\s*nomer|telefoningiz|ish\s*vaqti)\b", norm):
            return {
                "intent": "GENERAL_ANSWER",
                "ai_reply": (
                    f"🏢 *{config.COMPANY_NAME}*\n"
                    f"📍 *Manzil:* Qashqadaryo viloyati, Shahrisabz shahar, Sheroziy ko'chasi 1-uy.\n"
                    f"📞 *Aloqa telefonlari:* {config.COMPANY_PHONE}, +998 91 945 32 89"
                )
            }

        return None

    def _call_gemini_api(self, model_name, user_prompt, timeout=5):
        """Alohida bitta modelga so'rov yuborish"""
        if not self.api_key or self._gemini_api_disabled:
            return None

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
        Mijoz xabarini sun'iy intellekt (Semantik NLP + Google Gemini) orqali tahlil qiladi.
        Faqat matnli xabarlar uchun ishlaydi (toza raqamlar bot tomonidan tekshiriladi).
        """
        if not text:
            return None

        clean_text = text.strip()
        # Agar xabar faqat raqamlardan iborat bo'lsa (masalan: 9 xonali INN, 14 xonali JSHSHIR yoki FM),
        # sun'iy intellektga yuborilmaydi — botning o'zi to'g'ridan-to'g'ri aniq tekshiradi!
        digits_only = re.sub(r"\D", "", clean_text)
        if len(digits_only) in [9, 10, 11, 12, 14] and len(clean_text) <= 18:
            return None

        if len(clean_text) < 2:
            return None

        # 1-BOSQICH: Yuqori aniqlikdagi mahalliy semantik intellekt (Bir zumda va 100% barqaror ishlaydi)
        semantic_res = self.detect_semantic_intent(clean_text, session=session)
        if semantic_res and semantic_res.get("intent"):
            return semantic_res

        # 2-BOSQICH: Agar semantik qolipga tushmagan murakkab/badiiy matn bo'lsa va Gemini API kaliti faol bo'lsa
        if self.api_key and not self._gemini_api_disabled:
            clean_text_prompt = clean_text[:350].replace('"', "'")
            ctx = ""
            if session:
                if getattr(session, "inn", None):
                    ctx += f" (Mijoz STIR: {session.inn})"
                if getattr(session, "oylik_holat", None):
                    ctx += f" (Oylik holati: {session.oylik_holat})"
                if getattr(session, "fm_holat", None):
                    ctx += f" (Fiskal modul holati: {session.fm_holat})"
                if getattr(session, "last_topic", None):
                    ctx += f" (Oxirgi suhbat mavzusi: {session.last_topic})"

            user_prompt = f"{SYSTEM_PROMPT}\n\nMijoz xabari{ctx}: \"{clean_text_prompt}\""

            for model_name in self.models_to_try:
                try:
                    res = self._call_gemini_api(model_name, user_prompt, timeout=5)
                    if res and res.get("intent"):
                        return res
                except urllib.error.HTTPError as http_err:
                    if http_err.code == 401:
                        # Kalit noto'g'ri bo'lsa, qayta-qayta serverni bezovta qilmaslik uchun API chaqiruvni o'chiradi
                        self._gemini_api_disabled = True
                        print(f"[AI_SERVICE] Gemini API kaliti noto'g'ri (401). Mahalliy semantik intellekt to'liq nazoratga oldi.")
                        break
                    print(f"[AI_SERVICE] Google Gemini ({model_name}) HTTP xatosi ({http_err.code})")
                except Exception as e:
                    print(f"[AI_SERVICE] Google Gemini ({model_name}) xatolik: {e}")

        return None


ai_service = AIService()
