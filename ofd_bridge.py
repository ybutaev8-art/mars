import os
import sys
import json
import asyncio
import threading
import time
from telethon import TelegramClient, events
import config

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = os.path.join(os.path.dirname(__file__), "data", "ofd_user_session")
STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "userbot_state.json")

class OFDBridge:
    def __init__(self):
        self.session_path = SESSION_PATH
        self.client = None
        self.loop = None
        self.thread = None
        self.last_forwarded_msg_id = self._load_last_forwarded_id()

    def _load_last_forwarded_id(self):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("last_forwarded_msg_id", 0)
        except Exception:
            pass
        return 0

    def _save_last_forwarded_id(self, msg_id):
        self.last_forwarded_msg_id = msg_id
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_forwarded_msg_id": msg_id}, f)
        except Exception:
            pass

    def start_background(self):
        """Userbot va OFD servisni fonda doimiy ishlash uchun ishga tushirish"""
        if not os.path.exists(self.session_path + ".session"):
            print("[USERBOT] ⚠️ Sessiya fayli topilmadi, fon jarayoni ishga tushmadi.")
            return

        if self.thread and self.thread.is_alive():
            return

        self.thread = threading.Thread(target=self._run_event_loop, daemon=True, name="UserbotBackgroundThread")
        self.thread.start()
        print("[USERBOT] 🚀 Userbot fon oqimi ishga tushirildi (Nomi: txkmbot).")

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.client = TelegramClient(
            self.session_path,
            API_ID,
            API_HASH,
            device_model="txkmbot",
            app_version="txkmbot",
            system_version="Windows 11",
            lang_code="uz",
            system_lang_code="uz"
        )

        async def main():
            await self.client.start()
            print("[USERBOT] ✅ Telegram hisobiga muvaffaqiyatli ulandi (txkmbot).")

            # Boshlang'ich tekshiruv: agar eng oxirgi Excel tashlanmagan bo'lsa forward qilish
            await self._check_missed_excel()

            # 'Абонент тулови' guruhidan keluvchi yangi xabarlarni kuzatish
            @self.client.on(events.NewMessage(chats=config.EXCEL_SOURCE_GROUP_ID))
            async def handle_new_excel_message(event):
                await self._process_excel_message(event.message)

            @self.client.on(events.MessageEdited(chats=config.EXCEL_SOURCE_GROUP_ID))
            async def handle_edited_excel_message(event):
                await self._process_excel_message(event.message)

            await self.client.run_until_disconnected()

        try:
            self.loop.run_until_complete(main())
        except Exception as e:
            print(f"[USERBOT] Xatolik: {e}")

    async def _check_missed_excel(self):
        try:
            messages = await self.client.get_messages(config.EXCEL_SOURCE_GROUP_ID, limit=5)
            for m in messages:
                if m.file and m.file.name and m.file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
                    if m.id > self.last_forwarded_msg_id:
                        print(f"[USERBOT] 🔄 Yangi o'tkazilmagan fayl topildi: {m.file.name} (ID: {m.id})")
                        await self._process_excel_message(m)
                    break
        except Exception as e:
            print(f"[USERBOT] Tekshirishda xatolik: {e}")

    async def _process_excel_message(self, message):
        try:
            if not (message.file and message.file.name):
                return
            fname = message.file.name.lower()
            if not fname.endswith(('.xlsx', '.xls', '.csv')):
                return

            if message.id <= self.last_forwarded_msg_id:
                return

            print(f"[USERBOT] 📥 'Абонент тулови' guruhiga yangi hisob-kitob tashlandi: {message.file.name} (Msg ID: {message.id})")

            # 1. Yangi Excel hisob-kitobni foydalanuvchi akkounti orqali kanalga forward qilish
            sent = await self.client.forward_messages(config.EXCEL_TARGET_CHANNEL_ID, message)
            print(f"[USERBOT] 🚀 Yangi hisob-kitob kanalga (Oylik abanit) muvaffaqiyatli tashlandi! Yangi Msg ID: {sent.id}")
            self._save_last_forwarded_id(message.id)

            # 2. Mahalliy bot bazasini ham darhol yangilash
            temp_path = os.path.join(config.DATA_DIR, f"auto_{int(time.time())}_{message.file.name}")
            await self.client.download_media(message, file=temp_path)
            if os.path.exists(temp_path):
                from excel_service import excel_service
                count = excel_service.update_excel_file(temp_path)
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                print(f"[USERBOT] 📊 Botning lokal Excel bazasi ham avtomatik yangilandi! Jami: {count} ta tashkilot.")
        except Exception as err:
            print(f"[USERBOT] ❌ Excel faylni ishlashda xatolik: {err}")

    def query_bot(self, fm_number, timeout=6):
        """Sinxron chaqirish uchun @ofd943_bot dan natija oladi"""
        if self.loop and self.client and self.client.is_connected():
            future = asyncio.run_coroutine_threadsafe(self._async_live_query(fm_number, timeout), self.loop)
            try:
                return future.result(timeout=timeout + 2)
            except Exception as e:
                print(f"[OFD BRIDGE] Jonli so'rovda xatolik: {e}")
                return None
        else:
            try:
                return asyncio.run(self._async_standalone_query(fm_number, timeout))
            except Exception as e:
                print(f"[OFD BRIDGE] Standalone xatolik: {e}")
                return None

    async def _async_live_query(self, fm_number, timeout=6):
        bot = await self.client.get_entity("ofd943_bot")
        sent = await self.client.send_message(bot, str(fm_number).strip())
        sent_time = time.time()
        while time.time() - sent_time < timeout:
            await asyncio.sleep(0.4)
            async for msg in self.client.iter_messages(bot, limit=3):
                if msg.id > sent.id:
                    return msg.text
        return None

    async def _async_standalone_query(self, fm_number, timeout=6):
        if not os.path.exists(self.session_path + ".session"):
            return None

        client = TelegramClient(
            self.session_path,
            API_ID,
            API_HASH,
            device_model="txkmbot",
            app_version="txkmbot",
            system_version="Windows 11",
            lang_code="uz",
            system_lang_code="uz"
        )
        await client.connect()
        try:
            if not await client.is_user_authorized():
                return None
            bot = await client.get_entity("ofd943_bot")
            sent = await client.send_message(bot, str(fm_number).strip())
            sent_time = time.time()
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
