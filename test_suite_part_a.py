# -*- coding: utf-8 -*-
import os
import sys
import unittest
import json

from ai_service import AIService
from excel_service import excel_service
from session_manager import SessionManager, UserSession
from ticket_service import ticket_service
from receipt_service import receipt_service

class MasterUnitAndIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ai = AIService()
        cls.sm = SessionManager()

    def test_01_excel_service_clean_inn(self):
        info = excel_service.find_by_identifier("311790999")
        self.assertIsNotNone(info)
        self.assertEqual(info.get("has_debt"), False)
        self.assertEqual(info.get("active_count"), 1)
        self.assertIn("ALISHER BOBO", info.get("org_name", ""))

    def test_02_excel_service_debt_inn(self):
        info = excel_service.find_by_identifier("206011507")
        self.assertIsNotNone(info)
        self.assertEqual(info.get("has_debt"), True)
        self.assertIn("1 600 400", info.get("total_debt_text", ""))

    def test_03_excel_service_multi_pos(self):
        info = excel_service.find_by_identifier("308635722")
        self.assertIsNotNone(info)
        self.assertGreater(info.get("active_count", 0), 1)

    def test_04_excel_service_jshshir(self):
        info = excel_service.find_by_identifier("32212995720017")
        self.assertIsNotNone(info)
        self.assertIn("XUSHVAQTOV", info.get("org_name", ""))

    def test_05_excel_service_not_found(self):
        info = excel_service.find_by_identifier("999999999")
        self.assertIsNone(info)

    def test_06_identifier_classification(self):
        # We test identifier classification
        from bot import MarsBotEngine
        bot = MarsBotEngine.__new__(MarsBotEngine)
        
        self.assertEqual(bot.classify_identifier("311790999")["type"], "INN")
        self.assertEqual(bot.classify_identifier("32212995720017")["type"], "JSHSHIR")
        self.assertEqual(bot.classify_identifier("LG420230624507")["type"], "FM")
        self.assertEqual(bot.classify_identifier("VG298430008670")["type"], "FM")
        self.assertEqual(bot.classify_identifier("20208000405477989001")["type"], "BANK_ACCOUNT")
        self.assertEqual(bot.classify_identifier("UZ2028081065")["type"], "POS_ID")

    def test_07_waiting_promise_detection(self):
        session = self.sm.get_session(111222)
        session.state = "AWAITING_INN"
        session.fm_holat = "toza"
        
        phrases = [
            "hozir tashlayman", "xozir tashlayman", "hozir tashiman",
            "kutib turing", "bir minut", "hozir", "xop hozir",
            "hozir inn raqamimni tashlayman", "hozir topib beraman"
        ]
        for p in phrases:
            res = self.ai.detect_semantic_intent(p, session=session)
            self.assertEqual(res.get("intent"), "WAITING_PROMISE", f"Failed on: {p}")

    def test_08_error_videos_routing(self):
        session = self.sm.get_session(111222)
        session.reset_for_new_target()
        
        cases = [
            ("soati noturiykan", "CLOCK_PROBLEM", "SEND_CLOCK_GUIDE"),
            ("soatni qanday tugirlasam buladi", "CLOCK_PROBLEM", "SEND_CLOCK_GUIDE"),
            ("aparatim ikpu diyabdi", "IKPU_ERROR", "PROCESS_IKPU"),
            ("markirofkani qanday uchiraman", "GUIDE_DISABLE_MARKING", "SEND_DISABLE_MARKING_GUIDE"),
            ("narxni qanday ozgartiraman", "GUIDE_CHANGE_PRICE", "SEND_CHANGE_PRICE_GUIDE"),
            ("xato urilgan chekni bekor qilish videosi", "GUIDE_CANCEL_CHECK", "SEND_CANCEL_CHECK_GUIDE"),
            ("yangi tovar qoshish videosi", "GUIDE_ADD_PRODUCT", "SEND_ADD_PRODUCT_GUIDE"),
            ("kassa dasturini yangilash videosi", "GUIDE_UPDATE_APP", "SEND_UPDATE_APP_GUIDE"),
            ("skanerni qanday ulayman", "GUIDE_SCANNER_2D", "SEND_SCANNER_2D_GUIDE"),
            ("serverdan sinxronizatsiya qilish videosi", "GUIDE_DATA_LOAD", "SEND_DATA_LOAD_GUIDE"),
            ("z hisobot olish videosi", "GUIDE_PRINT_CHECK_Z", "SEND_PRINT_CHECK_Z_GUIDE"),
            ("hamma videolarni tashlab ber", "ALL_VIDEO_GUIDES", "SEND_ALL_VIDEO_GUIDES")
        ]
        for text, exp_intent, exp_action in cases:
            res = self.ai.detect_semantic_intent(text, session=session)
            self.assertEqual(res.get("intent"), exp_intent, f"Failed intent on: {text}")
            plan = self.ai.build_action_plan(res.get("intent"), text, session=session)
            self.assertEqual(plan.get("next_action"), exp_action, f"Failed action on: {text}")

    def test_09_yearly_expiration_limitation(self):
        session = self.sm.get_session(111222)
        session.reset_for_new_target()
        
        queries = [
            "yillik tolov qachongacha yetadi",
            "fiskal modul qachon tugaydi",
            "yillik tolovim qachon keladi"
        ]
        for q in queries:
            res = self.ai.detect_semantic_intent(q, session=session)
            self.assertEqual(res.get("intent"), "CHECK_YEARLY_EXPIRATION", f"Failed on: {q}")
            plan = self.ai.build_action_plan(res.get("intent"), q, session=session)
            self.assertEqual(plan.get("next_action"), "EXPLAIN_YEARLY_LIMITATION")

    def test_10_dispute_vs_history(self):
        session = self.sm.get_session(111222)
        session.reset_for_new_target()
        
        hist = self.ai.detect_semantic_intent("to'lovlarim tarixini ko'rsat", session=session)
        self.assertEqual(hist.get("intent"), "PAYMENT_HISTORY")

    def test_11_ticket_service_lifecycle(self):
        # Register a mock ticket
        client_data = {
            "chat_id": 999111,
            "message_id": 555,
            "user_id": 999111,
            "first_name": "Test User",
            "username": "testuser",
            "inn": "311790999",
            "org_name": "Test Org",
            "fm": "LG420230624507"
        }
        ticket = ticket_service.register_ticket(
            tech_msg_id=777,
            client_data=client_data,
            base_card="Test Card"
        )
        self.assertIsNotNone(ticket)
        self.assertEqual(str(ticket.get("user_id")), "999111")
        self.assertEqual(ticket.get("client_count"), 0)
        
        # Link discussion id
        ticket_service.link_discussion_id(888, 999)
        
        # Close ticket
        ticket_service.close_ticket(999111)
        self.assertIsNone(ticket_service.find_ticket_by_user_id(999111))

if __name__ == "__main__":
    unittest.main()
