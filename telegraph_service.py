"""
Telegraph xizmati - Telegram Instant View sahifalari yaratish va yangilash.
Texnik «📂 Barcha medialar va to'liq tarix» tugmasini bosganida Telegram ichida
alohida chiroyli sahifada barcha suhbat va medialarni ko'rsatib beradi.
"""
import urllib.request
import urllib.parse
import json
import time

TELEGRAPH_TOKEN = "a9397364fbc6147b91cf2f86d2d71544e99170fba37b323edea66a998e06"

class TelegraphService:
    def __init__(self, token=TELEGRAPH_TOKEN):
        self.token = token

    def get_telegram_file_url(self, file_id):
        """Telegram fayl ID sidan to'g'ridan-to'g'ri ko'rish havolasini oladi"""
        if not file_id:
            return None
        try:
            import config
            req_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/getFile?file_id={file_id}"
            req = urllib.request.Request(req_url)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                if data.get("ok"):
                    fpath = data["result"]["file_path"]
                    return f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{fpath}"
        except Exception as e:
            print(f"[TELEGRAPH_FILE_URL] Xatolik: {e}")
        return None

    def create_or_update_ticket_page(self, ticket):
        """Mijoz murojaati uchun Telegraph sahifasi yaratadi yoki mavjudini yangilaydi"""
        org_name = ticket.get("org_name", "Noma'lum tashkilot")
        inn = ticket.get("inn", "Ko'rsatilmagan")
        user_id = ticket.get("user_id", "")
        base_card = ticket.get("base_card", "")
        history = ticket.get("history", [])

        title = f"{org_name[:40]} (STIR: {inn})"
        
        content = [
            {"tag": "h3", "children": [f"🏢 {org_name}"]},
            {"tag": "p", "children": [f"📑 STIR / INN: {inn}"]},
            {"tag": "p", "children": [f"💳 Oylik to'lov: {ticket.get('oylik_info', 'Qarzi yo`q')}"]},
            {"tag": "p", "children": [f"📟 Yillik to'lov: {ticket.get('fm_info', 'Tekshirilmagan')}"]},
            {"tag": "p", "children": [f"🆔 Mijoz ID: {user_id}"]}
        ]

        # Dastlabki kassa apparati nosozligi rasmi mavjud bo'lsa
        initial_photo_url = ticket.get("initial_photo_url")
        if not initial_photo_url and ticket.get("last_photo_file_id"):
            initial_photo_url = self.get_telegram_file_url(ticket.get("last_photo_file_id"))
            if initial_photo_url:
                ticket["initial_photo_url"] = initial_photo_url

        if initial_photo_url:
            content.append({"tag": "hr"})
            content.append({"tag": "h4", "children": ["📷 Kassa aparati nosozlik rasmi:"]})
            content.append({"tag": "img", "attrs": {"src": initial_photo_url}})

        content.append({"tag": "hr"})
        content.append({"tag": "h4", "children": ["📋 Murojaat va yozishmalar to'liq tarixi:"]})

        if not history:
            content.append({"tag": "p", "children": ["ℹ️ Yangi murojaat ochildi, texnik mutaxassis javobi kutilmoqda."]})
        else:
            for item in history:
                sender = item.get("sender")
                num = item.get("num", 1)
                text = item.get("text", "").strip()
                t_str = time.strftime("%H:%M:%S", time.localtime(item.get("time", time.time())))
                
                m_url = item.get("media_url")
                if not m_url and item.get("file_id"):
                    m_url = self.get_telegram_file_url(item.get("file_id"))
                    if m_url:
                        item["media_url"] = m_url
                m_type = item.get("media_type")

                if sender == "client":
                    p_children = [
                        {"tag": "b", "children": [f"💬 Mijoz (Xabar {num} - {t_str}):"]},
                        {"tag": "br"},
                        text
                    ]
                    content.append({"tag": "p", "children": p_children})
                    if m_url:
                        if m_type == "photo":
                            content.append({"tag": "img", "attrs": {"src": m_url}})
                        elif m_type == "video":
                            content.append({"tag": "video", "attrs": {"src": m_url}})
                        elif m_type == "voice":
                            content.append({"tag": "p", "children": [
                                {"tag": "a", "attrs": {"href": m_url}, "children": ["▶️ Ovozli xabarni yuklab tinglash"]}
                            ]})
                elif sender == "tech":
                    content.append({"tag": "p", "children": [
                        {"tag": "b", "children": [f"👨‍💻 Texnik mutaxassis (Javob {num} - {t_str}):"]},
                        {"tag": "br"},
                        text
                    ]})

        content.append({"tag": "hr"})
        content.append({"tag": "p", "children": [f"🕒 Oxirgi yangilanish: {time.strftime('%d.%m.%Y %H:%M:%S')}"]})

        page_path = ticket.get("telegraph_path")
        
        try:
            if page_path:
                # Mavjud sahifani tahrirlaymiz
                payload = {
                    "access_token": self.token,
                    "path": page_path,
                    "title": title,
                    "content": json.dumps(content),
                    "author_name": "MARS ELEKTRON TEXNIKA"
                }
                data = urllib.parse.urlencode(payload).encode("utf-8")
                req = urllib.request.Request("https://api.telegra.ph/editPage", data=data)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res = json.loads(resp.read().decode())
                    if res.get("ok"):
                        return res["result"]["url"]

            # Yangi sahifa ochamiz
            payload = {
                "access_token": self.token,
                "title": title,
                "content": json.dumps(content),
                "author_name": "MARS ELEKTRON TEXNIKA"
            }
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request("https://api.telegra.ph/createPage", data=data)
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode())
                if res.get("ok"):
                    ticket["telegraph_path"] = res["result"]["path"]
                    ticket["telegraph_url"] = res["result"]["url"]
                    return res["result"]["url"]
        except Exception as e:
            print(f"[TELEGRAPH] Sahifa yaratishda xatolik: {e}")
            return None

telegraph_service = TelegraphService()
