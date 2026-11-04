"""
Texnik va mijoz o'rtasidagi murojaatlar (Tickets) xizmati.
Yagona jonli kartochka (Single Live Ticket Card) tizimi:
- Mijozning barcha qo'shimcha xabarlari (1, 2, ...) va texnikning javoblari (1, 2, ...)
  bitta xabarni (kartochkani) tahrirlash orqali to'ldirib boriladi.
- 1 ta texnik bir vaqtning o'zida bir nechta mijoz bilan chalkashmasdan ishlay oladi.
- «📂 Barcha medialar va to'liq tarix» tugmasi orqali Telegraph Instant View sahifasi ochiladi.
"""
import os
import json
import time
import config
from telegraph_service import telegraph_service

TICKETS_FILE = os.path.join(config.DATA_DIR, "tickets.json")

class TicketService:
    def __init__(self):
        self.tickets = {}      # tech_msg_id -> ticket_data
        self.user_tickets = {} # user_id -> ticket_data
        self.load_tickets()

    def load_tickets(self):
        if os.path.exists(TICKETS_FILE):
            try:
                with open(TICKETS_FILE, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    self.tickets = data.get("by_msg_id", {})
                    self.user_tickets = data.get("by_user_id", {})
            except Exception as e:
                print(f"[TICKETS] Faylni o'qishda xatolik: {e}")

    def save_tickets(self):
        try:
            with open(TICKETS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "by_msg_id": self.tickets,
                    "by_user_id": self.user_tickets
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[TICKETS] Faylni saqlashda xatolik: {e}")

    def register_ticket(self, tech_msg_id, client_data, base_card=None, admin_messages=None):
        """Texnikka yuborilgan chaqiruv xabari ID si va mijoz ma'lumotlarini bog'lash"""
        user_id = str(client_data.get("user_id"))
        ticket = self.user_tickets.get(user_id, {})
        
        # Mijoz ma'lumotlarini yangilaymiz
        for k, v in client_data.items():
            ticket[k] = v
        ticket["user_id"] = user_id
        
        if base_card:
            ticket["base_card"] = base_card.strip()
        elif "base_card" not in ticket:
            ticket["base_card"] = (
                f"🏢 Tashkilot: {ticket.get('org_name', 'Mavjud emas')}\n"
                f"📑 INN / JSHSHIR: `{ticket.get('inn', 'Ko`rsatilmagan')}`\n"
                f"💳 Oylik to'lov: {ticket.get('oylik_info', 'Tekshirilmagan')}\n"
                f"📟 Yillik to'lov: {ticket.get('fm_info', 'Tekshirilmagan')}\n"
                f"🆔 `{user_id}`"
            )
            
        if "history" not in ticket:
            ticket["history"] = []
        if "client_count" not in ticket:
            ticket["client_count"] = 0
        if "tech_count" not in ticket:
            ticket["tech_count"] = 0
            
        existing_admin_msgs = ticket.get("admin_messages", [])
        if admin_messages:
            for am in admin_messages:
                if am not in existing_admin_msgs:
                    existing_admin_msgs.append(am)
        ticket["admin_messages"] = existing_admin_msgs
        ticket["last_updated"] = time.time()
        
        # Telegraph sahifasini sinxronlashtiramiz
        try:
            tg_url = telegraph_service.create_or_update_ticket_page(ticket)
            if tg_url:
                ticket["telegraph_url"] = tg_url
        except Exception as tg_err:
            print(f"[TELEGRAPH_SYNC] Xatolik: {tg_err}")

        self.user_tickets[user_id] = ticket
        if tech_msg_id:
            self.tickets[str(tech_msg_id)] = ticket
        if admin_messages:
            for am in admin_messages:
                mid = am.get("message_id")
                if mid:
                    self.tickets[str(mid)] = ticket
                    
        self.save_tickets()
        return ticket

    def add_client_message(self, user_id, text, media_type=None, media_url=None, file_id=None, chat_id=None, message_id=None):
        """Mijoz yangi xabar yuborganda kartochka tarixiga qo'shimcha xabar N sifatida qo'shish"""
        ticket = self.find_ticket_by_user_id(user_id)
        if not ticket:
            return None
        if chat_id:
            ticket["chat_id"] = chat_id
        if message_id:
            ticket["message_id"] = message_id
        ticket["client_count"] = ticket.get("client_count", 0) + 1
        num = ticket["client_count"]
        
        prefix = ""
        if media_type == "photo":
            prefix = "📷 "
        elif media_type == "voice":
            prefix = "🎤 "
        elif media_type == "video":
            prefix = "📹 "
        elif media_type == "document":
            prefix = "📁 "
            
        clean_text = f"{prefix}{text}".strip()
        hist_item = {
            "sender": "client",
            "num": num,
            "text": clean_text,
            "time": time.time(),
            "media_type": media_type
        }
        if media_url:
            hist_item["media_url"] = media_url
        if file_id:
            hist_item["file_id"] = file_id

        ticket.setdefault("history", []).append(hist_item)
        ticket["last_updated"] = time.time()
        
        # Telegraph sahifasini yangilaymiz
        try:
            tg_url = telegraph_service.create_or_update_ticket_page(ticket)
            if tg_url:
                ticket["telegraph_url"] = tg_url
        except Exception:
            pass

        self.save_tickets()
        return ticket

    def add_tech_response(self, user_id, text, media_type=None):
        """Texnik javob qaytarganda kartochka tarixiga javob N sifatida qo'shish"""
        ticket = self.find_ticket_by_user_id(user_id)
        if not ticket:
            return None
        ticket["tech_count"] = ticket.get("tech_count", 0) + 1
        num = ticket["tech_count"]
        
        prefix = ""
        if media_type == "photo":
            prefix = "📷 "
        elif media_type == "voice":
            prefix = "🎤 "
        elif media_type == "video":
            prefix = "📹 "
        elif media_type == "document":
            prefix = "📁 "
            
        clean_text = f"{prefix}{text}".strip()
        ticket.setdefault("history", []).append({
            "sender": "tech",
            "num": num,
            "text": clean_text,
            "time": time.time()
        })
        ticket["last_updated"] = time.time()
        
        # Telegraph sahifasini yangilaymiz
        try:
            tg_url = telegraph_service.create_or_update_ticket_page(ticket)
            if tg_url:
                ticket["telegraph_url"] = tg_url
        except Exception:
            pass

        self.save_tickets()
        return ticket

    def get_keyboard(self, ticket):
        """Kartochka tagiga «📂 Barcha medialar va to'liq tarix» tugmasini qaytaradi"""
        if isinstance(ticket, (str, int)):
            ticket = self.find_ticket_by_user_id(ticket)
        if not ticket:
            return None
        url = ticket.get("telegraph_url")
        user_id = ticket.get("user_id")
        if url:
            return {
                "inline_keyboard": [
                    [{"text": "📂 Barcha medialar va to'liq tarix", "url": url}]
                ]
            }
        elif user_id:
            return {
                "inline_keyboard": [
                    [{"text": "📂 Barcha medialar va to'liq tarix", "callback_data": f"view_history_{user_id}"}]
                ]
            }
        return None

    def get_channel_keyboard(self, ticket):
        """Telegram kanal postida tabiiy 'Fikr bildirish' paneli chiqishi uchun xabarga bot tugmasi qo'shilmaydi"""
        return None

    def is_tech_authorized(self, ticket, user_id):
        """Ushbu texnik murojaatga biriktirilganmi (yoki murojaatni qabul qilganmi) tekshirish"""
        if not ticket or not user_id:
            return False
        user_str = str(user_id)
        c_by = ticket.get("claimed_by")
        if c_by and str(c_by.get("user_id")) == user_str:
            return True
        for t in ticket.get("claimed_techs", []):
            if str(t.get("user_id")) == user_str:
                return True
        return False

    def add_technician_to_ticket(self, ticket, user_id, tech_name, tech_username):
        """Murojaatga yangi texnik mutaxassisni qo'shish (/davomettirish)"""
        if isinstance(ticket, (str, int)):
            ticket = self.find_ticket_by_user_id(ticket)
        if not ticket:
            return False

        techs = ticket.setdefault("claimed_techs", [])
        c_by = ticket.get("claimed_by")
        if c_by and not any(str(t.get("user_id")) == str(c_by.get("user_id")) for t in techs):
            techs.append(c_by)

        user_str = str(user_id)
        if not any(str(t.get("user_id")) == user_str for t in techs):
            new_tech = {
                "user_id": user_id,
                "name": tech_name,
                "username": tech_username,
                "time": time.time()
            }
            techs.append(new_tech)
            if not ticket.get("claimed_by"):
                ticket["claimed_by"] = new_tech
            self.save_tickets()
            return True
        return True

    def format_channel_card(self, ticket):
        """Kanalga yuboriladigan kartochka matni (texniklar nomi va holati bilan)"""
        if isinstance(ticket, (str, int)):
            ticket = self.find_ticket_by_user_id(ticket)
        if not ticket:
            return ""
        base = ticket.get("base_card", "").strip()
        claimed_techs = ticket.get("claimed_techs", [])
        claimed_by = ticket.get("claimed_by")
        if not claimed_techs and claimed_by:
            claimed_techs = [claimed_by]

        if claimed_techs:
            tech_names = []
            for t in claimed_techs:
                t_name = t.get("name", "Texnik")
                username = t.get("username")
                u_str = f" (@{username})" if username else ""
                tech_names.append(f"{t_name}{u_str}")
            tech_str = ", ".join(tech_names)
            label = "Mas'ul mutaxassislar" if len(claimed_techs) > 1 else "Mas'ul mutaxassis"
            return f"{base}\n\n━━━━━━━━━━━━━━━━━━━━\n👨‍💻 *{label}:* {tech_str}\n✅ *Holat:* Qabul qilindi"
        else:
            return f"{base}\n\n━━━━━━━━━━━━━━━━━━━━\n⏳ *Holat:* Kutilmoqda (Qabul qilinmagan)\n💬 _Murojaatni qabul qilish uchun pastdagi «Fikr bildirish»ga kirib «+» yuboring._"

    def find_ticket_by_channel_msg_id(self, chan_msg_id):
        """Kanal xabari ID si bo'yicha tiketni topish"""
        if not chan_msg_id:
            return None
        str_id = str(chan_msg_id)
        for ticket in self.user_tickets.values():
            if str(ticket.get("channel_message_id")) == str_id:
                if ticket.get("status") == "closed":
                    return None
                return ticket
        return None

    def find_ticket_by_discussion_id(self, disc_id):
        """Muhokama guruhi xabari / mavzusi ID si bo'yicha tiketni topish"""
        if not disc_id:
            return None
        str_id = str(disc_id)
        for ticket in self.user_tickets.values():
            if str(ticket.get("group_discussion_id")) == str_id:
                if ticket.get("status") == "closed":
                    return None
                return ticket
        t = self.tickets.get(str_id)
        if t and t.get("status") == "closed":
            return None
        return t

    def link_discussion_id(self, chan_msg_id, disc_msg_id):
        """Kanal posti ID si va Muhokama guruhi xabari ID sini o'zaro bog'lash"""
        ticket = self.find_ticket_by_channel_msg_id(chan_msg_id)
        if ticket:
            ticket["group_discussion_id"] = disc_msg_id
            self.tickets[str(disc_msg_id)] = ticket
            self.save_tickets()
            return ticket
        return None

    def format_card(self, ticket, max_len=None):
        """
        Jonli kartochka matnini shakllantiradi:
        Asosiy ma'lumotlar (Tashkilot, INN, Oylik, Yillik, ID)
        ━━━━━━━━━━━━━━━━━━━━
        💬 Qo'shimcha xabar 1: ...
        👨‍💻 Javob 1: ...
        💬 Qo'shimcha xabar 2: ...
        """
        if isinstance(ticket, (str, int)):
            ticket = self.find_ticket_by_user_id(ticket)
        if not ticket:
            return ""
            
        base = ticket.get("base_card", "").strip()
        history = ticket.get("history", [])
        
        if not history:
            return base
            
        entries = []
        for item in history:
            sender = item.get("sender")
            num = item.get("num", 1)
            text = item.get("text", "").strip()
            if sender == "client":
                entries.append(f"💬 *Qo'shimcha xabar {num}:*\n{text}")
            elif sender == "tech":
                entries.append(f"👨‍💻 *Javob {num}:*\n{text}")
                
        header = f"{base}\n\n━━━━━━━━━━━━━━━━━━━━"
        
        if max_len:
            all_body = "\n\n".join(entries)
            candidate = f"{header}\n\n{all_body}"
            if len(candidate) <= max_len:
                return candidate
                
            # Telegram limiti (1024 rasm caption uchun) oshib ketsa, eng so'nggi xabarlarni saqlaymiz:
            trimmed_entries = []
            for e in reversed(entries):
                test_body = "\n\n".join([f"⚠️ _(Oldingi {len(entries) - len(trimmed_entries)} ta xabar saqlangan)_"] + [e] + trimmed_entries)
                if len(f"{header}\n\n{test_body}") > max_len:
                    break
                trimmed_entries.insert(0, e)
            if not trimmed_entries and entries:
                avail = max_len - len(header) - 30
                if avail > 10:
                    trimmed_entries = [entries[-1][:avail] + "..."]
                else:
                    return base[:max_len]
            return f"{header}\n\n" + "\n\n".join(trimmed_entries)
        else:
            return f"{header}\n\n" + "\n\n".join(entries)

    def close_ticket(self, user_id):
        """Murojaatni yopish (arxivlash)"""
        user_id = str(user_id)
        ticket = self.user_tickets.pop(user_id, None)
        if ticket:
            ticket["status"] = "closed"
            # self.tickets lug'atidan ushbu tiketga tegishli barcha murojaat kalitlarini tozalaymiz
            keys_to_remove = [k for k, v in list(self.tickets.items()) if v == ticket or str(v.get("user_id")) == user_id]
            for k in keys_to_remove:
                self.tickets.pop(k, None)
            self.save_tickets()
        return ticket

    def clean_expired(self, max_age_hours=8):
        """8 soatdan oshgan yoki faol bo'lmagan eski tiketlarni tozalash"""
        now = time.time()
        expired_uids = []
        for uid, ticket in list(self.user_tickets.items()):
            last_up = ticket.get("last_updated", 0)
            if now - last_up > max_age_hours * 3600:
                expired_uids.append(uid)
        for uid in expired_uids:
            self.close_ticket(uid)

    def reset_all(self):
        """Barcha murojaatlar va tarixlarni to'liq tozalash (yangi start)"""
        self.tickets = {}
        self.user_tickets = {}
        self.save_tickets()
        print("[TICKETS] Barcha eski tiketlar va suhbatlar to'liq tozalandi.")

    def find_ticket_by_tech_msg(self, tech_msg_id):
        t = self.tickets.get(str(tech_msg_id))
        if t and t.get("status") == "closed":
            return None
        return t

    def find_ticket_by_user_id(self, user_id):
        t = self.user_tickets.get(str(user_id))
        if t and t.get("status") == "closed":
            return None
        return t

ticket_service = TicketService()
