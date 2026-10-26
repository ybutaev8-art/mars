import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from excel_service import excel_service

print("=== 1. STIR 312420017 Tekshiruvi ===")
res = excel_service.find_by_identifier("312420017")
if res:
    print(f"Topildi:")
    print(f"INN/STIR: {res['query']}")
    print(f"Tashkilot: {res['org_name']}")
    print(f"Jami apparatlar soni: {res['total_pos_count']} ta")
    for idx, p in enumerate(res['pos_list'], 1):
        print(f"  {idx}-aparat: {p['pos_model']} (rang: {p['color_type']})")
    print(f"Qarzdorlik: {res['total_debt_text']} so'm")
    print(f"Shu oy oxirigacha: {res['shu_oy_oxirigacha_text']} so'm")
    print(f"Yil oxirigacha: {res['yil_oxirigacha_text']} so'm")
else:
    print("TOPILMADI!")

print("\n=== 2. Bir nechta apparatli tashkilot qidiramiz ===")
multi_found = None
for k, v in excel_service.cache_by_inn.items():
    if len(v) > 1:
        multi_found = k
        break

if multi_found:
    m_res = excel_service.find_by_identifier(multi_found)
    print(f"Ko'p apparatli tashkilot topildi (STIR: {multi_found}):")
    print(f"Tashkilot: {m_res['org_name']}")
    print(f"Apparatlar soni: {m_res['total_pos_count']} ta")
    for idx, p in enumerate(m_res['pos_list'], 1):
        print(f"  {idx}-aparat: {p['pos_model']} (rang: {p['color_type']})")
    print(f"Shu oy oxirigacha: {m_res['shu_oy_oxirigacha_text']} so'm")
    print(f"Yil oxirigacha: {m_res['yil_oxirigacha_text']} so'm")

print("\n=== 3. Qizil (ro'yxatdan chiqarilgan) apparat qidiramiz ===")
red_found = None
for k, v in excel_service.cache_by_inn.items():
    if any(p['color_type'] == 'red' for p in v):
        red_found = k
        break

if red_found:
    r_res = excel_service.find_by_identifier(red_found)
    print(f"Ro'yxatdan chiqarilgan tashkilot topildi (STIR: {red_found}):")
    print(f"Tashkilot: {r_res['org_name']}")
    for idx, p in enumerate(r_res['pos_list'], 1):
        print(f"  {idx}-aparat: {p['pos_model']} ({p['pos_status']})")

print("\n=== 4. Sariq (P3 model) apparat qidiramiz ===")
yellow_found = None
for k, v in excel_service.cache_by_inn.items():
    if any(p['color_type'] == 'yellow' for p in v):
        yellow_found = k
        break

if yellow_found:
    y_res = excel_service.find_by_identifier(yellow_found)
    print(f"P3 modelli tashkilot topildi (STIR: {yellow_found}):")
    print(f"Tashkilot: {y_res['org_name']}")
    for idx, p in enumerate(y_res['pos_list'], 1):
        print(f"  {idx}-aparat: {p['pos_model']} ({p['pos_status']})")
