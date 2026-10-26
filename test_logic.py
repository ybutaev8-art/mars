"""
Mantiqiy testlar skripti
Botning barcha ssenariylarini Telegramsiz lokal ravishda tekshirish
"""
import sys
import os

# UTF-8 chiqish
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Loyiha papkasini yo'lga qo'shamiz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import MarsBotEngine
from session_manager import session_mgr
from excel_service import excel_service
from ofd_service import ofd_service

engine = MarsBotEngine()

class MockBot:
    def __init__(self):
        self.sent_messages = []

    def send_message(self, chat_id, text, reply_to_message_id=None, parse_mode="Markdown", reply_markup=None):
        self.sent_messages.append({
            "chat_id": chat_id,
            "text": text,
            "reply_to": reply_to_message_id
        })
        return {"ok": True}

    def copy_message(self, chat_id, from_chat_id, message_id, caption=None, reply_to_message_id=None, **kwargs):
        self.sent_messages.append({
            "chat_id": chat_id,
            "text": caption or f"fiskal modul video darslik va rekvizitlar (post #{message_id})",
            "reply_to": reply_to_message_id
        })
        return {"ok": True}

# Bot obyektini almashtiramiz
mock_bot = MockBot()
engine.bot = mock_bot

def simulate_msg(user_id, text, msg_id=1, first_name="Ali"):
    mock_bot.sent_messages.clear()
    msg = {
        "message_id": msg_id,
        "chat": {"id": -1001234567, "type": "supergroup"},
        "from": {"id": user_id, "first_name": first_name, "username": f"user_{user_id}"},
        "text": text
    }
    engine.handle_message(msg)
    return mock_bot.sent_messages[-1] if mock_bot.sent_messages else None

print("=== 1. Salomlashish testi ===")
res = simulate_msg(101, "salom", 1)
print(f"Mijoz: salom\nBot (reply_to={res['reply_to']}):\n{res['text']}\n")
assert "MARS ELEKTRON TEXNIKA MCHJ ning texnik hizmat kursatuvchi" in res["text"]

print("=== 2. Aparatim ishlamayabdi testi ===")
res = simulate_msg(101, "aparatim ishlamayabdi", 2)
print(f"Mijoz: aparatim ishlamayabdi\nBot:\n{res['text']}\n")
assert "Tashkilotingizning INN yoki JSHSHIR raqamini yuboring" in res["text"]
assert "STIR" in res["text"] and "deb yozilgan" in res["text"]

print("=== 3. Oylik to'lovni tekshirish (adashtirmaslik) testi ===")
res = simulate_msg(102, "oylik tolovni tekshirib ber", 3)
print(f"Mijoz: oylik tolovni tekshirib ber\nBot:\n{res['text']}\n")
assert "Tashkilotingizning INN yoki JSHSHIR raqamini yuboring" in res["text"]

print("=== 4. Oylik abonent to'lash (rekvizit va video) testi ===")
res = simulate_msg(103, "oylik abonent tolash", 4)
print(f"Mijoz: oylik abonent tolash\nBot:\n{res['text']}\n")
assert "video darslik" in res["text"].lower()
assert "rekvizitlar" in res["text"].lower()

print("=== 5. Yillik to'lovni tekshirish testi ===")
res = simulate_msg(104, "yilllik tlov tekshir", 5)
print(f"Mijoz: yilllik tlov tekshir\nBot:\n{res['text']}\n")
assert "fiskal modul raqamini yuboring" in res["text"].lower()

print("=== 6. Yillik to'lov to'lash testi ===")
res = simulate_msg(105, "yillik tulov", 6)
print(f"Mijoz: yillik tulov\nBot:\n{res['text']}\n")
assert "video darslik" in res["text"].lower()
assert "fiskal modul" in res["text"].lower()

print("=== 7. Qarzdor INN tekshiruvi (123456789) ===")
res = simulate_msg(106, "123456789", 7)
print(f"Mijoz: 123456789\nBot:\n{res['text']}\n")
assert "qarzdorlik mavjud" in res["text"].lower()

print("=== 8. Qarzi yo'q INN tekshiruvi (987654321) ===")
res = simulate_msg(107, "987654321", 8)
print(f"Mijoz: 987654321\nBot:\n{res['text']}\n")
assert "qarzdorlik mavjud emas" in res["text"].lower()
assert "perezagruska" in res["text"].lower()
assert "feskal modul raqamini yuboring" in res["text"].lower() or "fiskal modul raqamini yuboring" in res["text"].lower()

print("=== 9. FM raqami tekshiruvi (FM987654321098) ===")
res = simulate_msg(107, "FM987654321098", 9)
print(f"Mijoz: FM987654321098\nBot:\n{res['text']}\n")
assert "ofd943bot" in res["text"].lower()

print("=== 10. Aparatim ishlamayabdiku (Admin bilan bog'lash) testi ===")
res = simulate_msg(107, "unda nimaga aparat ishlamayabdi", 10)
print(f"Mijoz: unda nimaga aparat ishlamayabdi\nBot:\n{res['text']}\n")
assert "admin" in res["text"].lower() or "mutaxassis" in res["text"].lower()

print("\n BARCHA TESTLAR MUVAFFAQIYATLI O'TDI!")
