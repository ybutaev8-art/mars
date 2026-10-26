import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from bot import MarsBotEngine

engine = MarsBotEngine()

class MockBot:
    def __init__(self):
        self.sent = []
    def send_message(self, chat_id, text, reply_to_message_id=None, parse_mode="Markdown", reply_markup=None):
        self.sent.append(text)
        return {"ok": True}

engine.bot = MockBot()

# 1. Quvonchbek INN tekshiradi
print("=== 1. Quvonchbek INN (312420017) tekshiradi ===")
msg1 = {
    "message_id": 100,
    "chat": {"id": -1001234567, "type": "supergroup"},
    "from": {"id": 999, "first_name": "Quvonchbek", "username": "quvonchbek"},
    "text": "312420017"
}
engine.handle_message(msg1)
print(engine.bot.sent[-1][:200] + "...\n")

# 2. Quvonchbek aynan rasmda yozgan matnni yozadi:
print("=== 2. Quvonchbek yozadi: 'oylikka kiyingi oy uchunam tulab quyudimku' ===")
msg2 = {
    "message_id": 101,
    "chat": {"id": -1001234567, "type": "supergroup"},
    "from": {"id": 999, "first_name": "Quvonchbek", "username": "quvonchbek"},
    "text": "oylikka kiyingi oy uchunam tulab quyudimku"
}
engine.handle_message(msg2)
res_text = engine.bot.sent[-1]
print("BOTNING JAVOBI:")
print(res_text)

# Tekshiramiz: OFD yoki Fiskal modul deb yubormasligi kerak! To'lovlar tarixini yuborishi kerak!
assert "OFD" not in res_text
assert "Fiskal Modul raqami: OYLIKKAKIYINGI" not in res_text
assert "to'lovlar hisoboti" in res_text or "to'lovlar ro'yxati" in res_text
print("\n TEST MUVAFFAQIYATLI O'TDI! Bot endi so'zlarni FM deb qabul qilmaydi va to'lovlar tarixini chiqaradi!")
