"""
MARS ELEKTRON TEXNIKA MCHJ - Texnik xizmat telegram boti
Asosiy yadro va Telegram API mijozi
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

LOG_PATH = os.path.join(BASE_DIR, "bot_activity.log")

class LoggerWriter:
    def __init__(self, stream, log_file):
        self.stream = stream
        self.log_file = log_file

    def write(self, data):
        if self.stream is not None:
            try:
                self.stream.write(data)
                self.stream.flush()
            except Exception:
                pass
        if self.log_file is not None:
            try:
                self.log_file.write(data)
                self.log_file.flush()
            except Exception:
                pass

    def flush(self):
        if self.stream is not None:
            try:
                self.stream.flush()
            except Exception:
                pass
        if self.log_file is not None:
            try:
                self.log_file.flush()
            except Exception:
                pass

try:
    log_fp = open(LOG_PATH, "a", encoding="utf-8")
except Exception:
    log_fp = None

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr is not None and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.stdout = LoggerWriter(sys.stdout, log_fp)
sys.stderr = LoggerWriter(sys.stderr, log_fp)

import time
import json
import urllib.request
import urllib.parse
import re
import uuid
import difflib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import config
from session_manager import session_mgr
from excel_service import excel_service
from ofd_service import ofd_service
from ticket_service import ticket_service
from receipt_service import receipt_service
from ai_service import ai_service

MEDIA_CACHE_FILE = os.path.join(config.DATA_DIR, "media_cache.json")

def load_media_cache():
    if os.path.exists(MEDIA_CACHE_FILE):
        try:
            with open(MEDIA_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "oylik_photo_file_id": "AgACAgIAAxkDAANcatMcxciszlvcGKgeVhwmXxUdtwsAAioeaxtujZhKTAWM-wH5y0IBAAMCAAN4AAM9BA",
        "oylik_video_file_id": None
    }

def save_media_cache(cache):
    try:
        with open(MEDIA_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE] Media cache saqlashda xatolik: {e}")


class TelegramBot:
    def __init__(self, token=config.BOT_TOKEN):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    def api_request(self, method, data=None):
        """Telegram Bot API so'rov yuborish"""
        url = f"{self.api_url}/{method}"
        try:
            if data:
                json_data = json.dumps(data).encode("utf-8")
                req = urllib.request.Request(
                    url, 
                    data=json_data, 
                    headers={"Content-Type": "application/json"}
                )
            else:
                req = urllib.request.Request(url)

            with urllib.request.urlopen(req, timeout=35) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result
        except Exception as e:
            # Kutubxona ulanish xatolari yoki timeout
            return {"ok": False, "error": str(e)}

    def send_message(self, chat_id, text, reply_to_message_id=None, parse_mode="Markdown", reply_markup=None):
        """Xabar yuborish (reply_to_message_id bilan mijozga belgilab javob yozish)"""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        res = self.api_request("sendMessage", payload)
        # Agar Markdown formatlashda yoki reply_to da xatolik yuz bersa
        if not res.get("ok"):
            if reply_to_message_id:
                payload.pop("reply_to_message_id", None)
                res = self.api_request("sendMessage", payload)
            if not res.get("ok") and parse_mode:
                payload.pop("parse_mode", None)
                res = self.api_request("sendMessage", payload)
        return res

    def edit_message_text(self, chat_id, message_id, text, parse_mode="Markdown", reply_markup=None):
        """Xabar matnini tahrirlash"""
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "disable_web_page_preview": True
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = self.api_request("editMessageText", payload)
        if not res.get("ok") and parse_mode:
            payload.pop("parse_mode", None)
            res = self.api_request("editMessageText", payload)
        return res

    def edit_message_caption(self, chat_id, message_id, caption, parse_mode="Markdown", reply_markup=None):
        """Rasm yoki media xabar sarlavhasi (caption)ni tahrirlash"""
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": caption
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = self.api_request("editMessageCaption", payload)
        if not res.get("ok") and parse_mode:
            payload.pop("parse_mode", None)
            res = self.api_request("editMessageCaption", payload)
        return res

    def edit_ticket_card(self, chat_id, message_id, new_content, is_photo=False, reply_markup=None):
        """Murojaat kartochkasini tahrirlash (photo caption yoki text orqali)"""
        if is_photo:
            res = self.edit_message_caption(chat_id, message_id, new_content, reply_markup=reply_markup)
            if res.get("ok"):
                return res
            return self.edit_message_text(chat_id, message_id, new_content, reply_markup=reply_markup)
        else:
            res = self.edit_message_text(chat_id, message_id, new_content, reply_markup=reply_markup)
            if res.get("ok"):
                return res
            return self.edit_message_caption(chat_id, message_id, new_content, reply_markup=reply_markup)

    def delete_message(self, chat_id, message_id):
        """Xabarni o'chirish"""
        return self.api_request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        """Callback query ga javob berish (loading aylanmasini to'xtatish)"""
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        if show_alert:
            payload["show_alert"] = show_alert
        return self.api_request("answerCallbackQuery", payload)

    def send_photo(self, chat_id, photo, caption=None, reply_to_message_id=None, parse_mode="Markdown", reply_markup=None):
        """Rasm yuborish (file_id yoki mahalliy fayl orqali)"""
        # 1. Agar photo file_id yoki URL bo'lsa
        if isinstance(photo, str) and (not os.path.isfile(photo)):
            payload = {
                "chat_id": chat_id,
                "photo": photo
            }
            if caption:
                payload["caption"] = caption
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            if parse_mode:
                payload["parse_mode"] = parse_mode
            if reply_markup:
                payload["reply_markup"] = reply_markup
            res = self.api_request("sendPhoto", payload)
            if not res.get("ok"):
                if reply_to_message_id:
                    payload.pop("reply_to_message_id", None)
                    res = self.api_request("sendPhoto", payload)
                if not res.get("ok") and parse_mode:
                    payload.pop("parse_mode", None)
                    res = self.api_request("sendPhoto", payload)
            return res

        # 2. Agar photo mahalliy fayl yo'li bo'lsa, multipart orqali yuklash
        if os.path.isfile(photo):
            try:
                boundary = uuid.uuid4().hex
                body = bytearray()
                body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
                if caption:
                    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
                if reply_to_message_id:
                    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="reply_to_message_id"\r\n\r\n{reply_to_message_id}\r\n'.encode('utf-8'))
                if parse_mode:
                    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\n{parse_mode}\r\n'.encode('utf-8'))
                if reply_markup:
                    rm_json = json.dumps(reply_markup) if not isinstance(reply_markup, str) else reply_markup
                    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="reply_markup"\r\n\r\n{rm_json}\r\n'.encode('utf-8'))
                with open(photo, 'rb') as f:
                    content_bytes = f.read()
                filename = os.path.basename(photo)
                body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="{filename}"\r\nContent-Type: image/png\r\n\r\n'.encode('utf-8'))
                body.extend(content_bytes)
                body.extend(f'\r\n--{boundary}--\r\n'.encode('utf-8'))

                req = urllib.request.Request(
                    f"{self.api_url}/sendPhoto",
                    data=bytes(body),
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
                )
                with urllib.request.urlopen(req, timeout=35) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "Invalid photo"}

    def send_document(self, chat_id, document, caption=None, reply_to_message_id=None, parse_mode="Markdown", reply_markup=None):
        """Hujjat (PDF yoki fayl) yuborish (file_id yoki mahalliy fayl orqali)"""
        if isinstance(document, str) and (not os.path.isfile(document)):
            payload = {
                "chat_id": chat_id,
                "document": document
            }
            if caption:
                payload["caption"] = caption
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            if parse_mode:
                payload["parse_mode"] = parse_mode
            if reply_markup:
                payload["reply_markup"] = reply_markup
            res = self.api_request("sendDocument", payload)
            if not res.get("ok"):
                if reply_to_message_id:
                    payload.pop("reply_to_message_id", None)
                    res = self.api_request("sendDocument", payload)
                if not res.get("ok") and parse_mode:
                    payload.pop("parse_mode", None)
                    res = self.api_request("sendDocument", payload)
            return res

        if os.path.isfile(document):
            try:
                boundary = uuid.uuid4().hex
                body = bytearray()
                body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
                if caption:
                    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
                if reply_to_message_id:
                    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="reply_to_message_id"\r\n\r\n{reply_to_message_id}\r\n'.encode('utf-8'))
                if parse_mode:
                    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\n{parse_mode}\r\n'.encode('utf-8'))
                if reply_markup:
                    rm_json = json.dumps(reply_markup) if not isinstance(reply_markup, str) else reply_markup
                    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="reply_markup"\r\n\r\n{rm_json}\r\n'.encode('utf-8'))
                with open(document, 'rb') as f:
                    content_bytes = f.read()
                filename = os.path.basename(document)
                body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode('utf-8'))
                body.extend(content_bytes)
                body.extend(f'\r\n--{boundary}--\r\n'.encode('utf-8'))

                req = urllib.request.Request(
                    f"{self.api_url}/sendDocument",
                    data=bytes(body),
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
                )
                with urllib.request.urlopen(req, timeout=35) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "Invalid document"}

    def send_video(self, chat_id, video, caption=None, reply_to_message_id=None, parse_mode="Markdown", reply_markup=None):
        """Video yoki animatsiya (GIF) yuborish"""
        payload = {
            "chat_id": chat_id,
            "video": video
        }
        if caption:
            payload["caption"] = caption
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = self.api_request("sendVideo", payload)
        if not res.get("ok"):
            if reply_to_message_id:
                payload.pop("reply_to_message_id", None)
                res = self.api_request("sendVideo", payload)
            if not res.get("ok"):
                payload["animation"] = payload.pop("video")
                res = self.api_request("sendAnimation", payload)
        return res

    def copy_message(self, chat_id, from_chat_id, message_id, caption=None, reply_to_message_id=None, parse_mode=None):
        """Xabarni kanaldan yoki chatdan nusxalab, mijozning xabariga reply (javob tariqasida) qilib yuborish"""
        payload = {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        if caption:
            payload["caption"] = caption
        if parse_mode:
            payload["parse_mode"] = parse_mode
        res = self.api_request("copyMessage", payload)
        # Agar reply_to_message_id xatolik bersa (masalan xabar o'chirilgan bo'lsa), unsiz qayta urinamiz
        if not res.get("ok") and reply_to_message_id:
            payload.pop("reply_to_message_id", None)
            res = self.api_request("copyMessage", payload)
        return res

    def forward_message(self, chat_id, from_chat_id, message_id):
        """Xabarni kanaldan yoki boshqa chatdan to'g'ridan-to'g'ri uzatish (Forward) qilib yuborish"""
        payload = {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id
        }
        return self.api_request("forwardMessage", payload)

    def get_updates(self, offset=None, timeout=25):
        """Yangi xabarlarni qabul qilish (Guruh xabarlari, Kanal postlari va Callback query)"""
        params = {
            "timeout": timeout,
            "allowed_updates": ["message", "edited_message", "channel_post", "edited_channel_post", "callback_query"]
        }
        if offset is not None:
            params["offset"] = offset
        return self.api_request("getUpdates", params)

    def download_file(self, file_id, dest_path):
        """Telegramdan fayl yuklab olish (masalan yangi Excel fayl)"""
        file_info = self.api_request("getFile", {"file_id": file_id})
        if file_info.get("ok"):
            file_path = file_info["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            urllib.request.urlretrieve(download_url, dest_path)
            return True
        return False



class MarsBotEngine:
    def __init__(self):
        self.bot = TelegramBot()
        self.executor = ThreadPoolExecutor(max_workers=8)

    def normalize_text(self, text):
        """Matnni tahlil qilish uchun qulay holatga keltiradi (xatoliklar, shevalar va imlo xatolarni to'g'irlaydi)"""
        if not text:
            return ""
        t = text.lower().strip()
        # Kirill-lotin unifikatsiyasi va apostroflar
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

        # 'w' harfini 'sh' ga o'tkazish (masalan: iwlamayapti -> ishlamayapti, gaplaw -> gaplash)
        t = re.sub(r"(\w)w(\w)", r"\1sh\2", t)
        t = re.sub(r"\bw(\w+)", r"sh\1", t)
        t = re.sub(r"(\w+)w\b", r"\1sh", t)

        # Takrorlangan ortiqcha harflarni tozalash (yilllik -> yillik, salooom -> salom)
        t = re.sub(r"l{3,}", "ll", t)
        t = re.sub(r"([a-z])\1{2,}", r"\1", t)

        # Dialekt va sheva qo'shimchalari / fe'l shakllari
        t = re.sub(r"\bvotti\b|\bvotdi\b|\bvoti\b", "yapti", t)
        t = re.sub(r"([a-z]+)votti\b|([a-z]+)votdi\b|([a-z]+)voti\b", r"\1yapti", t)
        t = re.sub(r"([a-z]+)yotti\b|([a-z]+)yobdi\b|([a-z]+)yovotti\b", r"\1yapti", t)
        t = re.sub(r"([a-z]+)ebdi\b|([a-z]+)epti\b", r"\1yapti", t)
        t = re.sub(r"([a-z]+)vor([a-z]*)\b", r"\1 yubor\2", t)

        # -moqchi / to'lash fe'l shakllari va dialekt variantlari
        t = re.sub(r"\b(to'?la|tola|tula|o'?tkaz|utkaz|tashla)moqchiydim(da)?\b", r"\1moqchiman", t)
        t = re.sub(r"\b(to'?la|tola|tula)y(da|m)?\b", r"to'lay", t)
        t = re.sub(r"\btul(a\w*)\b", r"to'l\1", t)
        t = re.sub(r"\btulov(\w*)\b", r"to'lov\1", t)

        # Qo'shimchalar va birikmalarni ajratish (oygaham -> oyga ham, uchunam -> uchun ham, manku -> man ku, vb.)
        t = re.sub(r"\buchunam\b|\buchunyam\b", "uchun ham", t)
        t = re.sub(r"([a-z]+)gaham\b", r"\1ga ham", t)
        t = re.sub(r"([a-z]+)gayam\b", r"\1ga ham", t)
        t = re.sub(r"([a-z]+)kaham\b", r"\1ka ham", t)
        t = re.sub(r"([a-z]+)kayam\b", r"\1ka ham", t)
        t = re.sub(r"([a-z]+)uchunam\b", r"\1 uchun ham", t)
        t = re.sub(r"([a-z]+)uchunham\b", r"\1 uchun ham", t)
        t = re.sub(r"([a-z]+)manku\b", r"\1man ku", t)
        t = re.sub(r"([a-z]+)dimku\b", r"\1dim ku", t)

        # O'zbek tilidagi keng tarqalgan so'zlashuv / imlo variantlari
        direct_replacements = {
            "uchunam": "uchun ham", "uchunyam": "uchun ham",
            "man": "men", "manku": "menku",
            "kelasi": "keyingi", "kelesi": "keyingi",
            "ohirigacha": "oxirigacha", "oxirgacha": "oxirigacha", "oxiri": "oxiri", "ohiri": "oxiri",
            "yetishi": "yetishi", "yetadi": "yetadi", "yetmaydi": "yetmaydi", "yetmedi": "yetmaydi",
            "yetar": "yetar", "yetardi": "yetardi",
            "qanaqasiga": "qanaqasiga", "qanaqasigaa": "qanaqasiga",
            "trxnik": "texnik", "tehnik": "texnik", "texnek": "texnik", "tehnek": "texnik",
            "tixnik": "texnik", "txnik": "texnik", "texnk": "texnik", "texnikk": "texnik",
            "tehnikka": "texnikka", "tehnikga": "texnikka", "texnikga": "texnikka",
            "admen": "admin", "admn": "admin", "adminn": "admin", "adminka": "admin", "adming": "adminga",
            "operatr": "operator", "aparatr": "operator", "aperatr": "operator",
            "opirator": "operator", "opiratr": "operator", "oprator": "operator",
            "mutahassis": "mutaxassis", "mutaxasis": "mutaxassis", "mutahasis": "mutaxassis",
            "mutassis": "mutaxassis", "spetsialist": "mutaxassis", "spesialist": "mutaxassis",
            "usda": "usta", "ustala": "ustalar",
            "apparat": "aparat", "oparat": "aparat", "opparat": "aparat", "aprat": "aparat",
            "kasa": "kassa", "kasssa": "kassa",
            "termenal": "terminal", "tirmenal": "terminal", "tirminal": "terminal",
            "feskal": "fiskal", "fiskl": "fiskal", "feskall": "fiskal", "fiskil": "fiskal", "fescal": "fiskal",
            "madul": "modul", "modil": "modul",
            "abanent": "abonent", "abanit": "abonent", "abonint": "abonent", "abament": "abonent", "abonet": "abonent",
            "yilik": "yillik", "yilllik": "yillik",
            "rekvizeti": "rekvizit", "rekviziti": "rekvizit", "rakvizit": "rekvizit",
            "rikvizit": "rekvizit", "rekvizet": "rekvizit", "rekvizid": "rekvizit",
            "vedio": "video", "vidyo": "video", "vedyo": "video", "vidio": "video",
            "shotini": "hisob raqam", "shoti": "hisob raqam", "shot": "hisob raqam",
            "qullanma": "qo'llanma", "qullanmasi": "qo'llanma",
            "kiyingi": "keyingi", "kengi": "keyingi", "keyngi": "keyingi", "kenggi": "keyingi",
            "quygandim": "qo'ygandim", "quygandimku": "qo'ygandimku", "quydim": "qo'ydim", "quydimku": "qo'ydimku",
            "quyganman": "qo'yganman", "quyganmanku": "qo'yganmanku", "quygandik": "qo'ygandik", "quyganmiz": "qo'yganmiz",
            "quymoqchi": "qo'ymoqchi", "quyildi": "qo'yildi", "quyilgan": "qo'yilgan",
            "tulamoqchiydimda": "to'lamoqchiman", "tulamoqchiydim": "to'lamoqchiman", "tulamoqchi": "to'lamoqchi", "tulamoqchiman": "to'lamoqchiman", "tulay": "to'lay", "tulasam": "to'lasam", "tulasa": "to'lasa",
            "tolamoqchiydimda": "to'lamoqchiman", "tolamoqchiydim": "to'lamoqchiman", "tolamoqchi": "to'lamoqchi", "tolamoqchiman": "to'lamoqchiman", "tolay": "to'lay", "tolasam": "to'lasam", "tolasa": "to'lasa",
            "utkazmoqchiydimda": "o'tkazmoqchiman", "utkazmoqchiydim": "o'tkazmoqchiman", "utkazmoqchi": "o'tkazmoqchi", "utkazmoqchiman": "o'tkazmoqchiman",
            "tashlamoqchiydimda": "tashlamoqchiman", "tashlamoqchiydim": "tashlamoqchiman", "tashlamoqchi": "tashlamoqchi", "tashlamoqchiman": "tashlamoqchiman",
            "tulov": "to'lov", "tolov": "to'lov", "tulash": "to'lash", "tolash": "to'lash",
            "tulovlar": "to'lovlar", "tolovlar": "to'lovlar", "tulovlari": "to'lovlari", "tolovlari": "to'lovlari",
            "tulovim": "to'lovim", "tolovim": "to'lovim", "tulovimiz": "to'lovimiz", "tolovimiz": "to'lovimiz",
            "tulanadi": "to'lanadi", "tolanadi": "to'lanadi",
            "tulovdim": "to'lagandim", "to'lovdim": "to'lagandim", "tolovdim": "to'lagandim",
            "tulovdimku": "to'lagandimku", "to'lovdimku": "to'lagandimku", "tolovdimku": "to'lagandimku",
            "tulovdik": "to'lagandik", "to'lovdik": "to'lagandik", "tolovdik": "to'lagandik",
            "tulagandim": "to'lagandim", "tulagandimku": "to'lagandimku", "tulaganman": "to'laganman", "tulaganmanku": "to'laganmanku",
            "tuladim": "to'ladim", "tuladimku": "to'ladimku", "tulaganmiz": "to'laganmiz", "tulagandik": "to'lagandik",
            "tolagan": "to'lagan", "tolab": "to'lab", "tolagandim": "to'lagandim", "tolaganman": "to'laganman",
            "toladim": "to'ladim", "toladimku": "to'ladimku", "tolaganmiz": "to'laganmiz", "tolagandik": "to'lagandik",
            "utkazdim": "o'tkazdim", "utkazdik": "o'tkazdik", "utkazildi": "o'tkazildi", "utkazish": "o'tkazish", "utkazib": "o'tkazib",
            "otkazdim": "o'tkazdim", "otkazdik": "o'tkazdik", "tashavordim": "tashladim", "utkazvordim": "o'tkazdim",
            "tulanmagan": "to'lanmagan", "tulangan": "to'langan", "tulagan": "to'lagan", "tulab": "to'lab",
            "buladi": "bo'ladi", "bulsa": "bo'lsa", "bulgan": "bo'lgan", "bulishi": "bo'lishi", "bular": "bo'lar",
            "qande": "qanday", "kere": "kerak", "kereg": "kerak", "keredi": "kerak",
            "cheka": "chek", "cek": "chek",
            "bogla": "bog'la", "boglang": "bog'lang", "boglanish": "bog'lanish", "boglavor": "bog'la", "boglaw": "bog'lash",
            "kurib": "ko'rib", "korib": "ko'rib", "beriyla": "bering", "berila": "bering", "berin": "bering",
            "qazr": "qarz", "qarzm": "qarzim", "ishlamyapti": "ishlamayapti", "iwlamayapti": "ishlamayapti",
            "ishlamayapdi": "ishlamayapti", "ishlamapti": "ishlamayapti", "ishlamidi": "ishlamaydi", "ishlameydi": "ishlamaydi",
            "notugri": "noto'g'ri", "notogri": "noto'g'ri", "noto'gri": "noto'g'ri",
            "tugirlash": "to'g'irlash", "tugirla": "to'g'irla", "tugirlayman": "to'g'irlayman",
            "togirlash": "to'g'irlash", "togirla": "to'g'irla", "togirlayman": "to'g'irlayman",
            "tugirlab": "to'g'irlab", "togirlab": "to'g'irlab"
        }

        words = re.findall(r"[a-z0-9']+", t)
        res_words = []
        canonical_list = [
            "texnik", "operator", "admin", "mutaxassis", "usta",
            "aparat", "kassa", "fiskal", "modul", "abonent",
            "oylik", "yillik", "rekvizit", "video", "qarz", "bog'la",
            "chaqir", "ishlamayapti", "tekshir", "to'lov"
        ]

        # Aynan oylik va yillik so'zlarini adashtirmaslik uchun alohida ro'yxat
        exact_keys = {"oylik", "oylikni", "oylikka", "oylikchi", "oyliknichi", "yillik", "yillikni", "yillikka", "yillikchi", "yilliknichi"}

        for w in words:
            clean_w = w.replace("'", "")
            if w in direct_replacements:
                res_words.append(direct_replacements[w])
            elif clean_w in direct_replacements:
                res_words.append(direct_replacements[clean_w])
            elif clean_w in exact_keys:
                res_words.append(w)
            elif len(clean_w) >= 4 and clean_w not in [c.replace("'", "") for c in canonical_list]:
                matches = difflib.get_close_matches(clean_w, [c.replace("'", "") for c in canonical_list], n=1, cutoff=0.82)
                if matches:
                    matched = [c for c in canonical_list if c.replace("'", "") == matches[0]][0]
                    res_words.append(matched)
                else:
                    res_words.append(w)
            else:
                res_words.append(w)

        res_text = " ".join(res_words)
        res_text = res_text.replace("[", "").replace("]", "")
        return res_text

    def is_bot_intro_query(self, norm_text):
        """Bot kimligi, vazifasi yoki imkoniyatlari haqidagi so'rovlar"""
        phrases = [
            "sen kimsan", "siz kimsiz", "kimsan", "kimsiz",
            "nima qila olasan", "nima qila olasiz", "nima qilasiz", "nima qilasan",
            "nima ish qilasan", "nima ish qilasiz", "vazifang nima", "vazifangiz nima",
            "bot vazifasi", "bu qanaqa bot", "bu nima bot", "qanday bot", "nimalar qila olasan",
            "kim bu bot", "nima bu bot", "qanday yordam bera olasan", "qanaqa xizmat",
            "nima xizmat", "nima yordam", "nima bilasan", "nima qila oladi bu bot"
        ]
        if any(p in norm_text for p in phrases):
            return True
        if ("kim" in norm_text or "nima" in norm_text) and ("san" in norm_text or "siz" in norm_text or "bot" in norm_text):
            if "qarz" not in norm_text and "to'la" not in norm_text and "ishlamay" not in norm_text:
                return True
        return False

    def get_duty_explanation_text(self, session=None):
        """Bot o'z vazifasini qisqa va tushunarli tarzda tushuntirib berishi"""
        text = (
            f"🤖 Men *{config.COMPANY_NAME}* ning online nazorat kassa apparatlari (SmartOne, P3) bo'yicha texnik xizmat ko'rsatuvchi botiman.\n\n"
            f"Men faqat kassa apparatlari bo'yicha quyidagi vazifalarni bajara olaman:\n"
            f"• 🛠 *Kassa apparatidagi muammolarni ko'rib berish* (aparat ishlamay qolganda)\n"
            f"• 💳 *Oylik abonent to'lovini tekshirish* (STIR / INN bo'yicha) va to'lash\n"
            f"• 📟 *Yillik Fiskal Modul (FM) to'lovini tekshirish* va to'lash\n"
            f"• 📊 *Yil davomida to'langan oylar hisobotini ko'rsatish*\n"
            f"• 👨‍💻 *Mas'ul texnik mutaxassis (admin) bilan bog'lash*\n\n"
            f"⚠️ Boshqa mavzulardagi savollarga javob bera olmayman.\n\n"
            f"Iltimos, kassa apparatingiz yoki to'lovlaringiz bo'yicha murojaatingiz bo'lsa yozing!"
        )
        if session and session.state == "AWAITING_INN":
            text += "\n\n👉 *Eslatma:* Kassa apparatingizni tekshirish uchun tashkilotingizning *STIR (INN)* yoki *JSHSHIR* raqamini yuboring."
        elif session and session.state == "AWAITING_FM":
            text += "\n\n👉 *Eslatma:* Fiskal modulni tekshirish uchun chekning pastki qismidagi *FM raqami*ni yuboring."
        return text

    def is_greeting(self, norm_text):
        greetings = ["salom", "assalom", "assalomu alaykum", "salomaleykum", "salom aleykum", "privet", "zdravstvuyte"]
        words = norm_text.split()
        if any(norm_text == g for g in greetings):
            return True
        if len(words) <= 3 and any(w in ["salom", "assalom", "assalomu", "aleykum", "alaykum"] for w in words):
            return True
        return False

    def is_forget_or_reset(self, norm_text):
        """Mijoz 'suhbatni unut', 'meni unut', 'boshidan' deb yozganda sessiyani tozalash"""
        reset_keywords = [
            "suhbatni unut", "suhbatimizni unut", "suhbatingni unut", "suhbatngni unut",
            "meni unut", "esdan chiqar", "unut", "boshidan boshla", "tozala", "reset",
            "clear", "/reset", "/clear", "/salombot", "salombot"
        ]
        return any(k in norm_text for k in reset_keywords)

    def is_keyboard_button_text(self, text: str, norm_text: str) -> bool:
        """Mijoz klaviaturadagi tayyor tugmalarni bosganda yuboriladigan standart xabarlarni aniqlash"""
        if not text:
            return False
        t_low = text.lower()
        norm = (norm_text or "").lower()
        btn_keywords = [
            "fiskal modul to'lovini tekshir",
            "fiskal modul tolovini tekshir",
            "fiskal modul to'lovini tekshirish",
            "fiskal modul tolovini tekshirish",
            "oylik abonent to'lov",
            "oylik abonent tolov",
            "oylik to'lov hisob raqami",
            "oylik tolov hisob raqami",
            "yillik fiskal modul to'lov",
            "yillik fiskal modul tolov",
            "yillik to'lov hisob raqami",
            "yillik tolov hisob raqami",
            "to'lovlar tarixi",
            "tolovlar tarixi",
            "texnik bilan bog'lan",
            "texnik bilan boglan",
            "oylik to'lov rekviziti",
            "oylik tolov rekviziti",
            "yillik to'lov rekviziti",
            "yillik tolov rekviziti"
        ]
        return any(k in t_low or k in norm for k in btn_keywords)

    def is_monthly_pay_info(self, norm_text, session=None):
        """Oylik to'lovni TO'LASH, REKVIZIT, VIDEO yoki QANDAY TO'LASH so'rovi"""
        # Yillik / Fiskal modul bo'lsa, bu yerga kirmaydi
        if any(y in norm_text for y in ["yillik", "fiskal", "modul", "fm"]):
            return False

        # Agar qarzni tekshirish yoki qancha qarz borligini bilish so'ralayotgan bo'lsa, tekshirishga o'tadi
        if any(c in norm_text for c in [
            "tekshir", "tekshirish", "tekshirib", "qancha qarz", "qarzim qancha",
            "qarz bormi", "qarzdorlik qancha", "qancha to'lashim kerak", "proverit"
        ]):
            return False

        # Agar to'lovlar tarixi, hisobot yoki to'lab bo'linganligi/norozilik bildirilayotgan bo'lsa, bu rekvizit/video emas!
        if any(h in norm_text for h in [
            "tarix", "hisobot", "xisobot", "oyma-oy", "oyma oy", "kesimida",
            "to'laganman", "to'lagandim", "to'lab qo'ygan", "to'lab qo'ydim", "to'lab qo'ygandim",
            "to'lab bo'lgan", "to'lab bo'ldik", "to'lagandik", "to'laganmiz", "to'ladim",
            "yetadigan", "qani", "nega qarz", "nimaga qarz", "qayerdan qarz", "qarzim yo'q",
            "adash", "xato", "noto'g'ri", "avans", "oldindan to'la", "ortiqcha"
        ]):
            return False

        # 1. Qisqa aniq so'zlar va iboralar (oyliknichi, oylikchi, oyligichi va h.k.)
        monthly_short_words = [
            "oylik", "oylikni", "oylikka", "oylikchi", "oyliknichi", "oyligichi", "oyligi", "oyligini",
            "oylik to'lov", "oylik tolov", "oylik to'lash", "oylik tolash",
            "oylik rekvizit", "oylik rekviziti", "oylik rekvizeti",
            "oylik abonent", "oylik abonent to'lovi", "oylik abonent tulovi",
            "abonent to'lovi", "abonent tolov", "abonent to'lash",
            "oylik to'lovichi", "oylik tolovichi", "oylik tolovnichi", "oylik to'lovnichi",
            "oylik to'lovchi", "oylik tolovchi", "oyliknikichi"
        ]
        if norm_text in monthly_short_words:
            return True

        if any(w in norm_text for w in ["oyliknichi", "oylikchi", "oyligichi", "abonentnichi"]):
            if not any(c in norm_text for c in ["tekshir", "qarz", "muddat"]):
                return True

        # Kontekst: Agar avval yillik to'lov haqida so'ralgan bo'lsa va hozir oylik haqida qisqa so'ralsa
        if session and getattr(session, "last_topic", None) == "pay_yearly":
            if any(m in norm_text for m in ["oylik", "abonent", "oyiga"]):
                if not any(c in norm_text for c in ["tekshir", "qarz", "muddat"]):
                    return True

        # 2. Rekvizit so'zi qatnashgan bo'lsa va oylik / abonent / to'lov bilan bog'liq bo'lsa
        if "rekvizit" in norm_text and any(w in norm_text for w in ["oylik", "abonent", "to'lov"]):
            return True

        # 3. Oylik / abonent haqida qanday to'lash, to'lash tartibi, video, rekvizit, click
        has_monthly = any(m in norm_text for m in ["oylik", "abonent", "oyiga"])
        pay_actions = [
            "to'lash", "tolash", "tulash", "to'lasam", "tolasam", "to'layman", "to'lasa", "to'lamoqchi", "to'lashga", "to'lash tartibi",
            "to'lov", "tolov", "tulov", "qanday", "qayerga", "tartibi", "video", "qo'llanma", "darslik", "click", "hisob raqam",
            "rekvizit", "pul tashla", "to'lov qilish", "to'lov qilsam"
        ]
        if has_monthly and (any(p in norm_text for p in pay_actions) or re.search(r"\b(t(?:o'?|o|u)la\w*|o'?tkaz\w*|utkaz\w*|tashla\w*|shot\w*|hisob\s*raqam|rekvizit\w*|click\w*)\b", norm_text)):
            return True

        # 4. Agar umumiy "qanday to'lasam bo'ladi" / "qanday to'layman" deb yozilgan bo'lsa
        if any(w in norm_text for w in ["qanday to'lasam", "qanday to'layman", "qanday to'lasa bo'ladi", "qanday to'lash mumkin", "qayerga to'layman"]):
            return True

        return False

    def is_monthly_check_query(self, norm_text):
        """Oylik to'lovni TEKSHIRISH bo'yicha so'rov (tugagan, kelgan, qancha qarz, tekshirish)"""
        # Yillik / Fiskal modul bo'lsa, bu yerga kirmaydi
        if any(y in norm_text for y in ["yillik", "fiskal", "modul", "fm"]):
            return False

        # Agar sof rekvizit / to'lash videosi so'ralayotgan bo'lsa va holat/qarz so'ralmagan bo'lsa
        if any(p in norm_text for p in ["rekvizit", "video", "darslik", "qanday to'la", "qayerga to'la"]):
            if not any(c in norm_text for c in ["tekshir", "qarz", "tugag", "kelgan", "muddat", "shekilli"]):
                return False

        check_words = [
            "tekshir", "tekshirish", "tekshirib", "qancha",
            "qarz", "qarzdor", "qarzim", "qarzimiz", "qarzdorlik",
            "tugagan", "tugadi", "tugabdi", "tugaganmi", "tugadimi", "tugab", "tugaganiga",
            "kelgan", "kelganmi", "keldimi", "kelibdi", "kelganiga",
            "muddat", "muddati", "vaqti",
            "proverit", "bormi", "holat", "holati", "holatini",
            "shekilli", "shekili", "deyman", "diyman", "yetgan", "o'tgan", "to'xtagan"
        ]
        monthly_words = ["oylik", "abonent", "oylikdan", "oylikni", "oyiga", "oylikka"]

        has_monthly = any(m in norm_text for m in monthly_words)
        has_check = any(c in norm_text for c in check_words)

        if has_monthly and has_check:
            return True

        if any(p in norm_text for p in [
            "oylikdan qancha", "oylik qarz", "oylik tekshir", "oylikni tekshir",
            "oylik to'lovga kelgan", "oylik kelgan", "oylik tugagan", "oylik to'lov tugagan",
            "abonent to'lov tugagan", "abonent tugagan", "oylik to'lovga kelganmi"
        ]):
            return True

        return False

    def is_yagona_darcha_query(self, norm_text, session=None):
        """Mijoz yagona darcha / davlat xizmatlari markazi bilan bog'lanish yoki telefonini so'rasa"""
        phrases = [
            "yagona darcha", "davlat xizmatlari", "davlat hizmatlari", "dxm",
            "yagona darchani", "yagona darchaning", "yagona darchaga", "yagona darchada"
        ]
        if any(p in norm_text for p in phrases):
            return True
        if session and getattr(session, "state", "") == "NOFAOL_GUTVOXNOMA":
            if any(w in norm_text for w in ["tel", "telefon", "raqam", "bog'la", "aloqa", "nomer"]):
                return True
        return False

    def is_general_rekvizit_query(self, norm_text):
        """Mijoz shunchaki 'rekvizit' deb so'raganda (oylik yoki yillik ekanligini aniqlash kerak)"""
        if any(w in norm_text for w in ["oylik", "abonent", "oyiga"]):
            return False
        if any(w in norm_text for w in ["yillik", "fiskal", "modul", "fm"]):
            return False

        if "rekvizit" in norm_text:
            return True
        return False

    def send_monthly_payment_media(self, chat_id, reply_to_id=None):
        """Oylik to'lov rekviziti va video qo'llanmasini yangi kanaldan (@POS_Terminal_UzSmart_Bank) mijozga yuborish"""
        cache = load_media_cache()
        channel_id = cache.get("channel_id") or getattr(config, "MATERIALS_CHANNEL_ID", -1001641871516)
        # @POS_Terminal_UzSmart_Bank kanalidan: post 148 (video) va 85 (rekvizit rasmi)
        post_ids = [cache.get("oylik_video_msg_id") or 148, cache.get("oylik_rekvizit_msg_id") or 85]
        seen = set()
        unique_post_ids = [x for x in post_ids if not (x in seen or seen.add(x))]

        sent_any = False
        for msg_id in unique_post_ids:
            try:
                res = self.bot.copy_message(chat_id, from_chat_id=channel_id, message_id=msg_id, reply_to_message_id=reply_to_id)
                if res.get("ok"):
                    sent_any = True
                else:
                    fwd_res = self.bot.forward_message(chat_id, from_chat_id=channel_id, message_id=msg_id)
                    if fwd_res.get("ok"):
                        sent_any = True
            except Exception as e:
                print(f"[MEDIA] Post #{msg_id} yuborishda xatolik: {e}")

        if not sent_any:
            self.bot.send_message(chat_id, config.REKVIZIT_OYLIK, reply_to_message_id=reply_to_id)

    def send_yearly_payment_media(self, chat_id, reply_to_id=None):
        """Yillik to'lov rekviziti va video qo'llanmasini yangi kanaldan (@POS_Terminal_UzSmart_Bank) mijozga yuborish"""
        cache = load_media_cache()
        channel_id = cache.get("channel_id") or getattr(config, "MATERIALS_CHANNEL_ID", -1001641871516)
        # @POS_Terminal_UzSmart_Bank kanalidan: post 145 (yillik fiskal modul to'lovi videosi)
        post_ids = [cache.get("yillik_video_msg_id") or 145, cache.get("yillik_rekvizit_msg_id") or 34]
        seen = set()
        unique_post_ids = [x for x in post_ids if not (x in seen or seen.add(x))]

        sent_any = False
        for msg_id in unique_post_ids:
            try:
                res = self.bot.copy_message(chat_id, from_chat_id=channel_id, message_id=msg_id, reply_to_message_id=reply_to_id)
                if res.get("ok"):
                    sent_any = True
                else:
                    fwd_res = self.bot.forward_message(chat_id, from_chat_id=channel_id, message_id=msg_id)
                    if fwd_res.get("ok"):
                        sent_any = True
            except Exception as e:
                print(f"[MEDIA] Yillik post #{msg_id} yuborishda xatolik: {e}")

        if not sent_any:
            resp = (
                f"📹 *Yillik Fiskal Modul to'lovini to'lash bo'yicha video darslik:*\n"
                f"{config.VIDEO_YILLIK_URL}\n\n"
                f"{config.REKVIZIT_YILLIK}"
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)

    def send_ikpu_solution_media(self, chat_id, reply_to_id=None):
        """IKPU / dastur yangilash xatoligi bo'yicha video qo'llanmani (post #126 / #125) mijozga reply qilib yuborish"""
        cache = load_media_cache()
        channel_id = cache.get("channel_id") or getattr(config, "MATERIALS_CHANNEL_ID", -1001641871516)
        post_id = cache.get("ikpu_video_msg_id") or 126
        sent = False
        try:
            res = self.bot.copy_message(chat_id, from_chat_id=channel_id, message_id=post_id, reply_to_message_id=reply_to_id)
            if res.get("ok"):
                sent = True
            else:
                fwd_res = self.bot.forward_message(chat_id, from_chat_id=channel_id, message_id=post_id)
                if fwd_res.get("ok"):
                    sent = True
        except Exception as e:
            print(f"[IKPU_MEDIA] Video #{post_id} yuborishda xatolik: {e}")

        resp_text = (
            f"⚠️ *Kassa apparatingizda 'Проверка кода ИКПУ устарела' (IKPU kodi eskirgan) xatoligi yuz bergan.*\n\n"
            f"📹 Ushbu xatolikni bartaraf etish uchun yuqoridagi video qo'llanmada ko'rsatilgan amallarni bajaring.\n\n"
            f"ℹ️ *Eslatma:* Agar videodagi ko'rsatmalarni bajarganingizdan keyin ham xatolik bartaraf bo'lmasa yoki yordam kerak bo'lsa, xabar qoldiring — sizni darhol mas'ul texnik mutaxassisimizga ulaymiz."
        )
        if not sent:
            resp_text += f"\n\n👉 [Video qo'llanmani ko'rish uchun havola](https://t.me/POS_Terminal_UzSmart_Bank/{post_id})"

        self.bot.send_message(chat_id, resp_text, reply_to_message_id=reply_to_id)

    def is_ikpu_error_text(self, text: str) -> bool:
        """Matn yoki OCR da IKPU xatoligi borligini aniqlash"""
        if not text:
            return False
        t_low = text.lower()
        # To'g'ridan-to'g'ri IKPU yoki OCR da 'MKny' / 'MKnu' ko'rinishidagi so'zlar:
        if any(w in t_low for w in ["икпу", "ikpu", "ikpy", "ikpn", "mkny", "mknu", "mkn"]):
            return True
        # "устарела" / "yctapena" / "ustarela" xatoligi:
        has_ustarela = any(w in t_low for w in ["устарел", "yctapen", "ustarel", "eskirgan"])
        has_kod_or_check = any(w in t_low for w in ["код", "kod", "kona", "проверк", "npobepk", "tekshir"])
        if has_ustarela and has_kod_or_check:
            return True
        if "yctapena" in t_low or "ustarela" in t_low or "устарела" in t_low:
            return True
        return False

    def is_offline_limit_error(self, text: str) -> bool:
        """406 (oflayn rejim muddati) yoki 36889 (day limit / ERROR_RECEIPT_STORE_DAYS_LIMIT_EXCEEDED) xatoligini aniqlash"""
        if not text:
            return False
        norm = text.lower()
        clean_no_space = re.sub(r"[^a-z0-9]", "", norm)

        # 1. 406 xatoligi (alohida son sifatida qatnashgan bo'lsa)
        has_isolated_406 = bool(re.search(r"(?:^|[^\d])406(?:[^\d]|$)", text))
        if has_isolated_406:
            return True

        # 2. 36889 xatoligi (alohida son sifatida qatnashgan bo'lsa)
        has_isolated_36889 = bool(re.search(r"(?:^|[^\d])36889(?:[^\d]|$)", text))
        if has_isolated_36889:
            return True

        # 3. Day limit / kunlik limit / smena limiti iboralari (har xil yozilish variantlari)
        day_limit_keywords = [
            "day limit", "day lemet", "day lemit", "dey limit", "dey lemet", "dey lemit",
            "daylimit", "daylemet", "daylemit", "deylimit", "deylemet", "deylemit",
            "days limit", "days lemet", "dayslimit", "dayslemet",
            "дэй лимит", "дей лимит", "дейлимит", "дэйлимит",
            "receipt_store_days_limit", "store_days", "receipt store days limit", "days_limit",
            "limit exceeded", "limit_exceeded", "limit_e", "error_receipt",
            "limit ashebka", "limit oshibka", "limit xato", "limit xatolik", "limit ashibka",
            "lemet ashebka", "lemet oshibka", "lemet xato", "lemet xatolik", "lemet ashibka",
            "kunlik limit", "kunlik lemet", "smena limiti", "smena limit",
            "oflayn rejim", "offline rejim", "oflayn limit", "offline limit",
            "oflayn interval", "offline interval", "maksimal oflayn"
        ]
        if any(k in norm for k in day_limit_keywords):
            return True

        clean_day_limit_tokens = [
            "daylimit", "daylemet", "daylemit", "deylimit", "deylemet", "deylemit",
            "dayslimit", "dayslemet", "receiptstoredayslimit", "storedays", "limitexceeded",
            "limitashebka", "lemetashebka", "limitxato", "lemetxato", "kunliklimit", "kunliklemet",
            "smenalimiti", "oflaynrejim", "offlinerejim", "oflaynlimit", "offlinelimit"
        ]
        if any(token in clean_no_space for token in clean_day_limit_tokens):
            return True

        # 4. Kassa apparati ekranidagi OCR matnlari (ruscha)
        screen_ocr_markers = [
            "продолжительност", "onaihpexuma", "pexuma", "максимальной",
            "фискализации счета", "фискализации", "счета: 406", "счета:406", "cyeta:406",
            "открытия фискальной", "смены: 36889", "смены:36889", "cmehbi:36889",
            "превышен"
        ]
        if any(m in norm for m in screen_ocr_markers):
            return True

        return False

    def get_offline_limit_explanation_text(self) -> str:
        """406 / day limit / oflayn rejim xatoligi bo'yicha mijozga tushuntirish matni"""
        return (
            "⚠️ *Aparatingizdagi ushbu xatolik (oflayn rejim / 406 / day limit)* odatda apparatning **yillik fiskal modul to'lovi** muddati tugaganida yoki apparatning **soati (sana va vaqti)** noto'g'ri bo'lganda yoki **internet** yaxshi ishlamaganda yuzaga keladi.\n\n"
            "🔧 *Muammoni bartaraf qilish uchun:*\n"
            "• Apparatdagi internet aloqasini tekshiring;\n"
            "• Soat va sana to'g'riligini tekshiring;\n"
            "• Apparatni internetga ulangan holda o'chirib, qayta yoqing.\n\n"
            "📟 *Agar aparatingiz baribir ishlamayotgan bo'lsa*, quyidagi **«📟 Yillik fiskal modul to'lovini tekshirish»** tugmasini bosing."
        )

    def get_offline_limit_keyboard(self) -> dict:
        return {
            "keyboard": [
                [{"text": "📟 Yillik fiskal modul to'lovini tekshirish"}],
                [{"text": "💳 Oylik abonent to'lovi hisob raqami"}],
                [{"text": "🧾 Yillik fiskal modul to'lovi hisob raqami"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True,
            "selective": True
        }

    def is_not_resolved_or_complaint(self, norm_text: str) -> bool:
        """Mijoz video yoki ko'rsatma yordam bermaganini, muammo baribir qolganini bildirishi"""
        if not norm_text:
            return False
        phrases = [
            "foydasi bo'lmadi", "foydasi bolmadi", "foyda bermadi", "foydasi yo'q", "foydasi yoq",
            "baribir ishlamayapti", "baribir ishlamayabdi", "baribir ishlamadi",
            "baribir shu", "baribir shu xato", "baribir shu ashebka",
            "o'xshamadi", "oxshamadi", "tuzalmadi", "tuzatmadi", "tuzalmayapti",
            "yo'qolmadi", "yoqolmadi", "ketmadi", "ketmayapti", "ochilmadi",
            "bo'lmadi", "bolmadi", "yordam bermadi", "qildim bo'lmadi", "qildim bolmadi",
            "qildim baribir", "qildik bo'lmadi", "o'chib yoqdim foydasi bo'lmadi",
            "yana shu", "yana shu xato", "yana chiqdi", "qaytadan chiqdi",
            "ishlamadi", "o'zgarmadi", "ozgarmadi", "hal bo'lmadi", "hal bolmadi"
        ]
        return any(p in norm_text for p in phrases)

    def send_clock_solution_media(self, chat_id, reply_to_id=None):
        """Kassa apparati soatini to'g'irlash bo'yicha video qo'llanmani (post #141) mijozga reply qilib yuborish"""
        cache = load_media_cache()
        channel_id = cache.get("channel_id") or getattr(config, "MATERIALS_CHANNEL_ID", -1001641871516)
        post_id = cache.get("clock_video_msg_id") or 141
        sent = False
        try:
            res = self.bot.copy_message(chat_id, from_chat_id=channel_id, message_id=post_id, reply_to_message_id=reply_to_id)
            if res.get("ok"):
                sent = True
            else:
                fwd_res = self.bot.forward_message(chat_id, from_chat_id=channel_id, message_id=post_id)
                if fwd_res.get("ok"):
                    sent = True
        except Exception as e:
            print(f"[CLOCK_MEDIA] Video #{post_id} yuborishda xatolik: {e}")

        resp_text = (
            f"🕒 *Kassa apparatida sana va vaqtni (soatni) to'g'rilash:*\n\n"
            f"📹 Kassa apparatingiz soatini to'g'ri sozlash uchun yuqoridagi video qo'llanmada ko'rsatilgan amallarni bajaring.\n\n"
            f"👉 Videoda ko'rsatilgandek apparat sozlamalariga kiring va sana hamda vaqtni to'g'rilab qo'ying.\n\n"
            f"🔐 *Parol bo'yicha muhim ko'rsatma:*\n"
            f"Agar aparatingiz soatni to'g'irlash jarayonida parol so'rasa yoki *«Parol noto'g'ri»* desa, quyidagi parollarni terib ko'ring:\n"
            f"1️⃣ `12341234`\n"
            f"2️⃣ `123498765`"
        )
        if not sent:
            resp_text += f"\n\n👉 [Video qo'llanmani ko'rish uchun havola](https://t.me/POS_Terminal_UzSmart_Bank/{post_id})"

        self.bot.send_message(chat_id, resp_text, reply_to_message_id=reply_to_id)

    def is_clock_password_query(self, norm_text: str, text: str = "") -> bool:
        """Soatni to'g'irlashdagi parol bo'yicha so'rovlar"""
        if not norm_text and not text:
            return False
        combined = f"{norm_text} {text}".lower().replace("'", "").replace("`", "").replace("ʻ", "").replace("’", "")
        clean = re.sub(r"[^\w\s]", " ", combined)
        has_parol = any(p in clean for p in ["parol", "paroli", "parollar", "parolini"])
        has_issue = any(w in clean for w in ["notogri", "notugri", "xato", "nima", "qanaqa", "qanday", "sorayapti", "surayapti", "teraman", "kiritaman", "qaysi", "boshqa"])
        return has_parol and has_issue

    def is_clock_problem_query(self, norm_text: str, text: str = "") -> bool:
        """Kassa apparati soati yoki vaqti noto'g'ri / soatni to'g'irlash bo'yicha so'rovlarni aniqlash"""
        if not norm_text and not text:
            return False

        combined = f"{norm_text} {text}".lower()
        # Apostroflarni olib tashlab tozalash (o' -> o, g' -> g)
        clean = combined.replace("'", "").replace("`", "").replace("ʻ", "").replace("’", "")
        clean = re.sub(r"[^\w\s]", " ", clean)

        # 1. Aniq iboralar (apostrofsiz)
        exact_phrases = [
            "soati notogri", "soati notugri", "soat notogri", "soat notugri",
            "soati xato", "soat xato", "soati togri emas", "soat togri emas",
            "soatni togirlash", "soatni tugirlash", "soat togirlash", "soat tugirlash",
            "soatini togirlash", "soatini tugirlash",
            "soat sozlash", "soatini sozlash", "soatni sozlash", "soatni nastroyka", "soat nastroyka",
            "soat orqada", "soati orqada", "soat oldinda", "soati oldinda",
            "soat paroli", "soatga parol", "soat parol", "vaqt paroli", "vaqtga parol",
            "vaqti notogri", "vaqti notugri", "vaqt notogri", "vaqt notugri",
            "vaqti xato", "vaqt xato", "vaqti togri emas", "vaqt togri emas",
            "vaqtni togirlash", "vaqtni tugirlash", "vaqt togirlash", "vaqt tugirlash",
            "vaqt sozlash", "vaqtni sozlash", "vaqt nastroyka",
            "vaqt orqada", "vaqti orqada", "vaqt oldinda", "vaqti oldinda",
            "неправильное время", "время неправильное", "настроить время", "настройка времени",
            "поменять время", "изменить время", "перевести время", "часы спешат", "время отстает", "не то время"
        ]
        if any(p in clean for p in exact_phrases):
            return True

        # 2. Kalit so'zlar birikmasi
        time_words = ["soat", "soati", "soatni", "soatini", "vaqt", "vaqti", "vaqtni", "vaqtini", "sana", "sanasi", "время", "часы", "часов"]
        action_problem_words = [
            "notogri", "notugri", "xato", "togirl", "tugirl", "togril", "tugril",
            "sozla", "sozlash", "nastroyk", "ozgartir", "almashtir", "orqada", "oldinda",
            "boshqacha", "adash", "qanday", "qanaqa", "qande", "parol", "paroli", "kod", "kodi",
            "неправильн", "настро", "поменя", "измени", "перевест", "отста", "спеш"
        ]

        has_time = any(tw in clean.split() or tw in clean for tw in time_words)
        has_action = any(aw in clean for aw in action_problem_words)

        if has_time and has_action:
            if any(w in clean for w in ["qaysi soatda", "qaysi soatgacha", "soat nechagacha", "soat nechada", "ish vaqtingiz", "ish vaqti"]):
                if not any(k in clean for k in ["aparat", "kassa", "terminal", "notogri", "notugri", "xato", "togirl", "tugirl"]):
                    return False
            return True

        return False

    def is_yearly_check_query(self, norm_text):
        """Yillik to'lov / Fiskal modul to'lovini TEKSHIRISH (tugagan, kelgan, muddat, qarz)"""
        # Agar sof rekvizit / to'lash videosi so'ralayotgan bo'lsa va holat/qarz so'ralmagan bo'lsa
        if any(p in norm_text for p in ["rekvizit", "video", "darslik", "qanday to'la", "qayerga to'la"]):
            if not any(c in norm_text for c in ["tekshir", "qarz", "tugag", "kelgan", "muddat", "shekilli"]):
                return False

        check_words = [
            "tekshir", "tekshirish", "tekshirib", "muddat", "muddati", "qachon tugaydi",
            "tugagan", "tugadi", "tugabdi", "tugaganmi", "tugadimi", "tugab", "tugaganiga",
            "kelgan", "kelganmi", "keldimi", "kelibdi", "kelganiga",
            "qarz", "qarzdor", "qarzdorlik", "proverit",
            "shekilli", "shekili", "deyman", "diyman", "bormi", "yetgan", "o'tgan", "to'xtagan"
        ]
        yearly_words = ["yillik", "fiskal", "feskal", "modul", "fm", "yillikni", "yillikdan", "yillikka"]

        has_yearly = any(y in norm_text for y in yearly_words)
        has_check = any(c in norm_text for c in check_words)

        if has_yearly and has_check:
            return True

        if any(p in norm_text for p in [
            "yillik tekshir", "yillikni tekshir", "fm tekshir", "fiskal tekshir",
            "yillik to'lovga kelgan", "yillik kelgan", "yillik tugagan", "yillik to'lov tugagan",
            "fiskal modul tugagan", "fm tugagan", "fm muddati", "yillik to'lovga kelganmi"
        ]):
            return True

        return False

    def is_yearly_pay_info(self, norm_text, session=None):
        """Yillik to'lovni TO'LASH (rekvizit, video darslik)"""
        if self.is_yearly_check_query(norm_text):
            return False

        # 1. Qisqa aniq so'zlar va iboralar (yilliknichi, yillikchi, yilligichi va h.k.)
        yearly_short_words = [
            "yillik", "yillikni", "yillikka", "yillikchi", "yilliknichi", "yilligichi", "yilligi", "yilligini",
            "yillik tolov", "yillik to'lov", "yillik tolash", "yillik to'lash",
            "yillik rekvizit", "yillik rekviziti", "yillik rekvizeti",
            "feskal modul tulovini tulash", "fiskal modul tolash", "fiskal modul to'lash",
            "fiskal modul rekvizit", "fm rekvizit", "fm to'lash",
            "yillik to'lovichi", "yillik tolovichi", "yillik tolovnichi", "yillik to'lovnichi",
            "yillik to'lovchi", "yillik tolovchi", "yilliknikichi"
        ]
        if norm_text in yearly_short_words:
            return True

        if any(w in norm_text for w in ["yilliknichi", "yillikchi", "yilligichi", "fiskalnichi", "fmnichi", "modulnichi"]):
            if not any(c in norm_text for c in ["tekshir", "qarz", "muddat"]):
                return True

        # Kontekst: Agar avval oylik to'lov haqida so'ralgan bo'lsa va hozir yillik haqida qisqa so'ralsa
        if session and getattr(session, "last_topic", None) == "pay_monthly":
            if any(y in norm_text for y in ["yillik", "fiskal", "modul", "fm"]):
                if not any(c in norm_text for c in ["tekshir", "qarz", "muddat"]):
                    return True

        # 2. Yillik / Fiskal modul bo'yicha to'lash, rekvizit, video, qo'llanma
        has_yearly = any(y in norm_text for y in ["yillik", "fiskal", "modul", "fm"])
        pay_actions = [
            "to'lash", "to'lasam", "to'layman", "to'lasa", "to'lamoqchi", "to'lashga", "to'lash tartibi",
            "qanday", "qayerga", "tartibi", "video", "qo'llanma", "darslik", "click", "hisob raqam",
            "rekvizit", "pul tashla", "to'lov qilish", "to'lov qilsam"
        ]
        if has_yearly and (any(p in norm_text for p in pay_actions) or re.search(r"\b(t(?:o'?|o|u)la\w*|o'?tkaz\w*|utkaz\w*|tashla\w*|shot\w*|hisob\s*raqam|rekvizit\w*|duk\b)\b", norm_text)):
            return True

        return False

    def is_pos_problem(self, norm_text):
        """Aparat ishlamayapti, nosozlik yoki aparatni tekshirib berish murojaati"""
        # Agar aynan yillik / fiskal modul tekshiruvi so'ralgan bo'lsa, bu yerga kirmaydi
        if any(y in norm_text for y in ["yillik", "fiskal", "modul", "fm"]):
            return False

        # 1. Kassa apparati so'zlari
        pos_words = ["aparat", "apparat", "kassa", "terminal", "pos", "smartone", "p3"]
        has_pos = any(w in norm_text for w in pos_words)

        # Muammo yoki tekshirish so'zlari
        check_or_problem_words = [
            "tekshir", "tekshirish", "tekshirib", "tekshiruv", "tekshiraylik", "tekshiring",
            "ko'rib", "kurib", "ko'rish", "kurish", "qarab", "ko'ring",
            "ishlamay", "ishlamiy", "ishlamadi", "ishlamayabdi", "ishlamayapti", "ishlamayaptiku",
            "xato", "xatolik", "nosozlik", "buzildi", "buzilgan", "qotib", "o'chib", "ochilmay",
            "blok", "bloklandi", "to'xtadi", "to'xtab", "tushmayapti", "muammo", "otkaz",
            "chek chiqmay", "chek urmay", "chek bermay", "chek urmayapti", "chek chiqmayapti", "chek chiqmayabdi"
        ]
        has_check_or_problem = any(w in norm_text for w in check_or_problem_words)

        if has_pos and has_check_or_problem:
            return True

        # 2. Chek chiqmayapti / bermayapti
        if "chek" in norm_text and any(w in norm_text for w in ["chiqmay", "urmay", "bermay", "tushmay", "chiqarmay", "bermiy", "chiqmidi", "bermidi", "chiqmayapti", "chiqmayabdi"]):
            return True

        # 3. Aniq nosozlik iboralari
        if any(w in norm_text for w in [
            "ishlamayapti", "ishlamayabdi", "ishlamadi", "ishlamayaptiku", "ishlamaydi",
            "buzildi", "qotib qoldi", "yonmayapti", "ochilmayapti", "nosozlik", "xatolik beryapti"
        ]):
            return True

        # 4. Apparat so'zi aytilmagan bo'lsa ham aniq kassa/nosozlik iboralari
        phrases = [
            "ishlamayapti", "ishlamayabdi", "ishlamay qoldi", "ishlamay qobdi",
            "cheka chiqmayapti", "chek chiqmayapti", "chek urmayapti", "chek bermayapti", "chek chiqmayabdi",
            "ishlamayapti aparatim", "nosozlik", "aparat qotib qoldi", "kassada xatolik", "xatolik beryapti", "xato beryapti",
            "tekshirib bering", "tekshirib beriyla", "tekshirib berila", "tekshirib beringlar", "tekshirib ber",
            "ko'rib bering", "kurib bering", "ko'rib beriyla", "kurib beriyla", "ko'rib beringlar", "kurib berila"
        ]
        if any(p in norm_text for p in phrases):
            return True

        return False

    def is_still_not_working(self, norm_text, session):
        """Mijozning oylik va yillik to'lovi toza bo'lsa ham 'baribir ishlamayapti' degan savoli"""
        phrases = [
            "aparatim ishlamayabdiku", "aparatim ishlamayaptiku", "unda nimaga aparat ishlamayabdi",
            "unda nimaga ishlamayapti", "nimaga ishlamayapti unda", "nega ishlamayapti",
            "baribir ishlamayapti", "ishlamayaptiku", "ishlamayapti baribir", "aparat yoqilmayapti",
            "muammo hal bo'lmadi", "baribir chek chiqmayapti", "baribir ishlamayapti kassa"
        ]
        if any(p in norm_text for p in phrases):
            return True
        if "ishlamayabdiku" in norm_text or "ishlamayaptiku" in norm_text:
            return True
        return False

    def is_technician_request(self, norm_text):
        """Mijoz admin, texnik, usta yoki mutaxassis chaqirganda yoki bog'lanish so'raganda"""
        phrases = [
            "admin bilan bog'la", "admin bilan bogla", "admin bn bogla", "admin bilan bog'lanish", "admin bilan boglanish", "admin bilan",
            "texnik bilan bog'la", "texnik bilan bogla", "texnik bn bogla", "texnik bilan bog'lanish", "texnik bilan boglanish", "texnik bilan",
            "menga odam javob bersin", "odam javob bersin", "odam bn gaplashay", "odam bilan gaplashay", "odam bilan gaplashmoqchi", "odam bormi", "tirik odam",
            "operator bilan bog'la", "operator bilan bogla", "operator kerak", "operator bormi", "operator",
            "mutaxassis bilan bog'la", "mutaxassis bilan bogla", "mutaxassis kerak", "mutaxassis chaqiring", "mutaxassis",
            "texnik kerak", "admin kerak", "texnik chaqir", "admin chaqir", "usta kerak", "usta bilan bog'la", "usta chaqir",
            "tirik odam bormi", "adminga yozish", "texnikka yozish", "aloqa admin", "admin aloqa", "texnik aloqa"
        ]
        if any(p in norm_text for p in phrases):
            return True
        if norm_text in ["admin", "texnik", "operator", "mutaxassis", "usta"]:
            return True
        person_words = ["admin", "texnik", "operator", "mutaxassis", "usta", "odam", "xodim"]
        action_words = [
            "bog'la", "bogla", "ula", "ulash", "ulang", "chaqir", "kerak", "kere",
            "javob", "kut", "yordam", "gaplash", "aloqa", "yoz", "nomer", "raqam",
            "telefon", "kontakt", "tel"
        ]
        if any(p in norm_text for p in person_words) and any(a in norm_text for a in action_words):
            return True
        return False

    def cross_delete_other(self, ticket, accepted_source):
        """
        Texnik murojaatni qaysi joydan (kanal/guruh yoki shaxsiy chat) qabul qilsa,
        ikkinchi joyga yuborilgan ma'lumotni o'chirib tashlash.
        accepted_source: 'group' yoki 'chat'
        """
        if not ticket:
            return
        if accepted_source == "group":
            # Guruh/kanal orqali qabul qilindi -> Texniklarning shaxsiy chatiga yuborilgan alert xabarlarni o'chirish
            admin_msgs = ticket.get("admin_messages", [])
            for am in admin_msgs:
                try:
                    self.bot.delete_message(am["chat_id"], am["message_id"])
                except Exception as e:
                    print(f"[CROSS_DELETE_CHAT] Xatolik: {e}")
            ticket["admin_messages"] = []
            ticket_service.save_tickets()
        elif accepted_source == "chat":
            # Shaxsiy chat orqali qabul qilindi -> Kanaldagi va muhokama guruhidagi xabarlarni o'chirish
            chan_id = config.TECHNICIAN_CHANNEL_ID
            chan_mid = ticket.get("channel_message_id")
            if chan_id and chan_mid:
                try:
                    self.bot.delete_message(chan_id, chan_mid)
                except Exception as e:
                    print(f"[CROSS_DELETE_CHAN] Xatolik: {e}")
                ticket["channel_message_id"] = None
            disc_mid = ticket.get("group_discussion_id")
            if config.DISCUSSION_GROUP_ID and disc_mid:
                try:
                    self.bot.delete_message(config.DISCUSSION_GROUP_ID, disc_mid)
                except Exception as e:
                    pass
                ticket["group_discussion_id"] = None
            ticket_service.save_tickets()

    def mark_ticket_finished(self, ticket, tech_name, tech_username, status_text="Tugatilgan (Suhbat yakunlandi)"):
        """
        Suhbat tugatilganda texnikka yuborilgan mijoz ma'lumotlarini (kanal va/yoki chatda)
        tahrirlab, tagidan 'Tugatilgan' deb yozib qo'yish.
        """
        if not ticket:
            return
        base = ticket.get("base_card", "").strip()
        u_tag = f"@{tech_username}" if tech_username else tech_name
        finished_tag = f"\n\n━━━━━━━━━━━━━━━━━━━━\n👨‍💻 *Mas'ul mutaxassis:* {u_tag}\n🔴 *Holat:* {status_text}"

        # 1. Kanaldagi kartochkani tahrirlash (agar hali mavjud bo'lsa)
        chan_id = config.TECHNICIAN_CHANNEL_ID
        chan_mid = ticket.get("channel_message_id")
        if chan_id and chan_mid:
            try:
                self.bot.edit_ticket_card(chan_id, chan_mid, f"{base}{finished_tag}", is_photo=ticket.get("is_photo", False))
            except Exception as e:
                print(f"[MARK_FINISHED_CHAN] Xatolik: {e}")

        # 2. Texnikning shaxsiy chatidagi kartochkani tahrirlash (agar hali mavjud bo'lsa)
        admin_msgs = ticket.get("admin_messages", [])
        for am in admin_msgs:
            try:
                self.bot.edit_ticket_card(am["chat_id"], am["message_id"], f"{base}{finished_tag}", is_photo=am.get("is_photo", False))
            except Exception as e:
                print(f"[MARK_FINISHED_CHAT] Xatolik: {e}")

    def notify_technician(self, chat_id, message_id, session, first_name, username, user_id, text, is_ikpu_exception=False):
        """Mijozning barcha ma'lumotlari (INN, Tashkilot, oylik holat, FM, yillik holat, rasm)ni texnik (@Yashnarbek_butaev)ga yetkazish"""
        is_ikpu = is_ikpu_exception or getattr(session, "ikpu_exception_active", False)

        # 1. Agar bu IKPU istisnosi bo'lmasa, shartlar tekshiriladi:
        if not is_ikpu:
            # 1. Rasm tekshiruvi:
            if not getattr(session, "last_photo_file_id", None):
                resp = (
                    "📷 Agar aparatingiz ishlamayotgan bo'lsa, apparat chiqargan xatolikni aparat ekrani to'liq ko'ringan holda (tepadagi soat va interneti bilan) **rasmga olib yuboring** — sizni mas'ul texnik mutaxassisimiz bilan bog'laymiz."
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=message_id)
                return

            # 2. Oylik to'lov tekshiruvi:
            if session.oylik_holat != "toza":
                if session.oylik_holat == "qarzdor":
                    pay_prompt_text = (
                        f"⚠️ *Kassa aparatingiz ishlashi uchun oylik abonent to'lovidan qarzdorlikni to'lashingiz lozim.*\n\n"
                        f"Qarzdorlik bartaraf etilgach, apparat faoliyati tiklanadi.\n"
                        f"Oylik abonent to'lovi hisob raqami va to'lov qo'llanmasi quyida yuborildi 👇"
                    )
                    self.bot.send_message(chat_id, pay_prompt_text, reply_to_message_id=message_id)
                    self.send_monthly_payment_media(chat_id, reply_to_id=message_id)
                    return
                resp = (
                    f"Kassa apparatidagi muammoni aniqlash uchun tashkilotingizning 9 xonali STIR (INN) yoki 14 xonali JSHSHIR raqamini yuboring.\n\n"
                    f"ℹ️ *Ma'lumot uchun:* Tashkilotingiz INN yoki JSHSHIR raqami aparatingiz chiqargan chekda *STIR* deb yozilgan bo'limida ko'rsatilgan."
                )
                session.state = "AWAITING_INN"
                session_mgr.save_sessions()
                self.bot.send_message(chat_id, resp, reply_to_message_id=message_id)
                return

            # 3. Rasm bor va Oylik toza! Endi rasmdagi xatolikni tekshiramiz:
            photo_ocr = getattr(session, "last_photo_text", "")
            caption_text = getattr(session, "last_photo_caption", "")
            is_offline = self.is_offline_limit_error(photo_ocr) or self.is_offline_limit_error(caption_text)

            if is_offline:
                # Ushbu xatoliklar (406 / 36889) aks etgan bo'lsa: yillikni tekshirish majburiy!
                # Agar yillikdan ham, oylikdan ham faol bo'lsa texnikka bog'laymiz!
                if session.fm_holat != "toza":
                    if session.fm_holat == "qarzdor":
                        resp = (
                            f"⚠️ Kassa aparatingiz ishlashi uchun yillik fiskal modul to'lovini amalga oshirishingiz lozim. "
                            f"To'lov amalga oshirilgach apparat faoliyati tiklanadi.\n\n"
                            f"To'lov qilish bo'yicha video qo'llanma va hisob raqam rekvizitini yubormoqdaman 👇"
                        )
                        self.bot.send_message(chat_id, resp, reply_to_message_id=message_id)
                        self.send_yearly_payment_media(chat_id, reply_to_id=message_id)
                        return
                    resp = self.get_offline_limit_explanation_text()
                    session.state = "AWAITING_FM"
                    session.offline_limit_error_active = True
                    session_mgr.save_sessions()
                    self.bot.send_message(chat_id, resp, reply_to_message_id=message_id, reply_markup=self.get_offline_limit_keyboard())
                    return
            else:
                # Yuborilgan rasmda 406 / 36889 xatoliklari bo'lmasa:
                # Yillik tekshirish majburiy emas (ixtiyoriy). Oylik toza bo'lgani sababli to'g'ridan-to'g'ri texnikka ulanadi!
                pass

        inn_str = session.inn if session.inn else "Ko'rsatilmagan"
        org_str = session.org_name if session.org_name else "Mavjud emas"
        fm_str = session.fm_number if session.fm_number else "Ko'rsatilmagan"

        # Oylik to'lov holati
        if session.oylik_holat == "toza":
            oylik_info = "Qarzi yo'q"
        elif session.oylik_holat == "qarzdor":
            oylik_info = f"Qarzdorlik mavjud ({session.oylik_qarz or ''} so'm)".strip()
        else:
            oylik_info = "Tekshirilmagan"

        # Yillik Fiskal Modul holati
        if session.fm_holat == "toza":
            fm_info = "Qarzi yo'q"
        elif session.fm_holat == "qarzdor":
            fm_info = "Qarzdorlik mavjud"
        elif session.fm_holat == "royxatdan_chiqarilgan":
            fm_info = "Ro'yxatdan chiqarilgan"
        else:
            fm_info = "Tekshirilmagan"

        if is_ikpu:
            header_prefix = "🚨 *ISTISNO: APARATDA 'ИКПУ' XATOLIGI!*\nℹ️ Mijozga video qo'llanma yuborilgan, ammo muammo bartaraf bo'lmagan.\n\n"
        elif getattr(session, "offline_limit_error_active", False) or is_offline:
            header_prefix = "🚨 *APARATDA OFLAYN REJIM (406 / 36889) XATOLIGI!*\nℹ️ Oylik va Yillik to'lovlar tekshirildi (Ikkalasi ham faol).\n\n"
        else:
            header_prefix = ""

        alert_text = (
            f"{header_prefix}"
            f"🏢 Tashkilot: {org_str}\n"
            f"📑 INN / JSHSHIR: `{inn_str}`\n"
            f"💳 Oylik to'lov: {oylik_info}\n"
            f"📟 Yillik to'lov: {fm_info}\n"
            f"🆔 `{user_id}`"
        )

        client_data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "inn": inn_str,
            "org_name": org_str,
            "fm": fm_str,
            "last_photo_file_id": getattr(session, "last_photo_file_id", None)
        }

        # 1. Tiketni ro'yxatga olamiz
        ticket = ticket_service.register_ticket(
            tech_msg_id=None,
            client_data=client_data,
            base_card=alert_text
        )
        card_kb = ticket_service.get_channel_keyboard(ticket)
        card_text = ticket_service.format_channel_card(ticket)

        # 2. Texniklar kanaliga (@mars_tex_xizmat) yuborish
        chan_id = config.TECHNICIAN_CHANNEL_ID
        channel_msg_id = None
        is_photo_card = False

        try:
            if getattr(session, "last_photo_file_id", None):
                photo_res = self.bot.send_photo(
                    chan_id,
                    session.last_photo_file_id,
                    caption=card_text,
                    reply_markup=card_kb
                )
                if photo_res.get("ok"):
                    channel_msg_id = photo_res["result"]["message_id"]
                    is_photo_card = True
            if not channel_msg_id:
                msg_res = self.bot.send_message(chan_id, card_text, reply_markup=card_kb)
                if msg_res.get("ok"):
                    channel_msg_id = msg_res["result"]["message_id"]
                    is_photo_card = False
        except Exception as e:
            print(f"[ALERT_CHANNEL] Kanalga yuborishda xatolik: {e}")

        if channel_msg_id:
            ticket["channel_message_id"] = channel_msg_id
            ticket["is_photo"] = is_photo_card
            ticket_service.tickets[str(channel_msg_id)] = ticket

        # 3. Texnik va adminlarning shaxsiy chatiga ham mijoz ma'lumotlarini yuborish
        target_ids = list(set([config.TECHNICIAN_TELEGRAM_ID] + config.ADMIN_TELEGRAM_IDS))
        admin_messages = []
        tech_chat_text = (
            f"🚨 *Yangi murojaat:*\n\n"
            f"{alert_text}\n\n"
            f"💬 _Javob berish yoki qabul qilish uchun ushbu xabarga «Reply» (Javob) qilib yozing yoki «+» yuboring._"
        )
        photo_file_id = getattr(session, "last_photo_file_id", None)
        for adm_id in target_ids:
            try:
                if photo_file_id:
                    res_alert = self.bot.send_photo(adm_id, photo_file_id, caption=tech_chat_text)
                    if res_alert.get("ok"):
                        alert_mid = res_alert["result"]["message_id"]
                        admin_messages.append({"chat_id": adm_id, "message_id": alert_mid, "is_photo": True})
                else:
                    res_alert = self.bot.send_message(adm_id, tech_chat_text)
                    if res_alert.get("ok"):
                        alert_mid = res_alert["result"]["message_id"]
                        admin_messages.append({"chat_id": adm_id, "message_id": alert_mid, "is_photo": False})
            except Exception as e_alert:
                print(f"[NOTIFY_TECH_DIRECT] Texnik ({adm_id}) ga yuborishda xatolik: {e_alert}")

        if admin_messages:
            ticket["admin_messages"] = admin_messages
            ticket["tech_msg_id"] = admin_messages[0]["message_id"]
            for am in admin_messages:
                ticket_service.tickets[str(am["message_id"])] = ticket

        ticket_service.save_tickets()

        # Mijozga yuboriladigan muloyim va chiroyli javob
        if is_ikpu:
            reply_msg = (
                f"👨‍💻 Aparatingizdagi 'ИКПУ' xatoligi bo'yicha barcha ma'lumotlar mas'ul texnik mutaxassisimizga yetkazildi.\n\n"
                f"Mutaxassisimiz tez orada vaziyatni o'rganib chiqib sizga javob beradi yoki siz bilan bog'lanadi. Sabr qilishingizni so'raymiz!"
            )
        elif getattr(session, "offline_limit_error_active", False) or is_offline:
            reply_msg = (
                f"👨‍💻 Aparatingizdagi oflayn rejim (406 / 36889) xatoligi bo'yicha ma'lumotlar mas'ul texnik mutaxassisimizga yetkazildi.\n\n"
                f"✅ Oylik va Yillik to'lovlaringiz faol ekanligi tasdiqlandi. Mutaxassisimiz tez orada apparat sozlamalarini tekshirib siz bilan bog'lanadi yoki javob beradi. Iltimos, biroz kutib turing!"
            )
        else:
            reply_msg = (
                f"👨‍💻 Barcha ma'lumotlar va yuborgan rasmingiz mas'ul texnik mutaxassisimizga yetkazildi.\n\n"
                f"✅ Oylik abonent to'lovingiz faol holatda. Mutaxassisimiz tez orada apparatdagi nosozlikni o'rganib chiqib sizga javob beradi yoki siz bilan bog'lanadi. Javobni kutishingizni so'raymiz!"
            )
        session.state = "ADMIN_BOGLANISH"
        session_mgr.save_sessions()
        self.bot.send_message(chat_id, reply_msg, reply_to_message_id=message_id)

    def is_payment_made_notification(self, norm_text):
        """Mijoz to'lov amalga oshirganligini (to'ladim, to'lov qildim, pul o'tkazdim va h.k.) bildirsa"""
        # 1. Agar to'lash yo'riqnomasi / rekvizit / qanday to'lash so'ralayotgan bo'lsa, bu to'lov xabarnomasi emas
        if any(q in norm_text for q in [
            "qanday to'la", "qayerga to'la", "qayerdan to'la", "to'lash tartibi", "to'lash kerak",
            "to'lamoqchiman", "to'lasam bo'ladi", "to'lash mumkin", "rekvizit", "video", "darslik"
        ]):
            return False

        # 2. Agar aniq to'lovlar tarixi, hisobot yoki to'lov hisob-kitobidan norozilik/e'tiroz/savol bo'lsa
        if any(h in norm_text for h in [
            "tarix", "hisobot", "xisobot", "oyma-oy", "oyma oy", "kesimida",
            "qaysi oy", "qaysi oylar", "yetadigan", "yetishi", "yetadi", "yetmaydi", "yetardi",
            "qanaqasiga", "qanaqa qilib", "qanday qilib", "qani", "nega qarz", "nimaga qarz", "qayerdan qarz",
            "nega", "nimaga", "qayerga", "qayerdan",
            "oldindan to'la", "avans", "ortiqcha",
            "keyingi oy", "kelasi oy", "yil oxirigacha", "yil oxiri",
            "xato", "adash", "noto'g'ri", "qarzim yo'q", "qarz emas"
        ]):
            return False

        # 3. To'lov qilinganligini bildiruvchi aniq iboralar va fe'llar
        payment_phrases = [
            # To'lov qildim / qildik / qilindi
            "to'lov qildim", "to'lov qildik", "to'lov qilindi", "to'lov qilingan", "to'lov qilib bo'ldim",
            "to'lov qilib bo'ldik", "to'lov qilib bo'lingan", "to'lov qilib qo'ydim", "to'lov qilib qo'ydik",
            "to'lov amalga oshirildi", "to'lov amalga oshirdim", "to'lov amalga oshirdik",
            "to'lov bo'ldi", "to'lov bo'lgan", "to'lov o'tdi", "to'lov tushdi",
            "to'lovni qildim", "to'lovni qildik", "to'lovimni qildim", "to'lovimizni qildik",
            "to'lovini qildim", "to'lovini qildik", "to'lovni to'ladim", "to'lovini to'ladim",

            # To'ladim / to'ladik / to'landi
            "to'ladim", "to'ladik", "to'landi", "to'ladimku", "to'ladikku",
            "to'lab bo'ldim", "to'lab bo'ldik", "to'lab bo'lingan",
            "to'lab qo'ydim", "to'lab qo'ydik", "to'lab berdim", "to'lab berdik",
            "to'lab tashladim", "to'lab tashladik", "to'lab yubordim", "to'lab yubordik",
            "to'lab ketdim", "to'lab o'tdim",

            # Pul o'tkazdim / tashladim
            "pul o'tkazdim", "pul o'tkazdik", "pul o'tkazildi", "pul o'tdi", "pul tushdi",
            "pul tashladim", "pul tashladik", "pul tashlandi",
            "pulini to'ladim", "pulini to'ladik", "pulini o'tkazdim", "pulini tashladim",
            "puli to'landi", "puli o'tkazildi", "puli tashlandi",
            "pul o'tkazib berdim", "pul tashlab berdim", "pul o'tkazib yubordim", "pul tashlab yubordim",

            # Oplata
            "oplata qildim", "oplata qildik", "oplata qilindi", "oplata bo'ldi",
            "oplata qilib bo'ldik", "oplata qilib qo'ydik",
            "oplatili", "oplatil", "oplacheno", "oplata sdelana",

            # Ilovalar orqali
            "clickdan to'ladim", "click orqali to'ladim", "clickdan to'lov qildim",
            "paymedan to'ladim", "payme orqali to'ladim", "paymedan to'lov qildim",
            "bankdan to'ladim", "bank orqali to'ladim", "paynetdan to'ladim",

            # Mana to'ladim
            "mana to'ladim", "mana to'lov qildim", "mana tashladim", "mana o'tkazdim", "mana to'ladik"
        ]

        if any(p in norm_text for p in payment_phrases):
            return True

        words = norm_text.split()
        if any(w in ["to'ladim", "to'ladik", "to'landi", "to'ladimku", "to'ladikku", "oplatil", "oplatili", "oplacheno"] for w in words):
            return True

        has_pay = any(w in norm_text for w in ["to'lov", "pul", "oplata", "to'lovni"])
        has_done = any(w in norm_text for w in ["qildim", "qildik", "bo'ldi", "o'tkazdim", "tashladim", "o'tdi", "yubordim", "berdim", "utkazdim", "utkazdik"])
        if has_pay and has_done:
            return True

        return False

    def is_payment_history_query(self, norm_text, session=None):
        """Mijoz qaysi oyga qancha to'laganini bilmoqchi bo'lsa yoki to'lov/qarzdorlik bo'yicha norozilik bildirsa"""
        # Agar to'lov amalga oshirilganligi haqida toza xabar berilayotgan bo'lsa, bu tarix emas!
        if self.is_payment_made_notification(norm_text):
            return False

        # Faqat toza to'lash yo'riqnomasi / qanday to'lash so'ralayotgan bo'lsa (tarix/e'tiroz bo'lmasa)
        pure_pay_intents = ["qanday to'lasam", "qanday to'layman", "qanday to'lash kerak", "qayerga to'layman", "to'lash tartibi", "to'lov qilish tartibi"]
        if any(p in norm_text for p in pure_pay_intents) and not any(h in norm_text for h in ["tarix", "hisobot", "to'lagan", "to'lab", "qani", "yetadigan", "yetishi", "yetadi", "oldindan"]):
            return False

        phrases = [
            # Aniq tarix va hisobot so'rovlari
            "to'lovlar tarixi va hisoboti", "to'lovlar tarixi va xisoboti", "tulovlar tarixi va xisoboti", "tulovlar tarixi va hisoboti",
            "to'lovlar tarixi", "to'lov tarixi", "to'lovlarim tarixi", "tarixni ko'rsat", "to'lovlar hisoboti", "to'lov hisoboti",
            "tolovlar tarixi", "tolov tarixi", "tulov tarixi", "tulovlar tarixi", "oylik tarixi", "oylik to'lovlar tarixi",
            "to'lovlar tarixi", "tarixini ko'rsat", "tarixini ber", "hisobotini ko'rsat", "hisobotini ber",
            "oyma-oy", "oyma oy", "oylar kesimida", "oylar boyicha", "oylar bo'yicha",
            "qaysi oylar to'langan", "qaysi oylarga to'langan", "qaysi oy to'langan", "qaysi oylarga to'langanini",
            "qaysi oylar to'lanmagan", "qaysi oy to'lanmagan", "to'langan oylar", "to'lanmagan oylar",
            "qancha to'laganman", "qancha to'langan", "qaysi oy qancha",

            # To'langanini ta'kidlash / norozilik (o'tgan oylar yoki oldindan to'langanligi)
            "to'laganman", "to'laganmanku", "to'lagandim", "to'lagandimku",
            "to'lab qo'yganman", "to'lab qo'yganmanku",
            "to'lab qo'ygandim", "to'lab qo'ygandimku", "to'lab qo'yganmiz", "to'lab qo'yganmizku", "to'lab qo'ygandik", "to'lab qo'ygandikku",
            "to'lab bo'lganman", "to'lab bo'lganmanku", "to'lab bo'lgandim", "to'lab bo'lgandimku", "to'lab bo'lganmiz",
            "to'lagandik", "to'lagandikku", "to'laganmiz", "to'laganmizku",
            "men to'laganman", "men to'lagandim", "biz to'laganmiz", "biz to'lagandik",
            "to'langan bo'lishi kerak", "to'langan bo'lishi", "to'langan edi", "to'lagan edim",
            "to'lab ketganman", "to'lab ketgandim", "to'lab bergandim",

            # Yetishi kerak / yetadi / yetmaydi / qanaqasiga
            "qanaqasiga", "yetishi kerak", "yetishi", "yetadi", "yetmaydi", "yetardi", "yetmasligi",
            "yetadigan qilib", "yetadigan",

            # Keyingi oylar / avans / oldindan to'lov da'vosi / yil oxirigacha
            "keyingi oyga ham", "keyingi oyga", "keyingi oy uchun ham", "keyingi oy uchun", "keyingi oylarga",
            "kelasi oyga ham", "kelasi oyga", "kelasi oy uchun ham", "kelasi oy uchun", "kelasi oylarga",
            "yil oxirigacha", "yil oxiri", "yil oxirigacha ham", "yilgacha",
            "oldindan to'langan", "oldindan to'lab", "oldindan to'lagan", "avans to'langan", "avans to'lagan",
            "ortiqcha to'lagan", "ortiqcha to'langan", "to'laganim qani", "pulim qani", "to'lagan pulim",
            "to'lagan pullarim", "to'langan pul", "pul to'lagan", "to'lagan pullar", "to'lagan pul",

            # Qarzdorlikdan norozilik va e'tirozlar
            "nimaga qarz", "nimaga qarzdorlik", "nega qarz", "nega qarzdorlik",
            "qayerdan qarz", "qayerdan qarzdorlik", "qarzim yo'q", "qarz yo'q", "qarz yo'q edi", "qarzdor emas",
            "qarz emasman", "qarz emasmiz", "qarz chiqaryapti", "qarz ko'rsatyapti",
            "adashyapsiz", "noto'g'ri", "xato hisoblangan", "noto'g'ri hisoblangan"
        ]

        if any(p in norm_text for p in phrases):
            return True

        # Tarix yoki hisobot so'zi bo'lsa
        if any(w in norm_text for w in ["tarix", "tarixi", "hisobot", "hisoboti", "xisobot", "xisoboti"]):
            return True

        # Qaysi oylar: masalan "qaysi oylarga to'langanini ko'rsat"
        if "qaysi" in norm_text and ("oy" in norm_text or "oylar" in norm_text):
            return True

        # Semantik tekshiruv: agar to'lov/pul so'zi bilan birga e'tiroz, savol, muddat yoki qo'shimchalar bo'lsa
        has_pay_word = any(w in norm_text for w in [
            "to'la", "to'lov", "pul", "tulan", "tulov", "to'lag", "to'lagan", "to'lovdim", "to'lashim"
        ])
        has_complaint_marker = any(w in norm_text for w in [
            "ku", "edi", "edim", "ediku", "qo'ygan", "qo'ydim", "qo'ygandim", "bo'lgan", "bo'lgandim", 
            "yetadigan", "yetishi", "yetadi", "yetmaydi", "yetardi", "keyingi", "kelasi",
            "yil", "oxirigacha", "oxiri",
            "avans", "oldindan", "ortiqcha", "qani", "nega", "nimaga", "qayerga", "qayerdan", "qanaqasiga",
            "adash", "xato", "noto'g'ri", "yo'q edi"
        ])
        if has_pay_word and has_complaint_marker:
            return True

        # Agar session da INN mavjud bo'lsa (mijoz hozirgina abonent holatini tekshirgan bo'lsa):
        # Har qanday e'tiroz yoki savol (masalan: "yetishi kerak", "qanaqasiga", "yil oxirigacha", "xato") to'lovlar tarixini chiqarishi kerak!
        if session and getattr(session, "inn", None):
            dispute_terms = [
                "qanaqasiga", "yetishi kerak", "yetishi", "yetadi", "yetmaydi", "adashyapsiz", 
                "xato", "noto'g'ri", "qarzim yo'q", "qarz emas", "nega qarz", "nimaga qarz",
                "yil oxirigacha", "keyingi oy", "kelasi oy"
            ]
            if any(term in norm_text for term in dispute_terms):
                return True

        return False

    def extract_inn(self, text):
        """Matndan 9 xonali (INN) yoki 14 xonali (JSHSHIR) raqamni topish (havolalarni inkor qiladi)"""
        if not text:
            return None
        # Agar matnda havola (URL / link) bo'lsa, uni mutlaqo INN deb olmaslik kerak!
        if any(h in text.lower() for h in ["http://", "https://", "t.me/", "telegram.me/"]):
            return None

        # 1. Telefon raqam sifatida ko'rsatilgan bo'lsa, uni inkor qilish (masalan: "tel: 901234567")
        tel_match = re.search(r"(?:tel|telefon|aloqa|nomer)\s*[:\-]?\s*(\d{9})\b", text, re.IGNORECASE)
        excluded_tel = tel_match.group(1) if tel_match else None

        # 2. INN / STIR / JSHSHIR deb belgilangan raqam:
        # masalan: "INN 305 123 456", "STIR: 305-123-456", "JSHSHIR 31234567890123"
        m_inn_labeled = re.search(r"(?:inn|stir|jshshir|инн|стир|жшшир)[:\s\-]*([0-9\s\-]{9,20})", text, re.IGNORECASE)
        if m_inn_labeled:
            digits = re.sub(r"\D", "", m_inn_labeled.group(1))
            if len(digits) == 9 or len(digits) == 14:
                return digits

        # 3. 3-3-3 ko'rinishida probel yoki tire bilan ajratilgan 9 ta raqam (masalan: 305 123 456 yoki 305-123-456)
        m_spaced = re.search(r"\b(\d{3})[\s\-](\d{3})[\s\-](\d{3})\b", text)
        if m_spaced:
            d9 = f"{m_spaced.group(1)}{m_spaced.group(2)}{m_spaced.group(3)}"
            if d9 != excluded_tel:
                return d9

        # 4. So'z chegarasidagi aniq 9 xonali (STIR) yoki 14 xonali (JSHSHIR) raqam
        matches = re.findall(r"\b\d{9}\b|\b\d{14}\b", text)
        for m in matches:
            if m == excluded_tel:
                continue
            return m

        # 5. Agar butun matn toza 9 yoki 14 ta raqam bo'lsa (probel va defislardan tozalanganda)
        clean_text = re.sub(r"[\s\-_]", "", text)
        clean_matches = re.findall(r"^\d{9}$|^\d{14}$", clean_text)
        if clean_matches and clean_matches[0] != excluded_tel:
            return clean_matches[0]

        return None

    def extract_fm(self, text, is_awaiting_fm=False):
        """Matndan Fiskal Modul (FM) raqamini topish (har qanday vaziyatda)"""
        if not text:
            return None
        cleaned_text = text.strip()
        # Havolalarni inkor qilish
        if any(h in cleaned_text.lower() for h in ["http://", "https://", "t.me/"]):
            return None

        # 1. Boshida 2 ta harf (Lotin yoki Kirill: LG, FM, MF, ЛГ, ФМ, МФ) va 10-12 ta raqam
        # masalan: LG420230615712, ЛГ420230615712, FM1234567890, ФМ 1234567890, LG-123456789012
        m = re.search(r"\b([A-Za-zА-Яа-яЁё]{2})[:\-_\s]?(\d{10,12})\b", cleaned_text)
        if m:
            letters_raw = m.group(1).upper()
            cyr_map = {"ЛГ": "LG", "ФМ": "FM", "МФ": "MF", "ЛG": "LG", "LГ": "LG"}
            letters = cyr_map.get(letters_raw, letters_raw)
            if re.match(r"^[A-Z]{2}$", letters):
                digits = m.group(2)
                return f"{letters}{digits}"

        # 2. "FM", "ФМ", "fiskal modul", "фискал модуль" so'zlari bilan birga kelgan 10-12 ta raqam
        # masalan: "FM 420230615712", "FM raqami: 420230615712", "fiskal modul 420230615712"
        m_fm_word = re.search(r"(?:fm|фм|fiskal\s*modul|фискал\s*модул[ья]?)[:\s\-a-zа-яё]*(\d{10,12})\b", cleaned_text, re.IGNORECASE)
        if m_fm_word:
            clean_d = m_fm_word.group(1)
            if not (len(clean_d) == 12 and clean_d.startswith("998")):
                return clean_d

        # 3. Matndagi 10-12 ta toza raqam (998 bilan boshlanadigan 12 xonali tel raqamlar bundan mustasno)
        # Bu orqali mijoz har qanday vaziyatda shunchaki 10-12 xonali raqam yuborganda ham yillik FM tekshiriladi!
        all_10_12 = re.findall(r"\b\d{10,12}\b", cleaned_text)
        for num in all_10_12:
            if len(num) == 12 and num.startswith("998"):
                continue
            return num

        # 4. Probellar yoki defislar bilan yozilgan 10-12 xonali raqam (masalan: 420 230 615 712)
        clean_digits = re.sub(r"\D", "", cleaned_text)
        if 10 <= len(clean_digits) <= 12 and not (len(clean_digits) == 12 and clean_digits.startswith("998")):
            # Agar matnda uzun boshqa so'zlar bo'lmasa
            words_only = re.findall(r"[a-zA-Zа-яА-Я]{3,}", cleaned_text)
            if len(words_only) <= 2:
                return clean_digits

        return None
    def handle_channel_post(self, post):
        """Telegram kanalga tashlangan yangi hisob-kitob jadvallari, video va rasmlarni avtomatik qabul qilish"""
        chat_id = post["chat"]["id"]
        chat_title = post["chat"].get("title", "Telegram Kanal")
        cache = load_media_cache()

        # 1. Yangi hisob-kitob jadvali (Excel/CSV fayl)
        if "document" in post:
            doc = post["document"]
            file_name = doc.get("file_name", "").lower()
            if file_name.endswith(".xlsx") or file_name.endswith(".csv") or file_name.endswith(".xls"):
                timestamp = int(time.time())
                temp_path = os.path.join(config.DATA_DIR, f"channel_{timestamp}_{file_name}")
                print(f"[KANAL] 📥 Yangi hisob-kitob jadvali qabul qilindi: {file_name} (Kanal: '{chat_title}')")
                
                if self.bot.download_file(doc["file_id"], temp_path):
                    count = excel_service.update_excel_file(temp_path)
                    print(f"[KANAL] ✅ Baza muvaffaqiyatli yangilandi! Jami: {count} ta tashkilot ma'lumotlari yuklandi.")
                    try:
                        self.bot.send_message(
                            chat_id, 
                            f"✅ *Oylik abonent hisob-kitob jadvali muvaffaqiyatli yangilandi!*\n\n"
                            f"📁 Fayl: `{file_name}`\n"
                            f"👥 Bazadagi jami tashkilotlar: *{count} ta*\n"
                            f"🤖 Bot endi aynan ushbu yangi hisob-kitob bo'yicha mijozlarga javob beradi."
                        )
                    except Exception:
                        pass
                else:
                    print(f"[KANAL] ❌ Faylni yuklab olishda xatolik yuz berdi: {file_name}")

        # 2. Yangi Video yoki animatsiya (Qo'llanmalar va darsliklar)
        if "video" in post or "animation" in post:
            media_obj = post.get("video") or post.get("animation")
            file_id = media_obj.get("file_id")
            caption = (post.get("caption", "") or "").strip()
            c_low = caption.lower()
            cache["channel_id"] = chat_id
            mid = post["message_id"]

            if any(k in c_low for k in ["yillik", "fiskal modul", "feskal modul", "ofd"]):
                cache["yillik_video_msg_id"] = mid
                cache["yillik_video_file_id"] = file_id
                print(f"[KANAL] 🎬 Yillik to'lov video qo'llanmasi post ID #{mid} saqlandi!")
            elif any(k in c_low for k in ["sana", "vaqt", "soat"]):
                cache["clock_video_msg_id"] = mid
                print(f"[KANAL] 🎬 Soat / sana sozlash video qo'llanmasi post ID #{mid} saqlandi!")
            elif any(k in c_low for k in ["ikpu", "mxik", "o'lchov", "olchov", "dastur"]):
                cache["ikpu_video_msg_id"] = mid
                print(f"[KANAL] 🎬 IKPU / dastur video qo'llanmasi post ID #{mid} saqlandi!")
            else:
                cache["oylik_video_msg_id"] = mid
                cache["oylik_video_file_id"] = file_id
                cache["oylik_video_caption"] = caption or config.VIDEO_OYLIK_CAPTION
                print(f"[KANAL] 🎬 Oylik to'lov video qo'llanmasi post ID #{mid} saqlandi!")
            save_media_cache(cache)

        # 3. Yangi Rasm yoki Matn (Click rekvizit rasmi / matni)
        if "photo" in post or "text" in post:
            caption = (post.get("caption", "") or post.get("text", "")).strip()
            c_low = caption.lower()
            cache["channel_id"] = chat_id
            mid = post["message_id"]
            if any(k in c_low for k in ["inn", "jshshir", "chek"]):
                cache["inn_jshshir_msg_id"] = mid
            else:
                cache["oylik_rekvizit_msg_id"] = mid
                if "photo" in post:
                    photo_arr = post.get("photo", [])
                    if photo_arr:
                        cache["oylik_photo_file_id"] = photo_arr[-1]["file_id"]
                cache["oylik_photo_caption"] = caption or config.REKVIZIT_OYLIK
            save_media_cache(cache)
            print(f"[KANAL] 🖼 Post ID #{mid} rekvizit/ma'lumot sifatida saqlandi!")

    def handle_callback_query(self, callback_query):
        """Inline tugmalar bosilganda qayta ishlash"""
        cq_id = callback_query.get("id")
        data = callback_query.get("data", "")
        message = callback_query.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")
        from_user = callback_query.get("from", {})
        user_id = from_user.get("id")

        if not chat_id:
            return

        # 0.0. Murojaatni qabul qilish (Texnik tomonidan)
        if data.startswith("claim_ticket_"):
            target_uid = data.replace("claim_ticket_", "")
            ticket = ticket_service.find_ticket_by_user_id(target_uid)
            if not ticket:
                self.bot.answer_callback_query(cq_id, "⚠️ Murojaat topilmadi!", show_alert=True)
                return

            claimed_by = ticket.get("claimed_by")
            tech_name = from_user.get("first_name", "") + (" " + from_user.get("last_name", "") if from_user.get("last_name") else "")
            tech_name = tech_name.strip() or f"Texnik {user_id}"
            tech_username = from_user.get("username", "")

            if claimed_by:
                c_name = claimed_by.get("name", "Boshqa texnik")
                self.bot.answer_callback_query(cq_id, f"⚠️ Ushbu murojaatni allaqachon {c_name} qabul qilgan!", show_alert=True)
                return

            # Qabul qilish
            ticket["claimed_by"] = {
                "user_id": user_id,
                "name": tech_name,
                "username": tech_username,
                "time": time.time()
            }
            ticket_service.save_tickets()

            # Kanal postini tahrirlash:
            chan_id = config.TECHNICIAN_CHANNEL_ID
            chan_msg_id = ticket.get("channel_message_id")
            if chan_id and chan_msg_id:
                updated_text = ticket_service.format_channel_card(ticket)
                new_kb = ticket_service.get_channel_keyboard(ticket)
                is_photo = ticket.get("is_photo", False)
                self.bot.edit_ticket_card(chan_id, chan_msg_id, updated_text, is_photo=is_photo, reply_markup=new_kb)

            self.bot.answer_callback_query(cq_id, "✅ Murojaat sizga biriktirildi!\n'💬 Fikr bildirish' tugmasini bosib mijozga javob yozing.", show_alert=True)

            # Mijozga xabar berish
            try:
                self.bot.send_message(
                    target_uid,
                    "👨‍💻 *Murojaatingizni mas'ul texnik mutaxassisimiz qabul qildi.*\n\n"
                    "Mutaxassisimiz tez orada sizga javob yozadi, iltimos kuting!"
                )
            except Exception:
                pass

            # Muhokama guruhiga bildirishnoma
            disc_id = ticket.get("group_discussion_id")
            if disc_id and config.DISCUSSION_GROUP_ID:
                try:
                    u_tag = f"@{tech_username}" if tech_username else tech_name
                    self.bot.send_message(
                        config.DISCUSSION_GROUP_ID,
                        f"👨‍💻 *Murojaatni texnik mutaxassis {u_tag} qabul qildi.*\n"
                        f"Mijoz bilan shu yerda sharhlar orqali muloqot qilishingiz mumkin 👇",
                        reply_to_message_id=disc_id
                    )
                except Exception:
                    pass
            return

        if data.startswith("claimed_info_"):
            target_uid = data.replace("claimed_info_", "")
            ticket = ticket_service.find_ticket_by_user_id(target_uid)
            c_name = ticket.get("claimed_by", {}).get("name", "Texnik") if ticket else "Texnik"
            self.bot.answer_callback_query(cq_id, f"ℹ️ Ushbu murojaatni {c_name} qabul qilgan va hozirda xizmat ko'rsatmoqda.", show_alert=True)
            return

        self.bot.answer_callback_query(cq_id)
        session = session_mgr.get_session(user_id) if user_id else None

        # Bot o'z xabariga reply qilmasligi uchun mijozning asl xabariga reply qilamiz
        reply_target_id = message.get("reply_to_message", {}).get("message_id") or message_id

        # 0. Texnik uchun murojaat va medialar tarixi (Telegraph Instant View)
        if data.startswith("view_history_"):
            target_uid = data.replace("view_history_", "")
            ticket = ticket_service.find_ticket_by_user_id(target_uid)
            if ticket:
                tg_url = ticket.get("telegraph_url")
                if not tg_url:
                    from telegraph_service import telegraph_service
                    tg_url = telegraph_service.create_or_update_ticket_page(ticket)
                    ticket["telegraph_url"] = tg_url
                    ticket_service.save_tickets()
                resp = (
                    f"📂 *Murojaat va medialar to'liq tarixi:*\n\n"
                    f"🌐 [Instant View oynasida ochish]({tg_url})\n\n"
                    f"{ticket_service.format_card(ticket)}"
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=message_id)
            return

        # 1. To'lovlar tarixi
        if data.startswith("action_history_") or data == "action_history":
            inn = data.replace("action_history_", "") if data.startswith("action_history_") else (session.inn if session else None)
            if inn:
                info = excel_service.find_by_identifier(inn)
                if info:
                    resp = excel_service.get_payment_history_text(info)
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_target_id)
                    return
            resp = (
                "Yil davomida qaysi oylar uchun qancha to'lov qilinganligini tekshirish uchun "
                "tashkilotingizning INN yoki JSHSHIR raqamini yuboring."
            )
            if session:
                session.state = "AWAITING_INN_HISTORY"
                session_mgr.save_sessions()
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_target_id)
            return

        # 2. Yillik fiskal modul to'lovini tekshirish
        if data.startswith("action_check_yearly_") or data == "action_check_yearly":
            if session:
                session.unclear_count = 0
                session.state = "AWAITING_FM"
                session.last_intent = "check_yearly"
                session_mgr.save_sessions()
            resp = (
                "Yillik fiskal modul to'lovingizni tekshirib berishimni istasangiz, aparatingizning fiskal modul raqamini yuboring.\n\n"
                "ℹ️ *Ma'lumot uchun:* Fiskal modul raqami aparatingiz chiqargan chekning pastki qismida *FM raqami* deb yozilgan bo'limda ko'rsatiladi."
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_target_id)
            return

        # 3. Oylik abonent to'lovi (rekvizit va video)
        if data.startswith("action_pay_monthly_") or data == "action_pay_monthly":
            if session:
                session.last_topic = "pay_monthly"
                session_mgr.save_sessions()
            self.send_monthly_payment_media(chat_id, reply_to_id=reply_target_id)
            return

        # 4. Yillik fiskal modul to'lovi (rekvizit va video)
        if data.startswith("action_pay_yearly_") or data == "action_pay_yearly":
            if session:
                session.last_topic = "pay_yearly"
                session_mgr.save_sessions()
            self.send_yearly_payment_media(chat_id, reply_to_id=reply_target_id)
            return

        # 5. Mas'ul texnik bilan bog'lanish tugmasi
        if data.startswith("action_contact_tech"):
            first_name = from_user.get("first_name", "")
            username = from_user.get("username", "")
            if session and getattr(session, "last_photo_file_id", None):
                self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text="[Tugma bosildi: Mas'ul texnik bilan bog'lanish]")
            else:
                resp = "Agar aparatingiz baribir ishlamayotgan bo'lsa, aparat ekrani to'liq ko'ringan holda rasm olib tashlang men sizni masul texnik bilan bog'layman."
                self.bot.send_message(chat_id, resp, reply_to_message_id=message_id)
            return

    def process_inn_check(self, chat_id, message_id, reply_to_id, session, first_name, username, user_id, text, norm_text, found_inn):
        """Mijoz yuborgan STIR (INN) yoki JSHSHIR bo'yicha oylik abonent to'lovini tekshirish"""
        session.unclear_count = 0
        if self.is_offline_limit_error(text) or self.is_offline_limit_error(norm_text):
            session.offline_limit_error_active = True

        # 0. Agar to'lov kvitansiyasi uchun INN/JSHSHIR kutilayotgan bo'lsa:
        pending_rec = getattr(session, "pending_receipt", None)
        if pending_rec:
            info = excel_service.find_by_identifier(found_inn)
            if not info:
                resp = (
                    f"❌ *{found_inn}* raqami bo'yicha tashkilot ma'lumotlari hisob-kitob jadvalidan topilmadi.\n\n"
                    f"Iltimos, kassa apparatingiz chekidagi 9 xonali STIR (INN) yoki 14 xonali JSHSHIR raqamini tekshirib, qaytadan yuboring."
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            # Tashkilot Exceldan topildi!
            org_name = info["org_name"]
            inn = found_inn
            id_type = info.get("id_type", "STIR / INN")

            has_debt = info.get("has_debt", False)
            total_debt = info.get("total_debt", 0.0)
            has_advance = info.get("has_advance", False)
            advance_amount = info.get("advance_amount", 0.0)
            if has_debt and total_debt > 0:
                balans_str = f"⚠️ Qarzdorlik: *{total_debt:,.0f} so'm*".replace(",", " ")
            elif has_advance and advance_amount > 0:
                balans_str = f"💰 Ortiqcha to'lov (avans): *{advance_amount:,.0f} so'm*".replace(",", " ")
            else:
                balans_str = "✅ Qarzdorlik yo'q (0 so'm)"

            uname_str = f"@{username}" if username else "Mavjud emas"

            # Texnik va adminlarga kvitansiyani jo'natish
            target_ids = list(set([config.TECHNICIAN_TELEGRAM_ID] + config.ADMIN_TELEGRAM_IDS))
            tech_caption = (
                f"🧾 *Yangi to'lov kvitansiyasi keldi:*\n\n"
                f"🏢 Tashkilot: *{org_name}*\n"
                f"📑 {id_type}: `{inn}`\n"
                f"💳 Oylik abonent balansi: {balans_str}\n"
                f"👤 Yuboruvchi: {first_name} ({uname_str})\n"
                f"🆔 ID: `{user_id}`"
            )
            rec_file_id = pending_rec["file_id"]
            is_doc = pending_rec.get("is_doc", False)

            admin_messages = []
            for adm_id in target_ids:
                try:
                    if is_doc:
                        res_alert = self.bot.send_document(adm_id, rec_file_id, caption=tech_caption)
                    else:
                        res_alert = self.bot.send_photo(adm_id, rec_file_id, caption=tech_caption)
                    if res_alert.get("ok"):
                        alert_mid = res_alert["result"]["message_id"]
                        admin_messages.append({"chat_id": adm_id, "message_id": alert_mid, "is_photo": not is_doc})
                except Exception as e_alert:
                    print(f"[KVITANSIYA_PENDING_ALERT] Alert yuborishda xatolik: {e_alert}")

            ticket = ticket_service.register_ticket(
                tech_msg_id=admin_messages[0]["message_id"] if admin_messages else None,
                client_data={
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "first_name": first_name,
                    "org_name": org_name,
                    "inn": inn,
                    "type": "kvitansiya"
                },
                base_card=tech_caption,
                admin_messages=admin_messages
            )

            # Texniklar kanaliga (@mars_tex_xizmat) yuborish
            try:
                card_kb = ticket_service.get_channel_keyboard(ticket)
                card_text = ticket_service.format_channel_card(ticket)
                chan_id = config.TECHNICIAN_CHANNEL_ID
                if is_doc:
                    c_res = self.bot.send_document(chan_id, rec_file_id, caption=card_text, reply_markup=card_kb)
                else:
                    c_res = self.bot.send_photo(chan_id, rec_file_id, caption=card_text, reply_markup=card_kb)
                if not c_res.get("ok"):
                    c_res = self.bot.send_message(chan_id, card_text, reply_markup=card_kb)
                if c_res.get("ok"):
                    c_mid = c_res["result"]["message_id"]
                    ticket["channel_message_id"] = c_mid
                    ticket["is_photo"] = not is_doc
                    ticket_service.tickets[str(c_mid)] = ticket
                    ticket_service.save_tickets()
            except Exception as chan_e:
                print(f"[KVITANSIYA_CHANNEL_ALERT] Xatolik: {chan_e}")

            # Mijozga qisqa va muloyim javob
            client_resp = "🧾 *To'lov kvitansiyangiz mas'ul texnik mutaxassisimizga yetkazildi. Iltimos, kutib turing!*"
            session.state = "ADMIN_BOGLANISH"
            session.inn = inn
            session.org_name = org_name
            session.pending_receipt = None
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, client_resp, reply_to_message_id=reply_to_id)
            return

        # Yangi INN yoki JSHSHIR yuborilganda oldingi suhbat va aparat xotirasi to'liq unutiladi!
        is_history_req = (session.state == "AWAITING_INN_HISTORY" or (self.is_payment_history_query(norm_text, session) and not norm_text.strip().isdigit()))
        
        # Agar bot avval FM ni tekshirib, mijozdan INN so'ragan bo'lsa (AWAITING_INN) yoki FM tekshirilgan bo'lsa,
        # FM ma'lumotlarini va oflayn xatolik holatini saqlab qolamiz!
        preserve_fm = bool(session.state == "AWAITING_INN" or session.fm_holat is not None or getattr(session, "offline_limit_error_active", False))

        # Mijoz avvalroq rasm yuborgan bo'lsa, uni xotirada saqlab qolamiz (qayta rasm so'ramaslik uchun!):
        saved_photo_id = getattr(session, "last_photo_file_id", None)
        saved_photo_cap = getattr(session, "last_photo_caption", None)
        saved_photo_txt = getattr(session, "last_photo_text", None)
        saved_msg_id = getattr(session, "last_msg_id", None)

        # Mijoz bilan bo'lgan avvalgi suhbat holati yangilanadi (lekin yuborilgan rasm va tekshirilgan FM saqlanadi!)
        session.reset_for_new_target(preserve_photo=True, preserve_fm=preserve_fm)
        ticket_service.user_tickets.pop(str(user_id), None)
        ticket_service.save_tickets()

        if saved_photo_id:
            session.last_photo_file_id = saved_photo_id
            session.last_photo_caption = saved_photo_cap
            session.last_photo_text = saved_photo_txt
            session.last_msg_id = saved_msg_id

        if self.is_offline_limit_error(text) or self.is_offline_limit_error(norm_text):
            session.offline_limit_error_active = True

        inn_to_check = found_inn
        session.inn = inn_to_check

        # Agar mijoz aynan to'lovlar tarixini ko'rish uchun INN yuborgan bo'lsa
        if is_history_req:
            info = excel_service.find_by_identifier(inn_to_check)
            if info:
                session.inn = inn_to_check
                session.org_name = info["org_name"]
                session.state = "NORMAL"
                session_mgr.save_sessions()
                resp = excel_service.get_payment_history_text(info)
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

        # Excel bazadan tekshiramiz
        info = excel_service.find_by_inn(inn_to_check)
        session.inn = inn_to_check

        if info:
            session.org_name = info["org_name"]

            # Agar apparat (yoki barcha apparatlar) ro'yxatdan chiqarilgan bo'lsa
            if info["active_count"] == 0:
                session.oylik_holat = "ruyxatdan_chiqarilgan"
                session.state = "NORMAL"
                session_mgr.save_sessions()
                resp = (
                    f"🏢 *Tashkilot:* {info['org_name']}\n"
                    f"📑 *{info['id_type']}:* `{inn_to_check}`\n\n"
                    f"❌ *Ro'yxatdan chiqarilgan (kassa apparati faoliyati to'xtatilgan)*"
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            pos_lines = []
            for idx, p in enumerate(info["pos_list"], 1):
                if p["color_type"] == "red":
                    pos_lines.append(f"  {idx}-aparat: ❌ *Ro'yxatdan chiqarilgan* (kassa apparati faoliyati to'xtatilgan)")
                elif p["color_type"] == "yellow":
                    pos_lines.append(f"  {idx}-aparat: 📱 *P3 model kassa apparati*")
                else:
                    pos_lines.append(f"  {idx}-aparat: 📟 *SmartOne model kassa apparati*")
            pos_details_text = "\n".join(pos_lines)

            # Faol apparatlar soniga qarab so'z shakli
            if info["active_count"] == 1:
                pay_prompt_text = "Kassa aparatingiz ishlashi uchun oylik abonent qarzdorligingizni to'lashingiz so'raladi."
            else:
                pay_prompt_text = "Kassa aparatlaringiz ishlashi uchun oylik abonent qarzdorligingizni to'lashingiz so'raladi."

            if info["inactive_count"] > 0:
                pos_count_text = f"📌 *Faol kassa apparatlari soni:* *{info['active_count']} ta* (Jami: {info['total_pos_count']} ta, {info['inactive_count']} tasi ro'yxatdan chiqarilgan)"
            else:
                pos_count_text = f"📌 *Faol kassa apparatlari soni:* *{info['active_count']} ta*"

            if info["has_debt"]:
                session.oylik_qarz = info["total_debt"]
                session.oylik_holat = "qarzdor"
                session.state = "DEBT_EXISTS"

                fee_info_text = (
                    f"💳 *Oylik abonent tarifi:* Har bir apparat uchun 100 000 so'm/oy\n"
                    f"🗓 *Shu oyning oxirigacha to'lanishi kerak:* *{info['shu_oy_oxirigacha_text']} so'm*\n"
                    f"📅 *Yil oxirigacha to'lanishi kerak bo'lgan jami summa:* *{info['yil_oxirigacha_text']} so'm*"
                )

                resp = (
                    f"🏢 *Tashkilot:* {info['org_name']}\n"
                    f"📑 *STIR / INN:* `{inn_to_check}`\n"
                    f"{pos_count_text}\n\n"
                    f"📋 *Apparatlar modeli va holati:*\n{pos_details_text}\n\n"
                    f"⚠️ *DIQQAT:* Sizda oylik abonent to'lovidan *{info['total_debt_text']} so'm* qarzdorlik mavjud!\n\n"
                    f"{fee_info_text}\n\n"
                    f"{pay_prompt_text}"
                )
                session_mgr.save_sessions()
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                self.send_monthly_payment_media(chat_id, reply_to_id=reply_to_id)
                return
            else:
                session.oylik_qarz = 0
                session.oylik_holat = "toza"
                session.state = "NORMAL"

                if info.get("has_advance"):
                    fee_info_text = info["advance_text"]
                else:
                    next_months = info["next_months_count"]
                    if next_months > 0:
                        fee_info_text = (
                            f"💳 *Oylik abonent tarifi:* Har bir apparat uchun 100 000 so'm/oy\n"
                            f"🗓 *Shu oyning oxirigacha to'lanishi kerak:* *0 so'm (joriy oy to'langan)*\n"
                            f"📅 *Keyingi oydan boshlab yil oxirigacha ({next_months} oy uchun):* *{info['yil_oxirigacha_text']} so'm*"
                        )
                    else:
                        fee_info_text = (
                            f"💳 *Oylik abonent tarifi:* Har bir apparat uchun 100 000 so'm/oy\n"
                            f"🗓 *Shu oyning oxirigacha to'lanishi kerak:* *0 so'm*\n"
                            f"📅 *Joriy yil uchun barcha oylik abonent to'lovlari to'liq to'langan.*"
                        )

                photo_ocr = getattr(session, "last_photo_text", "")
                caption_text = getattr(session, "last_photo_caption", "")
                is_offline = (
                    getattr(session, "offline_limit_error_active", False)
                    or self.is_offline_limit_error(photo_ocr)
                    or self.is_offline_limit_error(caption_text)
                )
                if is_offline or session.fm_holat == "toza":
                    if is_offline:
                        session.offline_limit_error_active = True
                    if session.fm_holat == "toza":
                        session_mgr.save_sessions()
                        if getattr(session, "last_photo_file_id", None):
                            self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text)
                            return
                        else:
                            resp = (
                                f"🏢 *Tashkilot:* {info['org_name']}\n"
                                f"📑 *STIR / INN:* `{inn_to_check}`\n"
                                f"{pos_count_text}\n\n"
                                f"✅ *Kassa aparatingizning oylik va yillik to'lovlarida qarzdorlik yo'q (ikkalasi ham toza).*\n\n"
                                f"📷 Ekranda ko'rsatilayotgan ushbu nosozlikni bartaraf etish uchun mas'ul texnik mutaxassisimizga yetkazishimiz lozim. "
                                f"Iltimos, aparat ekranidagi xatolikni (soat va interneti ko'ringan holda) **rasmga olib yuboring** — darhol texnikka ulaymiz."
                            )
                            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                            return
                    elif session.fm_holat == "qarzdor":
                        session_mgr.save_sessions()
                        self.send_yearly_payment_media(chat_id, reply_to_id=reply_to_id)
                        return
                    else:
                        resp = (
                            f"🏢 *Tashkilot:* {info['org_name']}\n"
                            f"📑 *STIR / INN:* `{inn_to_check}`\n"
                            f"{pos_count_text}\n\n"
                            f"✅ *Sizda oylik abonent to'lovidan qarzdorlik mavjud emas, aparatingiz oylik abonent tomonlama faol holatda.*\n\n"
                            f"{self.get_offline_limit_explanation_text()}\n\n"
                            f"{fee_info_text}"
                        )
                        session.state = "AWAITING_FM"
                        session_mgr.save_sessions()
                        buttons_markup = {
                            "keyboard": [
                                [{"text": "📊 To'lovlar tarixi va hisoboti"}],
                                [{"text": "📟 Yillik fiskal modul to'lovini tekshirish"}],
                                [{"text": "💳 Oylik abonent to'lovi hisob raqami"}],
                                [{"text": "🧾 Yillik fiskal modul to'lovi hisob raqami"}]
                            ],
                            "resize_keyboard": True,
                            "one_time_keyboard": True,
                            "selective": True
                        }
                        self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id, reply_markup=buttons_markup)
                        return
                elif getattr(session, "last_photo_file_id", None):
                    session_mgr.save_sessions()
                    self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text)
                    return
                else:
                    resp = (
                        f"🏢 *Tashkilot:* {info['org_name']}\n"
                        f"📑 *STIR / INN:* `{inn_to_check}`\n"
                        f"{pos_count_text}\n\n"
                        f"📋 *Apparatlar modeli va holati:*\n{pos_details_text}\n\n"
                        f"✅ *Sizda oylik abonent to'lovidan qarzdorlik mavjud emas, aparatingiz oylik abonent tomonlama faol holatda.*\n\n"
                        f"📷 Agar kassa apparatingizda biror nosozlik yoki xatolik bo'lsa, apparat chiqargan xatolikni aparat ekrani to'liq ko'ringan holda (tepasidagi soat va interneti bilan) **rasmga olib yuboring** — sizni mas'ul texnik mutaxassisimiz bilan bog'laymiz.\n\n"
                        f"Agar apparatingizning yillik fiskal modul to'lovini ham tekshirmoqchi bo'lsangiz, 📟 **Yillik fiskal modul to'lovini tekshirish** tugmasini bosing.\n\n"
                        f"{fee_info_text}"
                    )
                    buttons_markup = {
                        "keyboard": [
                            [{"text": "📊 To'lovlar tarixi va hisoboti"}],
                            [{"text": "📟 Yillik fiskal modul to'lovini tekshirish"}],
                            [{"text": "💳 Oylik abonent to'lovi hisob raqami"}],
                            [{"text": "🧾 Yillik fiskal modul to'lovi hisob raqami"}]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": True,
                        "selective": True
                    }
                    session_mgr.save_sessions()
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id, reply_markup=buttons_markup)
                    return
        else:
            resp = (
                f"🏢 *STIR / INN:* `{inn_to_check}`\n\n"
                f"⚠️ Ushbu INN yoki JSHSHIR bo'yicha hisob-kitob jadvalidan ma'lumot topilmadi.\n"
                f"Iltimos, raqamni to'g'ri kiritganingizni chekdagi *STIR* bo'limidan tekshirib, qaytadan yuboring."
            )
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

    def process_fm_check(self, chat_id, message_id, reply_to_id, session, first_name, username, user_id, text, norm_text, found_fm):
        """Mijoz yuborgan FM raqami bo'yicha yillik fiskal modul to'lovini tekshirish"""
        session.unclear_count = 0
        if self.is_offline_limit_error(text) or self.is_offline_limit_error(norm_text):
            session.offline_limit_error_active = True

        fm_to_check = found_fm
        session.fm_number = fm_to_check

        # Agar avval sessionda INN bo'lmasa, FM bo'yicha bazadan tashkilotni aniqlash
        if not session.inn:
            excel_fm_info = excel_service.find_by_fm(fm_to_check)
            if excel_fm_info and excel_fm_info.get("inn"):
                session.inn = excel_fm_info.get("inn")
                session.org_name = excel_fm_info.get("org_name")

        # OFD boti orqali tekshirish
        res = ofd_service.check_fm(fm_to_check, session)
        session.fm_holat = res["status"]
        session.state = "NORMAL"
        session_mgr.save_sessions()

        if res.get("status") in ["qarzdor", "tekshirildi"]:
            self.bot.send_message(chat_id, res["text"], reply_to_message_id=reply_to_id)
            self.send_yearly_payment_media(chat_id, reply_to_id=reply_to_id)
        elif res.get("status") == "toza":
            self.bot.send_message(chat_id, res["text"], reply_to_message_id=reply_to_id)
            if session.oylik_holat == "toza":
                if getattr(session, "last_photo_file_id", None):
                    self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text="Aparat nosozligi rasmi yuborilgan (Ikkala to'lov toza)")
                elif getattr(session, "offline_limit_error_active", False):
                    resp_photo = (
                        f"✅ *Kassa aparatingizning oylik va yillik to'lovlarida qarzdorlik yo'q (ikkalasi ham toza).*\n\n"
                        f"📷 Ekranda ko'rsatilayotgan ushbu nosozlikni bartaraf etish uchun mas'ul texnik mutaxassisimizga yetkazishimiz lozim. "
                        f"Iltimos, aparat ekranidagi xatolikni (soat va interneti ko'ringan holda) **rasmga olib yuboring** — darhol texnikka ulaymiz."
                    )
                    self.bot.send_message(chat_id, resp_photo, reply_to_message_id=reply_to_id)
            else:
                if getattr(session, "last_photo_file_id", None) or getattr(session, "offline_limit_error_active", False):
                    resp_inn = (
                        f"✅ *Yillik fiskal modul to'lovingiz toza (qarzdorlik yo'q).*\n\n"
                        f"🔍 Kassa apparatingizdagi ushbu xatolik bo'yicha mas'ul texnik mutaxassisimizga ulashimiz uchun tashkilotingizning **oylik abonent to'lovini** ham tekshirishimiz lozim.\n\n"
                        f"Iltimos, tashkilotingizning 9 xonali *STIR (INN)* yoki 14 xonali *JSHSHIR* raqamini yuboring."
                    )
                    session.state = "AWAITING_INN"
                    session_mgr.save_sessions()
                    self.bot.send_message(chat_id, resp_inn, reply_to_message_id=reply_to_id)
        else:
            self.bot.send_message(chat_id, res["text"], reply_to_message_id=reply_to_id)
        return

    def handle_message(self, message):
        """Har bir xabarni qayta ishlash"""
        chat_id = message["chat"]["id"]
        chat_type = message["chat"].get("type", "private")
        message_id = message["message_id"]
        from_user = message.get("from") or {}
        sender_chat = message.get("sender_chat") or {}
        user_id = from_user.get("id") or sender_chat.get("id") or chat_id
        first_name = from_user.get("first_name") or sender_chat.get("title") or "Foydalanuvchi"
        username = from_user.get("username") or sender_chat.get("username") or ""

        # Guruhda yoki shaxsiy chatda bo'lsa ham javobni aynan o'sha xabarga reply qilamiz
        reply_to_id = message_id

        # 0. GIF animatsiya yoki .APK fayl yuborilsa darhol guruhdan yoki chatdan o'chirish
        is_gif = ("animation" in message)
        is_apk = False
        if "document" in message:
            doc = message["document"]
            doc_name = (doc.get("file_name") or "").lower()
            doc_mime = (doc.get("mime_type") or "").lower()
            if doc_name.endswith(".apk") or "application/vnd.android.package-archive" in doc_mime:
                is_apk = True
            if doc_name.endswith(".gif") or "image/gif" in doc_mime:
                is_gif = True

        if is_gif or is_apk:
            try:
                self.bot.api_request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
            except Exception as del_err:
                print(f"[DELETE] GIF/APK xabarni o'chirishda xatolik: {del_err}")
            return

        # 0.0. Kanalga bog'langan Muhokama (Fikr bildirish) guruhi xabarlari
        if str(chat_id) == str(config.DISCUSSION_GROUP_ID):
            # A) Kanal postining avtomatik nusxasi (automatic forward):
            fwd_chat = message.get("forward_from_chat", {})
            chan_msg_id = message.get("forward_from_message_id")
            if chan_msg_id and (str(fwd_chat.get("id")) == str(config.TECHNICIAN_CHANNEL_ID) or message.get("is_automatic_forward")):
                group_msg_id = message_id
                ticket = ticket_service.link_discussion_id(chan_msg_id, group_msg_id)
                if ticket:
                    print(f"[DISCUSSION_LINK] Bog'landi: Kanal post {chan_msg_id} -> Guruh xabar {group_msg_id}")
                return

            # B) Texnik mutaxassis tomonidan sharh (fikr bildirish) yozilgan bo'lsa:
            if from_user.get("is_bot"):
                return

            # Qaysi tiketga tegishli ekanligini aniqlaymiz:
            thread_id = message.get("message_thread_id")
            reply_to = message.get("reply_to_message")
            ticket = None
            if thread_id:
                ticket = ticket_service.find_ticket_by_discussion_id(thread_id)
            if not ticket and reply_to:
                rep_id = reply_to.get("message_id")
                ticket = ticket_service.find_ticket_by_discussion_id(rep_id)
                if not ticket and reply_to.get("forward_from_message_id"):
                    ticket = ticket_service.find_ticket_by_channel_msg_id(reply_to["forward_from_message_id"])

            if ticket:
                client_uid = ticket.get("user_id")
                target_chat_id = ticket.get("chat_id") or client_uid
                is_group_chat = (str(target_chat_id) != str(client_uid))
                target_reply_id = ticket.get("message_id") if is_group_chat else None

                tech_name = from_user.get("first_name", "") + (" " + from_user.get("last_name", "") if from_user.get("last_name") else "")
                tech_name = tech_name.strip() or "Texnik mutaxassis"
                tech_username = from_user.get("username", "")
                raw_text = (message.get("text") or message.get("caption") or "").strip()
                claimed_by = ticket.get("claimed_by")

                norm_cmd = raw_text.lower().strip()
                base_cmd = norm_cmd.split("@")[0].strip()

                # 0.9. Boshqa texnik suhbatga qo'shilishi (/davomettirish):
                if base_cmd in ["/davomettirish", "davomettirish", "/davom_ettirish", "davom ettirish"]:
                    try:
                        self.bot.delete_message(chat_id, message_id)
                    except Exception:
                        pass

                    ticket_service.add_technician_to_ticket(ticket, user_id, tech_name, tech_username)

                    # Kanaldagi asosiy postni yangilaymiz (Mas'ul mutaxassislar ro'yxati yangilanadi)
                    chan_id = config.TECHNICIAN_CHANNEL_ID
                    chan_msg_id = ticket.get("channel_message_id")
                    if chan_id and chan_msg_id:
                        updated_text = ticket_service.format_channel_card(ticket)
                        is_photo = ticket.get("is_photo", False)
                        self.bot.edit_ticket_card(chan_id, chan_msg_id, updated_text, is_photo=is_photo)

                    # Muhokama guruhiga tasdiqlovchi xabar yuboramiz
                    u_tag = f"@{tech_username}" if tech_username else tech_name
                    self.bot.send_message(
                        chat_id,
                        f"👨‍💻 *Texnik mutaxassis {u_tag} suhbatga muvaffaqiyatli qo'shildi.*\nEndi ushbu mijoz bilan avvalgi texnik ham, yangi texnik ham birgalikda muloqot qilishi mumkin 👇",
                        reply_to_message_id=ticket.get("group_discussion_id")
                    )
                    # Mijozga yangi texnik qo'shilgani haqida xabar yuborilmaydi (mijozga bildirish shart emas)
                    return

                # 1. Texnik '+' yuborganda:
                if raw_text == "+" or (raw_text.startswith("+") and len(raw_text) <= 3):
                    # '+' xabarini guruhdan darhol o'chiramiz
                    try:
                        self.bot.delete_message(chat_id, message_id)
                    except Exception:
                        pass

                    # Guruh orqali qabul qilindi -> Texnikning shaxsiy chatiga borgan xabarni o'chirish (Cross-delete)
                    ticket["claimed_in"] = "group"
                    self.cross_delete_other(ticket, accepted_source="group")

                    # A) Agar bu to'lov kvitansiyasi bo'lsa: '+' bosilganda avtomatik faollashtirildi xabari yuborilib suhbat yopiladi!
                    if ticket.get("type") == "kvitansiya" or ticket.get("is_receipt"):
                        client_msg = "✅ *To'lov kvitansiyangiz qabul qilindi va apparatingiz faollashtirildi. Apparatingizni ishlatib ko'rishingiz mumkin!*"
                        self.bot.send_message(target_chat_id, client_msg, reply_to_message_id=target_reply_id)

                        # Kanaldagi asosiy postni tahrirlash (To'lov tasdiqlandi va tugatildi deb yoziladi)
                        self.mark_ticket_finished(ticket, tech_name, tech_username, status_text="To'lov tasdiqlandi (Faollashtirildi va tugatilgan)")

                        ticket_service.close_ticket(client_uid)
                        if client_uid:
                            cs = session_mgr.get_session(client_uid)
                            if cs and cs.state == "ADMIN_BOGLANISH":
                                cs.state = "NORMAL"
                                session_mgr.save_sessions()

                        self.bot.send_message(
                            chat_id,
                            f"✅ *To'lov kvitansiyasi tasdiqlandi ({tech_name}).*\nMijozga apparat faollashtirilgani haqida xabar yuborildi va suhbat yakunlandi.",
                            reply_to_message_id=ticket.get("group_discussion_id")
                        )
                        return

                    # B) Oddiy nosozlik murojaati bo'lsa:
                    # Agar allaqachon boshqa texnik qabul qilgan bo'lsa va bu texnik hali biriktirilmagan bo'lsa:
                    if claimed_by and not ticket_service.is_tech_authorized(ticket, user_id):
                        c_name = claimed_by.get("name", "Boshqa texnik")
                        self.bot.send_message(
                            chat_id,
                            f"⚠️ *Ushbu murojaatni allaqachon {c_name} qabul qilgan.*\nAgar siz ham muloqotni birga davom ettirmoqchi bo'lsangiz, «/davomettirish» buyrug'ini yuboring.",
                            reply_to_message_id=ticket.get("group_discussion_id")
                        )
                        return

                    # Qabul qilish
                    tech_info = {
                        "user_id": user_id,
                        "name": tech_name,
                        "username": tech_username,
                        "time": time.time()
                    }
                    ticket["claimed_by"] = tech_info
                    ticket_service.add_technician_to_ticket(ticket, user_id, tech_name, tech_username)

                    # Kanaldagi asosiy postni tahrirlash (Kim qabul qilgani va holati yangilanadi)
                    chan_id = config.TECHNICIAN_CHANNEL_ID
                    chan_msg_id = ticket.get("channel_message_id")
                    if chan_id and chan_msg_id:
                        updated_text = ticket_service.format_channel_card(ticket)
                        is_photo = ticket.get("is_photo", False)
                        self.bot.edit_ticket_card(chan_id, chan_msg_id, updated_text, is_photo=is_photo)

                    # Muhokama (Fikr bildirish) guruhiga tasdiqlovchi xabar
                    u_tag = f"@{tech_username}" if tech_username else tech_name
                    self.bot.send_message(
                        chat_id,
                        f"👨‍💻 *Murojaatni texnik mutaxassis {u_tag} qabul qildi.*\nEndi mijoz bilan shu yerda sharhlar orqali muloqot qilishingiz mumkin 👇",
                        reply_to_message_id=ticket.get("group_discussion_id")
                    )

                    # Mijozga muloyim xabarnoma (tegishli chat yoki guruhga)
                    try:
                        self.bot.send_message(
                            target_chat_id,
                            "👨‍💻 *Murojaatingizni mas'ul texnik mutaxassisimiz qabul qildi, tez orada javob yozadi!*",
                            reply_to_message_id=target_reply_id
                        )
                    except Exception:
                        pass
                    return

                # 2. Oddiy xabar yozilganda:
                # Guruh orqali qabul qilindi -> Texnik shaxsiy chatidagi xabarni o'chirish (Cross-delete)
                if not ticket.get("claimed_in") or ticket.get("claimed_in") != "group":
                    ticket["claimed_in"] = "group"
                    self.cross_delete_other(ticket, accepted_source="group")

                # Agar murojaat hali hech kim tomonidan qabul qilinmagan bo'lsa:
                if not claimed_by:
                    tech_info = {
                        "user_id": user_id,
                        "name": tech_name,
                        "username": tech_username,
                        "time": time.time()
                    }
                    ticket["claimed_by"] = tech_info
                    ticket_service.add_technician_to_ticket(ticket, user_id, tech_name, tech_username)
                    chan_id = config.TECHNICIAN_CHANNEL_ID
                    chan_msg_id = ticket.get("channel_message_id")
                    if chan_id and chan_msg_id:
                        updated_text = ticket_service.format_channel_card(ticket)
                        is_photo = ticket.get("is_photo", False)
                        self.bot.edit_ticket_card(chan_id, chan_msg_id, updated_text, is_photo=is_photo)

                    try:
                        self.bot.send_message(
                            target_chat_id,
                            "👨‍💻 *Murojaatingizni mas'ul texnik mutaxassisimiz qabul qildi, tez orada javob yozadi!*",
                            reply_to_message_id=target_reply_id
                        )
                    except Exception:
                        pass
                    claimed_by = ticket["claimed_by"]

                # Agar murojaatni boshqa texnik qabul qilgan bo'lsa va bu texnik hali ruxsat olmagan bo'lsa:
                if not ticket_service.is_tech_authorized(ticket, user_id):
                    c_name = claimed_by.get("name", "Boshqa texnik") if claimed_by else "Boshqa texnik"
                    self.bot.send_message(
                        chat_id,
                        f"⚠️ *Diqqat!* Ushbu murojaatni {c_name} qabul qilgan.\nXizmat ko'rsatishda chalkashlik bo'lmasligi uchun faqat biriktirilgan mutaxassislar yoza oladi.\n\nAgar siz ham muloqotni birga davom ettirmoqchi bo'lsangiz, «/davomettirish» buyrug'ini yuboring.",
                        reply_to_message_id=message_id
                    )
                    return

                # 2.1 Murojaatni yopish (/yakun, yakun, /tugatish, tugatish, /yopish, yopish, /tamom, tamom, /done)
                if base_cmd in ["/yakun", "yakun", "/tugatish", "tugatish", "/yopish", "yopish", "/tamom", "tamom", "/done"]:
                    try:
                        self.bot.delete_message(chat_id, message_id)
                    except Exception:
                        pass

                    # Texnikka yuborilgan mijoz ma'lumotlarini tahrirlab, tagidan 'Tugatilgan' deb yozib qo'yish
                    self.mark_ticket_finished(ticket, tech_name, tech_username, status_text="Tugatilgan (Suhbat yakunlandi)")

                    ticket_service.close_ticket(client_uid)
                    if client_uid:
                        cs = session_mgr.get_session(client_uid)
                        if cs and cs.state == "ADMIN_BOGLANISH":
                            cs.state = "NORMAL"
                            session_mgr.save_sessions()
                    close_msg = "✅ *Texnik mutaxassis bilan suhbat yakunlandi.*\n\nAgar yangi savollaringiz bo'lsa, bemalol murojaat qilishingiz mumkin!"
                    self.bot.send_message(target_chat_id, close_msg, reply_to_message_id=target_reply_id)
                    self.bot.send_message(
                        chat_id,
                        f"✅ *Murojaat muvaffaqiyatli yakunlandi.*\nMijoz bilan suhbat tugatildi.",
                        reply_to_message_id=ticket.get("group_discussion_id")
                    )
                    return

                # 3. Mas'ul mutaxassis xabarini mijozga yetkazish (tegishli chat yoki guruhga):
                tech_text = message.get("text", "") or message.get("caption", "")
                has_delivered = False
                hist_desc = None
                hist_type = None

                if "photo" in message:
                    ph_id = message["photo"][-1]["file_id"]
                    cap = f"👨‍💻 *Mas'ul mutaxassis:*\n\n{tech_text}".strip()
                    res = self.bot.send_photo(target_chat_id, ph_id, caption=cap, reply_to_message_id=target_reply_id)
                    has_delivered = res.get("ok", False)
                    hist_desc = f"Rasm: {tech_text}" if tech_text else "Rasm"
                    hist_type = "photo"
                elif "voice" in message or "audio" in message:
                    v_id = (message.get("voice") or message.get("audio", {})).get("file_id")
                    cap = "🎤 *Mas'ul mutaxassisdan ovozli xabar*"
                    payload = {"chat_id": target_chat_id, "voice": v_id, "caption": cap}
                    if target_reply_id:
                        payload["reply_to_message_id"] = target_reply_id
                    res = self.bot.api_request("sendVoice", payload)
                    if not res.get("ok") and target_reply_id:
                        payload.pop("reply_to_message_id", None)
                        res = self.bot.api_request("sendVoice", payload)
                    has_delivered = res.get("ok", False)
                    hist_desc = "Ovozli xabar"
                    hist_type = "voice"
                elif "video" in message or "animation" in message:
                    vid_id = (message.get("video") or message.get("animation", {})).get("file_id")
                    cap = f"👨‍💻 *Mas'ul mutaxassis:*\n\n{tech_text}".strip()
                    res = self.bot.send_video(target_chat_id, vid_id, caption=cap, reply_to_message_id=target_reply_id)
                    has_delivered = res.get("ok", False)
                    hist_desc = f"Video: {tech_text}" if tech_text else "Video"
                    hist_type = "video"
                elif "document" in message:
                    doc_id = message["document"]["file_id"]
                    doc_name = message["document"].get("file_name", "Fayl")
                    cap = f"👨‍💻 *Mas'ul mutaxassis:*\n\n{tech_text}".strip() if tech_text else f"📁 *Mas'ul mutaxassis yuborgan fayl:* {doc_name}"
                    res = self.bot.send_document(target_chat_id, doc_id, caption=cap, reply_to_message_id=target_reply_id)
                    has_delivered = res.get("ok", False)
                    hist_desc = f"Fayl: {doc_name} ({tech_text})" if tech_text else f"Fayl: {doc_name}"
                    hist_type = "document"
                elif tech_text:
                    resp_to_client = f"👨‍💻 *Mas'ul texnik mutaxassis:*\n\n{tech_text}"
                    res = self.bot.send_message(target_chat_id, resp_to_client, reply_to_message_id=target_reply_id)
                    has_delivered = res.get("ok", False)
                    hist_desc = tech_text
                    hist_type = None

                if has_delivered:
                    if hist_desc:
                        ticket_service.add_tech_response(client_uid, hist_desc, media_type=hist_type)
                    dest_str = f"Guruh {target_chat_id}" if is_group_chat else f"Mijoz {client_uid}"
                    print(f"[TECH_REPLY_DELIVERED] {tech_name} -> {dest_str}")
            return

        # Admin / Texnik tekshiruvi
        is_admin_user = (str(user_id) in [str(i) for i in config.ADMIN_TELEGRAM_IDS]) or (f"@{username}".lower() in [u.lower() for u in config.ADMIN_USERNAMES])

        # 0.1. Agar guruhda admin / texnik biror mijozning xabariga javob (reply) yozsa:
        if chat_type in ["group", "supergroup"] and is_admin_user:
            reply_to_msg = message.get("reply_to_message")
            if reply_to_msg:
                replied_from = reply_to_msg.get("from", {})
                replied_uid = replied_from.get("id")
                if replied_uid and not replied_from.get("is_bot") and str(replied_uid) != str(user_id):
                    # Texnik guruhda mijozga javob bermoqda
                    tech_reply_text = message.get("text", "") or message.get("caption", "")
                    ticket = ticket_service.find_ticket_by_user_id(replied_uid)
                    if ticket and tech_reply_text:
                        ticket = ticket_service.add_tech_response(replied_uid, tech_reply_text)
                        card_kb = ticket_service.get_keyboard(ticket)
                        for am in ticket.get("admin_messages", []):
                            c_text = ticket_service.format_card(ticket, max_len=1000 if am.get("is_photo") else 4000)
                            self.bot.edit_ticket_card(am["chat_id"], am["message_id"], c_text, is_photo=am.get("is_photo"), reply_markup=card_kb)
                    return  # Admin / texnik guruhda mijozga javob berganda bot aralashmaydi va jim turadi!

        if chat_type == "private" and is_admin_user:
            # 1. Texnik alert xabariga Telegram'da "Reply" (javob) qilib yozgan bo'lsa
            reply_to_msg = message.get("reply_to_message")
            if reply_to_msg:
                alert_id = reply_to_msg.get("message_id")
                ticket = ticket_service.find_ticket_by_tech_msg(alert_id)
                if not ticket:
                    alert_content = reply_to_msg.get("text", "") or reply_to_msg.get("caption", "")
                    m_uid = re.search(r"ID:\s*`?(\d+)`?", alert_content)
                    if m_uid:
                        ticket = ticket_service.find_ticket_by_user_id(m_uid.group(1))

                if ticket:
                    target_chat_id = ticket["chat_id"]
                    target_msg_id = ticket.get("message_id")
                    client_name = ticket.get("first_name", "Mijoz")
                    c_uid = ticket.get("user_id")

                    # Chat orqali qabul qilindi -> Texnikni biriktiramiz va kanaldagi xabarni o'chiramiz (Cross-delete)
                    tech_name = from_user.get("first_name", "Texnik")
                    tech_username = from_user.get("username", "")
                    tech_info = {
                        "user_id": user_id,
                        "name": tech_name,
                        "username": tech_username,
                        "time": time.time()
                    }
                    ticket["claimed_by"] = tech_info
                    ticket["claimed_in"] = "chat"
                    ticket["claimed_chat_id"] = chat_id
                    ticket_service.add_technician_to_ticket(ticket, user_id, tech_name, tech_username)
                    self.cross_delete_other(ticket, accepted_source="chat")

                    # A) Matnli xabar
                    if "text" in message:
                        tech_text = message["text"].strip()
                        norm_tech = tech_text.lower().strip()
                        base_cmd = norm_tech.split("@")[0].strip()
                        if base_cmd in ["/yakun", "yakun", "/tugatish", "tugatish", "/yopish", "yopish", "/tamom", "tamom", "/done"]:
                            # Texnikka yuborilgan mijoz ma'lumotini tahrirlab, tagidan 'Tugatilgan' deb yozib qo'yish
                            self.mark_ticket_finished(ticket, tech_name, tech_username, status_text="Tugatilgan (Suhbat yakunlandi)")
                            ticket_service.close_ticket(c_uid)
                            if c_uid:
                                cs = session_mgr.get_session(c_uid)
                                if cs and cs.state == "ADMIN_BOGLANISH":
                                    cs.state = "NORMAL"
                                    session_mgr.save_sessions()
                            try:
                                self.bot.delete_message(chat_id, message_id)
                            except Exception:
                                pass
                            self.bot.send_message(target_chat_id, "✅ *Texnik mutaxassis bilan suhbat yakunlandi.*\n\nAgar yana savollaringiz bo'lsa, bemalol murojaat qilishingiz mumkin!", reply_to_message_id=target_msg_id)
                            self.bot.send_message(chat_id, "✅ *Murojaat muvaffaqiyatli yakunlandi.* Mijoz bilan suhbat tugatildi.", reply_to_message_id=reply_to_msg.get("message_id"))
                            return

                        # '+' yuborilganda:
                        if tech_text == "+" or (tech_text.startswith("+") and len(tech_text) <= 3):
                            try:
                                self.bot.delete_message(chat_id, message_id)
                            except Exception:
                                pass
                            if ticket.get("type") == "kvitansiya" or ticket.get("is_receipt"):
                                client_msg = "✅ *To'lov kvitansiyangiz qabul qilindi va apparatingiz faollashtirildi. Apparatingizni ishlatib ko'rishingiz mumkin!*"
                                self.bot.send_message(target_chat_id, client_msg, reply_to_message_id=target_msg_id)
                                self.mark_ticket_finished(ticket, tech_name, tech_username, status_text="To'lov tasdiqlandi (Faollashtirildi va tugatilgan)")
                                ticket_service.close_ticket(c_uid)
                                if c_uid:
                                    cs = session_mgr.get_session(c_uid)
                                    if cs and cs.state == "ADMIN_BOGLANISH":
                                        cs.state = "NORMAL"
                                        session_mgr.save_sessions()
                                self.bot.send_message(chat_id, "✅ *To'lov kvitansiyasi tasdiqlandi.* Mijozga apparat faollashtirilgani haqida xabar yuborildi va suhbat yakunlandi.", reply_to_message_id=reply_to_msg.get("message_id"))
                                return
                            else:
                                self.bot.send_message(target_chat_id, "👨‍💻 *Murojaatingizni mas'ul texnik mutaxassisimiz qabul qildi, tez orada javob yozadi!*", reply_to_message_id=target_msg_id)
                                self.bot.send_message(chat_id, "👨‍💻 *Murojaat qabul qilindi.* Endi mijoz bilan shu yerda muloqot qilishingiz mumkin.", reply_to_message_id=reply_to_msg.get("message_id"))
                                return

                        resp = f"👨‍💻 *Texnik mutaxassis javobi:*\n\n{tech_text}"
                        res = self.bot.send_message(target_chat_id, resp, reply_to_message_id=target_msg_id)
                        if res.get("ok"):
                            ticket = ticket_service.add_tech_response(c_uid, tech_text)
                            if ticket:
                                card_kb = ticket_service.get_keyboard(ticket)
                                for am in ticket.get("admin_messages", []):
                                    c_text = ticket_service.format_card(ticket, max_len=1000 if am.get("is_photo") else 4000)
                                    self.bot.edit_ticket_card(am["chat_id"], am["message_id"], c_text, is_photo=am.get("is_photo"), reply_markup=card_kb)
                            # Texnik yozgan xabarni chatdan avtomatik o'chirib tashlaymiz (chalkashmaslik uchun)
                            self.bot.delete_message(chat_id, message_id)
                        else:
                            self.bot.send_message(chat_id, f"❌ Xatolik: Xabar mijozga bormadi ({res.get('error')}).", reply_to_message_id=reply_to_id)
                        return

                    # B) Rasm
                    if "photo" in message:
                        photo_id = message["photo"][-1]["file_id"]
                        tech_cap = message.get("caption", "").strip()
                        caption = f"👨‍💻 *Texnik mutaxassis javobi:*\n\n{tech_cap}" if tech_cap else "👨‍💻 *Texnik mutaxassis javobi*"
                        res = self.bot.send_photo(target_chat_id, photo_id, caption=caption, reply_to_message_id=target_msg_id)
                        if res.get("ok"):
                            desc = f"Rasm: {tech_cap}" if tech_cap else "Rasm"
                            ticket = ticket_service.add_tech_response(c_uid, desc, media_type="photo")
                            if ticket:
                                card_kb = ticket_service.get_keyboard(ticket)
                                for am in ticket.get("admin_messages", []):
                                    c_text = ticket_service.format_card(ticket, max_len=1000 if am.get("is_photo") else 4000)
                                    self.bot.edit_ticket_card(am["chat_id"], am["message_id"], c_text, is_photo=am.get("is_photo"), reply_markup=card_kb)
                            self.bot.delete_message(chat_id, message_id)
                        else:
                            self.bot.send_message(chat_id, f"❌ Xatolik: Rasm mijozga bormadi ({res.get('error')}).", reply_to_message_id=reply_to_id)
                        return

                    # C) Ovozli xabar (Voice)
                    if "voice" in message:
                        payload = {"chat_id": target_chat_id, "voice": message["voice"]["file_id"], "caption": "👨‍💻 *Texnik mutaxassis ovozli xabari*", "reply_to_message_id": target_msg_id}
                        res = self.bot.api_request("sendVoice", payload)
                        if res.get("ok"):
                            ticket = ticket_service.add_tech_response(c_uid, "Ovozli xabar", media_type="voice")
                            if ticket:
                                card_kb = ticket_service.get_keyboard(ticket)
                                for am in ticket.get("admin_messages", []):
                                    c_text = ticket_service.format_card(ticket, max_len=1000 if am.get("is_photo") else 4000)
                                    self.bot.edit_ticket_card(am["chat_id"], am["message_id"], c_text, is_photo=am.get("is_photo"), reply_markup=card_kb)
                            self.bot.delete_message(chat_id, message_id)
                        else:
                            self.bot.send_message(chat_id, f"❌ Xatolik: Ovozli xabar bormadi ({res.get('error')}).", reply_to_message_id=reply_to_id)
                        return

                    # D) Hujjat / Fayl (PDF, rasm, fayllar)
                    if "document" in message:
                        doc_id = message["document"]["file_id"]
                        tech_cap = message.get("caption", "").strip()
                        caption = f"👨‍💻 *Texnik mutaxassis javobi:*\n\n{tech_cap}" if tech_cap else "👨‍💻 *Texnik mutaxassis yuborgan fayl*"
                        res = self.bot.send_document(target_chat_id, doc_id, caption=caption, reply_to_message_id=target_msg_id)
                        if res.get("ok"):
                            doc_title = message["document"].get("file_name", "Fayl")
                            ticket = ticket_service.add_tech_response(c_uid, f"Fayl: {doc_title}", media_type="document")
                            if ticket:
                                card_kb = ticket_service.get_keyboard(ticket)
                                for am in ticket.get("admin_messages", []):
                                    c_text = ticket_service.format_card(ticket, max_len=1000 if am.get("is_photo") else 4000)
                                    self.bot.edit_ticket_card(am["chat_id"], am["message_id"], c_text, is_photo=am.get("is_photo"), reply_markup=card_kb)
                            self.bot.delete_message(chat_id, message_id)
                        else:
                            self.bot.send_message(chat_id, f"❌ Xatolik: Fayl bormadi ({res.get('error')}).", reply_to_message_id=reply_to_id)
                        return

                    # E) Video
                    if "video" in message or "animation" in message:
                        vid_id = message.get("video", {}).get("file_id") or message.get("animation", {}).get("file_id")
                        tech_cap = message.get("caption", "").strip()
                        caption = f"👨‍💻 *Texnik mutaxassis javobi:*\n\n{tech_cap}" if tech_cap else "👨‍💻 *Texnik mutaxassis yuborgan video*"
                        res = self.bot.send_video(target_chat_id, vid_id, caption=caption, reply_to_message_id=target_msg_id)
                        if res.get("ok"):
                            desc = f"Video: {tech_cap}" if tech_cap else "Video"
                            ticket = ticket_service.add_tech_response(c_uid, desc, media_type="video")
                            if ticket:
                                card_kb = ticket_service.get_keyboard(ticket)
                                for am in ticket.get("admin_messages", []):
                                    c_text = ticket_service.format_card(ticket, max_len=1000 if am.get("is_photo") else 4000)
                                    self.bot.edit_ticket_card(am["chat_id"], am["message_id"], c_text, is_photo=am.get("is_photo"), reply_markup=card_kb)
                            self.bot.delete_message(chat_id, message_id)
                        else:
                            self.bot.send_message(chat_id, f"❌ Xatolik: Video bormadi ({res.get('error')}).", reply_to_message_id=reply_to_id)
                        return

            # 1.5. Texnik to'g'ridan-to'g'ri /yakun yoki /yakun <ID> deb yozgan bo'lsa:
            raw_admin_text = (message.get("text") or "").strip()
            clean_first = raw_admin_text.lower().split("@")[0].strip()
            m_yakun_direct = re.match(r"^(?:/yakun|yakun|/tugatish|tugatish|/yopish|yopish)\s+(\d{8,14})$", raw_admin_text, re.IGNORECASE)

            ticket_to_end = None
            if m_yakun_direct:
                ticket_to_end = ticket_service.find_ticket_by_user_id(m_yakun_direct.group(1))
            elif clean_first in ["/yakun", "yakun", "/tugatish", "tugatish", "/yopish", "yopish", "/tamom", "tamom", "/done"]:
                active_list = [t for t in ticket_service.user_tickets.values() if t.get("status") != "closed"]
                if len(active_list) == 1:
                    ticket_to_end = active_list[0]
                elif len(active_list) > 1:
                    self.bot.send_message(chat_id, "⚠️ Bir nechta faol murojaat mavjud. Qaysi mijoz bilan suhbatni tugatmoqchi bo'lsangiz, o'sha xabarga «Reply» qilib /yakun deb yozing yoki «/yakun <ID>» yuboring.", reply_to_message_id=reply_to_id)
                    return
                else:
                    self.bot.send_message(chat_id, "ℹ️ Hozirda faol murojaat mavjud emas.", reply_to_message_id=reply_to_id)
                    return

            if ticket_to_end:
                t_uid = ticket_to_end.get("user_id")
                t_target_chat = ticket_to_end.get("chat_id") or t_uid
                t_target_msg = ticket_to_end.get("message_id")
                t_tech_name = from_user.get("first_name", "Texnik")
                t_tech_uname = from_user.get("username", "")

                self.mark_ticket_finished(ticket_to_end, t_tech_name, t_tech_uname, status_text="Tugatilgan (Suhbat yakunlandi)")
                ticket_service.close_ticket(t_uid)
                cs = session_mgr.get_session(t_uid)
                if cs and cs.state == "ADMIN_BOGLANISH":
                    cs.state = "NORMAL"
                    session_mgr.save_sessions()
                try:
                    self.bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
                self.bot.send_message(t_target_chat, "✅ *Texnik mutaxassis bilan suhbat yakunlandi.*\n\nAgar yana savollaringiz bo'lsa, bemalol murojaat qilishingiz mumkin!", reply_to_message_id=t_target_msg)
                self.bot.send_message(chat_id, f"✅ *Murojaat muvaffaqiyatli yakunlandi.* (Mijoz ID: `{t_uid}` bilan suhbat tugatildi).")
                return

            # 2. Texnik /javob <ID> <matn> yoki <ID> <matn> deb yozgan bo'lsa
            cmd_match = re.match(r"^(?:/javob\s+|javob\s+)?(\d{8,12})\s+(.+)$", raw_admin_text, re.DOTALL | re.IGNORECASE)
            if cmd_match:
                target_user_id = cmd_match.group(1)
                tech_text = cmd_match.group(2).strip()
                ticket = ticket_service.find_ticket_by_user_id(target_user_id)
                target_chat_id = ticket["chat_id"] if ticket else target_user_id
                target_msg_id = ticket.get("message_id") if ticket else None
                client_name = ticket.get("first_name", target_user_id) if ticket else target_user_id

                if tech_text.lower() in ["/yakun", "yakun", "/tugatish", "tugatish", "/yopish", "yopish", "/tamom", "tamom", "/done"]:
                    t_tech_name = from_user.get("first_name", "Texnik")
                    t_tech_uname = from_user.get("username", "")
                    if ticket:
                        self.mark_ticket_finished(ticket, t_tech_name, t_tech_uname, status_text="Tugatilgan (Suhbat yakunlandi)")
                    ticket_service.close_ticket(target_user_id)
                    cs = session_mgr.get_session(target_user_id)
                    if cs and cs.state == "ADMIN_BOGLANISH":
                        cs.state = "NORMAL"
                        session_mgr.save_sessions()
                    self.bot.delete_message(chat_id, message_id)
                    self.bot.send_message(target_chat_id, "✅ *Texnik mutaxassis bilan suhbat yakunlandi.*\n\nAgar yangi savollaringiz bo'lsa, bemalol murojaat qilishingiz mumkin!", reply_to_message_id=target_msg_id)
                    self.bot.send_message(chat_id, f"✅ *Murojaat muvaffaqiyatli yakunlandi.* (Mijoz ID: `{target_user_id}` bilan suhbat tugatildi).")
                    return

                resp = f"👨‍💻 *Texnik mutaxassis javobi:*\n\n{tech_text}"
                res = self.bot.send_message(target_chat_id, resp, reply_to_message_id=target_msg_id)
                if res.get("ok"):
                    ticket = ticket_service.add_tech_response(target_user_id, tech_text)
                    if ticket:
                        card_kb = ticket_service.get_keyboard(ticket)
                        for am in ticket.get("admin_messages", []):
                            c_text = ticket_service.format_card(ticket, max_len=1000 if am.get("is_photo") else 4000)
                            self.bot.edit_ticket_card(am["chat_id"], am["message_id"], c_text, is_photo=am.get("is_photo"), reply_markup=card_kb)
                    self.bot.delete_message(chat_id, message_id)
                else:
                    self.bot.send_message(chat_id, f"❌ Xatolik: Xabar mijozga bormadi ({res.get('error')}).", reply_to_message_id=reply_to_id)
                return

            cache = load_media_cache()
            fwd_chat = message.get("forward_from_chat")
            fwd_msg_id = message.get("forward_from_message_id")

            # Agar kanaldan uzatilgan (forward qilingan) bo'lsa
            if fwd_chat and fwd_msg_id:
                channel_id = fwd_chat.get("id")
                channel_title = fwd_chat.get("title", "Telegram Kanal")
                cache["channel_id"] = channel_id

                if "video" in message or "animation" in message:
                    media_obj = message.get("video") or message.get("animation")
                    cache["oylik_video_msg_id"] = fwd_msg_id
                    cache["oylik_video_file_id"] = media_obj.get("file_id")
                    save_media_cache(cache)
                    self.bot.send_message(
                        chat_id, 
                        f"✅ *Oylik to'lov video qo'llanmasi qabul qilindi!*\n\n"
                        f"📢 Kanal: *{channel_title}*\n"
                        f"🔢 Post ID: *#{fwd_msg_id}*\n\n"
                        f"Endi mijozlarga ushbu video aynan ushbu kanaldan uzatish (forward) qilib yuboriladi.",
                        reply_to_message_id=reply_to_id
                    )
                    return
                else:
                    cache["oylik_rekvizit_msg_id"] = fwd_msg_id
                    if "photo" in message:
                        photo_arr = message.get("photo", [])
                        if photo_arr:
                            cache["oylik_photo_file_id"] = photo_arr[-1]["file_id"]
                    save_media_cache(cache)
                    self.bot.send_message(
                        chat_id, 
                        f"✅ *Oylik to'lov rekviziti qabul qilindi!*\n\n"
                        f"📢 Kanal: *{channel_title}*\n"
                        f"🔢 Post ID: *#{fwd_msg_id}*\n\n"
                        f"Endi mijozlarga ushbu rekvizit aynan ushbu kanaldan uzatish (forward) qilib yuboriladi.",
                        reply_to_message_id=reply_to_id
                    )
                    return

            # Oddiy yuborilgan video yoki rasm bo'lsa (faqat maxsus buyruq yoki izoh bilan kiritilganda)
            caption_lower = (message.get("caption") or "").lower()
            text_lower = (message.get("text") or "").lower()
            is_rekvizit_cmd = any(k in caption_lower or k in text_lower for k in ["/set_rekvizit", "/rekvizit", "oylik rekvizit", "oylik_rekvizit", "shablon"])

            if is_rekvizit_cmd:
                if "video" in message or "animation" in message:
                    media_obj = message.get("video") or message.get("animation")
                    file_id = media_obj.get("file_id")
                    caption = message.get("caption", "").strip() or config.VIDEO_OYLIK_CAPTION
                    cache["oylik_video_file_id"] = file_id
                    cache["oylik_video_caption"] = caption
                    save_media_cache(cache)
                    self.bot.send_message(chat_id, "✅ *Oylik to'lov video qo'llanmasi qabul qilindi va bazaga saqlandi!*\nEndi mijozlar oylik to'lov haqida yozganda aynan ushbu video yuboriladi.", reply_to_message_id=reply_to_id)
                    return
                if "photo" in message:
                    photo_arr = message.get("photo", [])
                    if photo_arr:
                        file_id = photo_arr[-1]["file_id"]
                        caption = message.get("caption", "").strip() or config.REKVIZIT_OYLIK
                        cache["oylik_photo_file_id"] = file_id
                        cache["oylik_photo_caption"] = caption
                        save_media_cache(cache)
                        self.bot.send_message(chat_id, "✅ *Oylik to'lov rekvizit rasmi qabul qilindi va bazaga saqlandi!*\nEndi mijozlarga aynan ushbu rasm va rekvizit yuboriladi.", reply_to_message_id=reply_to_id)
                        return

        # 0.99. MIJOZ VA TEXNIK O'RTASIDAGI JONLI KO'PRIK (BRIDGE) REJIMI:
        # Agar mijoz texnikka bog'langan bo'lsa (ADMIN_BOGLANISH yoki faol tiket mavjud bo'lsa),
        # bot sun'iy intellekt, rasm klassifikatori, OCR yoki boshqa tahlillarni butunlay to'xtatadi.
        # Mijoz nima yuborsa (matn, rasm, ovozli xabar, video, dumaloq video, hujjat, stiker)
        # o'zgarishsiz to'g'ridan-to'g'ri texniklar muhokama (Fikr bildirish) guruhiga yetkaziladi.
        session = session_mgr.get_session(user_id, chat_id=chat_id, first_name=first_name, username=username)
        ticket = ticket_service.find_ticket_by_user_id(user_id)
        is_connected_to_tech = bool((session and session.state == "ADMIN_BOGLANISH") or ticket)

        if is_connected_to_tech:
            raw_text = (message.get("text") or message.get("caption") or "").strip()
            first_word = raw_text.split()[0].lower() if raw_text else ""

            # 1. Agar mijoz suhbatni to'xtatib yangitdan boshlamoqchi bo'lsa (/salombot):
            if first_word in ["/salombot", "/salombot@txkmrobot"] or "/salombot" in raw_text.lower():
                session_mgr.reset_session(user_id)
                ticket_service.close_ticket(user_id)
                session_mgr.save_sessions()
                resp = (
                    f"Assalomu alaykum, *{first_name}*!\n\n"
                    f"Men *{config.COMPANY_NAME}* ning online nazorat kassa apparatlari (SmartOne / P3) bo'yicha texnik xizmat ko'rsatuvchi rasmiy telegram botiman.\n\n"
                    f"🔄 Siz bilan bo'lgan avvalgi barcha suhbat ma'lumotlari xotiradan tozalandi. Yangitdan boshlaymiz!\n\n"
                    f"🔧 *Bot imkoniyatlari:*\n"
                    f"• Aparatdagi muammolarni aniqlash va bartaraf etish\n"
                    f"• Oylik abonent to'lovini tekshirish (STIR / INN yuboring)\n"
                    f"• Oylik to'lov qilish rekvizitlari va video darsligi\n"
                    f"• Yillik Fiskal Modul to'lovini tekshirish (FM raqamini yuboring)\n"
                    f"• Yillik to'lov rekvizitlari va qo'llanmasi\n"
                    f"• Mas'ul texnik xodim (admin) bilan bog'lanish\n\n"
                    f"Savolingiz yoki murojaatingizni yozib qoldirishingiz mumkin!"
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            disc_id = ticket.get("group_discussion_id") if ticket else None
            is_claimed = bool(ticket and ticket.get("claimed_by"))
            claimed_cid = ticket.get("claimed_chat_id") if (ticket and ticket.get("claimed_in") == "chat") else None

            # 2. Rasm yuborilganda (Hech qanday OCR/tahlilsiz to'g'ridan-to'g'ri texnikka):
            if "photo" in message:
                photo_arr = message.get("photo", [])
                if photo_arr:
                    photo_file_id = photo_arr[-1]["file_id"]
                    desc = f"Rasm: {raw_text}" if raw_text else "Rasm"
                    ticket = ticket_service.add_client_message(user_id, desc, media_type="photo", file_id=photo_file_id, chat_id=chat_id, message_id=message_id)
                    disc_id = ticket.get("group_discussion_id") if ticket else None
                    cap = f"📷 *Mijoz ({first_name}, ID: `{user_id}`):*\n{raw_text}".strip() if raw_text else f"📷 *Mijoz ({first_name}, ID: `{user_id}`)*"
                    if claimed_cid:
                        self.bot.send_photo(claimed_cid, photo_file_id, caption=cap)
                    elif config.DISCUSSION_GROUP_ID and photo_file_id:
                        self.bot.send_photo(
                            config.DISCUSSION_GROUP_ID,
                            photo_file_id,
                            caption=cap,
                            reply_to_message_id=disc_id
                        )
                return

            # 3. Ovozli xabar (Voice / Audio) yuborilganda:
            if "voice" in message or "audio" in message:
                voice_id = (message.get("voice") or message.get("audio", {})).get("file_id")
                ticket = ticket_service.add_client_message(user_id, "Ovozli xabar", media_type="voice", file_id=voice_id, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                cap = f"🎤 *Mijoz ({first_name}, ID: `{user_id}`)*" + (f"\n{raw_text}" if raw_text else "")
                if claimed_cid and voice_id:
                    self.bot.api_request("sendVoice", {"chat_id": claimed_cid, "voice": voice_id, "caption": cap})
                elif config.DISCUSSION_GROUP_ID and voice_id:
                    payload = {
                        "chat_id": config.DISCUSSION_GROUP_ID,
                        "voice": voice_id,
                        "caption": cap
                    }
                    if disc_id:
                        payload["reply_to_message_id"] = disc_id
                    res = self.bot.api_request("sendVoice", payload)
                    if not res.get("ok") and disc_id:
                        payload.pop("reply_to_message_id", None)
                        self.bot.api_request("sendVoice", payload)
                return

            # 4. Dumaloq video (Video note) yuborilganda:
            if "video_note" in message:
                vnote_id = message["video_note"]["file_id"]
                ticket = ticket_service.add_client_message(user_id, "Dumaloq video xabar", media_type="video", file_id=vnote_id, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                if claimed_cid and vnote_id:
                    self.bot.api_request("sendVideoNote", {"chat_id": claimed_cid, "video_note": vnote_id})
                elif config.DISCUSSION_GROUP_ID and vnote_id:
                    payload = {
                        "chat_id": config.DISCUSSION_GROUP_ID,
                        "video_note": vnote_id
                    }
                    if disc_id:
                        payload["reply_to_message_id"] = disc_id
                    res = self.bot.api_request("sendVideoNote", payload)
                    if not res.get("ok") and disc_id:
                        payload.pop("reply_to_message_id", None)
                        self.bot.api_request("sendVideoNote", payload)
                return

            # 5. Video yoki animatsiya (GIF) yuborilganda:
            if "video" in message or "animation" in message:
                vid_id = (message.get("video") or message.get("animation", {})).get("file_id")
                desc = f"Video: {raw_text}" if raw_text else "Video"
                ticket = ticket_service.add_client_message(user_id, desc, media_type="video", file_id=vid_id, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                cap = f"📹 *Mijoz ({first_name}, ID: `{user_id}`):*\n{raw_text}".strip() if raw_text else f"📹 *Mijoz ({first_name}, ID: `{user_id}`)*"
                if claimed_cid and vid_id:
                    self.bot.send_video(claimed_cid, vid_id, caption=cap)
                elif config.DISCUSSION_GROUP_ID and vid_id:
                    self.bot.send_video(
                        config.DISCUSSION_GROUP_ID,
                        vid_id,
                        caption=cap,
                        reply_to_message_id=disc_id
                    )
                return

            # 6. Hujjat / Fayl (PDF, ZIP, rasm fayl va boshqalar) yuborilganda:
            if "document" in message:
                doc = message["document"]
                doc_id = doc.get("file_id")
                doc_name = doc.get("file_name", "Fayl")
                desc = f"Fayl: {doc_name} ({raw_text})" if raw_text else f"Fayl: {doc_name}"
                ticket = ticket_service.add_client_message(user_id, desc, media_type="document", file_id=doc_id, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                cap = f"📁 *Mijoz ({first_name}, ID: `{user_id}`):* {doc_name}" + (f"\n{raw_text}" if raw_text else "")
                if claimed_cid and doc_id:
                    self.bot.send_document(claimed_cid, doc_id, caption=cap)
                elif config.DISCUSSION_GROUP_ID and doc_id:
                    self.bot.send_document(
                        config.DISCUSSION_GROUP_ID,
                        doc_id,
                        caption=cap,
                        reply_to_message_id=disc_id
                    )
                return

            # 7. Stiker yuborilganda:
            if "sticker" in message:
                stk_id = message["sticker"]["file_id"]
                disc_id = ticket.get("group_discussion_id") if ticket else None
                if claimed_cid and stk_id:
                    self.bot.api_request("sendSticker", {"chat_id": claimed_cid, "sticker": stk_id})
                elif config.DISCUSSION_GROUP_ID and stk_id:
                    payload = {
                        "chat_id": config.DISCUSSION_GROUP_ID,
                        "sticker": stk_id
                    }
                    if disc_id:
                        payload["reply_to_message_id"] = disc_id
                    res = self.bot.api_request("sendSticker", payload)
                    if not res.get("ok") and disc_id:
                        payload.pop("reply_to_message_id", None)
                        self.bot.api_request("sendSticker", payload)
                return

            # 8. Matnli xabar yuborilganda:
            if raw_text:
                ticket = ticket_service.add_client_message(user_id, raw_text, media_type=None, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                client_fwd = f"💬 *Mijoz ({first_name}, ID: `{user_id}`):*\n\n{raw_text}"
                if claimed_cid:
                    try:
                        self.bot.send_message(claimed_cid, client_fwd)
                    except Exception as chat_err:
                        print(f"[BRIDGE_CHAT_TEXT] Xatolik: {chat_err}")
                elif config.DISCUSSION_GROUP_ID:
                    try:
                        self.bot.send_message(
                            config.DISCUSSION_GROUP_ID,
                            client_fwd,
                            reply_to_message_id=disc_id
                        )
                    except Exception as disc_err:
                        print(f"[BRIDGE_TEXT] Xatolik: {disc_err}")
                return


        # Hujjat (Excel/CSV yoki PDF/Rasm kvitansiya) tashlangan bo'lsa
        if "document" in message:
            doc = message["document"]
            file_name = doc.get("file_name", "").lower()
            file_mime = (doc.get("mime_type") or "").lower()

            # 1. Admin tomonidan Excel/CSV baza yangilanishi
            if file_name.endswith(".xlsx") or file_name.endswith(".csv"):
                temp_path = os.path.join(config.DATA_DIR, f"temp_{int(time.time())}_{file_name}")
                if self.bot.download_file(doc["file_id"], temp_path):
                    count = excel_service.update_excel_file(temp_path)
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    resp = (
                        f"📊 *Excel oylik abonent hisob-kitob jadvali muvaffaqiyatli yangilandi!*\n\n"
                        f"📁 Fayl nomi: `{file_name}`\n"
                        f"👥 Bazadagi jami tashkilotlar soni: *{count} ta*"
                    )
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                    return
                else:
                    self.bot.send_message(chat_id, "❌ Faylni yuklab olishda xatolik yuz berdi.", reply_to_message_id=reply_to_id)
                    return

            # 2. PDF yoki hujjat ko'rinishidagi rasm / kvitansiya
            is_pdf_or_image = (
                file_name.endswith(".pdf") or
                any(file_name.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]) or
                ("pdf" in file_mime) or ("image" in file_mime)
            )

            if is_pdf_or_image:
                session = session_mgr.get_session(user_id, chat_id=chat_id, first_name=first_name, username=username)
                doc_file_id = doc["file_id"]
                ext = ".pdf" if (file_name.endswith(".pdf") or "pdf" in file_mime) else ".jpg"
                temp_doc_path = os.path.join(config.DATA_DIR, f"doc_{int(time.time())}_{user_id}{ext}")
                is_down = self.bot.download_file(doc_file_id, temp_doc_path)

                if is_down:
                    receipt_check = {"is_receipt": False}
                    try:
                        receipt_check = receipt_service.process_file(temp_doc_path, session=session)
                    except Exception as err:
                        print(f"[RECEIPT_DOC] Tahlilda xatolik: {err}")

                    if receipt_check.get("is_transfer_screen"):
                        resp = (
                            "🧾 *Siz yuborgan rasm to'lov kvitansiyasi emas, balki to'lov ilovasidagi o'tkazma ekrani (skrinshot) hisoblanadi.*\n\n"
                            "To'lovni to'liq hisobga olishimiz uchun bizga rasmiy to'lov kvitansiyasi kerak bo'ladi.\n\n"
                            "📲 *Kvitansiyani yuklab olish tartibi:*\n"
                            "Ilovangizda (masalan, *Click* yoki *Payme* dasturida) ekranning pastki qismidagi **«Kvitansiyani yuklab olish»** (yoki **«Kvitansiya» / «Chek»**) tugmasini bosing va saqlab olingan rasmiy to'lov kvitansiyasini (PDF yoki rasm ko'rinishida) botga yuboring."
                        )
                        self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                        if os.path.exists(temp_doc_path):
                            try:
                                os.remove(temp_doc_path)
                            except Exception:
                                pass
                        return

                    if receipt_check.get("is_foreign_receipt"):
                        f_info = receipt_check.get("foreign_info", {})
                        rec_name = f_info.get("receiver", "Boshqa tashkilot")
                        amt = f_info.get("amount", "Ko'rsatilmagan")
                        foreign_msg = (
                            f"⚠️ *Diqqat: Ushbu to'lov «Mars Elektron Texnika»ga ham, «Yangi Texnologiyalar» DUK ga ham tegishli emasdek ko'rinmoqda.*\n\n"
                            f"📌 *Kvitansiyadagi qabul qiluvchi:* {rec_name}\n"
                            f"💵 *Summa:* {amt}\n\n"
                            f"🏢 *«Mars Elektron Texnika» (Oylik to'lov):* `20208000800208044003`\n"
                            f"📟 *«Yangi Texnologiyalar» DUK (Yillik to'lov):* `20210000100431200010`\n\n"
                            f"Iltimos, to'lov rekvizitlarini tekshiring yoki adminga murojaat qiling."
                        )
                        self.bot.send_message(chat_id, foreign_msg, reply_to_message_id=reply_to_id)
                        if os.path.exists(temp_doc_path):
                            try:
                                os.remove(temp_doc_path)
                            except Exception:
                                pass
                        return

                    if receipt_check.get("is_receipt"):
                        # To'lov kvitansiyasi aniqlandi
                        org_info = receipt_check.get("org_info")

                        # 1. Agar kvitansiyadan tashkilot topilgan bo'lsa va Excelda mavjud bo'lsa:
                        if org_info and org_info.get("found"):
                            org_name = org_info["org_name"]
                            inn = org_info["inn"]
                            id_type = org_info.get("id_type", "STIR / INN")
                            balans_str = org_info["balance_str"]
                            uname_str = f"@{username}" if username else "Mavjud emas"

                            # Texnik va adminlarga kvitansiyani jo'natish
                            target_ids = list(set([config.TECHNICIAN_TELEGRAM_ID] + config.ADMIN_TELEGRAM_IDS))
                            tech_caption = (
                                f"🧾 *Yangi to'lov kvitansiyasi (Fayl/PDF) keldi:*\n\n"
                                f"🏢 Tashkilot: *{org_name}*\n"
                                f"📑 {id_type}: `{inn}`\n"
                                f"💳 Oylik abonent balansi: {balans_str}\n"
                                f"👤 Yuboruvchi: {first_name} ({uname_str})\n"
                                f"🆔 ID: `{user_id}`"
                            )
                            admin_messages = []
                            for adm_id in target_ids:
                                try:
                                    res_alert = self.bot.send_document(adm_id, doc_file_id, caption=tech_caption)
                                    if res_alert.get("ok"):
                                        alert_mid = res_alert["result"]["message_id"]
                                        admin_messages.append({"chat_id": adm_id, "message_id": alert_mid, "is_photo": False})
                                except Exception as e_alert:
                                    print(f"[KVITANSIYA_DOC_ALERT] Alert yuborishda xatolik: {e_alert}")

                            ticket = ticket_service.register_ticket(
                                tech_msg_id=admin_messages[0]["message_id"] if admin_messages else None,
                                client_data={
                                    "user_id": user_id,
                                    "chat_id": chat_id,
                                    "message_id": message_id,
                                    "first_name": first_name,
                                    "org_name": org_name,
                                    "inn": inn,
                                    "type": "kvitansiya",
                                    "is_receipt": True
                                },
                                base_card=tech_caption,
                                admin_messages=admin_messages
                            )

                            # Texniklar kanaliga (@mars_tex_xizmat) ham yuborish
                            try:
                                card_kb = ticket_service.get_channel_keyboard(ticket)
                                card_text = ticket_service.format_channel_card(ticket)
                                chan_id = config.TECHNICIAN_CHANNEL_ID
                                c_res = self.bot.send_document(chan_id, doc_file_id, caption=card_text, reply_markup=card_kb)
                                if not c_res.get("ok"):
                                    c_res = self.bot.send_message(chan_id, card_text, reply_markup=card_kb)
                                if c_res.get("ok"):
                                    c_mid = c_res["result"]["message_id"]
                                    ticket["channel_message_id"] = c_mid
                                    ticket["is_photo"] = False
                                    ticket_service.tickets[str(c_mid)] = ticket
                                    ticket_service.save_tickets()
                            except Exception as chan_e:
                                print(f"[KVITANSIYA_DOC_CHANNEL] Xatolik: {chan_e}")

                            # Mijozga qisqa va aniq javob
                            client_resp = "🧾 *To'lov kvitansiyangiz mas'ul texnik mutaxassisimizga yetkazildi. Iltimos, kutib turing!*"
                            session.state = "ADMIN_BOGLANISH"
                            session.inn = inn
                            session.org_name = org_name
                            session.pending_receipt = None
                            session_mgr.save_sessions()
                            self.bot.send_message(chat_id, client_resp, reply_to_message_id=reply_to_id)
                        else:
                            # 2. Tashkilot ma'lumotlari kvitansiyaning «To'lov maqsadi» yoki «Yuboruvchi» bo'limidan topilmadi yoki Excelda yo'q
                            session.pending_receipt = {
                                "file_id": doc_file_id,
                                "is_doc": True,
                                "file_name": file_name,
                                "message_id": message_id
                            }
                            session.state = "AWAITING_RECEIPT_INN"
                            session_mgr.save_sessions()
                            client_resp = (
                                "🧾 *To'lov kvitansiyangiz qabul qilindi.*\n\n"
                                "⚠️ Kvitansiyadagi «To'lov maqsadi» yoki «Yuboruvchi» bo'limidan tashkilotingiz ma'lumotlarini topa olmadim.\n\n"
                                "Iltimos, to'lovni hisobga olishimiz uchun tashkilotingizning 9 xonali *STIR (INN)* yoki 14 xonali *JSHSHIR* raqamini yuboring."
                            )
                            self.bot.send_message(chat_id, client_resp, reply_to_message_id=reply_to_id)

                        if os.path.exists(temp_doc_path):
                            try:
                                os.remove(temp_doc_path)
                            except Exception:
                                pass
                        return
                    else:
                        # Kvitansiya bo'lmasa, agar rasm fayl bo'lsa, kassa apparati nosozligi deb tekshiramiz
                        if not file_name.endswith(".pdf"):
                            try:
                                from image_analyzer import analyze_pos_image
                                analysis = analyze_pos_image(temp_doc_path)
                                if analysis.get("status") == "VALID_POS":
                                    session.last_photo_file_id = doc_file_id
                                    session.last_photo_caption = message.get("caption", "")
                                    session.last_photo_text = analysis.get("text", "")
                                    session.last_msg_id = message_id
                                    session_mgr.save_sessions()
                                    if os.path.exists(temp_doc_path):
                                        os.remove(temp_doc_path)
                                    # Quyida has_new_photo logikasiga o'tadi
                            except Exception:
                                pass

                    if os.path.exists(temp_doc_path):
                        try:
                            os.remove(temp_doc_path)
                        except Exception:
                            pass

                if session and session.state == "ADMIN_BOGLANISH":
                    doc_id = doc.get("file_id")
                    doc_name = doc.get("file_name", "Fayl")
                    cap = message.get("caption", "").strip()
                    desc = f"Fayl: {doc_name} ({cap})" if cap else f"Fayl: {doc_name}"
                    ticket = ticket_service.add_client_message(user_id, desc, media_type="document", file_id=doc_id, chat_id=chat_id, message_id=message_id)
                    disc_id = ticket.get("group_discussion_id") if ticket else None
                    if disc_id and config.DISCUSSION_GROUP_ID and doc_id:
                        try:
                            self.bot.send_document(
                                config.DISCUSSION_GROUP_ID,
                                doc_id,
                                caption=f"📁 *Mijoz ({first_name}) dan fayl:* {doc_name}\n{cap}".strip(),
                                reply_to_message_id=disc_id
                            )
                        except Exception as e:
                            print(f"[DISC_DOC] Xatolik: {e}")
                    if not ticket or not ticket.get("claimed_by"):
                        resp = (
                            "👨‍💻 *Faylingiz mas'ul texnik mutaxassislar guruhiga yetkazildi.*\n\n"
                            "Iltimos, mutaxassisimiz javobini kutib turing!"
                        )
                        self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                    return

                self.bot.send_message(chat_id, "⚠️ Iltimos, to'lov kvitansiyasini (rasm/PDF) yoki kassa apparati nosozlik rasmini yuboring.", reply_to_message_id=reply_to_id)
                return

        # Ovozli xabar (Voice / Audio) yuborilgan bo'lsa
        if "voice" in message or "audio" in message:
            session = session_mgr.get_session(user_id, chat_id=chat_id, first_name=first_name, username=username)
            if session and session.state == "ADMIN_BOGLANISH":
                voice_id = (message.get("voice") or message.get("audio", {})).get("file_id")
                ticket = ticket_service.add_client_message(user_id, "Ovozli xabar", media_type="voice", file_id=voice_id, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                if disc_id and config.DISCUSSION_GROUP_ID and voice_id:
                    try:
                        self.bot.api_request("sendVoice", {
                            "chat_id": config.DISCUSSION_GROUP_ID,
                            "voice": voice_id,
                            "caption": f"🎤 *Mijoz ({first_name}) dan ovozli xabar*",
                            "reply_to_message_id": disc_id
                        })
                    except Exception as e:
                        print(f"[DISC_VOICE] Xatolik: {e}")
                if not ticket or not ticket.get("claimed_by"):
                    resp = (
                        "👨‍💻 *Ovozli xabaringiz mas'ul texnik mutaxassislar guruhiga yetkazildi.*\n\n"
                        "Iltimos, mutaxassisimiz javobini kutib turing!"
                    )
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return
            else:
                resp = (
                    "🎤 *Kechirasiz, men ovozli xabarlarni tinglay olmayman.*\n\n"
                    "Iltimos, murojaatingizni *yozma ravishda* yozing yoki apparatingiz chiqargan xatolikni *rasmga olgan holda* yuboring."
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

        # Dumaloq video (Video note) yuborilgan bo'lsa
        if "video_note" in message:
            session = session_mgr.get_session(user_id, chat_id=chat_id, first_name=first_name, username=username)
            if session and session.state == "ADMIN_BOGLANISH":
                vnote_id = message["video_note"]["file_id"]
                ticket = ticket_service.add_client_message(user_id, "Dumaloq video xabar", media_type="video", file_id=vnote_id, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                if disc_id and config.DISCUSSION_GROUP_ID and vnote_id:
                    try:
                        self.bot.api_request("sendVideoNote", {
                            "chat_id": config.DISCUSSION_GROUP_ID,
                            "video_note": vnote_id,
                            "reply_to_message_id": disc_id
                        })
                    except Exception as e:
                        print(f"[DISC_VNOTE] Xatolik: {e}")
                if not ticket or not ticket.get("claimed_by"):
                    resp = (
                        "👨‍💻 *Video xabaringiz mas'ul texnik mutaxassislar guruhiga yetkazildi.*\n\n"
                        "Iltimos, mutaxassisimiz javobini kutib turing!"
                    )
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return
            else:
                resp = (
                    "⭕ *Kechirasiz, men dumaloq video xabarlarni ko'ra olmayman.*\n\n"
                    "Iltimos, murojaatingizni *yozma ravishda* yozing yoki apparatingiz chiqargan xatolikni *rasmga olgan holda* yuboring."
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

        # Video yoki animatsiya yuborilgan bo'lsa
        if "video" in message or "animation" in message:
            session = session_mgr.get_session(user_id, chat_id=chat_id, first_name=first_name, username=username)
            if session and session.state == "ADMIN_BOGLANISH":
                vid_cap = message.get("caption", "").strip()
                desc = f"Video: {vid_cap}" if vid_cap else "Video"
                vid_id = message.get("video", {}).get("file_id") or message.get("animation", {}).get("file_id")
                ticket = ticket_service.add_client_message(user_id, desc, media_type="video", file_id=vid_id, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                if disc_id and config.DISCUSSION_GROUP_ID and vid_id:
                    try:
                        self.bot.send_video(
                            config.DISCUSSION_GROUP_ID,
                            vid_id,
                            caption=f"📹 *Mijoz ({first_name}) dan video:*\n{vid_cap}".strip(),
                            reply_to_message_id=disc_id
                        )
                    except Exception as e:
                        print(f"[DISC_VIDEO] Xatolik: {e}")
                if not ticket or not ticket.get("claimed_by"):
                    resp = (
                        "👨‍💻 *Video xabaringiz mas'ul texnik mutaxassislar guruhiga yetkazildi.*\n\n"
                        "Iltimos, mutaxassisimiz javobini kutib turing!"
                    )
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return
            else:
                resp = (
                    "📹 *Kechirasiz, men videolarni ko'ra olmayman.*\n\n"
                    "Iltimos, murojaatingizni *yozma ravishda* yozing yoki apparatingiz chiqargan xatolikni *rasmga olgan holda* yuboring."
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

        # 8 soatlik sessiyani olish
        session = session_mgr.get_session(user_id, chat_id=chat_id, first_name=first_name, username=username)

        # Agar mijoz rasm yuborgan bo'lsa (Kvitansiya yoki Kassa xatoligi ekrani)
        has_new_photo = False
        if "photo" in message:
            photo_arr = message.get("photo", [])
            if photo_arr:
                file_id = photo_arr[-1]["file_id"]

                # Rasmni yuklab olamiz
                temp_img_path = os.path.join(config.DATA_DIR, f"check_{int(time.time())}_{user_id}.jpg")
                is_downloaded = self.bot.download_file(file_id, temp_img_path)

                if is_downloaded:
                    # Rasm qaysi toifaga tegishli ekanligini (KVITANSIYA, KASSA_APARAT yoki BOSHQA) aniqlaymiz
                    from image_analyzer import classify_image_type
                    img_classification = classify_image_type(temp_img_path)
                    img_category = img_classification.get("category", "BOSHQA")

                    # 1. BOSHQA (Kassa apparati ham, to'lov kvitansiyasi ham emas - odam, tabiat, mashina, skrinshot va h.k.)
                    if img_category == "BOSHQA":
                        resp = (
                            "⚠️ *Iltimos, kassa apparati nosozligi aks etgan ekranni yoki to'lov kvitansiyasini yuboring.*\n\n"
                            "Siz yuborgan rasm kassa apparatiga ham, to'lov chekiga ham o'xshamaydi."
                        )
                        self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                        if os.path.exists(temp_img_path):
                            try:
                                os.remove(temp_img_path)
                            except Exception:
                                pass
                        return

                    # 2. KVITANSIYA bo'lsa (Click, Payme, bank kvitansiyasi)
                    if img_category == "KVITANSIYA":
                        try:
                            receipt_check = receipt_service.process_file(temp_img_path, session=session)
                        except Exception as r_err:
                            print(f"[RECEIPT_PHOTO] Tahlilda xatolik: {r_err}")
                            receipt_check = {"is_receipt": False}

                        if receipt_check.get("is_transfer_screen"):
                            resp = (
                                "🧾 *Siz yuborgan rasm to'lov kvitansiyasi emas, balki to'lov ilovasidagi o'tkazma ekrani (skrinshot) hisoblanadi.*\n\n"
                                "To'lovni to'liq hisobga olishimiz uchun bizga rasmiy to'lov kvitansiyasi kerak bo'ladi.\n\n"
                                "📲 *Kvitansiyani yuklab olish tartibi:*\n"
                                "Ilovangizda (masalan, *Click* yoki *Payme* dasturida) ekranning pastki qismidagi **«Kvitansiyani yuklab olish»** (yoki **«Kvitansiya» / «Chek»**) tugmasini bosing va saqlab olingan rasmiy to'lov kvitansiyasini (PDF yoki rasm ko'rinishida) botga yuboring."
                            )
                            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                            if os.path.exists(temp_img_path):
                                try:
                                    os.remove(temp_img_path)
                                except Exception:
                                    pass
                            return

                        if receipt_check.get("is_foreign_receipt"):
                            f_info = receipt_check.get("foreign_info", {})
                            rec_name = f_info.get("receiver", "Boshqa tashkilot")
                            amt = f_info.get("amount", "Ko'rsatilmagan")
                            foreign_msg = (
                                f"⚠️ *Diqqat: Ushbu to'lov «Mars Elektron Texnika»ga ham, «Yangi Texnologiyalar» DUK ga ham tegishli emasdek ko'rinmoqda.*\n\n"
                                f"📌 *Kvitansiyadagi qabul qiluvchi:* {rec_name}\n"
                                f"💵 *Summa:* {amt}\n\n"
                                f"🏢 *«Mars Elektron Texnika» (Oylik to'lov):* `20208000800208044003`\n"
                                f"📟 *«Yangi Texnologiyalar» DUK (Yillik to'lov):* `20210000100431200010`\n\n"
                                f"Iltimos, to'lov rekvizitlarini tekshiring yoki adminga murojaat qiling."
                            )
                            self.bot.send_message(chat_id, foreign_msg, reply_to_message_id=reply_to_id)
                            if os.path.exists(temp_img_path):
                                try:
                                    os.remove(temp_img_path)
                                except Exception:
                                    pass
                            return

                        if receipt_check.get("is_receipt"):
                            # Rasm to'lov kvitansiyasi ekanligi tasdiqlandi!
                            org_info = receipt_check.get("org_info")

                            # 1. Agar kvitansiyadan tashkilot topilgan bo'lsa va Excelda mavjud bo'lsa:
                            if org_info and org_info.get("found"):
                                org_name = org_info["org_name"]
                                inn = org_info["inn"]
                                id_type = org_info.get("id_type", "STIR / INN")
                                balans_str = org_info["balance_str"]
                                uname_str = f"@{username}" if username else "Mavjud emas"

                                # Texnik va adminlarga kvitansiyani jo'natish
                                target_ids = list(set([config.TECHNICIAN_TELEGRAM_ID] + config.ADMIN_TELEGRAM_IDS))
                                tech_caption = (
                                    f"🧾 *Yangi to'lov kvitansiyasi keldi:*\n\n"
                                    f"🏢 Tashkilot: *{org_name}*\n"
                                    f"📑 {id_type}: `{inn}`\n"
                                    f"💳 Oylik abonent balansi: {balans_str}\n"
                                    f"👤 Yuboruvchi: {first_name} ({uname_str})\n"
                                    f"🆔 ID: `{user_id}`"
                                )
                                admin_messages = []
                                for adm_id in target_ids:
                                    try:
                                        res_alert = self.bot.send_photo(adm_id, file_id, caption=tech_caption)
                                        if res_alert.get("ok"):
                                            alert_mid = res_alert["result"]["message_id"]
                                            admin_messages.append({"chat_id": adm_id, "message_id": alert_mid, "is_photo": True})
                                    except Exception as e_alert:
                                        print(f"[KVITANSIYA_PHOTO_ALERT] Alert yuborishda xatolik: {e_alert}")

                                ticket = ticket_service.register_ticket(
                                    tech_msg_id=admin_messages[0]["message_id"] if admin_messages else None,
                                    client_data={
                                        "user_id": user_id,
                                        "chat_id": chat_id,
                                        "message_id": message_id,
                                        "first_name": first_name,
                                        "org_name": org_name,
                                        "inn": inn,
                                        "type": "kvitansiya"
                                    },
                                    base_card=tech_caption,
                                    admin_messages=admin_messages
                                )

                                # Texniklar kanaliga (@mars_tex_xizmat) yuborish
                                try:
                                    card_kb = ticket_service.get_channel_keyboard(ticket)
                                    card_text = ticket_service.format_channel_card(ticket)
                                    chan_id = config.TECHNICIAN_CHANNEL_ID
                                    c_res = self.bot.send_photo(chan_id, file_id, caption=card_text, reply_markup=card_kb)
                                    if not c_res.get("ok"):
                                        c_res = self.bot.send_message(chan_id, card_text, reply_markup=card_kb)
                                    if c_res.get("ok"):
                                        c_mid = c_res["result"]["message_id"]
                                        ticket["channel_message_id"] = c_mid
                                        ticket["is_photo"] = True
                                        ticket_service.tickets[str(c_mid)] = ticket
                                        ticket_service.save_tickets()
                                except Exception as chan_e:
                                    print(f"[KVITANSIYA_CHANNEL_ALERT] Xatolik: {chan_e}")

                                # Mijozga qisqa va aniq javob
                                client_resp = "🧾 *To'lov kvitansiyangiz mas'ul texnik mutaxassisimizga yetkazildi. Iltimos, kutib turing!*"
                                session.state = "ADMIN_BOGLANISH"
                                session.inn = inn
                                session.org_name = org_name
                                session.pending_receipt = None
                                session_mgr.save_sessions()
                                self.bot.send_message(chat_id, client_resp, reply_to_message_id=reply_to_id)
                            else:
                                # 2. Tashkilot ma'lumotlari kvitansiyaning «To'lov maqsadi» yoki «Yuboruvchi» bo'limidan topilmadi yoki Excelda yo'q
                                session.pending_receipt = {
                                    "file_id": file_id,
                                    "is_doc": False,
                                    "file_name": "photo.jpg",
                                    "message_id": message_id
                                }
                                session.state = "AWAITING_RECEIPT_INN"
                                session_mgr.save_sessions()
                                client_resp = (
                                    "🧾 *To'lov kvitansiyangiz qabul qilindi.*\n\n"
                                    "⚠️ Kvitansiyadagi «To'lov maqsadi» yoki «Yuboruvchi» bo'limidan tashkilotingiz ma'lumotlarini topa olmadim.\n\n"
                                    "Iltimos, to'lovni hisobga olishimiz uchun tashkilotingizning 9 xonali *STIR (INN)* yoki 14 xonali *JSHSHIR* raqamini yuboring."
                                )
                                self.bot.send_message(chat_id, client_resp, reply_to_message_id=reply_to_id)

                            if os.path.exists(temp_img_path):
                                try:
                                    os.remove(temp_img_path)
                                except Exception:
                                    pass
                            return

                    # 3. KASSA_APARAT bo'lsa (Kassa apparati ekrani yoki xatolik oynasi)
                    analysis = img_classification.get("pos_analysis") or {"status": "VALID_POS"}
                    if os.path.exists(temp_img_path):
                        try:
                            os.remove(temp_img_path)
                        except Exception:
                            pass

                    # Aparat ekrani to'liq ko'rinmagan bo'lsa (tepa qismidagi internet va soat ko'rinmagan bo'lsa)
                    if analysis.get("status") == "TOP_BAR_MISSING":
                        resp = "⚠️ Iltimos, aparatning yuqori qismidagi internet va soat ko'rinib turadigan joylarini ham o'z ichiga olgan holda ekranni to'liq rasmga olib tashlang."
                        self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                        return

                    # Kassa apparati va to'liq ekrani tasdiqlandi
                    session.last_photo_file_id = file_id
                    session.last_photo_caption = message.get("caption", "")
                    session.last_photo_text = analysis.get("text", "")
                    session.last_msg_id = message_id
                    has_new_photo = True
                    session_mgr.save_sessions()

        text = message.get("text", "") or message.get("caption", "")
        norm_text = self.normalize_text(text) if text else ""
        is_both_clean = (session.oylik_holat == "toza" and session.fm_holat == "toza")

        # 0.5. Sun'iy intellekt (Gemini AI) orqali xabar tahlili (FAQAT sof matnli xabarlar uchun!)
        # Mijoz rasm yuborgan bo'lsa yoki klaviatura tugmasini bosgan bo'lsa, sun'iy intellekt aralashmaydi — botning o'zi tahlil qiladi.
        ai_result = None
        ai_intent = None
        is_slash_cmd = bool(text and text.strip().startswith("/"))
        is_btn_click = self.is_keyboard_button_text(text, norm_text)
        if text and not has_new_photo and not is_slash_cmd and not is_btn_click:
            ai_result = ai_service.analyze_message(text, session=session)
            ai_intent = ai_result.get("intent") if ai_result else None
            if ai_result:
                print(f"[AI_RESULT] Niyat: {ai_intent}")

        # 1. Agar rasm yuborilgan bo'lsa (Botning o'zi tahlil qiladi):
        if has_new_photo:
            # Agar mijoz allaqachon texnikka yetkazilib, javob kutayotgan bo'lsa:
            if session.state == "ADMIN_BOGLANISH":
                caption_text = message.get("caption", "").strip()
                desc = f"Rasm: {caption_text}" if caption_text else "Rasm"
                photo_file_id = getattr(session, "last_photo_file_id", None)
                ticket = ticket_service.add_client_message(user_id, desc, media_type="photo", file_id=photo_file_id, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                if disc_id and config.DISCUSSION_GROUP_ID and photo_file_id:
                    try:
                        self.bot.send_photo(
                            config.DISCUSSION_GROUP_ID,
                            photo_file_id,
                            caption=f"📷 *Mijoz ({first_name}) dan yangi rasm:*\n{caption_text}".strip(),
                            reply_to_message_id=disc_id
                        )
                    except Exception as disc_err:
                        print(f"[DISC_PHOTO] Xatolik: {disc_err}")
                if not ticket or not ticket.get("claimed_by"):
                    resp = (
                        f"👨‍💻 *Yangi rasm qabul qilindi va mas'ul texniklar guruhiga yetkazildi.*\n\n"
                        f"Iltimos, mutaxassisimiz javobini kutib turing!"
                    )
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            # 0. IKPU xatoligi tekshiruvi:
            photo_ocr = getattr(session, "last_photo_text", "")
            caption_text = message.get("caption", "")
            is_ikpu_photo = self.is_ikpu_error_text(photo_ocr) or self.is_ikpu_error_text(caption_text)

            if is_ikpu_photo:
                session.ikpu_error_active = True
                # Agar mijozga avval video yuborilgan bo'lsa va endi qaytadan rasm yuborayotgan bo'lsa:
                if getattr(session, "ikpu_video_sent", False):
                    # Istisno tariqasida darrov texnik bilan bog'laymiz!
                    self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text="Aparatda IKPU xatoligi (Qayta rasm yuborildi, video foyda bermadi)", is_ikpu_exception=True)
                    return
                else:
                    # Birinchi marta: video qo'llanmani avtomatik yuboramiz!
                    session.ikpu_video_sent = True
                    session_mgr.save_sessions()
                    self.send_ikpu_solution_media(chat_id, reply_to_id=reply_to_id)
                    return

            # 0.1. Soat / vaqt muammosi tekshiruvi (caption yoki OCR):
            is_clock_photo = (caption_text and self.is_clock_problem_query(self.normalize_text(caption_text), caption_text)) or self.is_clock_problem_query(self.normalize_text(photo_ocr), photo_ocr)
            if is_clock_photo:
                session.clock_video_sent = True
                session_mgr.save_sessions()
                self.send_clock_solution_media(chat_id, reply_to_id=reply_to_id)
                return

            # 0.2. 406 yoki Day Limit (oflayn rejim / 36889) xatoligi tekshiruvi (Yillik to'lovni tekshirish talabi):
            is_offline_limit_photo = self.is_offline_limit_error(photo_ocr) or self.is_offline_limit_error(caption_text)
            if is_offline_limit_photo:
                session.unclear_count = 0
                session.offline_limit_error_active = True
                session_mgr.save_sessions()

                # 1) Agar yillikdan allaqachon qarzdorligi aniqlangan bo'lsa:
                if session.fm_holat == "qarzdor":
                    resp = (
                        f"⚠️ Kassa aparatingiz ishlashi uchun yillik fiskal modul to'lovini amalga oshirishingiz lozim. "
                        f"To'lov amalga oshirilgach apparat faoliyati tiklanadi.\n\n"
                        f"To'lov qilish bo'yicha video qo'llanma va hisob raqam rekvizitini yubormoqdaman 👇"
                    )
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                    self.send_yearly_payment_media(chat_id, reply_to_id=reply_to_id)
                    return

                # 2) Agar yillik toza bo'lsa va oylik ham toza bo'lsa:
                if session.fm_holat == "toza" and session.oylik_holat == "toza":
                    self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text)
                    return

                # 3) Agar yillik to'lov hali tekshirilmagan bo'lsa:
                resp = (
                    "⚠️ *Kassa apparatingiz ekranidagi ushbu nosozlik (406 / Day Limit xatoligi)* odatda apparatning **yillik fiskal modul to'lovi** muddati tugaganida yoki to'lov qilinmaganida yuzaga keladi.\n\n"
                    "Kassa apparatingiz ishlashi uchun **yillik fiskal modul to'lovingizni tekshirishingiz lozim**.\n\n"
                    "Iltimos, apparatingiz chiqargan chekning pastki qismidagi **FM raqamini** yuboring yoki quyidagi **«📟 Yillik fiskal modul to'lovini tekshirish»** tugmasini bosing."
                )
                session.state = "AWAITING_FM"
                session_mgr.save_sessions()
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id, reply_markup=self.get_offline_limit_keyboard())
                return

            # 0.3. Agar rasm tagiga (caption) STIR yoki JSHSHIR raqami birga yozilgan bo'lsa:
            caption_inn = self.extract_inn(caption_text) if caption_text else None
            if caption_inn:
                self.process_inn_check(chat_id, message_id, reply_to_id, session, first_name, username, user_id, text, norm_text, caption_inn)
                return

            # Texnikka ulanish shartlari tekshiruvi:
            # A) Agar INN yoki oylik to'lov hali tekshirilmagan bo'lsa:
            if not session.inn or not session.oylik_holat:
                resp = (
                    f"📷 *Aparatingiz ekranidagi nosozlik rasmi qabul qilindi.*\n\n"
                    f"Kassa apparatidagi muammoni aniqlash uchun, avvalo, apparatning to'lovlari holatini tekshirishimiz lozim.\n\n"
                    f"Kassa apparatingizni tekshirish uchun tashkilotingizning 9 xonali STIR (INN) yoki 14 xonali JSHSHIR raqamini yuboring.\n\n"
                    f"ℹ️ *Ma'lumot uchun:* Tashkilotingiz INN yoki JSHSHIR raqami aparatingiz chiqargan chekda *STIR* deb yozilgan bo'limida ko'rsatilgan."
                )
                session.state = "AWAITING_INN"
                session_mgr.save_sessions()
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            # B) Agar oylikdan qarzdor bo'lsa:
            if session.oylik_holat == "qarzdor":
                pay_prompt_text = (
                    f"⚠️ *Kassa aparatingiz ishlashi uchun oylik abonent to'lovidan qarzdorlikni to'lashingiz lozim.*\n\n"
                    f"Qarzdorlik bartaraf etilgach, apparat faoliyati tiklanadi.\n"
                    f"Oylik abonent to'lovi hisob raqami va to'lov qo'llanmasi quyida yuborildi 👇"
                )
                self.bot.send_message(chat_id, pay_prompt_text, reply_to_message_id=reply_to_id)
                self.send_monthly_payment_media(chat_id, reply_to_id=reply_to_id)
                return

            # C) Agar oylik toza bo'lsa:
            if session.oylik_holat == "toza":
                self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text)
                return

        if not text:
            return

        # Reply yoki mention orqali botga murojaat qilinganligini aniqlash
        reply_to = message.get("reply_to_message", {})
        is_reply_to_bot = False
        if reply_to:
            from_reply = reply_to.get("from", {})
            if from_reply.get("id") == 8927157387 or (from_reply.get("username") or "").lower() == "txkmrobot" or from_reply.get("is_bot"):
                is_reply_to_bot = True

        is_mention = ("@txkmrobot" in text.lower()) or ("mars bot" in text.lower()) or ("txkm" in text.lower()) or ("robot" in text.lower())
        entities = message.get("entities", [])
        for ent in entities:
            if ent.get("type") == "mention":
                offset = ent.get("offset", 0)
                length = ent.get("length", 0)
                mention_text = text[offset:offset+length].lower()
                if "txkm" in mention_text or "mars" in mention_text or "robot" in mention_text:
                    is_mention = True

        # 0.9. /salombot buyrug'i: mijoz bilan bo'lgan avvalgi barcha suhbatni unutish va yangi mijoz sifatida boshlash
        clean_first_word = text.strip().split()[0].lower() if text else ""
        if clean_first_word in ["/salombot", "/salombot@txkmrobot"] or "/salombot" in text.lower():
            session_mgr.reset_session(user_id)
            ticket_service.close_ticket(user_id)
            session_mgr.save_sessions()
            resp = (
                f"Assalomu alaykum, *{first_name}*!\n\n"
                f"Men *{config.COMPANY_NAME}* ning online nazorat kassa apparatlari (SmartOne / P3) bo'yicha texnik xizmat ko'rsatuvchi rasmiy telegram botiman.\n\n"
                f"🔄 Siz bilan bo'lgan avvalgi barcha suhbat ma'lumotlari xotiradan tozalandi. Yangitdan boshlaymiz!\n\n"
                f"🔧 *Bot imkoniyatlari:*\n"
                f"• Aparatdagi muammolarni aniqlash va bartaraf etish\n"
                f"• Oylik abonent to'lovini tekshirish (STIR / INN yuboring)\n"
                f"• Oylik to'lov qilish rekvizitlari va video darsligi\n"
                f"• Yillik Fiskal Modul to'lovini tekshirish (FM raqamini yuboring)\n"
                f"• Yillik to'lov rekvizitlari va qo'llanmasi\n"
                f"• Mas'ul texnik xodim (admin) bilan bog'lanish\n\n"
                f"Savolingiz yoki murojaatingizni yozib qoldirishingiz mumkin!"
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 0.92. Agar mijoz allaqachon mas'ul texnik bilan bog'langan bo'lsa (ADMIN_BOGLANISH):
        # Texnik javob bermaguncha mijoz NIMA DEB YOZISHIDAN QAT'IY NAZAR (matn, raqam, STIR, FM, tugma)
        # uning xabari kartochkaga tahrirlanib kiritiladi va faqat texnik javobini kutish aytiladi!
        if session.state == "ADMIN_BOGLANISH":
            if text and not text.startswith("/"):
                ticket = ticket_service.add_client_message(user_id, text, media_type=None, chat_id=chat_id, message_id=message_id)
                disc_id = ticket.get("group_discussion_id") if ticket else None
                if disc_id and config.DISCUSSION_GROUP_ID:
                    try:
                        self.bot.send_message(
                            config.DISCUSSION_GROUP_ID,
                            f"💬 *Mijoz ({first_name}, ID: `{user_id}`):*\n{text}",
                            reply_to_message_id=disc_id
                        )
                    except Exception as disc_err:
                        print(f"[DISC_POST] Xatolik: {disc_err}")

            session.unclear_count = 0
            session_mgr.save_sessions()
            if not ticket or not ticket.get("claimed_by"):
                resp = (
                    "👨‍💻 *Xabaringiz mas'ul texnik mutaxassislar guruhiga yetkazildi.*\n\n"
                    "Iltimos, mutaxassisimiz javobini kutib turing — tez orada mutaxassisimiz sizga javob yozadi."
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 0.95. Klaviaturadagi tayyor tugmalar bosilganda (Sun'iy intellektsiz, botning o'zi bevosita javob beradi)
        if self.is_keyboard_button_text(text, norm_text):
            session.unclear_count = 0
            t_low = text.lower()
            # A) Yillik fiskal modul to'lovini tekshirish
            if any(k in t_low or k in norm_text for k in ["fiskal modul to'lovini tekshir", "fiskal modul tolovini tekshir"]):
                session.state = "AWAITING_FM"
                session.last_intent = "check_yearly"
                session_mgr.save_sessions()
                resp = (
                    "Yillik fiskal modul to'lovingizni tekshirib berishimni istasangiz, aparatingizning fiskal modul raqamini yuboring.\n\n"
                    "ℹ️ *Ma'lumot uchun:* Fiskal modul raqami aparatingiz chiqargan chekning pastki qismida *FM raqami* deb yozilgan bo'limda ko'rsatiladi."
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            # B) Oylik abonent to'lovi hisob raqami (rekvizit va video)
            if any(k in t_low or k in norm_text for k in ["oylik abonent to'lov", "oylik abonent tolov", "oylik to'lov hisob raqami", "oylik tolov hisob raqami", "oylik to'lov rekviziti"]):
                session.state = "NORMAL"
                session.last_topic = "pay_monthly"
                session_mgr.save_sessions()
                self.send_monthly_payment_media(chat_id, reply_to_id=reply_to_id)
                return

            # C) Yillik fiskal modul to'lovi hisob raqami
            if any(k in t_low or k in norm_text for k in ["yillik fiskal modul to'lov", "yillik fiskal modul tolov", "yillik to'lov hisob raqami", "yillik tolov hisob raqami", "yillik to'lov rekviziti"]):
                session.state = "NORMAL"
                session.last_topic = "pay_yearly"
                session_mgr.save_sessions()
                self.send_yearly_payment_media(chat_id, reply_to_id=reply_to_id)
                return

            # D) To'lovlar tarixi va hisoboti
            if any(k in t_low or k in norm_text for k in ["to'lovlar tarixi", "tolovlar tarixi"]):
                inn_to_use = session.inn or self.extract_inn(text)
                if inn_to_use:
                    info = excel_service.find_by_identifier(inn_to_use)
                    if info:
                        resp = excel_service.get_payment_history_text(info)
                        session_mgr.save_sessions()
                        self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                        return
                resp = (
                    f"Yil davomida qaysi oylar uchun qancha to'lov qilinganligini tekshirish uchun "
                    f"tashkilotingizning INN yoki JSHSHIR raqamini yuboring.\n\n"
                    f"ℹ️ *Ma'lumot uchun:* Tashkilotingiz INN yoki JSHSHIR raqami aparatingiz chiqargan chekda *STIR* deb yozilgan bo'limida ko'rsatilgan."
                )
                session.state = "AWAITING_INN_HISTORY"
                session_mgr.save_sessions()
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            # E) Mas'ul texnik bilan bog'lanish
            if any(k in t_low or k in norm_text for k in ["mas'ul texnik bilan bog'lan", "masul texnik bilan bog'lan", "texnik bilan bog'lan"]):
                if not getattr(session, "last_photo_file_id", None):
                    resp = "Agar aparatingiz baribir ishlamayotgan bo'lsa, aparat ekrani to'liq ko'ringan holda rasm olib tashlang men sizni masul texnik bilan bog'layman."
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                    return
                self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text)
                return

        # 1. /start yoki /help buyruqlari
        if text.startswith("/start") or text.startswith("/help"):
            session.reset_for_new_target()
            session_mgr.save_sessions()
            resp = (
                f"Assalomu alaykum, *{first_name}*!\n\n"
                f"Men *{config.COMPANY_NAME}* ning online nazorat kassa apparatlari (NKA) bo'yicha texnik xizmat ko'rsatuvchi rasmiy telegram botiman.\n\n"
                f"🔧 *Bot imkoniyatlari:*\n"
                f"• Aparatdagi muammolarni aniqlash va bartaraf etish\n"
                f"• Oylik abonent to'lovini tekshirish (STIR / INN bo'yicha)\n"
                f"• Oylik to'lov qilish rekvizitlari va video darsligi\n"
                f"• Yillik Fiskal Modul to'lovini tekshirish (FM raqami bo'yicha)\n"
                f"• Yillik to'lov rekvizitlari va qo'llanmasi\n"
                f"• Mas'ul texnik xodim (admin) bilan bog'lanish\n\n"
                f"Savolingiz yoki murojaatingizni yozib qoldirishingiz mumkin!"
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 1.5. Suhbatni unutish / tozalash (foydalanuvchi suhbatni unutishni so'raganda yoki /reset, /clear yozganda)
        if self.is_forget_or_reset(norm_text) or text.startswith("/reset") or text.startswith("/clear") or ai_intent == "FORGET":
            session_mgr.reset_session(user_id)
            resp = "🔄 Siz bilan bo'lgan avvalgi barcha suhbat ma'lumotlari xotiradan tozalandi va unutilgan holda yangilandi. Yangidan boshlaymiz, sizga qanday yordam bera olaman?"
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # HAR QANDAY VAZIYATDA: agar mijoz INN, JSHSHIR yoki FM raqami yuborgan bo'lsa,
        # darhol birinchi navbatda oylik yoki yillik to'lovni tekshirib beramiz!
        found_inn = self.extract_inn(text)
        found_fm = self.extract_fm(text)

        # Agar bitta raqam adashib ikkalasiga ham tushib qolgan bo'lsa:
        if found_inn and found_fm == found_inn:
            found_fm = None

        if found_inn:
            self.process_inn_check(chat_id, message_id, reply_to_id, session, first_name, username, user_id, text, norm_text, found_inn)
            # Faqat ayni xabarda alohida boshqa FM raqami ham birga yozilgan bo'lsa:
            if found_fm and found_fm != found_inn:
                self.process_fm_check(chat_id, message_id, reply_to_id, session, first_name, username, user_id, text, norm_text, found_fm)
            return

        if found_fm:
            self.process_fm_check(chat_id, message_id, reply_to_id, session, first_name, username, user_id, text, norm_text, found_fm)
            return

        # 1.8. IKPU xatoligi haqida matn yozilgan bo'lsa:
        if self.is_ikpu_error_text(text) or self.is_ikpu_error_text(norm_text) or ai_intent == "IKPU_ERROR":
            session.unclear_count = 0
            session.ikpu_error_active = True
            if getattr(session, "ikpu_video_sent", False):
                # Video allaqachon yuborilgan bo'lsa, istisno tariqasida darrov texnikka ulaymiz!
                self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text, is_ikpu_exception=True)
                return
            else:
                # Birinchi marta: video qo'llanmani avtomatik yuboramiz!
                session.ikpu_video_sent = True
                session_mgr.save_sessions()
                self.send_ikpu_solution_media(chat_id, reply_to_id=reply_to_id)
                return

        # 1.9. Agar avval IKPU videosi yuborilgan bo'lsa va mijoz foydasi bo'lmadi / tuzalmadi / muammo qoldi deb yozsa:
        if getattr(session, "ikpu_error_active", False) and getattr(session, "ikpu_video_sent", False):
            if (self.is_not_resolved_or_complaint(norm_text) or 
                self.is_technician_request(norm_text) or 
                self.is_still_not_working(norm_text, session)):
                session.unclear_count = 0
                self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text, is_ikpu_exception=True)
                return

        # 1.10. Kassa apparati soati yoki vaqti noto'g'ri / soatni to'g'irlash so'rovi:
        if self.is_clock_problem_query(norm_text, text) or ai_intent == "CLOCK_PROBLEM":
            session.unclear_count = 0
            session.clock_video_sent = True
            session_mgr.save_sessions()
            self.send_clock_solution_media(chat_id, reply_to_id=reply_to_id)
            return

        # 1.11. Agar soat bo'yicha parol so'ralsa yoki "parol noto'g'ri" desa:
        if self.is_clock_password_query(norm_text, text):
            session.unclear_count = 0
            session_mgr.save_sessions()
            resp = (
                f"🔐 *Kassa apparatida soatni sozlash parollari:*\n\n"
                f"Agar aparatingiz soatni to'g'irlash jarayonida parol so'rasa yoki *«Parol noto'g'ri»* desa, quyidagi parollarni terib ko'ring:\n"
                f"1️⃣ `12341234`\n"
                f"2️⃣ `123498765`\n\n"
                f"ℹ️ *Eslatma:* Agar ikkala parol ham to'g'ri kelmasa yoki boshqa xatolik bersa, bemalol xabar qoldiring — sizga texnik xodimimiz yordam beradi."
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 1.12. 406 yoki Day Limit (oflayn rejim / 36889) xatoligi haqida matn yozilgan bo'lsa:
        if self.is_offline_limit_error(text) or self.is_offline_limit_error(norm_text):
            session.unclear_count = 0
            session.offline_limit_error_active = True
            session_mgr.save_sessions()

            # 1) Agar yillikdan qarzdor bo'lsa:
            if session.fm_holat == "qarzdor":
                resp = (
                    f"⚠️ Kassa aparatingiz ishlashi uchun yillik fiskal modul to'lovini amalga oshirishingiz lozim. "
                    f"To'lov amalga oshirilgach apparat faoliyati tiklanadi.\n\n"
                    f"To'lov qilish bo'yicha video qo'llanma va hisob raqam rekvizitini yubormoqdaman 👇"
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                self.send_yearly_payment_media(chat_id, reply_to_id=reply_to_id)
                return

            # 2) Agar oylikdan qarzdor bo'lsa:
            if session.oylik_holat == "qarzdor":
                resp = (
                    f"⚠️ Kassa aparatingiz ishlashi uchun oylik abonent to'lovidan qarzdorlikni to'lashingiz lozim.\n\n"
                    f"To'lov qilish bo'yicha hisob raqam rekvizitini yubormoqdaman 👇"
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                self.send_monthly_payment_media(chat_id, reply_to_id=reply_to_id)
                return

            # 3) Agar ikkalasi ham toza bo'lsa:
            if session.fm_holat == "toza" and session.oylik_holat == "toza":
                if getattr(session, "last_photo_file_id", None):
                    self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text)
                    return
                else:
                    resp = (
                        f"✅ *Kassa aparatingizning oylik va yillik to'lovlarida qarzdorlik yo'q (ikkalasi ham toza).*\n\n"
                        f"📷 Ekranda ko'rsatilayotgan ushbu nosozlikni bartaraf etish uchun mas'ul texnik mutaxassisimizga yetkazishimiz lozim. "
                        f"Iltimos, aparat ekranidagi xatolikni (soat va interneti ko'ringan holda) **rasmga olib yuboring** — darhol texnikka ulaymiz."
                    )
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                    return

            # 4) Agar yillik toza, lekin oylik hali tekshirilmagan bo'lsa:
            if session.fm_holat == "toza" and session.oylik_holat != "toza":
                resp = (
                    f"✅ *Yillik fiskal modul to'lovingiz toza (qarzdorlik yo'q).*\n\n"
                    f"🔍 Kassa apparatingizdagi ushbu xatolik bo'yicha mas'ul texnik mutaxassisimizga ulashimiz uchun tashkilotingizning **oylik abonent to'lovini** ham tekshirishimiz lozim.\n\n"
                    f"Iltimos, tashkilotingizning 9 xonali *STIR (INN)* yoki 14 xonali *JSHSHIR* raqamini yuboring."
                )
                session.state = "AWAITING_INN"
                session_mgr.save_sessions()
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            # 5) Yillik hali tekshirilmagan bo'lsa -> mijozga tushuntirish va yillikni tekshirish tugmasi beriladi
            resp = self.get_offline_limit_explanation_text()
            session.state = "AWAITING_FM"
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id, reply_markup=self.get_offline_limit_keyboard())
            return

        # 2. Salomlashish
        if self.is_greeting(norm_text) or ai_intent == "GREETING":
            session.unclear_count = 0
            session_mgr.save_sessions()
            resp = (
                f"Assalomu alaykum! Men *{config.COMPANY_NAME}* ning kassa apparatlariga (SmartOne / P3) texnik xizmat ko'rsatuvchi rasmiy botiman.\n\n"
                f"Vazifam — kassa apparatingiz ishlashini, oylik abonent va yillik fiskal modul to'lovlarini tekshirish hamda to'lov rekvizitlarini taqdim etish.\n\n"
                f"Sizga qanday yordam kerak?"
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 2.5. Bot kimligi, vazifasi yoki nima qila olishi haqida so'ralganda
        if self.is_bot_intro_query(norm_text):
            session.unclear_count = 0
            session_mgr.save_sessions()
            resp = self.get_duty_explanation_text(session)
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 3. Admin / Texnik bilan bog'lanish yoki "Baribir ishlamayapti" murojaatlari
        # A) Agar ma'lumotlar allaqachon texnikka yetkazilgan bo'lsa va javob kutilayotgan bo'lsa:
        if session.state == "ADMIN_BOGLANISH" and (self.is_technician_request(norm_text) or self.is_still_not_working(norm_text, session) or any(w in norm_text for w in ["admin", "texnik", "qachon", "javob", "kutayapman", "kutib", "alo", "tezroq", "nima boldi", "nima bo'ldi", "kutaman", "kutib turaymi"])):
            resp = (
                f"👨‍💻 *Iltimos, kutib turing!*\n\n"
                f"Ma'lumotlaringiz allaqachon mas'ul texnik mutaxassisimizga yetkazilgan. "
                f"Mutaxassisimiz tez orada vaziyatni o'rganib chiqib sizga javob beradi yoki siz bilan bog'lanadi. Sabr qilishingizni so'raymiz!"
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        if self.is_technician_request(norm_text) or self.is_still_not_working(norm_text, session) or ai_intent == "OPERATOR":
            # Mijoz rasm tashlamagan bo'lsa, hech qanday holatda texnikka bog'lanmaydi
            if not getattr(session, "last_photo_file_id", None):
                resp = "Agar aparatingiz baribir ishlamayotgan bo'lsa, aparat ekrani to'liq ko'ringan holda rasm olib tashlang men sizni masul texnik bilan bog'layman."
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                return

            self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text)
            return

        # 3.7. Agar avval rekvizit so'ralib, oylik yoki yillik tanlashi kutilayotgan bo'lsa
        if session.state == "AWAITING_REKVIZIT_CHOICE":
            # Oylik tanlansa
            if any(w in norm_text for w in ["oylik", "1", "bir", "birinchi", "abonent"]):
                session.state = "NORMAL"
                session.unclear_count = 0
                session_mgr.save_sessions()
                self.send_monthly_payment_media(chat_id, reply_to_id=reply_to_id)
                return
            # Yillik tanlansa
            elif any(w in norm_text for w in ["yillik", "2", "ikki", "ikkinchi", "fiskal", "modul", "fm"]):
                session.state = "NORMAL"
                session.unclear_count = 0
                session_mgr.save_sessions()
                self.send_yearly_payment_media(chat_id, reply_to_id=reply_to_id)
                return

        # 3.75. Yagona darcha / Davlat xizmatlari markazi bo'yicha murojaat (tel raqami, bog'lash va h.k.)
        if self.is_yagona_darcha_query(norm_text, session):
            session.unclear_count = 0
            session_mgr.save_sessions()
            resp = self.get_duty_explanation_text(session)
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 3.8. Shunchaki "rekvizit" / "rekvizet" deb so'ralganda (oylik yoki yillik ekanligini so'rash)
        if self.is_general_rekvizit_query(norm_text) or ai_intent == "GENERAL_REKVIZIT":
            session.unclear_count = 0
            resp = (
                f"💳 *Sizga qaysi to'lov rekviziti kerak?*\n\n"
                f"1️⃣ *Oylik abonent to'lovi* rekviziti\n"
                f"2️⃣ *Yillik Fiskal Modul (FM)* to'lovi rekviziti\n\n"
                f"Iltimos, *[Oylik to'lov rekviziti]* yoki *[Yillik to'lov rekviziti]* deb yozing."
            )
            session.state = "AWAITING_REKVIZIT_CHOICE"
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 3.9. Mijoz to'lov amalga oshirganligini bildirsa (to'ladim, to'lov qildim, pul o'tkazdim va h.k.) -> Faqat to'lov kvitansiyasini so'rash
        if self.is_payment_made_notification(norm_text) or ai_intent == "PAYMENT_MADE":
            session.unclear_count = 0
            session.state = "AWAITING_RECEIPT"
            session_mgr.save_sessions()
            resp = (
                f"🧾 *To'lovingizni hisobga olishimiz uchun, iltimos, to'lov kvitansiyasini (chek rasmi yoki PDF shaklida) yuboring.*"
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 4. Oylar kesimida to'lovlar tarixi / qaysi oylar to'langanligi hisoboti (tarix so'ralganda yoki to'lovdan norozilik bildirilganda)
        if self.is_payment_history_query(norm_text, session) or ai_intent == "PAYMENT_HISTORY":
            session.unclear_count = 0
            inn_to_use = session.inn or self.extract_inn(text)
            if inn_to_use:
                info = excel_service.find_by_identifier(inn_to_use)
                if info:
                    resp = excel_service.get_payment_history_text(info)
                    session_mgr.save_sessions()
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                    return

            resp = (
                f"Yil davomida qaysi oylar uchun qancha to'lov qilinganligini tekshirish uchun "
                f"tashkilotingizning INN yoki JSHSHIR raqamini yuboring.\n\n"
                f"ℹ️ *Ma'lumot uchun:* Tashkilotingiz INN yoki JSHSHIR raqami aparatingiz chiqargan chekda *STIR* deb yozilgan bo'limida ko'rsatilgan."
            )
            session.state = "AWAITING_INN_HISTORY"
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 5. Oylik to'lovni TO'LASH / REKVIZIT / QANDAY TO'LASH so'rovi (Click video va rekviziti)
        if self.is_monthly_pay_info(norm_text, session=session) or ai_intent == "PAY_MONTHLY":
            session.state = "NORMAL"
            session.unclear_count = 0
            session.last_topic = "pay_monthly"
            session_mgr.save_sessions()
            self.send_monthly_payment_media(chat_id, reply_to_id=reply_to_id)
            return

        # 6. Yillik to'lovni TO'LASH / REKVIZIT / QANDAY TO'LASH so'rovi (video va rekvizit)
        if self.is_yearly_pay_info(norm_text, session=session) or ai_intent == "PAY_YEARLY":
            session.state = "NORMAL"
            session.unclear_count = 0
            session.last_topic = "pay_yearly"
            session_mgr.save_sessions()
            self.send_yearly_payment_media(chat_id, reply_to_id=reply_to_id)
            return

        # 7. Oylik to'lovni TEKSHIRISH so'rovi (qancha qarzdorlik borligini bilish)
        if self.is_monthly_check_query(norm_text) or ai_intent == "CHECK_MONTHLY":
            session.unclear_count = 0
            session.last_topic = "check_monthly"
            resp = (
                f"Tashkilotingizning INN yoki JSHSHIR raqamini yuboring.\n\n"
                f"ℹ️ *Ma'lumot uchun:* Tashkilotingiz INN yoki JSHSHIR raqami aparatingiz chiqargan chekda *STIR* deb yozilgan bo'limida ko'rsatilgan."
            )
            session.state = "AWAITING_INN"
            session.last_intent = "check_monthly"
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 8. Yillik to'lovni TEKSHIRISH so'rovi (fiskal modul muddatini bilish)
        if self.is_yearly_check_query(norm_text) or ai_intent == "CHECK_YEARLY":
            session.unclear_count = 0
            session.last_topic = "check_yearly"
            resp = (
                f"Yillik fiskal modul to'lovingizni tekshirib berishimni istasangiz, aparatingizning fiskal modul raqamini yuboring.\n\n"
                f"ℹ️ *Ma'lumot uchun:* Fiskal modul raqami aparatingiz chiqargan chekning pastki qismida *FM raqami* deb yozilgan bo'limda ko'rsatiladi."
            )
            session.state = "AWAITING_FM"
            session.last_intent = "check_yearly"
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 8.5. Aparat ishlamayapti / o'chibdi / ko'rib bering / nosozlik
        if self.is_pos_problem(norm_text) or ai_intent == "POS_BROKEN":
            session.unclear_count = 0
            session.last_intent = "pos_broken"

            # A) Agar oylik abonentdan qarzi bo'lsa
            if session.oylik_holat == "qarzdor":
                resp = (
                    f"⚠️ Kassa aparatingiz ishlashi uchun avvalo mavjud oylik abonent qarzdorligini to'lashingiz lozim. "
                    f"To'lov amalga oshirilgach apparat faoliyati tiklanadi.\n\n"
                    f"To'lov qilish bo'yicha video qo'llanma va hisob raqam rekvizitini yubormoqdaman:"
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                self.send_monthly_payment_media(chat_id, reply_to_id=reply_to_id)
                session_mgr.save_sessions()
                return

            # B) Agar yillik fiskal moduldan qarzdor bo'lsa
            if session.fm_holat == "qarzdor":
                resp = (
                    f"⚠️ Kassa aparatingiz ishlashi uchun yillik fiskal modul to'lovini amalga oshirishingiz lozim. "
                    f"To'lov amalga oshirilgach apparat faoliyati tiklanadi.\n\n"
                    f"To'lov qilish bo'yicha video qo'llanma va hisob raqam rekvizitini yubormoqdaman:"
                )
                self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                self.send_yearly_payment_media(chat_id, reply_to_id=reply_to_id)
                session_mgr.save_sessions()
                return

            # C) Agar oylik toza bo'lsa
            if session.oylik_holat == "toza":
                if getattr(session, "last_photo_file_id", None):
                    self.notify_technician(chat_id, message_id, session, first_name, username, user_id, text)
                    return
                else:
                    resp = (
                        f"✅ *Kassa aparatingizning oylik abonent to'lovida qarzdorlik yo'q, aparatingiz oylik abonent tomonlama faol holatda.*\n\n"
                        f"📷 Sizni mas'ul texnik mutaxassisimiz bilan bog'lashimiz uchun kassa apparatingiz chiqargan xatolikni aparat ekrani to'liq ko'ringan holda (tepasidagi soat va interneti bilan) **rasmga olib yuboring**."
                    )
                    self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
                    session_mgr.save_sessions()
                    return

            # E) Agar hali INN / oylik tekshirilmagan bo'lsa
            resp = (
                f"Aparatingiz ishlamayotganining sababini aniqlab ko'rishim uchun tashkilotingizning 9 xonali STIR (INN) yoki 14 xonali JSHSHIR raqamini yuboring.\n\n"
                f"ℹ️ *Ma'lumot uchun:* Tashkilotingiz INN yoki JSHSHIR raqami kassa aparatingiz chiqargan chekning pastki qismida *STIR* deb yozilgan bo'limda ko'rsatilgan bo'ladi."
            )
            session.state = "AWAITING_INN"
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        # 9 & 10. Matn ichidagi STIR (INN) yoki FM raqamlari har qanday vaziyatda yuqorida birinchi navbatda avtomatik tekshirildi

        # Agar sessiya kutilayotgan holatda bo'lsa
        if session.state == "AWAITING_RECEIPT":
            session.unclear_count = 0
            session_mgr.save_sessions()
            resp = (
                f"🧾 *To'lovingizni hisobga olishimiz uchun, iltimos, to'lov kvitansiyasini (chek rasmi yoki PDF shaklida) yuboring.*"
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        if session.state == "AWAITING_RECEIPT_INN":
            session.unclear_count = 0
            session_mgr.save_sessions()
            resp = (
                f"🧾 To'lov kvitansiyangizni texnik mutaxassisimizga yetkazishimiz uchun tashkilotingizning 9 xonali *STIR (INN)* yoki 14 xonali *JSHSHIR* raqamini yuboring."
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        if session.state == "AWAITING_INN":
            session.unclear_count = 0
            session_mgr.save_sessions()
            resp = (
                f"Kassa apparatingiz ishlamayotganining sababini aniqlab ko'rishim uchun tashkilotingizning 9 xonali STIR (INN) yoki 14 xonali JSHSHIR raqamini yuboring.\n\n"
                f"ℹ️ *Ma'lumot uchun:* Tashkilotingiz INN yoki JSHSHIR raqami kassa aparatingiz chiqargan chekning pastki qismida *STIR* deb yozilgan bo'limda ko'rsatilgan bo'ladi."
            )
            self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
            return

        if session.state == "AWAITING_FM":
            # Agar mijoz FM raqami o'rniga boshqa narsa yozsa, uni AWAITING_FM dan chiqaramiz va qayta FM talab qilmaymiz
            session.state = "NORMAL"
            session.unclear_count = 0
            session_mgr.save_sessions()

        # 11. Agar sun'iy intellekt (Gemini AI) muloyim va to'liq javob tayyorlagan bo'lsa:
        if ai_result and ai_result.get("ai_reply"):
            session.unclear_count = 0
            session_mgr.save_sessions()
            self.bot.send_message(chat_id, ai_result["ai_reply"], reply_to_message_id=reply_to_id)
            return

        # Bot vazifasiga kirmaydigan boshqa mavzudagi savollar va murojaatlar
        session.unclear_count = 0
        session_mgr.save_sessions()
        resp = (
            f"Kechirasiz, men faqat kassa apparatingizni (SmartOne / P3) tekshirish va texnik xizmat ko'rsatish bo'yicha yordam bera olaman.\n\n"
            f"Kassa apparatingizni tekshirish uchun tashkilotingizning 9 xonali STIR (INN) yoki 14 xonali JSHSHIR raqamini yuboring."
        )
        self.bot.send_message(chat_id, resp, reply_to_message_id=reply_to_id)
        return

    def run(self):
        """Botni ishga tushirish (Long polling)"""
        print("=" * 60)
        print(f"🚀 {config.COMPANY_NAME} Telegram Boti ishga tushdi!")
        print("Telegram guruhda admin qilinganida barcha mijozlarga")
        print("o'z xabarlariga reply tariqasida javob beradi.")
        print("8 soatlik suhbat sessiyalari faol.")
        print("=" * 60)

        # Telegram serveridagi eski kutib qolgan barcha xabarlarni tozalash (drop pending updates)
        try:
            self.bot.api_request("deleteWebhook", {"drop_pending_updates": True})
            print("[POLLING] Telegram serveridagi eski xabarlar navbati tozalandi.")
        except Exception:
            pass

        # Eski xabarlarni tozalash (faqat yangilarini olish)
        updates = self.bot.get_updates(offset=-1, timeout=1)
        if updates.get("ok") and updates["result"]:
            self.bot.offset = updates["result"][-1]["update_id"] + 1

        while True:
            try:
                # 8 soatdan oshgan eski sessiyalarni tozalash
                session_mgr.clean_expired()
                ticket_service.clean_expired()

                updates = self.bot.get_updates(offset=self.bot.offset, timeout=20)
                if not updates.get("ok"):
                    time.sleep(2)
                    continue

                for update in updates.get("result", []):
                    self.bot.offset = update["update_id"] + 1

                    # 1. Telegram kanal posti (yangi fayl yoki tahrirlangan post)
                    channel_post = update.get("channel_post") or update.get("edited_channel_post")
                    if channel_post:
                        self.executor.submit(self._safe_handle_channel_post, channel_post)
                        continue

                    # 2. Guruh yoki shaxsiy chat xabari
                    if "message" in update:
                        self.executor.submit(self._safe_handle_message, update["message"])

                    # 3. Inline tugmalar bosilganda (callback_query)
                    if "callback_query" in update:
                        self.executor.submit(self._safe_handle_callback_query, update["callback_query"])

            except KeyboardInterrupt:
                print("\nBot to'xtatildi.")
                break
            except Exception as e:
                print(f"[EXCEPTION] Asosiy tsiklda xatolik: {e}")
                time.sleep(3)

    def _safe_handle_message(self, message):
        try:
            chat_id = message.get("chat", {}).get("id")
            u_name = message.get("from", {}).get("first_name", "Foydalanuvchi")
            text_preview = (message.get("text") or message.get("caption") or "[Media/Fayl]")[:30]
            print(f"[MSG] Yangi xabar (Chat: {chat_id}, Kimdan: {u_name}): {text_preview}")
            self.handle_message(message)
        except Exception as msg_err:
            print(f"[ERROR] Xabarni ishlashda xatolik: {msg_err}")

    def _safe_handle_callback_query(self, callback_query):
        try:
            self.handle_callback_query(callback_query)
        except Exception as cq_err:
            print(f"[ERROR] Callback query ishlashda xatolik: {cq_err}")

    def _safe_handle_channel_post(self, channel_post):
        try:
            self.handle_channel_post(channel_post)
        except Exception as ch_err:
            print(f"[ERROR] Kanal postini qayta ishlashda xatolik: {ch_err}")


if __name__ == "__main__":
    engine = MarsBotEngine()
    engine.run()
