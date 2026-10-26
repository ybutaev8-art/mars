"""
Kassa apparati va to'lov kvitansiyalari rasmlarini tahlil qilish moduli.
- Rasmdan matnlarni OCR orqali aniqlaydi.
- Rasm toifasini aniqlaydi (KVITANSIYA, KASSA_APARAT, yoki BOSHQA).
- POS apparati ekranning yuqori qismidagi internet va soat holatini tekshiradi.
"""
import re
import os
from PIL import Image

# Kvitansiya, to'lov cheki va bank operatsiyalari kalit so'zlari
RECEIPT_KEYWORDS = [
    "kvitansiya", "квитанция", "chek raqami", "chek no", "чек №", "чек номер",
    "amaliyot muvaffaqiyatli", "муваффақиятли", "операция успешна", "o'tkazma muvaffaqiyatli",
    "муваффақиятли тўланди", "muvaffaqiyatli to'landi", "muvaffaqiyatli tolandi",
    "to'lov topshirig'nomasi", "tolov topshirignomasi", "платежное поручение",
    "мемориальный ордер", "patta", "патт", "elektron kvitansiya", "электронная квитанция",
    "click evolution", "click", "payme", "uzum", "apelsin", "paynet",
    "anorbank", "agrobank", "ipoteka", "kapitalbank", "halyk", "xalq banki",
    "yechiladigan summa", "pul yechish", "to'lovni saqlash", "kvitansiyani yuklab olish",
    "kvitansiya yukl", "скачать квитанцию", "скачать чек", "talaba", "kontrakt to'lovi",
    "to'lov maqsadi", "tolov maqsadi", "назначение платежа", "qabul qiluvchi", "получатель",
    "yuboruvchi", "отправитель", "to'lovchi", "плательщик", "komissiya", "комиссия", "tranzaksiya"
]

# Kassa apparati va POS xatoliklariga oid kalit so'zlar
POS_KEYWORDS = [
    # Ruscha kassa va xatolik terminlari
    "ошибка", "фискал", "касс", "smartone", "smartcne", "p3", "ofd", "офлайн", "offline", 
    "счета", "счету", "по счету", "интервал", "оплата", "оплатить", "summa", "so'm", "qarzdorlik", "fmo", 
    "xatolik", "terminal", "uz", "pax", "sunmi", "bankpro", "оплачено", "к оплате",
    "закрыть чек", "закрыть", "продажа", "возврат", "смена", "отчет", "не фискальный",
    "продолжительности", "режима", "добавить скидку", "наличные", "карта",
    "время", "дата", "итог", "итoг", "скидка", "электрон", "приход", "внесение",
    "результатов", "фискализации",
    
    # O'zbekcha / lotincha kassa terminlari
    "fiskal", "kassa", "to'lov", "tulov", "xato", "xatolik", "chek", "aparat",
    "fiskallash", "so'm", "som", "uzkassa", "oflayn", "onlayn",
    # IKPU kalit so'zlari
    "икпу", "ikpu", "устарела", "ustarela", "yctapena", "yctapen", "mkny", "mknu", "mkn",
    "проверка кода", "выберите товар", "bbi6epute", "tobap", "товар", "maxsulot", "shirinliklar",

    # LCD ekrandan olingan OCR transliteratsiya variantlari (lotincha o'qilgan ruscha so'zlar)
    "onnatutb", "onnatu", "onnat", "oplatit", "oplata", "cetry", "tlo cetry", "po schetu",
    "kontare", "kontat", "k oplate", "k1c04", "k1c", "kac0", "kacca", "zakrit"
]

TOP_BRANDS = ["smartone", "smartcne", "smart-one", "bankpro", "pax", "sunmi", "ingenico", "uzkassa", "a930", "n5"]
NET_PATTERN = re.compile(r"\b(?:4g|3g|2g|lte|e|h\+|wifi|wi-fi|ucell|beeline|mobiuz|uztelecom|sim|gprs)\b", re.IGNORECASE)

