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

2. "PAYMENT_HISTORY": To'lovlar tarixi yoki oylar kesimidagi hisobotni so'rash (birinchi marta hisobot so'ralganda).
   Misollar: "to'lovlarim tarixini tashlab ber", "qaysi oylarga to'langan hisobotini ber", "oyma-oy to'lovlar tarixi", "to'lov hisoboti".

3. "PAYMENT_DISPUTE": Mijoz to'lov hisobotidan norozi bo'lganda, keyingi oyga yetadigan qilib to'laganman, avval to'lab qo'ygandim, hisob-kitobingiz noto'g'ri, pulim qayerga ketdi deb e'tiroz bildirsa.
   Misollar: "kiyingi oyga yetadigan qilib tulab quyudimku", "notugri hisoblayabsila meni tulovim kiyingi oyga ham yitardi", "dekabrgacham to'lab qo'yganman qayerga ketdi pulim", "yil oxirigacha to'lov qilingan", "adashyapsiz qarzim yo'q".

4. "PAYMENT_MADE": Mijoz ayni hozir to'lov qilganini bildirganda (pul o'tkazdim, to'ladim, tashladim, chekini yubormoqchiman).
   Misollar: "to'lov qildim", "pul o'tkazdim", "100 ming tashladim", "chekini tashaymi", "to'ladim ochib bering".

5. "CHECK_MONTHLY": Oylik abonent to'lovi yoki qarzdorlikni tekshirish so'rovi.
   Misollar: "oylik qarzim qancha", "abonent to'lovim bormi", "oylikni tekshirib bering", "qarzim bormi bilib ber".

6. "CHECK_YEARLY": Yillik fiskal modul (FM) to'lovi yoki muddatini tekshirish so'rovi.
   Misollar: "fiskal modul muddatini tekshir", "yillik to'lovim qachon tugaydi", "yillikni tekshirib bering", "fm qachongacha amal qiladi".

7. "PAY_MONTHLY": Oylik abonent to'lovini to'lash uchun hisob raqami rekviziti, Click video qo'llanmasi yoki qanday to'lash tartibini so'rash.
   Misollar: "ha qannay tulaman buni", "qanday to'lasam bo'ladi", "oylik tulamoqchiydimda", "oylik tolamoqchiman", "oylik rekvizit", "clickdan to'lash videosi", "qayerga to'layman".

8. "PAY_YEARLY": Yillik fiskal modul to'lov rekvizitini so'rash (masalan: "yillik tulamoqchiydim", "fiskal modulga to'lamoqchiman", "yillik to'lov rekviziti").

9. "CLOCK_PROBLEM": Kassa apparati soati yoki vaqti noto'g'ri ko'rsatayotgani, vaqt orqada qolgani.

10. "IKPU_ERROR": IKPU / MXIK kodi xatoligi, shtrix-kod, tovar kodi xatosi.

11. "OPERATOR": Mas'ul texnik mutaxassis, usta, admin yoki tirik odam bilan bog'lanish so'rovi.

12. "OFFICE_LOCATION": Kompaniya ofisi qayerdaligi, lokatsiyasi, manzili yoki kelish yo'li so'ralganda.
    Misollar: "ofis qayerda", "ishxonalaring qayda joylashgan", "lokatsa tashlang", "adresingiz qayerda", "qayerga borsak bo'ladi".

13. "FORGET": Suhbatni unutish, tozalash, boshidan boshlash.

14. "GENERAL_REKVIZIT": Umumiy to'lov rekviziti so'ralganda (oylik yoki yillik ekanligi belgilanmagan holda).

15. "GREETING": Salomlashish.

16. "GENERAL_ANSWER": Minnatdorchilik ("rahmat", "tushundim"), aloqa telefonlari, ish vaqti, kompaniya haqida umumiy savollar.

17. "WAITING_PROMISE": Mijoz so'ralgan ma'lumotni (STIR/INN, FM raqami, xatolik rasmi, kvitansiya cheki) ayni damda tayyorlayotgani, qidirayotgani yoki hozir yuborishini, kutib turishni aytayotganda.
    Misollar: "hozir tashlayman", "hozir tashiman", "hozir yuboraman", "kutib turing", "kutib turinglar", "hozir", "bir daqiqa", "bir minut", "hozircha", "qidirayapman", "topay", "hozir beraman", "qaraychi", "sal kutib turing".

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

        # So'roq va olmoshlar unifikatsiyasi:
        t = re.sub(r"\b(qannay|qande|qandey|qandoq)\b", "qanday", t)
        t = re.sub(r"\b(qatta|qattda|qattan|qayga|qayda)\b", "qayerda", t)
        t = re.sub(r"\b(qattagi|qaydagi)\b", "qayerdagi", t)

        # To'lov, abonent va fe'l shevalari unifikatsiyasi:
        t = re.sub(r"\b(tulaman|tuliman|toliyman|tulayman|tulaymiz|tulaylik)\b", "to'layman", t)
        t = re.sub(r"\b(tulash|tulov|tolov|tulovlar|tolovlar)\b", "to'lov", t)
        t = re.sub(r"\b(tulovim|tolovim|tulovimiz)\b", "to'lovim", t)
        t = re.sub(r"\b(tulab|tolap|tulap)\b", "to'lab", t)
        t = re.sub(r"\b(tulagandim|tulagandik|tulaganman|tulaganmiz|tuladim|toladim)\b", "to'laganman", t)
        t = re.sub(r"\b(quyudim|quydim|quygandim|quygandik|quyganmiz|quygandimku|quyudimku|quydimku)\b", "qo'ygandimku", t)
        t = re.sub(r"\b(yitardi|yitadi|yitar|yitish|yitishi|yitmasligi)\b", "yetardi", t)
        t = re.sub(r"\b(notugri|notogri|noto'gri|noto'g'ri)\b", "noto'g'ri", t)
        t = re.sub(r"\b(hisoblayabsila|xisoblayabsila|hisoblayapsilar|hisoblayapsizlar)\b", "noto'g'ri hisob", t)
        t = re.sub(r"\b(abanit|abenent|abanent|abonentlik)\b", "abonent", t)
        t = re.sub(r"\b(opparat\w*|apparat\w*|aparat\w*|mashinka\w*)\b", "aparat", t)
        t = re.sub(r"\b(ashebka\w*|oshibka\w*|ashepka\w*)\b", "xato", t)
        t = re.sub(r"\b(lokat[sc]a\w*|lokatsiya\w*|adres\w*)\b", "manzil", t)
        t = re.sub(r"\b(ishxona\w*|ofis\w*)\b", "ofis", t)
        t = re.sub(r"\b(kurib|kuring|korib)\b", "ko'rib", t)
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
        if re.search(r"^[\/\\#]?(?:salom[\s_]?bot)(?:@\w+)?(?:\s.*)?$", norm) or re.search(r"^salom\s+bot$", norm) or re.search(r"[\/\\#]salom[\s_]?bot\b", norm):
            return {"intent": "FORGET", "ai_reply": None}
        if re.search(r"\b(suhbat(ni|imizni|ingizni)?\s*unut|meni\s*unut|esdan\s*chiqar|boshidan\s*boshla|tozala|reset|clear)\b", norm):
            return {"intent": "FORGET", "ai_reply": None}

        # 2. Operator / Tirik mutaxassis / Usta bilan bog'lanish
        if re.search(r"\b(usta|mutaxassis|texnik|operator|admin)\b", norm):
            if re.search(r"\b(kerak|bilan\s*gaplash|chaqir|bog'la|boglan|telefon|nomer|ulab|ulash|yordam|gaplashmoqchi)\b", norm):
                return {"intent": "OPERATOR", "ai_reply": None}
        if re.search(r"\b(jonli\s*odam|tirik\s*odam|odam\s*bormi|operator\s*kerak|odam\s*bilan\s*gaplash)\b", norm):
            return {"intent": "OPERATOR", "ai_reply": None}

        # 2.5 Kompaniya ofisi manzili / lokatsiyasi / qayerda joylashganligi
        if re.search(r"\b(ofis\w*|ishxona\w*|manzil\w*|adres\w*|lokatsiya\w*|lokatsa\w*)\b", norm):
            if re.search(r"\b(qayerda\w*|qayda\w*|joylashgan\w*|ber\w*|tashla\w*|ko'?rsat\w*|boramiz\w*|bormoqchi\w*|kelmoqchi\w*|qayerga\w*)\b", norm) or len(norm.split()) <= 4:
                return {"intent": "OFFICE_LOCATION", "ai_reply": None}

        # 2.6 Kutib turish, ma'lumotni hozir yuborishini aytish (Waiting / Promise to send requested data)
        # Masalan: "hozir tashlayman", "hozir tashiman", "kutib turing", "bir minut", "hozir", "topay", "hozir beraman"
        is_waiting_phrase = bool(
            re.search(r"\b(hozir\s*(?:tashlayman|tashiman|yuboraman|beraman|tashayman|tashay|yuboray|tashvoraman|jo'?nataman|jonataman|junataman|topaman|topay|qidirayapman|qaraychi|qaray|ko'ray|kuray|olay|chiqaray)|kutib\s*tur\w*|kuting\w*|bir\s*(?:daqiqa|minut|pas|sekund)|sal\s*tur\w*|pas\s*tur\w*|hozir\s*topib|hozircha|tayyorlayapman)\b", norm)
            or norm in [
                "hozir", "xozir", "kutib turing", "kutib turinglar", "kuting",
                "bir minut", "bir daqiqa", "pas turing", "sal turing",
                "hozir topay", "qidirayapman", "hozir tashlayman", "hozir tashiman", "hozir yuboraman"
            ]
        )
        current_state = getattr(session, "state", "NORMAL") if session else "NORMAL"
        is_state_agreement = (
            current_state in ["AWAITING_INN", "AWAITING_FM", "AWAITING_ERROR_PHOTO", "AWAITING_RECEIPT", "AWAITING_RECEIPT_INN"]
            and norm in ["xop", "xo'p", "hop", "mayli", "yaxshi", "boldi", "bo'ldi", "ok", "hop hozir", "xop hozir", "hop buladi", "xop bo'ladi"]
        )
        if is_waiting_phrase or is_state_agreement:
            if not re.search(r"\b(pul\s*tashladim|100\s*ming|440\s*ming|to'?lov\s*qildim)\b", norm):
                return {"intent": "WAITING_PROMISE", "ai_reply": None}

        # 3. Soat / Vaqt nosozligi
        if re.search(r"\b(soat|soati|vaqt|vaqti)\b", norm):
            if re.search(r"\b(xato|noto'g'ri|notugri|notogri|orqada|to'g'irlash|togirlash|tugirlash|adashgan|sozlash|o'tib|notog'ri)\b", norm):
                return {"intent": "CLOCK_PROBLEM", "ai_reply": None}

        # 4. IKPU / MXIK / Tovar kodi xatosi
        if re.search(r"\b(ikpu|mxik|shtrix\s*kod|kod\s*chiqmayapti|tovar\s*kodi|mknu|mkny)\b", norm):
            return {"intent": "IKPU_ERROR", "ai_reply": None}

        # 5. Suhbat konteksti (8 soatlik xotira ma'lumotlari)
        ctx_topic = getattr(session, "last_topic", None) if session else None
        ctx_oylik = getattr(session, "oylik_holat", None) if session else None
        ctx_fm = getattr(session, "fm_holat", None) if session else None
        ctx_offline = getattr(session, "offline_limit_error_active", False) if session else None
        history_shown = getattr(session, "history_shown", False) if session else False
        recent_dialog_txt = session.get_dialog_summary(4).lower() if (session and hasattr(session, "get_dialog_summary")) else ""

        # 5.1. Yillik fiskal modul to'lovi qachon kelishi / qachongacha yetishi so'rovi (CHECK_YEARLY_EXPIRATION)
        # Mijoz yillik to'lov qachon tugashi, qachon kelishi yoki qachongacha yetishini so'raganida
        # Bu oylik to'lovlar tarixi (PAYMENT_HISTORY) yoki to'lov bahsi (PAYMENT_DISPUTE) bilan aslo aralashmasligi shart!
        yearly_kw_pattern = r"(yillik\w*|fiskal\w*|feskal\w*|feskalmopdul\w*|fiskalmopdul\w*|modul\w*|mopdul\w*|fm\b|duk\b|yangi\s*texnologiyalar)"
        has_yearly_kw = bool(re.search(yearly_kw_pattern, norm))
        yearly_timing_kw = r"(qachon\w*|qachongacha|yetadi\w*|yetish\w*|muddat\w*|tuga\w*|amal\s*qil\w*|kelish\w*|keladi\w*)"

        if has_yearly_kw and re.search(yearly_timing_kw, norm):
            return {"intent": "CHECK_YEARLY_EXPIRATION", "ai_reply": None}

        # Agar mijoz "yo'q yillik to'lovni aytyapman" desa
        if re.search(r"\b(yo'?q|yuq)\b", norm) and has_yearly_kw:
            return {"intent": "CHECK_YEARLY_EXPIRATION", "ai_reply": None}

        # Z-Hisobot / Smena yopish so'rovi (Z_REPORT - bu to'lovlar tarixi emas!)
        if re.search(r"\b(z\s*hisobot\w*|z\s*otchet\w*|z\s*otchyot\w*|x\s*hisobot\w*|smena\s*yop\w*|kun\s*yop\w*)\b", norm):
            if re.search(r"\b(video\w*|vedio\w*|vidyo\w*|darslik\w*|qo'?llanma\w*|rolik\w*|chek\s*ur\w*|chek\s*chiqar\w*)\b", norm):
                return {"intent": "GUIDE_PRINT_CHECK_Z", "ai_reply": None}
            return {
                "intent": "Z_REPORT",
                "ai_reply": (
                    f"📊 *Z-hisobot (Smenani yopish) tartibi:*\n\n"
                    f"1. Kassa apparati ekranidagi asosiy menyudan **«Hisobotlar» (Отчеты)** bo'limiga kiring.\n"
                    f"2. **«Z-hisobot» (Smenani yopish)** bandini tanlang va tasdiqlang.\n"
                    f"3. Apparat kunlik savdo bo'yicha yakuniy fiskal chekni chiqaradi va yangi smena ochiladi.\n\n"
                    f"ℹ️ Kunlik savdo cheklarini har kuni smena yakunida yopish qonuniy talab hisoblanadi."
                )
            }

        # To'lovdan keyin qachon ochilishi / ishga tushishi (ACTIVATION_TIME)
        if re.search(r"\b(qachon\s*ochiladi|qachon\s*yoqiladi|qachon\s*ishga\s*tushadi|qachon\s*yonadi|blokdan\s*qachon|qancha\s*vaqtda\s*ochiladi)\b", norm):
            return {
                "intent": "ACTIVATION_TIME",
                "ai_reply": (
                    f"⚡ *To'lov amalga oshirilgach apparat qachon ishga tushadi?*\n\n"
                    f"To'lov qilinib, to'lov kvitansiyasi (chek rasmi) tasdiqlangach, kassa apparati odatda **10-15 daqiqa ichida** avtomatik tarzda blokdan ochiladi va ishlashni boshlaydi.\n\n"
                    f"Agar to'lov qilgan bo'lsangiz, iltimos, to'lov kvitansiyasini (chek rasmi yoki PDF) shu yerga yuboring."
                )
            }

        # Narxlar haqida umumiy savollar (PRICE_INFO)
        if re.search(r"\b(oylik\s*(?:to'?lov\s*)?(?:qancha|necha\s*pul|narxi)|yillik\s*(?:to'?lov\s*)?(?:qancha|necha\s*pul|narxi)|xizmat\s*narxi|narxlar\w*|qancha\s*to'?lanadi)\b", norm) and not re.search(r"\b(qarz\w*|qarzdor\w*)\b", norm):
            return {
                "intent": "PRICE_INFO",
                "ai_reply": (
                    f"💰 *Kassa apparatiga xizmat ko'rsatish tariflari:*\n\n"
                    f"• **Oylik abonent to'lovi:** oyiga **100 000 so'm** ({config.COMPANY_NAME} hisob raqamiga to'lanadi)\n"
                    f"• **Yillik Fiskal Modul to'lovi:** yiliga **440 000 so'm** (DUK Yangi Texnologiyalar hisob raqamiga to'lanadi)\n\n"
                    f"To'lov qilish bo'yicha video yoki rasmiy hisob raqam rekvizitlari kerak bo'lsa, bemalol xabar qoldiring."
                )
            }

        # To'lov hisob-kitobidan e'tiroz, norozilik yoki oldindan/kelgusi oyga to'langanligi da'vosi (FAQAT oylik abonent uchun)
        is_dispute_claim = bool(
            not has_yearly_kw and re.search(r"\b(yetadigan\w*|yetardi\w*|yetadi\w*|yetmaydi\w*|qo'?ygandimku\w*|to'?lagandimku\w*|to'?laganmanku\w*|to'?ladimku\w*|noto'?g'?ri\w*|xato\w*|adash\w*|qayerga\s*ketdi\w*|pulim\s*qani\w*|to'?lagan\s*pulim\w*|nega\s*qarz\w*|nimaga\s*qarz\w*|yil\s*oxirigacha\w*|keyingi\s*oyga\w*|kelasi\s*oyga\w*|avans\w*|ortiqcha\w*|qarzim\s*yo'?q\w*|qarz\s*emas\w*)\b", norm)
        )
        is_explicit_history = bool(
            not has_yearly_kw and not re.search(r"\b(z\s*hisobot|z\s*otchet|z\s*otchyot|x\s*hisobot|smena\s*yop)\b", norm) and re.search(r"\b(tarix\w*|hisobot\w*|xisobot\w*|oyma-oy\w*|oyma\s*oy\w*|kesimida\w*|qaysi\s*oylar\w*|oylar\s*bo'?yicha\w*)\b", norm)
        )

        # Agar mijozga allaqachon to'lovlar jadvali ko'rsatilgan bo'lsa va u norozilik bildirsa -> PAYMENT_DISPUTE
        if is_dispute_claim:
            if history_shown or ctx_topic in ["payment_history", "payment_dispute"] or "hisoboti" in recent_dialog_txt or (session and getattr(session, "inn", None)):
                return {"intent": "PAYMENT_DISPUTE", "ai_reply": None}
            else:
                return {"intent": "PAYMENT_HISTORY", "ai_reply": None}

        if is_explicit_history:
            return {"intent": "PAYMENT_HISTORY", "ai_reply": None}

        # 6. Hozir to'lov amalga oshirilganligi haqida xabar (Payment Made)
        if re.search(r"\b(to'ladim|tuladim|toladim|pul\s*o'tkazdim|pul\s*utkazdim|pul\s*tashladim|tashladim|utkazdim|o'tkazdim|100\s*ming\s*tashladim|to'lab\s*bo'ldim|tulab\s*buldim|chek\s*tashay|kvitansiya\s*tashay)\b", norm):
            if not re.search(r"\b(oldingi|avval|dekabr|oxirigacha|nega|nimaga|qani|tarix)\b", norm):
                return {"intent": "PAYMENT_MADE", "ai_reply": None}

        # 6.1 To'lov kvitansiyasini qanday yuklab olish/olish bo'yicha video qo'llanma so'rovi (DOWNLOAD_RECEIPT_GUIDE - Post 151)
        # Oylik abonent to'lash videosi (Post 148) bilan aslo adashmasligi shart:
        has_kvit = bool(re.search(r"\b(kvitansi\w*|kvitansa\w*|patta\w*|to'?lov\s*chek\w*|chek\w*)\b", norm))
        has_kvit_how = bool(
            (re.search(r"\b(qanday|qayerdan|qayerda|qanaqa|qattdan)\b", norm) and re.search(r"\b(yukla\w*|ol\w*|tashla\w*|top\w*|video\w*|darslik\w*|qo'?llanma\w*)\b", norm)) or
            re.search(r"\b(kvitansi\w*|chek\w*)\s*(?:yukla\w*|ol\w*)\b", norm) or
            re.search(r"\b(?:click\w*|clik\w*|payme\w*)\w*\s*(?:kvitansi\w*|chek\w*)", norm)
        )
        if has_kvit and has_kvit_how:
            if not re.search(r"\b(oylik\w*|abanit\w*|abonent\w*|to'?lash\s*videosi|tolash\s*videosi|to'?lov\s*videosi)\b", norm):
                return {"intent": "DOWNLOAD_RECEIPT_GUIDE", "ai_reply": None}

        # 6.2 Alohida video darsliklar so'rovlari:
        is_video_query = bool(re.search(r"\b(video\w*|vedio\w*|vidyo\w*|darslik\w*|qo'?llanma\w*|rolik\w*)\b", norm))

        # A) Barcha video darsliklar ro'yxati
        if re.search(r"\b(hamma|barcha|qanaqa|qaysi)\s*(?:video\w*|vedio\w*|darslik\w*)\b", norm) or norm in ["videolar", "vedyolar", "video darsliklar", "hamma videolar", "videolar royxati"]:
            return {"intent": "ALL_VIDEO_GUIDES", "ai_reply": None}

        # B) Ma'lumotlarni yuklash videosi (Post 138)
        if re.search(r"\b(ma'?lumot\w*|malumot\w*|baza\w*)\s*(?:yukla\w*|ol\w*)\b", norm) or (re.search(r"\b(ma'?lumot\w*|malumot\w*)\b", norm) and is_video_query):
            return {"intent": "GUIDE_DATA_LOAD", "ai_reply": None}

        # C) Tovar qo'shish va MXIK kod kiritish videosi (Post 15)
        if re.search(r"\b(tovar\w*|tavar\w*)\s*(?:q(?:o'?|u)sh\w*|kirit\w*)\b", norm):
            return {"intent": "GUIDE_ADD_PRODUCT", "ai_reply": None}

        # D) Tovar narxini o'zgartirish videosi (Post 140)
        if re.search(r"\b(?:tovar\w*|tavar\w*)?\s*narx\w*\s*(?:o'?zgartir\w*|almashtir\w*|yangila\w*)\b", norm):
            return {"intent": "GUIDE_CHANGE_PRICE", "ai_reply": None}

        # E) Tovarni atkaz qilish / bekor qilish videosi (Post 53)
        if re.search(r"\b(atkaz\w*|otkaz\w*)\b", norm) or (re.search(r"\b(qaytar\w*|bekor\s*qil\w*)\b", norm) and (is_video_query or re.search(r"\b(chek|tovar|tavar)\b", norm))):
            return {"intent": "GUIDE_CANCEL_CHECK", "ai_reply": None}

        # F) Chek urish va X/Z hisobot videosi (Post 2)
        if (re.search(r"\b(chek\s*ur\w*|z\s*hisobot|x\s*hisobot|smena\s*yop\w*)\b", norm) and is_video_query):
            return {"intent": "GUIDE_PRINT_CHECK_Z", "ai_reply": None}

        # G) Dasturni yangilash videosi (Post 142)
        if re.search(r"\b(dastur\w*|ilova\w*|app\w*|kassa\w*)\s*(?:yangila\w*|obnovlen\w*)\b", norm):
            return {"intent": "GUIDE_UPDATE_APP", "ai_reply": None}

        # H) 2D skaner videosi (Post 27)
        if re.search(r"\b(skaner\w*|2d\b)\b", norm) and (is_video_query or re.search(r"\b(ulash|ishlatish)\b", norm)):
            return {"intent": "GUIDE_SCANNER_2D", "ai_reply": None}

        # I) Markirovkani o'chirish videosi (Post 139)
        if re.search(r"\b(markirovk\w*|markirofk\w*)\s*(?:o'?chir\w*|yoq\w*|tuzat\w*)\b", norm):
            return {"intent": "GUIDE_DISABLE_MARKING", "ai_reply": None}

        # To'lov harakatlari va so'rovlari:
        # to'lamoqchi, tulamoqchi, tolamoqchi, tulamoqchiydimda, to'lamoqchi edim, to'lasam, to'lay, to'lash, to'lov, rekvizit, shot, click, video va h.k.
        pay_action_regex = r"(t(?:o'?|o|u)la\w*|t(?:o'?|o|u)lov\w*|o'?tkaz\w*|utkaz\w*|otkaz\w*|(?:pul|shot|rekvizit|to'?lov|\d+\s*ming)\s*(?:ni\s*)?tashla\w*|tashla\w*\s*(?:pul|shot|rekvizit)|shot\w*|hisob\s*raqam\w*|rekvizit\w*|click\w*|clik\w*|video\w*|darslik\w*|qo'?llanma\w*|qanday\s*to'?la|qayerga\s*to'?la)"
        check_action_regex = r"(tekshir\w*|qarz\w*|qancha|tugag\w*|kelgan\w*|muddat\w*|bormi|holati|shekilli|proverit|qachon\w*|amal\s*qil\w*|bil\w*|k(?:o'?|u)r\w*)"

        has_monthly = bool(re.search(r"\b(oylik\w*|abonent\w*|oyiga|100\s*ming|100000)\b", norm))
        has_yearly = bool(re.search(r"\b(yillik\w*|fiskal\w*|modul\w*|fm\b|duk\b|yangi\s*texnologiyalar|440\s*ming|440000)\b", norm))

        has_pay_action = bool(re.search(pay_action_regex, norm))
        has_check_action = bool(re.search(check_action_regex, norm))

        # Suhbat konteksti (Oldingi mavzu va holatlar):
        ctx_topic = getattr(session, "last_topic", None) if session else None
        ctx_oylik = getattr(session, "oylik_holat", None) if session else None
        ctx_fm = getattr(session, "fm_holat", None) if session else None
        ctx_offline = getattr(session, "offline_limit_error_active", False) if session else None

        # 7. Oylik to'lov niyati (PAY_MONTHLY - Post 148 video va Post 85 rekvizit)
        # Oylik to'lash videosi yoki rekvizit so'ralganda:
        if has_monthly and re.search(r"\b(video\w*|darslik\w*|qo'?llanma\w*)\b", norm):
            return {"intent": "PAY_MONTHLY", "ai_reply": None}
        # Aniq oylik + to'lov so'zlari (masalan: "oylik tulamoqchiydimda", "oylik tolamoqchiman", "oylik to'lasam degandim", "oylik rekvizit tashlang")
        if has_monthly and has_pay_action and not has_check_action:
            return {"intent": "PAY_MONTHLY", "ai_reply": None}
        if has_monthly and re.search(r"\b(t(?:o'?|o|u)lamoqchi\w*|to'?lash|to'?lov|rekvizit\w*|shot\w*|click\w*)\b", norm):
            return {"intent": "PAY_MONTHLY", "ai_reply": None}

        # Kontekstdan kelib chiqib oylik yoki yillik to'lovni aniqlash
        # (mijoz "oylik" yoki "yillik" so'zini takrorlamasdan "ha qanday to'layman buni", "shot bering", "qayerga to'lay", "qanaqa to'laydi" desa):
        if not has_monthly and not has_yearly and has_pay_action and not has_check_action:
            if ctx_topic in ["check_yearly", "pay_yearly"] or ctx_fm == "qarzdor" or ctx_offline:
                return {"intent": "PAY_YEARLY", "ai_reply": None}
            if ctx_topic in ["check_monthly", "pay_monthly", "payment_history", "payment_dispute"] or ctx_oylik in ["qarzdor", "toza"] or (session and getattr(session, "inn", None)):
                return {"intent": "PAY_MONTHLY", "ai_reply": None}
            # Agar kontekst bo'lmasa ham "qanday to'layman", "qayerga to'lay", "clickdan to'lash" desa oylik abonentga yo'naltiriladi
            if re.search(r"\b(qanday|qannay|qayerga|shot\w*|click\w*|kartadan|tartib\w*)\b", norm):
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

        # 12. Apparat ishlamayapti / Nosozlik / Qo'shib bering / Chek urilmayapti (POS_BROKEN)
        pos_nouns = r"\b(aparat\w*|apparat\w*|kassa\w*|terminal\w*|smartone|p3|mashinka\w*)\b"
        has_pos_noun = bool(re.search(pos_nouns, norm))

        act_verbs = r"\b(q(?:o'?|u)sh\w*|och\w*|yoq\w*|ul(?:a|an)\w*|faollashtir\w*|k(?:o'?|u)r\w*|t(?:o'?|u)g'irl\w*|tuzat\w*|qarab\w*)\b"
        has_act_verb = bool(re.search(act_verbs, norm))

        check_noun = bool(re.search(r"\b(chek\w*|savdo\w*)\b", norm))

        fail_verbs = r"\b(ur(?:o|a)[lmv]?\w*|urib\s*b(?:o'?|u)m\w*|urmay\w*|chiq(?:a|a)r\w*m\w*|chiq\w*may\w*|ishla\w*m\w*|to'?xta\w*|qot\w*|o'?ch\w*|o'?xsha\w*m\w*|blok\w*|ashebka\w*|nosoz\w*|xato\w*|zaryad\w*|yonmay\w*|quvvat\w*|ekran\w*)\b"
        has_fail_verb = bool(re.search(fail_verbs, norm))

        if (has_pos_noun or check_noun) and (has_act_verb or has_fail_verb):
            return {"intent": "POS_BROKEN", "ai_reply": None}
        if has_fail_verb and (has_pos_noun or check_noun or has_act_verb):
            return {"intent": "POS_BROKEN", "ai_reply": None}
        if re.search(r"\b(ashebka|nosozlik|xatolik)\b", norm):
            return {"intent": "POS_BROKEN", "ai_reply": None}
        if re.search(r"\b(savdo|ish)\s*to'?xta", norm):
            return {"intent": "POS_BROKEN", "ai_reply": None}
        if re.search(r"\b(chek\s*ur|chek\s*chiq)", norm) and (has_fail_verb or has_act_verb):
            return {"intent": "POS_BROKEN", "ai_reply": None}
        if re.search(r"\b(q(?:o'?|u)sh\w*|och\w*|yoq\w*|ul\w*)\s*(?:ber\w*|vor\w*|yubor\w*|ishlat\w*)", norm):
            return {"intent": "POS_BROKEN", "ai_reply": None}

        # 12.1. Narxlar haqida so'rov (PRICE_INFO)
        if re.search(r"\b(oylik\s*(?:to'?lov\s*)?(?:qancha|necha\s*pul|narxi)|yillik\s*(?:to'?lov\s*)?(?:qancha|necha\s*pul|narxi)|xizmat\s*narxi|narxlar\w*|qancha\s*to'?lanadi)\b", norm):
            return {
                "intent": "PRICE_INFO",
                "ai_reply": (
                    f"💰 *Kassa apparatiga xizmat ko'rsatish tariflari:*\n\n"
                    f"• **Oylik abonent to'lovi:** oyiga **100 000 so'm** ({config.COMPANY_NAME} hisob raqamiga to'lanadi)\n"
                    f"• **Yillik Fiskal Modul to'lovi:** yiliga **440 000 so'm** (DUK Yangi Texnologiyalar hisob raqamiga to'lanadi)\n\n"
                    f"To'lov qilish bo'yicha video yoki rasmiy hisob raqam rekvizitlari kerak bo'lsa, bemalol xabar qoldiring."
                )
            }

        # 12.2. Ish vaqti va tartibi (WORKING_HOURS)
        if re.search(r"\b(ish\s*vaqt\w*|ish\s*kun\w*|soat\s*nechagacha|qachongacha\s*ishla\w*|shanba\w*|yakshanba\w*|dam\s*olish\w*)\b", norm):
            return {
                "intent": "WORKING_HOURS",
                "ai_reply": (
                    f"🏢 *{config.COMPANY_NAME} ish tartibi va vaqtlari:*\n\n"
                    f"• **Dushanba — Shanba:** 09:00 dan 18:00 gacha\n"
                    f"• **Yakshanba:** Dam olish kuni\n\n"
                    f"📍 *Manzilimiz:* Qashqadaryo viloyati, Shahrisabz shahar, Sheroziy ko'chasi 1-uy.\n"
                    f"📞 *Telefonlar:* {config.COMPANY_PHONE}, +998 91 945 32 89"
                )
            }

        # 12.3. Z-hisobot / Smena yopish (Z_REPORT)
        if re.search(r"\b(z\s*hisobot\w*|z\s*otchet\w*|z\s*otchyot\w*|x\s*hisobot\w*|smena\s*yop\w*|kun\s*yop\w*)\b", norm):
            return {
                "intent": "Z_REPORT",
                "ai_reply": (
                    f"📊 *Z-hisobot (Smenani yopish) tartibi:*\n\n"
                    f"1. Kassa apparati ekranidagi asosiy menyudan **«Hisobotlar» (Отчеты)** bo'limiga kiring.\n"
                    f"2. **«Z-hisobot» (Smenani yopish)** bandini tanlang va tasdiqlang.\n"
                    f"3. Apparat kunlik savdo bo'yicha yakuniy fiskal chekni chiqaradi va yangi smena ochiladi.\n\n"
                    f"ℹ️ Kunlik savdo cheklarini har kuni smena yakunida yopish qonuniy talab hisoblanadi."
                )
            }

        # 12.4. Qaytarish cheki / Xato chekni bekor qilish (REFUND_CHECK)
        if re.search(r"\b(qaytarish\s*chek\w*|vozvrat\w*|chek\w*\s*bekor|bekor\s*qil\w*|xato\s*chek\w*|noto'?g'?ri\s*chek\w*|chek\w*\s*qaytar\w*|atkaz\w*|otkaz\w*)\b", norm):
            if re.search(r"\b(video\w*|vedio\w*|vidyo\w*|darslik\w*|qo'?llanma\w*|rolik\w*|atkaz\w*|otkaz\w*)\b", norm):
                return {"intent": "GUIDE_CANCEL_CHECK", "ai_reply": None}
            return {
                "intent": "REFUND_CHECK",
                "ai_reply": (
                    f"↩️ *Xato urilgan chekni bekor qilish (Qaytarish cheki):*\n\n"
                    f"1. Kassa dasturining bosh menyusidan **«Qaytarish» (Возврат)** bo'limiga kiring.\n"
                    f"2. Bekor qilinishi lozim bo'lgan chek raqami yoki fiskal belgisini (FM raqamini) kiriting.\n"
                    f"3. Tovarni tanlab, **«Qaytarish chekini chiqarish»** tugmasini bosing.\n\n"
                    f"Qo'shimcha texnik yordam kerak bo'lsa, xato urilgan chek rasmini yuboring, mutaxassislarimiz yordam berishadi."
                )
            }

        # 12.5. To'lovdan so'ng apparat qachon ochilishi (ACTIVATION_TIME)
        if re.search(r"\b(qachon\s*ochiladi|qachon\s*yoqiladi|qachon\s*ishga\s*tushadi|qachon\s*yonadi|blokdan\s*qachon|qancha\s*vaqtda\s*ochiladi)\b", norm):
            return {
                "intent": "ACTIVATION_TIME",
                "ai_reply": (
                    f"⚡ *To'lov amalga oshirilgach apparat qachon ishga tushadi?*\n\n"
                    f"To'lov qilinib, to'lov kvitansiyasi (chek rasmi) tasdiqlangach, kassa apparati odatda **10-15 daqiqa ichida** avtomatik tarzda blokdan ochiladi va ishlashni boshlaydi.\n\n"
                    f"Agar to'lov qilgan bo'lsangiz, iltimos, to'lov kvitansiyasini (chek rasmi yoki PDF) shu yerga yuboring."
                )
            }

        # 12.6. SIM-karta va Internet aloqasi (SIM_CARD_INFO)
        if re.search(r"\b(sim\s*karta\w*|simkarta\w*|megabayt\w*|trafik\w*)\b", norm):
            return {
                "intent": "SIM_CARD_INFO",
                "ai_reply": (
                    f"📶 *Kassa apparatining SIM-kartasi va Internet aloqasi:*\n\n"
                    f"1. SIM-karta raqamini bilish uchun kassa apparatining **«Sozlamalar» (Настройки) -> «SIM-karta holati»** bo'limiga kiring yoki apparat orqa qopqog'idagi stikerga qarang.\n"
                    f"2. Kassa apparatini SIM-karta o'rniga do'koningizdagi **Wi-Fi** tarmog'iga ulab ham uzluksiz ishlatishingiz mumkin.\n\n"
                    f"SIM-karta raqamini aniqlashda qiyinchilik bo'lsa, apparat orqasidagi stiker rasmini yuboring."
                )
            }

        # 12.7. YTT va JSHSHIR bo'yicha tushuntirish (YTT_JSHSHIR_GUIDE)
        if re.search(r"\b(ytt\b|yakka\s*tartib\w*|inn\s*yo'?q|inn\s*yuq|innimiz\s*yo'?q|jshshir\s*nima|jshshir\s*qayerda|pinfl)\b", norm):
            return {
                "intent": "YTT_JSHSHIR_GUIDE",
                "ai_reply": (
                    f"👤 *Yakka tartibdagi tadbirkorlar (YTT) uchun:*\n\n"
                    f"Agar sizda yuridik shaxsning 9 xonali STIR (INN) raqami bo'lmasa, pasportingizdagi yoki kassa chekining eng pastki qismida ko'rsatilgan **14 xonali JSHSHIR (PINFL)** raqamingizni yuboring.\n\n"
                    f"Bot 14 xonali JSHSHIR raqami orqali ham barcha to'lovlarni to'liq tekshirib bera oladi."
                )
            }

        # 12.8. Kassa apparati qog'ozi (CASSETTE_PAPER)
        if re.search(r"\b(termolenta\w*|kassa\s*qog'?oz\w*|chek\s*qog'?oz\w*|lenta\w*)\b", norm) and not re.search(r"\b(hisobot|kvitansiya|chek\s*chiqarmayapti)\b", norm):
            return {
                "intent": "CASSETTE_PAPER",
                "ai_reply": (
                    f"🧾 *Kassa apparati qog'ozi (termolenta):*\n\n"
                    f"SmartOne va PAX P3 kassa apparatlari uchun standart **57 mm** o'lchamdagi termolentalardan foydalaniladi.\n\n"
                    f"Kassa lentalarini bizning ofisimizdan yoki har qanday kantselyariya do'konlaridan xarid qilishingiz mumkin.\n"
                    f"🏢 *Ofisimiz:* Qashqadaryo viloyati, Shahrisabz shahar, Sheroziy ko'chasi 1-uy."
                )
            }

        # 12.9. Yangi apparat sotib olish (BUY_POS)
        if re.search(r"\b(aparat\s*sotib|kassa\s*sotib|yangi\s*aparat|kassa\s*olmoqchi|aparat\s*narxi|kassa\s*narxi|sotib\s*olish)\b", norm):
            return {
                "intent": "BUY_POS",
                "ai_reply": (
                    f"🛒 *Online nazorat kassa apparatlari xaridi:*\n\n"
                    f"Kompaniyamizda zamonaviy **SmartOne** va **PAX P3** online kassa apparatlari mavjud bo'lib, ular Davlat Soliq Qo'mitasi talablariga to'liq javob beradi.\n\n"
                    f"Apparat narxlari, muddatli to'lov va ro'yxatdan o'tkazish bo'yicha mutaxassisimiz siz bilan bog'lanishi uchun telefon raqamingizni yozib qoldiring yoki ofisimizga tashrif buyuring."
                )
            }

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

    def build_action_plan(self, intent: str, text: str, session=None, ai_reply: str=None) -> dict:
        """
        AI va Bot integratsiyasining aqlli harakatlar rejasi (Action Plan).
        Mijozning imlo xatolar, ko'cha tili yoki shevalarda yozgan matnini chuqur tahlil qilib,
        botga keyingi qadamda qaysi ma'lumotlarni tekshirish yoki qanday harakat qilish lozimligini
        aniq ko'rsatib beradi.
        """
        plan = {
            "intent": intent,
            "underlying_goal": "",
            "next_action": "",
            "explanation": "",
            "ai_reply": ai_reply
        }

        if intent == "POS_BROKEN":
            plan["underlying_goal"] = "Mijoz kassa apparatida chek urmoqchi yoki apparatni ishlatmoqchi, biroq apparat ishlamayapti / bloklangan / xatolik bermoqda."
            plan["next_action"] = "PROCESS_POS_ISSUE"
            plan["explanation"] = "Bot birinchi navbatda INN orqali oylik abonent holatini tekshirishi kerak. Agar oylik qarzdor bo'lsa, to'lov rekviziti beriladi. Agar oylik toza bo'lsa, xatolik (oshibka) sababini aniqlash uchun apparat ekrani rasmi so'raladi. Rasm olingach darhol texnikka ulanadi."

        elif intent == "PAYMENT_HISTORY":
            plan["underlying_goal"] = "Mijoz oylik to'lovlar tarixini va oylar kesimidagi hisobotni bilmoqchi."
            plan["next_action"] = "SHOW_PAYMENT_HISTORY"
            plan["explanation"] = "Bot INN bo'yicha to'lovlar tarixini chiqarib berishi kerak. Agar INN ma'lum bo'lmasa, INN so'raydi."

        elif intent == "PAYMENT_DISPUTE":
            plan["underlying_goal"] = "Mijoz keyingi oy uchun ham to'lov qilganini yoki to'lov hisobotidan norozi ekanligini bildirmoqda."
            plan["next_action"] = "HANDLE_PAYMENT_DISPUTE"
            plan["explanation"] = "Bot mijozga e'tirozi bo'yicha to'lov kvitansiyasini (cheki yoki PDF) yuborishni so'rashi kerak, shunda mutaxassislar tekshirib hisobga oladi."

        elif intent == "OFFICE_LOCATION":
            plan["underlying_goal"] = "Mijoz kompaniya ofisi, manzili yoki lokatsiyasini so'ramoqda."
            plan["next_action"] = "SEND_OFFICE_LOCATION"
            plan["explanation"] = "Bot ofis manzili, lokatsiya ma'lumotlari va aloqa telefonlarini yuborishi kerak."

        elif intent == "DOWNLOAD_RECEIPT_GUIDE":
            plan["underlying_goal"] = "Mijoz to'lov kvitansiyasini (chek) qanday yuklab olishni bilmoqchi."
            plan["next_action"] = "SEND_RECEIPT_GUIDE"
            plan["explanation"] = "Bot Click/Payme orqali to'lov kvitansiyasini yuklab olish bo'yicha 151-postdagi video qo'llanmani yuborishi kerak."

        elif intent == "ALL_VIDEO_GUIDES":
            plan["underlying_goal"] = "Mijoz barcha video darsliklar ro'yxatini ko'rmoqchi."
            plan["next_action"] = "SEND_ALL_VIDEO_GUIDES"
            plan["explanation"] = "Bot barcha rasmiy video darsliklar ro'yxatini havolalari bilan taqdim etishi kerak."

        elif intent == "GUIDE_DATA_LOAD":
            plan["underlying_goal"] = "Mijoz kassa apparatiga ma'lumotlarni yuklash bo'yicha video qo'llanma so'radi."
            plan["next_action"] = "SEND_DATA_LOAD_GUIDE"
            plan["explanation"] = "Bot 138-postdagi ma'lumotlarni yuklash videosini yuborishi kerak."

        elif intent == "GUIDE_ADD_PRODUCT":
            plan["underlying_goal"] = "Mijoz tovar qo'shish va MXIK kod kiritish videosini so'radi."
            plan["next_action"] = "SEND_ADD_PRODUCT_GUIDE"
            plan["explanation"] = "Bot 15-postdagi tovar qo'shish va MXIK kiritish videosini yuborishi kerak."

        elif intent == "GUIDE_CHANGE_PRICE":
            plan["underlying_goal"] = "Mijoz tovar narxini o'zgartirish bo'yicha video darslik so'radi."
            plan["next_action"] = "SEND_CHANGE_PRICE_GUIDE"
            plan["explanation"] = "Bot 140-postdagi tovar narxini o'zgartirish videosini yuborishi kerak."

        elif intent == "GUIDE_CANCEL_CHECK":
            plan["underlying_goal"] = "Mijoz tovarni atkaz qilish / bekor qilish videosini so'radi."
            plan["next_action"] = "SEND_CANCEL_CHECK_GUIDE"
            plan["explanation"] = "Bot 53-postdagi tovarni atkaz qilish va qayta urish videosini yuborishi kerak."

        elif intent == "GUIDE_PRINT_CHECK_Z":
            plan["underlying_goal"] = "Mijoz chek urish va X/Z hisobot olish videosini so'radi."
            plan["next_action"] = "SEND_PRINT_CHECK_Z_GUIDE"
            plan["explanation"] = "Bot 2-postdagi chek urish va X/Z hisobot videosini yuborishi kerak."

        elif intent == "GUIDE_UPDATE_APP":
            plan["underlying_goal"] = "Mijoz kassa dasturini yangilash videosini so'radi."
            plan["next_action"] = "SEND_UPDATE_APP_GUIDE"
            plan["explanation"] = "Bot 142-postdagi dastur yangilash videosini yuborishi kerak."

        elif intent == "GUIDE_SCANNER_2D":
            plan["underlying_goal"] = "Mijoz 2D skaner ishlatish videosini so'radi."
            plan["next_action"] = "SEND_SCANNER_2D_GUIDE"
            plan["explanation"] = "Bot 27-postdagi 2D skaner videosini yuborishi kerak."

        elif intent == "GUIDE_DISABLE_MARKING":
            plan["underlying_goal"] = "Mijoz markirovkani o'chirish videosini so'radi."
            plan["next_action"] = "SEND_DISABLE_MARKING_GUIDE"
            plan["explanation"] = "Bot 139-postdagi markirovkani o'chirish videosini yuborishi kerak."

        elif intent == "CLOCK_PROBLEM":
            plan["underlying_goal"] = "Kassa apparatida soat orqada qolgan yoki vaqt noto'g'ri ko'rsatmoqda."
            plan["next_action"] = "SEND_CLOCK_GUIDE"
            plan["explanation"] = "Bot soatni to'g'irlash video qo'llanmasi va parollarni yuborishi kerak."

        elif intent == "IKPU_ERROR":
            plan["underlying_goal"] = "Kassa apparatida IKPU / tovar kodi bo'yicha xatolik yuzaga kelgan."
            plan["next_action"] = "PROCESS_IKPU"
            plan["explanation"] = "Bot IKPU videosini yuborishi, agar video allaqachon yuborilgan bo'lsa darhol mas'ul texnikka ulashi lozim."

        elif intent == "PAY_MONTHLY":
            plan["underlying_goal"] = "Mijoz oylik abonent to'lovini amalga oshirmoqchi."
            plan["next_action"] = "SEND_MONTHLY_PAY"
            plan["explanation"] = "Bot oylik to'lov rekvizitlari va Click video qo'llanmasini yuborishi kerak."

        elif intent == "PAY_YEARLY":
            plan["underlying_goal"] = "Mijoz yillik fiskal modul to'lovini to'lamoqchi."
            plan["next_action"] = "SEND_YEARLY_PAY"
            plan["explanation"] = "Bot yillik to'lov hisob raqami rekvizitlarini yuborishi kerak."

        elif intent == "CHECK_MONTHLY":
            plan["underlying_goal"] = "Mijoz oylik to'lovi holatini yoki qarzini bilmoqchi."
            plan["next_action"] = "CHECK_MONTHLY"
            plan["explanation"] = "Bot INN bo'yicha oylik to'lovni tekshirishi yoki INN so'rashi kerak."

        elif intent == "CHECK_YEARLY":
            plan["underlying_goal"] = "Mijoz fiskal modul muddatini tekshirmoqchi."
            plan["next_action"] = "CHECK_YEARLY"
            plan["explanation"] = "Bot FM raqami bo'yicha tekshirishi yoki FM so'rashi kerak."

        elif intent == "CHECK_YEARLY_EXPIRATION":
            plan["underlying_goal"] = "Mijoz yillik fiskal modul qachongacha yetishi yoki qachon tugashini bilmoqchi."
            plan["next_action"] = "EXPLAIN_YEARLY_LIMITATION"
            plan["explanation"] = "Fiskal modulning kelgusi aniq sanasi tizimda ko'rinmasligini, faqat hozir to'lovga kelgan yoki faolligini tekshirish mumkinligini tushuntirishi lozim."

        elif intent == "PAYMENT_MADE":
            plan["underlying_goal"] = "Mijoz to'lov amalga oshirganini bildirdi."
            plan["next_action"] = "REQUEST_RECEIPT"
            plan["explanation"] = "Bot to'lovni hisobga olish uchun kvitansiya (chek rasmi yoki PDF) so'rashi lozim."

        elif intent == "OPERATOR":
            plan["underlying_goal"] = "Mijoz texnik mutaxassis / usta / admin bilan bog'lanmoqchi."
            plan["next_action"] = "CONNECT_OPERATOR"
            plan["explanation"] = "Agar rasm bo'lsa darhol texnikka ulanadi, aks holda apparat ekranidagi muammoni rasmga olib yuborish aytiladi."

        elif intent == "FORGET":
            plan["underlying_goal"] = "Mijoz suhbatni tozalash va unutishni so'ramoqda."
            plan["next_action"] = "RESET_SESSION"
            plan["explanation"] = "Bot sessiya xotirasini tozalab, yangidan boshlashi kerak."

        elif intent == "GENERAL_REKVIZIT":
            plan["underlying_goal"] = "Mijoz to'lov rekvizitini so'radi, lekin oylik yoki yillik ekanligini aytmadi."
            plan["next_action"] = "ASK_REKVIZIT_TYPE"
            plan["explanation"] = "Bot oylik yoki yillik rekvizit kerakligini so'rashi kerak."

        elif intent == "GREETING":
            plan["underlying_goal"] = "Mijoz salomlashdi."
            plan["next_action"] = "REPLY_GREETING"
            plan["explanation"] = "Bot muloyim va samimiy salomlashib, yordam taklif qiladi."

        elif intent == "GENERAL_ANSWER":
            plan["underlying_goal"] = "Umumiy murojaat, manzil, telefon yoki minnatdorchilik."
            plan["next_action"] = "REPLY_GENERAL"
            plan["explanation"] = "Bot tayyor samimiy javobni qaytaradi."

        elif intent == "WAITING_PROMISE":
            plan["underlying_goal"] = "Mijoz so'ralgan ma'lumotni (INN, FM, rasm, chek) ayni damda tayyorlayotgani yoki hozir yuborishini aytib, kutib turishni so'ramoqda."
            plan["next_action"] = "ACKNOWLEDGE_WAITING"
            plan["explanation"] = "Bot odam texnik kabi muloyim javob berib, ma'lumot kelishi bilan darhol ko'rib berishini bildiradi va kutish holatini saqlab qoladi."

        else:
            plan["underlying_goal"] = "Noma'lum murojaat."
            plan["next_action"] = "UNKNOWN"
            plan["explanation"] = "Mijozga kassa apparati tekshiruvi uchun INN so'rash taklif qilinadi."

        return plan

    def analyze_message(self, text, session=None):
        """
        Mijoz xabarini sun'iy intellekt (Semantik NLP + Google Gemini) orqali tahlil qiladi.
        Faqat matnli xabarlar uchun ishlaydi (toza raqamlar bot tomonidan tekshiriladi).
        Natija sifatida to'liq ActionPlan obyektini qaytaradi.
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
            return self.build_action_plan(
                semantic_res["intent"],
                clean_text,
                session=session,
                ai_reply=semantic_res.get("ai_reply")
            )

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

            history_ctx = ""
            if session and hasattr(session, "get_dialog_summary"):
                summary = session.get_dialog_summary(6)
                if summary:
                    history_ctx = f"\n\nOxirgi 8 soatlik suhbat tarixi:\n{summary}"

            user_prompt = f"{SYSTEM_PROMPT}{history_ctx}\n\nMijoz xabari{ctx}: \"{clean_text_prompt}\""

            for model_name in self.models_to_try:
                try:
                    res = self._call_gemini_api(model_name, user_prompt, timeout=5)
                    if res and res.get("intent"):
                        return self.build_action_plan(
                            res["intent"],
                            clean_text,
                            session=session,
                            ai_reply=res.get("ai_reply")
                        )
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
