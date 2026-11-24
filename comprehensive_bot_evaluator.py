# -*- coding: utf-8 -*-
import sys
import os
import re

from ai_service import AIService
from session_manager import SessionManager, UserSession

def run_evaluation():
    ai = AIService()
    sm = SessionManager()
    
    test_cases = [
        # --- 1. SOAT / VAQT (Post 141) ---
        ("soati noturiykan", "CLOCK_PROBLEM", "SEND_CLOCK_GUIDE"),
        ("soatni qanday tugirlasam buladi", "CLOCK_PROBLEM", "SEND_CLOCK_GUIDE"),
        ("vaqti orqada qolib ketibdi", "CLOCK_PROBLEM", "SEND_CLOCK_GUIDE"),
        ("soati adashib ketgan qanday togirlayman", "CLOCK_PROBLEM", "SEND_CLOCK_GUIDE"),
        ("soat xato ko'rsatyapti", "CLOCK_PROBLEM", "SEND_CLOCK_GUIDE"),
        ("soatini to'g'rilash kerak", "CLOCK_PROBLEM", "SEND_CLOCK_GUIDE"),

        # --- 2. IKPU / MXIK (Post 138) ---
        ("aparatim ikpu diyabdi", "IKPU_ERROR", "PROCESS_IKPU"),
        ("ikpu ashebka chiqdi", "IKPU_ERROR", "PROCESS_IKPU"),
        ("proverka koda ikpu ustarela deb chiqdi", "IKPU_ERROR", "PROCESS_IKPU"),
        ("ikpu kodini qanday yangilayman", "IKPU_ERROR", "PROCESS_IKPU"),
        ("mxik xatosi beryapti", "IKPU_ERROR", "PROCESS_IKPU"),
        ("shtrix kod xatosi chiqdi", "IKPU_ERROR", "PROCESS_IKPU"),

        # --- 3. MARKIROVKA (Post 139) ---
        ("markirofkani qanday uchiraman", "GUIDE_DISABLE_MARKING", "SEND_DISABLE_MARKING_GUIDE"),
        ("markirovkani ochirish videosi", "GUIDE_DISABLE_MARKING", "SEND_DISABLE_MARKING_GUIDE"),
        ("markirofka ashebka beryapti uchirib beringlar", "GUIDE_DISABLE_MARKING", "SEND_DISABLE_MARKING_GUIDE"),
        ("markirovkani ochirish darsligi", "GUIDE_DISABLE_MARKING", "SEND_DISABLE_MARKING_GUIDE"),

        # --- 4. NARX / INDEKS (Post 140) ---
        ("narxni qanday ozgartiraman", "GUIDE_CHANGE_PRICE", "SEND_CHANGE_PRICE_GUIDE"),
        ("indesni uzgartirish", "GUIDE_CHANGE_PRICE", "SEND_CHANGE_PRICE_GUIDE"),
        ("indeksni almashtirish videosi", "GUIDE_CHANGE_PRICE", "SEND_CHANGE_PRICE_GUIDE"),
        ("narx oshirish videosi bormi", "GUIDE_CHANGE_PRICE", "SEND_CHANGE_PRICE_GUIDE"),
        ("tovar narxini o'zgartirish darsligi", "GUIDE_CHANGE_PRICE", "SEND_CHANGE_PRICE_GUIDE"),

        # --- 5. CHEK BEKOR QILISH / QAYTARISH / ATKAZ (Post 53) ---
        ("xato urilgan chekni bekor qilish videosi", "GUIDE_CANCEL_CHECK", "SEND_CANCEL_CHECK_GUIDE"),
        ("chekni atkaz qilish darsligi", "GUIDE_CANCEL_CHECK", "SEND_CANCEL_CHECK_GUIDE"),
        ("qaytarish chekini urish videosi", "GUIDE_CANCEL_CHECK", "SEND_CANCEL_CHECK_GUIDE"),
        ("tovarni atkaz qilish", "GUIDE_CANCEL_CHECK", "SEND_CANCEL_CHECK_GUIDE"),

        # --- 6. YANGI MAXSULOT KIRITISH (Post 15) ---
        ("yangi tovar qoshish videosi", "GUIDE_ADD_PRODUCT", "SEND_ADD_PRODUCT_GUIDE"),
        ("maxsulot kiritish qanday boladi", "GUIDE_ADD_PRODUCT", "SEND_ADD_PRODUCT_GUIDE"),
        ("tovar qo'shish darsligi", "GUIDE_ADD_PRODUCT", "SEND_ADD_PRODUCT_GUIDE"),

        # --- 7. DASTURNI YANGILASH (Post 142) ---
        ("kassa dasturini yangilash videosi", "GUIDE_UPDATE_APP", "SEND_UPDATE_APP_GUIDE"),
        ("obnovleniye qilish videosi", "GUIDE_UPDATE_APP", "SEND_UPDATE_APP_GUIDE"),
        ("dasturni obnovit qilish", "GUIDE_UPDATE_APP", "SEND_UPDATE_APP_GUIDE"),

        # --- 8. 2D SKANER (Post 27) ---
        ("skanerni qanday ulayman", "GUIDE_SCANNER_2D", "SEND_SCANNER_2D_GUIDE"),
        ("2d skaner ishlatish darsligi", "GUIDE_SCANNER_2D", "SEND_SCANNER_2D_GUIDE"),

        # --- 9. BAZA YUKLASH / SINXRONIZATSIYA (Post 138) ---
        ("serverdan sinxronizatsiya qilish videosi", "GUIDE_DATA_LOAD", "SEND_DATA_LOAD_GUIDE"),
        ("baza yuklash darsligi", "GUIDE_DATA_LOAD", "SEND_DATA_LOAD_GUIDE"),

        # --- 10. Z-HISOBOT VA CHEK URISH (Post 2) ---
        ("z hisobot olish videosi", "GUIDE_PRINT_CHECK_Z", "SEND_PRINT_CHECK_Z_GUIDE"),
        ("chek urish videosi", "GUIDE_PRINT_CHECK_Z", "SEND_PRINT_CHECK_Z_GUIDE"),

        # --- 11. HIKMAT / KUTISH PROMISE ---
        ("hozir tashlayman", "WAITING_PROMISE", "ACKNOWLEDGE_WAITING"),
        ("xozir tashlayman", "WAITING_PROMISE", "ACKNOWLEDGE_WAITING"),
        ("kutib turing", "WAITING_PROMISE", "ACKNOWLEDGE_WAITING"),
        ("bir minut", "WAITING_PROMISE", "ACKNOWLEDGE_WAITING"),
        ("hozir inn raqamimni tashlayman", "WAITING_PROMISE", "ACKNOWLEDGE_WAITING"),

        # --- 12. YILLIK TO'LOV MUDDATI ---
        ("yillik tolov qachongacha yetadi", "CHECK_YEARLY_EXPIRATION", "EXPLAIN_YEARLY_LIMITATION"),
        ("fiskal modul qachon tugaydi", "CHECK_YEARLY_EXPIRATION", "EXPLAIN_YEARLY_LIMITATION"),

        # --- 13. TO'LOV REKVIZITLARI ---
        ("oylik tolov rekviziti", "PAY_MONTHLY", "SEND_MONTHLY_PAY"),
        ("yillik tolov rekviziti", "PAY_YEARLY", "SEND_YEARLY_PAY"),

        # --- 14. BARCHA VIDEOLAR ---
        ("hamma videolarni tashlab ber", "ALL_VIDEO_GUIDES", "SEND_ALL_VIDEO_GUIDES"),
        ("video darsliklar", "ALL_VIDEO_GUIDES", "SEND_ALL_VIDEO_GUIDES")
    ]

    passed = 0
    failed = 0
    results = []

    for text, expected_intent, expected_action in test_cases:
        session = sm.get_session(888888)
        intent_res = ai.detect_semantic_intent(text, session=session)
        actual_intent = intent_res.get("intent") if intent_res else None
        
        plan = ai.build_action_plan(actual_intent, text, session=session)
        actual_action = plan.get("next_action") if plan else None

        ok = (actual_intent == expected_intent) and (actual_action == expected_action)
        if ok:
            passed += 1
            results.append(f"✅ PASS: '{text}' -> Intent: {actual_intent}, Action: {actual_action}")
        else:
            failed += 1
            results.append(f"❌ FAIL: '{text}'\n   Expected: Intent={expected_intent}, Action={expected_action}\n   Actual:   Intent={actual_intent}, Action={actual_action}")

    print(f"\nJami testlar: {len(test_cases)}")
    print(f"O'tdi: {passed}")
    print(f"Xato: {failed}")
    for r in results:
        print(r)

if __name__ == "__main__":
    run_evaluation()
