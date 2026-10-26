import os
import sys
import asyncio
import time
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = os.path.join(os.path.dirname(__file__), "data", "ofd_user_session")

class OFDBridge:
    def __init__(self):
        self.session_path = SESSION_PATH
        self.client = None

    def query_bot(self, fm_number, timeout=6):
        """Sinxron chaqirish uchun asyncio orqali @ofd943_bot dan natija oladi"""
        try:
            return asyncio.run(self._async_query(fm_number, timeout))
        except Exception as e:
            print(f"[OFD BRIDGE] Xatolik: {e}")
            return None

    async def _async_query(self, fm_number, timeout=6):
        if not os.path.exists(self.session_path + ".session"):
            print("[OFD BRIDGE] Sessiya fayli topilmadi!")
            return None

        client = TelegramClient(
            self.session_path,
            API_ID,
            API_HASH,
            device_model="TXKMrobot",
            app_version="TXKMrobot",
            system_version="Windows 11"
        )
        await client.connect()
        try:
            if not await client.is_user_authorized():
                print("[OFD BRIDGE] User session avtorizatsiyadan o'tmagan!")
                return None

            bot = await client.get_entity("ofd943_bot")
            
            # Xabarni yuboramiz
            sent = await client.send_message(bot, str(fm_number).strip())
            sent_time = time.time()

            # Javobni kutamiz (timeout ichida)
            while time.time() - sent_time < timeout:
                await asyncio.sleep(0.4)
                async for msg in client.iter_messages(bot, limit=3):
                    if msg.id > sent.id:
                        return msg.text
            return None
        finally:
            await client.disconnect()

ofd_bridge = OFDBridge()

if __name__ == "__main__":
    test_fm = sys.argv[1] if len(sys.argv) > 1 else "LG420230615712"
    res = ofd_bridge.query_bot(test_fm)
    print("NATIJA:", repr(res))
