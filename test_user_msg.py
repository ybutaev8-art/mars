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

msg = {
    "message_id": 99,
    "chat": {"id": -1001234567, "type": "supergroup"},
    "from": {"id": 111, "first_name": "Quvonchbek", "username": "quvonch"},
    "text": "312420017"
}

engine.handle_message(msg)
print("=== BOTNING MIJOZGA BERADIGAN JAVOBI ===")
print(engine.bot.sent[-1])