def is_valid_time(text: str) -> bool:
    """Soat formati (masalan: 15:49, 9:32, 11:40, 011:40) ekanligini tekshiradi."""
    m = re.search(r"([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)", text)
    if not m:
        return False
    if "." in text:
        if re.search(r"\d{3,}\.\d{2}", text) or "0.00" in text:
            return False
    return True

_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_engine = RapidOCR()
        except Exception as e:
            print(f"[OCR] RapidOCR yuklashda xatolik: {e}")
            _ocr_engine = False
    return _ocr_engine

def classify_image_type(image_path: str) -> dict:
    """
    Rasm qaysi toifaga tegishli ekanligini OCR va aqlli qoidalar orqali aniqlaydi:
    - "KVITANSIYA": To'lov kvitansiyasi, chek, bank to'lov topshirig'nomasi, Click/Payme o'tkazmasi
    - "KASSA_APARAT": POS apparati ekrani, kassa qurilmasi (SmartOne, P3, PAX, Sunmi), xatolik oynasi
    - "BOSHQA": Umuman boshqa narsa (odam, tabiat, mashina, rasm, noaloqador skrinshot)
    
    Qaytaradi:
    {
        "category": "KVITANSIYA" | "KASSA_APARAT" | "BOSHQA",
        "reason": str,
        "text": str,
        "pos_analysis": dict or None
    }
    """
    if not os.path.exists(image_path):
        return {"category": "BOSHQA", "reason": "Fayl topilmadi", "text": "", "pos_analysis": None}

    try:
        with Image.open(image_path) as img:
            width, height = img.size
    except Exception as e:
        return {"category": "BOSHQA", "reason": f"Rasm ochilmadi: {e}", "text": "", "pos_analysis": None}

    ocr = get_ocr_engine()
    if not ocr:
        # OCR bo'lmasa xatolik chiqarmasdan o'tkaziladi
        return {"category": "KASSA_APARAT", "reason": "OCR mavjud emas", "text": "", "pos_analysis": {"status": "VALID_POS"}}

    try:
        ocr_res, _ = ocr(image_path)
    except Exception as e:
        print(f"[OCR] Tahlil jarayonida xatolik: {e}")
        return {"category": "KASSA_APARAT", "reason": f"OCR xatosi: {e}", "text": "", "pos_analysis": {"status": "VALID_POS"}}

    if not ocr_res:
        return {
            "category": "BOSHQA",
            "reason": "Rasmda hech qanday matn yoki apparat belgilari aniqlanmadi",
            "text": "",
            "pos_analysis": None
        }

    all_texts = []
    top_bar_found = False
    top_bar_reasons = []
    status_bar_threshold_y = height * 0.45

    for item in ocr_res:
        box, text_val = item[0], item[1].strip()
        if not text_val:
            continue
        all_texts.append(text_val)

        min_y = min(pt[1] for pt in box)
        norm_val = text_val.lower()

        # Soat
        if is_valid_time(text_val):
            if min_y <= status_bar_threshold_y:
                top_bar_found = True
                top_bar_reasons.append(f"Soat: {text_val}")

        # Internet / signal
        if NET_PATTERN.search(text_val):
            if min_y <= status_bar_threshold_y:
                top_bar_found = True
                top_bar_reasons.append(f"Internet: {text_val}")

        # Qurilma brendi
        if any(brand in norm_val for brand in TOP_BRANDS):
            top_bar_found = True
            top_bar_reasons.append(f"Brend: {text_val}")

    full_detected_text = " ".join(all_texts)
    norm = full_detected_text.lower()

    # 1. Kassa apparati indikatorlari
    has_pos_error_or_serial = bool(
        re.search(r"\b(?:406|401|400|404|500)\b", full_detected_text) or
        re.search(r"\b[uU][zZ2]\d{6,10}\b", full_detected_text) or
        (re.search(r"\b\d+\.00\b", full_detected_text) and any(w in norm for w in ["cetry", "schet", "onnat", "oplat", "kontar", "k1c", "kass", "чек", "chek", "summa"]))
    )
    has_brand = any(brand in norm for brand in TOP_BRANDS)
    pos_count = sum(1 for kw in POS_KEYWORDS if kw in norm)

    # 2. Kvitansiya indikatorlari
    rec_count = sum(1 for kw in RECEIPT_KEYWORDS if kw in norm)
    has_amount = bool(re.search(r"\b\d{1,3}(?:[.,\s]\d{3})+(?:\.\d{2})?\s*(?:so[\'\`]?m|som|сум|uzs)\b", norm))
    has_rec_strong = any(w in norm for w in [
        "kvitansiya", "квитанция", "to'lov topshirig'nomasi", "tolov topshirignomasi", 
        "patta", "chek raqami", "amaliyot muvaffaqiyatli", "o'tkazma muvaffaqiyatli", 
        "kvitansiyani yuklab olish", "qabul qiluvchi", "talaba", "kontrakt to'lovi"
    ])

    # KASSA_APARAT ekanligini tasdiqlash
    if has_pos_error_or_serial or has_brand or pos_count >= 1:
        # Agar bu to'lov topshirig'nomasi kabi sof bank hujjati bo'lsa va apparat belgilari mutlaqo bo'lmasa
        if (rec_count >= 2 or has_rec_strong) and not has_pos_error_or_serial and not has_brand and not any(w in norm for w in ["onnat", "cetry", "kontar", "406", "fmo", "smart", "касс"]):
            return {
                "category": "KVITANSIYA",
                "reason": f"To'lov kvitansiyasi aniqlandi (rec_count={rec_count})",
                "text": full_detected_text,
                "pos_analysis": None
            }

        # Kassa apparati status-bar (internet va soat) tekshiruvi
        pos_status = "VALID_POS" if top_bar_found else "TOP_BAR_MISSING"
        if not top_bar_found:
            # Sarlavha sohasi (header) borligini tekshiramiz
            app_headers = ["оплатить", "добавить", "скидку", "по счету", "счету", "оплачено", "к оплате", "касса", "продажа", "onnat", "oplat", "cetry", "kontar"]
            app_headers_y = [min(pt[1] for pt in item[0]) for item in ocr_res if any(h in item[1].lower() for h in app_headers)]
            if app_headers_y and min(app_headers_y) >= height * 0.05:
                pos_status = "VALID_POS"

        return {
            "category": "KASSA_APARAT",
            "reason": f"Kassa apparati ekrani aniqlandi (status: {pos_status})",
            "text": full_detected_text,
            "pos_analysis": {
                "status": pos_status,
                "text": full_detected_text,
                "reason": f"Kassa apparati ({', '.join(top_bar_reasons) if top_bar_found else 'Status bar etishmaydi'})"
            }
        }

    # KVITANSIYA ekanligini tasdiqlash
    if rec_count >= 1 or has_rec_strong or has_amount:
        return {
            "category": "KVITANSIYA",
            "reason": f"To'lov kvitansiyasi aniqlandi (rec_count={rec_count})",
            "text": full_detected_text,
            "pos_analysis": None
        }

    # Umuman boshqa narsaning rasmi
    return {
        "category": "BOSHQA",
        "reason": f"Kassa apparati ham, to'lov kvitansiyasi ham emas (rec={rec_count}, pos={pos_count})",
        "text": full_detected_text,
        "pos_analysis": {
            "status": "NOT_POS",
            "text": full_detected_text,
            "reason": "Kassa apparatiga aloqador matn yoki belgi topilmadi"
        }
    }

def analyze_pos_image(image_path: str) -> dict:
    """Oldingi chaqiriqlar bilan to'liq orqaga moslik uchun analyze_pos_image funksiyasi"""
    res = classify_image_type(image_path)
    if res.get("category") == "KVITANSIYA":
        return {
            "status": "NOT_POS",
            "is_receipt_likely": True,
            "text": res.get("text", ""),
            "reason": "To'lov kvitansiyasi yoki chek"
        }
    if res.get("pos_analysis"):
        return res["pos_analysis"]
    return {
        "status": "NOT_POS",
        "text": res.get("text", ""),
        "reason": res.get("reason", "")
    }
