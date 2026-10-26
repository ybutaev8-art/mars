"""
Kengaytirilgan mantiqiy testlar
- Apparatlar soni (nechta qator bo'lsa shuncha)
- Apparat modellari (Sariq -> P3, Oq/Rangsiz -> SmartOne, Qizil -> Ro'yxatdan chiqarilgan)
- To'lovlar (1 apparat = 100 000 so'm, shu oy oxirigacha va yil oxirigacha)
"""
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import MarsBotEngine
from session_manager import session_mgr
from excel_service import excel_service
from ofd_service import ofd_service

# Excel yo'lini .xlsx ga to'g'rilaymiz
excel_service.excel_path = os.path.join(os.path.dirname(__file__), "data", "abonent_jadvali.xlsx")
excel_service.load_data()

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

print("=== TEST 1: 2 ta apparatli tashkilot (123456789 - 1-sariq P3, 2-oq SmartOne, qarzdor) ===")
res = simulate_msg(201, "123456789", 1)
print(f"Javob:\n{res['text']}\n")
assert "2 ta" in res["text"]
assert "P3" in res["text"]
assert "SmartOne" in res["text"]
assert "100 000" in res["text"]
assert "Shu oyning oxirigacha" in res["text"]
assert "Yilning oxirigacha" in res["text"]
assert "qarzdorlik mavjud" in res["text"]

print("=== TEST 2: 1 ta apparatli sariq tashkilot (987654321 - P3, qarzi yo'q) ===")
res = simulate_msg(202, "987654321", 2)
print(f"Javob:\n{res['text']}\n")
assert "1 ta" in res["text"]
assert "P3" in res["text"]
assert "qarzdorlik mavjud emas" in res["text"]
assert "perezagruska" in res["text"]
assert "feskal modul" in res["text"] or "fiskal modul" in res["text"]

print("=== TEST 3: Ro'yxatdan chiqarilgan qizil tashkilot (777888999) ===")
res = simulate_msg(203, "777888999", 3)
print(f"Javob:\n{res['text']}\n")
assert "Ro'yxatdan chiqarilgan" in res["text"]
assert "faoliyati to'xtatilgan" in res["text"]

print("=== TEST 4: SmartOne (rangsiz/oq) tashkilot (305123456) ===")
res = simulate_msg(204, "305123456", 4)
print(f"Javob:\n{res['text']}\n")
assert "SmartOne" in res["text"]

print("\n BARCHA KENGAYTIRILGAN TESTLAR MUVAFFAQIYATLI O'TDI!")
