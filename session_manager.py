"""
Suhbat sessiyalarini boshqarish moduli (Har bir mijoz uchun 8 soatlik kontekst)
"""
import os
import json
import time
import threading
from datetime import datetime, timedelta
import config

SESSIONS_FILE = os.path.join(config.DATA_DIR, "sessions.json")

class UserSession:
    def __init__(self, user_id, chat_id=None, first_name="", username=""):
        self.user_id = str(user_id)
        self.chat_id = chat_id
        self.first_name = first_name
        self.username = username
        self.created_at = time.time()
        self.last_activity = time.time()
        self.state = "START"  # START, AWAITING_INN, AWAITING_FM, OYLIK_TOZA, ADMIN_BOGLANISH
        self.inn = None
        self.org_name = None
        self.oylik_qarz = None
        self.oylik_holat = None  # "qarzdor", "toza"
        self.fm_number = None
        self.fm_holat = None    # "qarzdor", "toza", "tekshirildi"
        self.last_intent = None
        self.last_topic = None
        self.unclear_count = 0
        self.last_photo_file_id = None
        self.last_photo_caption = None
        self.last_photo_text = None
        self.last_msg_id = None
        self.ikpu_video_sent = False
        self.ikpu_error_active = False
        self.offline_limit_error_active = False
        self.pending_receipt = None

    def reset_for_new_target(self, preserve_photo=False, preserve_fm=False):
        """Mijoz yangi INN yoki yangi FM kiritganda avvalgi suhbat va aparat xotirasini tozalash (agar preserve_photo=True bo'lsa rasm saqlanadi, preserve_fm=True bo'lsa FM va oflayn xatolik saqlanadi)"""
        saved_pid = self.last_photo_file_id if preserve_photo else None
        saved_pcap = self.last_photo_caption if preserve_photo else None
        saved_ptxt = self.last_photo_text if preserve_photo else None
        saved_mid = self.last_msg_id if preserve_photo else None
        saved_fm = self.fm_number if preserve_fm else None
        saved_fm_h = self.fm_holat if preserve_fm else None
        saved_off = self.offline_limit_error_active if preserve_fm else False

        self.state = "START"
        self.inn = None
        self.org_name = None
        self.oylik_qarz = None
        self.oylik_holat = None
        self.fm_number = saved_fm
        self.fm_holat = saved_fm_h
        self.last_intent = None
        self.last_topic = None
        self.unclear_count = 0
        self.last_photo_file_id = saved_pid
        self.last_photo_caption = saved_pcap
        self.last_photo_text = saved_ptxt
        self.last_msg_id = saved_mid
        self.ikpu_video_sent = False
        self.ikpu_error_active = False
        self.offline_limit_error_active = saved_off
        self.pending_receipt = None
        self.update_activity()

    def update_activity(self):
        self.last_activity = time.time()

    def is_expired(self, ttl_hours=config.SESSION_TTL_HOURS):
        return (time.time() - self.last_activity) > (ttl_hours * 3600)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "first_name": self.first_name,
            "username": self.username,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "state": self.state,
            "inn": self.inn,
            "org_name": self.org_name,
            "oylik_qarz": self.oylik_qarz,
            "oylik_holat": self.oylik_holat,
            "fm_number": self.fm_number,
            "fm_holat": self.fm_holat,
            "last_intent": self.last_intent,
            "last_topic": getattr(self, "last_topic", None),
            "unclear_count": getattr(self, "unclear_count", 0),
            "last_photo_file_id": getattr(self, "last_photo_file_id", None),
            "last_photo_caption": getattr(self, "last_photo_caption", None),
            "last_msg_id": getattr(self, "last_msg_id", None),
            "ikpu_video_sent": getattr(self, "ikpu_video_sent", False),
            "ikpu_error_active": getattr(self, "ikpu_error_active", False),
            "offline_limit_error_active": getattr(self, "offline_limit_error_active", False),
            "pending_receipt": getattr(self, "pending_receipt", None),
        }

    @classmethod
    def from_dict(cls, data):
        session = cls(data.get("user_id"), data.get("chat_id"), data.get("first_name", ""), data.get("username", ""))
        session.created_at = data.get("created_at", time.time())
        session.last_activity = data.get("last_activity", time.time())
        session.state = data.get("state", "START")
        session.inn = data.get("inn")
        session.org_name = data.get("org_name")
        session.unclear_count = data.get("unclear_count", 0)
        session.oylik_qarz = data.get("oylik_qarz")
        session.oylik_holat = data.get("oylik_holat")
        session.fm_number = data.get("fm_number")
        session.fm_holat = data.get("fm_holat")
        session.last_intent = data.get("last_intent")
        session.last_topic = data.get("last_topic")
        session.last_photo_file_id = data.get("last_photo_file_id")
        session.last_photo_caption = data.get("last_photo_caption")
        session.last_msg_id = data.get("last_msg_id")
        session.ikpu_video_sent = data.get("ikpu_video_sent", False)
        session.ikpu_error_active = data.get("ikpu_error_active", False)
        session.offline_limit_error_active = data.get("offline_limit_error_active", False)
        session.pending_receipt = data.get("pending_receipt")
        return session


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self._lock = threading.Lock()
        self.load_sessions()

    def get_session(self, user_id, chat_id=None, first_name="", username=""):
        user_key = str(user_id)
        with self._lock:
            session = self.sessions.get(user_key)
            
            # Agar mavjud bo'lmasa yoki 8 soatdan oshgan bo'lsa yangilaymiz
            if not session or session.is_expired():
                session = UserSession(user_id, chat_id, first_name, username)
                self.sessions[user_key] = session
            else:
                session.update_activity()
                if chat_id:
                    session.chat_id = chat_id
                if first_name:
                    session.first_name = first_name
                if username:
                    session.username = username
                    
            self.save_sessions_unlocked()
            return session

    def reset_session(self, user_id):
        user_key = str(user_id)
        with self._lock:
            if user_key in self.sessions:
                del self.sessions[user_key]
                self.save_sessions_unlocked()

    def clean_expired(self):
        with self._lock:
            expired_keys = [k for k, s in self.sessions.items() if s.is_expired()]
            for k in expired_keys:
                del self.sessions[k]
            if expired_keys:
                self.save_sessions_unlocked()

    def reset_all(self):
        with self._lock:
            self.sessions = {}
            self.save_sessions_unlocked()
            print("[SESSIONS] Barcha sessiyalar to'liq tozalandi.")

    def save_sessions_unlocked(self):
        try:
            os.makedirs(os.path.dirname(SESSIONS_FILE), exist_ok=True)
            data = {k: s.to_dict() for k, s in self.sessions.items()}
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] Sessiyani saqlashda xatolik: {e}")

    def save_sessions(self):
        with self._lock:
            self.save_sessions_unlocked()

    def load_sessions(self):
        if not os.path.exists(SESSIONS_FILE):
            return
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                for k, v in data.items():
                    sess = UserSession.from_dict(v)
                    if not sess.is_expired():
                        self.sessions[k] = sess
        except Exception as e:
            print(f"[ERROR] Sessiyalarni yuklashda xatolik: {e}")

# Global sessiya menejeri
session_mgr = SessionManager()
