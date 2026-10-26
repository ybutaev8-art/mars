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

# 1. Mijoz INN tekshiradi
print("=== 1. Mijoz INN yuboradi ===")
msg1 = {
    "message_id": 1,
    "chat": {"id": -1001234567, "type": "supergroup"},
    "from": {"id": 555, "first_name": "Vali", "username": "vali"},
    "text": "312420017"
}
engine.handle_message(msg1)
print(engine.bot.sent[-1][:200] + "...\n")

# 2. Keyin mijoz: "qaysi oylarni to'laganman?" deb so'raydi
print("=== 2. Mijoz: 'qaysi oylarni tolaganman?' deb so'raydi ===")
msg2 = {
    "message_id": 2,
    "chat": {"id": -1001234567, "type": "supergroup"},
    "from": {"id": 555, "first_name": "Vali", "username": "vali"},
    "text": "qaysi oylarni tolaganman?"
}
engine.handle_message(msg2)
print(engine.bot.sent[-1])
print("\n" + "="*50 + "\n")

# 3. Yana bir mijoz: "men to'lagandimku nimaga qarz chiqdi" deb yozadi
print("=== 3. Boshqa mijoz: 'men tolaganman nimaga qarz' deb yozadi (avval INN yo'q) ===")
msg3 = {
    "message_id": 3,
    "chat": {"id": -1001234567, "type": "supergroup"},
    "from": {"id": 777, "first_name": "Ali", "username": "ali"},
    "text": "men tolaganman nimaga qarz chiqdi?"
}
engine.handle_message(msg3)
print(engine.bot.sent[-1])
print("\n" + "="*50 + "\n")

# 4. Ali o'z INN sini yuboradi
print("=== 4. Ali o'z INN sini (312420017) yuboradi ===")
msg4 = {
    "message_id": 4,
    "chat": {"id": -1001234567, "type": "supergroup"},
    "from": {"id": 777, "first_name": "Ali", "username": "ali"},
    "text": "312420017"
}
engine.handle_message(msg4)
print(engine.bot.sent[-1])
