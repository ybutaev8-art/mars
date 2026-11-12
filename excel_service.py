"""
Excel Oylik Abonent Hisob-Kitob Jadvali Servisi
- 9 xonali INN yuborilganda: СТИР bo'limi bo'yicha qidiradi
- 14 xonali JSHSHIR yuborilganda: ЖШШИР bo'limi bo'yicha qidiradi
- Ranglar bo'yicha model va holat:
  * Qizil (FFFF0000): Ro'yxatdan chiqarilgan (faoliyati to'xtatilgan)
  * Sariq (FFFFFF00, FFFFEB9C, FFFFC000...): P3 model kassa apparati
  * Rangsiz / Oq: SmartOne model kassa apparati
- Qatorlar soni = Kassa apparatlari soni
- Qoldiq (Колдик) ustunidan qarzdorlikni aniqlash
- Oylik stavka: 1 apparat = 100 000 so'm/oy
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import shutil
import zipfile
import xml.etree.ElementTree as ET
import csv
import re
from datetime import datetime, timedelta
import config

class ExcelService:
    def __init__(self, excel_path=config.EXCEL_PATH):
        self.excel_path = excel_path
        self.cache_by_inn = {}
        self.cache_by_jshshir = {}
        self.last_mtime = 0
        self.load_data()

    def parse_excel_date(self, raw_val):
        """Excel B ustunidagi sanani aniqlash (serial float yoki matn)"""
        if not raw_val:
            return None
        val_str = str(raw_val).strip()
        try:
            f_val = float(val_str)
            if f_val > 1000:
                return datetime(1899, 12, 30) + timedelta(days=f_val)
        except ValueError:
            pass
        m = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", val_str)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                pass
        m2 = re.search(r"(\d{1,2})[-./](\d{1,2})[-./](\d{4})", val_str)
        if m2:
            try:
                return datetime(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
            except ValueError:
                pass
        return None

    def get_color_type(self, rgb):
        """RGB hex kodidan rang turini aniqlash: 'red', 'yellow', 'none'"""
        if not rgb:
            return "none"
        rgb_str = str(rgb).upper().strip()
        if "FFFF0000" in rgb_str or "FFC00000" in rgb_str or "FFFFC7CE" in rgb_str or "FFCC0000" in rgb_str:
            return "red"
        if "FFFFFF00" in rgb_str or "FFFFEB9C" in rgb_str or "FFFFC000" in rgb_str or "FFFFFFCC" in rgb_str or "FFFFCC99" in rgb_str or "FFFFD700" in rgb_str:
            return "yellow"
        return "none"

    def load_data(self):
        """Excel jadvalini yuklash va indekslash"""
        if not os.path.exists(self.excel_path):
            print(f"[EXCEL] Fayl topilmadi: {self.excel_path}")
            return

        try:
            mtime = os.path.getmtime(self.excel_path)
            if mtime == self.last_mtime and self.cache_by_inn:
                return

            if self.excel_path.endswith(".xlsx"):
                self._parse_xlsx(self.excel_path)
            elif self.excel_path.endswith(".csv"):
                self._parse_csv(self.excel_path)

            self.last_mtime = mtime
            print(f"[EXCEL] Muvaffaqiyatli yuklandi: {len(self.cache_by_inn)} ta STIR, {len(self.cache_by_jshshir)} ta JSHSHIR mavjud.")
        except Exception as e:
            print(f"[ERROR] Excel bazani yuklashda xatolik: {e}")

    def _parse_xlsx(self, path):
        with zipfile.ZipFile(path, 'r') as z:
            # 1. Shared Strings ni yuklash
            shared_strings = []
            if "xl/sharedStrings.xml" in z.namelist():
                tree = ET.parse(z.open("xl/sharedStrings.xml"))
                root = tree.getroot()
                ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for si in root.findall(".//ns:si", ns):
                    texts = si.findall(".//ns:t", ns)
                    shared_strings.append("".join(t.text or "" for t in texts))

            # 2. Styles (Fills va cellXfs)
            fills_rgb = []
            if "xl/styles.xml" in z.namelist():
                tree = ET.parse(z.open("xl/styles.xml"))
                root = tree.getroot()
                ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                fills_elem = root.find("ns:fills", ns)
                if fills_elem is not None:
                    for f in fills_elem.findall("ns:fill", ns):
                        pat = f.find("ns:patternFill", ns)
                        fg = pat.find("ns:fgColor", ns) if pat is not None else None
                        fills_rgb.append(fg.get("rgb") if fg is not None else None)

                xfs = [int(xf.get("fillId", 0)) for xf in root.find("ns:cellXfs", ns).findall("ns:xf", ns)]
            else:
                xfs = []

            # 3. Sheet1.xml ni o'qish (asosiy jadval)
            sheet_target = "xl/worksheets/sheet1.xml"
            if sheet_target not in z.namelist():
                for name in z.namelist():
                    if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                        sheet_target = name
                        break

            tree = ET.parse(z.open(sheet_target))
            root = tree.getroot()
            ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

            # Sarlavhalarni topish (Row 1 dan Row 5 gacha qidiramiz)
            col_map = {}
            header_row_found = False

            for row in root.findall(".//ns:row", ns)[:10]:
                for c in row.findall("ns:c", ns):
                    v = c.find("ns:v", ns)
                    val = v.text if v is not None else ""
                    if c.get("t") == "s" and val.isdigit():
                        val = shared_strings[int(val)] if int(val) < len(shared_strings) else ""
                    val_clean = str(val).strip().upper()
                    col_letter = "".join(filter(str.isalpha, c.get("r", "")))

                    if "СТИР" in val_clean or "STIR" in val_clean or val_clean == "INN" or val_clean == "ИНН":
                        col_map["stir"] = col_letter
                        header_row_found = True
                    elif "ЖШШИР" in val_clean or "JSHSHIR" in val_clean or "ПИНФЛ" in val_clean or "PINFL" in val_clean:
                        col_map["jshshir"] = col_letter
                        header_row_found = True
                    elif "КОРХОНА" in val_clean or "НОМИ" in val_clean or "TASHKILOT" in val_clean:
                        col_map["name"] = col_letter
                    elif "НКМ" in val_clean or "ОНЛАЙН" in val_clean or "FM" in val_clean or "ФМ" in val_clean:
                        col_map["pos_id"] = col_letter
                    elif "КОЛДИК" in val_clean or "ҚОЛДИҚ" in val_clean or "QOLDIQ" in val_clean or "БАЛАНС" in val_clean:
                        col_map["qoldiq"] = col_letter

                if header_row_found and "stir" in col_map:
                    break

            # Agar topilmasa, standart ustunlar:
            col_stir = col_map.get("stir", "C")
            col_jshshir = col_map.get("jshshir", "D")
            col_name = col_map.get("name", "E")
            col_pos_id = col_map.get("pos_id", "F")
            col_qoldiq = col_map.get("qoldiq", "BI")

            print(f"[EXCEL] Ustunlar xaritasi: STIR={col_stir}, JSHSHIR={col_jshshir}, Nomi={col_name}, Qoldiq={col_qoldiq}")

            new_by_inn = {}
            new_by_jshshir = {}

            # Qatorlarni aylanish
            for row in root.findall(".//ns:row", ns):
                row_num = row.get("r", "")
                if row_num in ["1", "2"]:  # Sarlavhalarni o'tkazib yuboramiz
                    continue

                row_data = {}
                row_colors = []

                for c in row.findall("ns:c", ns):
                    col_letter = "".join(filter(str.isalpha, c.get("r", "")))
                    v = c.find("ns:v", ns)
                    val = v.text if v is not None else ""
                    if c.get("t") == "s" and val.isdigit():
                        val = shared_strings[int(val)] if int(val) < len(shared_strings) else ""
                    row_data[col_letter] = str(val).strip()

                    # Boshlang'ich ustunlar rangi (A, B, C, D, E, F)
                    if col_letter in ["A", "B", "C", "D", "E", "F"]:
                        s_id = int(c.get("s", 0))
                        if s_id < len(xfs):
                            f_id = xfs[s_id]
                            if f_id < len(fills_rgb):
                                rgb = fills_rgb[f_id]
                                c_type = self.get_color_type(rgb)
                                if c_type != "none":
                                    row_colors.append(c_type)

                # Qator rangini aniqlash
                if "red" in row_colors:
                    color_type = "red"
                    pos_model = "Ro'yxatdan chiqarilgan"
                    pos_status = "Ro'yxatdan chiqarilgan (faoliyati to'xtatilgan)"
                    is_active = False
                elif "yellow" in row_colors:
                    color_type = "yellow"
                    pos_model = "P3"
                    pos_status = "P3 model kassa apparati"
                    is_active = True
                else:
                    color_type = "none"
                    pos_model = "SmartOne"
                    pos_status = "SmartOne model kassa apparati"
                    is_active = True

                raw_stir = re.sub(r"\D", "", row_data.get(col_stir, ""))
                raw_jshshir = re.sub(r"\D", "", row_data.get(col_jshshir, ""))
                org_name = row_data.get(col_name, "")
                if not org_name:
                    org_name = "Noma'lum tashkilot"

                # Ro'yxatga olingan sana (B ustun)
                raw_b = row_data.get("B", "")
                reg_date = self.parse_excel_date(raw_b)

                # Yil boshida qoldiq (G ustun: musbat = qarz, manfiy = haqdorlik/avans)
                raw_g = row_data.get("G", "0")
                g_digits = re.sub(r"[^\d.-]", "", raw_g.replace(" ", "").replace(",", "."))
                try:
                    prev_year_balance = float(g_digits) if g_digits else 0.0
                except ValueError:
                    prev_year_balance = 0.0

                pos_id = row_data.get(col_pos_id, "")

                # Qoldiq (qarzdorlik summasi)
                raw_qoldiq = row_data.get(col_qoldiq, "0")
                qoldiq_digits = re.sub(r"[^\d.-]", "", raw_qoldiq.replace(" ", "").replace(",", "."))
                try:
                    qoldiq_amount = float(qoldiq_digits) if qoldiq_digits else 0.0
                except ValueError:
                    qoldiq_amount = 0.0

                orig_qoldiq_amount = qoldiq_amount

                # Oylik to'lovlar va hisoblangan summalar (2026 yil)
                months_paid = {}
                months_paid_cols = [
                    ("Yanvar", "AV"), ("Fevral", "AW"), ("Mart", "AX"), ("Aprel", "AY"),
                    ("May", "AZ"), ("Iyun", "BA"), ("Iyul", "BB"), ("Avgust", "BC"),
                    ("Sentabr", "BD"), ("Oktabr", "BE"), ("Noyabr", "BF"), ("Dekabr", "BG")
                ]
                for m_name, m_col in months_paid_cols:
                    raw_val = row_data.get(m_col, "").strip()
                    digits = re.sub(r"[^\d.-]", "", raw_val.replace(" ", "").replace(",", "."))
                    try:
                        amt = float(digits) if digits else 0.0
                    except ValueError:
                        amt = 0.0
                    months_paid[m_name] = amt

                months_calc = {}
                months_calc_cols = [
                    ("Yanvar", "AI"), ("Fevral", "AJ"), ("Mart", "AK"), ("Aprel", "AL"),
                    ("May", "AM"), ("Iyun", "AN"), ("Iyul", "AO"), ("Avgust", "AP"),
                    ("Sentabr", "AQ"), ("Oktabr", "AR"), ("Noyabr", "AS"), ("Dekabr", "AT")
                ]
                for m_name, m_col in months_calc_cols:
                    raw_val = row_data.get(m_col, "").strip()
                    digits = re.sub(r"[^\d.-]", "", raw_val.replace(" ", "").replace(",", "."))
                    try:
                        amt = float(digits) if digits else 0.0
                    except ValueError:
                        amt = 0.0
                    months_calc[m_name] = amt

                # Qizil qator ro'yxatdan chiqarilgan va butunlay hisob-kitobdan chiqarilgan hisoblanadi
                if color_type == "red":
                    qoldiq_amount = 0.0
                    prev_year_balance = 0.0
                    months_paid = {m_name: 0.0 for m_name, _ in months_paid_cols}
                    months_calc = {m_name: 0.0 for m_name, _ in months_calc_cols}

                pos_record = {
                    "stir": raw_stir,
                    "jshshir": raw_jshshir,
                    "org_name": org_name,
                    "pos_id": pos_id,
                    "color_type": color_type,
                    "pos_model": pos_model,
                    "pos_status": pos_status,
                    "is_active": is_active,
                    "reg_date": reg_date,
                    "raw_reg_date": raw_b,
                    "prev_year_balance": prev_year_balance,
                    "qoldiq_raw": qoldiq_amount,
                    "orig_qoldiq_raw": orig_qoldiq_amount,
                    "qarz_amount": max(0.0, qoldiq_amount),
                    "months_paid": months_paid,
                    "months_calc": months_calc,
                    "total_paid_year": sum(months_paid.values()),
                    "total_calc_year": sum(months_calc.values()),
                    "row_num": row_num
                }

                if raw_stir and len(raw_stir) == 9:
                    if raw_stir not in new_by_inn:
                        new_by_inn[raw_stir] = []
                    new_by_inn[raw_stir].append(pos_record)

                if raw_jshshir and len(raw_jshshir) == 14:
                    if raw_jshshir not in new_by_jshshir:
                        new_by_jshshir[raw_jshshir] = []
                    new_by_jshshir[raw_jshshir].append(pos_record)

            self.cache_by_inn = new_by_inn
            self.cache_by_jshshir = new_by_jshshir

    def _parse_csv(self, path):
        """CSV faylni o'qish"""
        new_by_inn = {}
        new_by_jshshir = {}
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))
            if len(reader) < 2:
                return

            for r in reader[1:]:
                if not r:
                    continue
                raw_stir = re.sub(r"\D", "", r[0] if len(r) > 0 else "")
                org_name = r[1] if len(r) > 1 else "Tashkilot"
                raw_qoldiq = r[2] if len(r) > 2 else "0"
                pos_id = r[3] if len(r) > 3 else ""

                try:
                    q_num = float(re.sub(r"[^\d.-]", "", raw_qoldiq.replace(" ", "")))
                except ValueError:
                    q_num = 0.0

                color_type = "none"
                if len(r) > 5:
                    last_val = str(r[5]).lower()
                    if "qizil" in last_val: color_type = "red"
                    elif "sariq" in last_val: color_type = "yellow"

                orig_q_num = q_num
                if color_type == "red":
                    q_num = 0.0

                pos_record = {
                    "stir": raw_stir,
                    "jshshir": "",
                    "org_name": org_name,
                    "pos_id": pos_id,
                    "color_type": color_type,
                    "pos_model": "P3" if color_type == "yellow" else ("Ro'yxatdan chiqarilgan" if color_type == "red" else "SmartOne"),
                    "pos_status": "P3 model" if color_type == "yellow" else ("Ro'yxatdan chiqarilgan" if color_type == "red" else "SmartOne model"),
                    "is_active": color_type != "red",
                    "reg_date": None,
                    "raw_reg_date": "",
                    "prev_year_balance": 0.0,
                    "qoldiq_raw": q_num,
                    "orig_qoldiq_raw": orig_q_num,
                    "qarz_amount": max(0.0, q_num),
                    "months_paid": {},
                    "months_calc": {},
                    "total_paid_year": 0.0,
                    "total_calc_year": 0.0,
                    "row_num": "0"
                }
                if raw_stir:
                    if raw_stir not in new_by_inn:
                        new_by_inn[raw_stir] = []
                    new_by_inn[raw_stir].append(pos_record)

        self.cache_by_inn = new_by_inn
        self.cache_by_jshshir = new_by_jshshir

    def find_by_identifier(self, query):
        """
        9 xonali bo'lsa: СТИР (INN) bo'yicha filtr
        14 xonali bo'lsa: ЖШШИР bo'yicha filtr
        """
        self.load_data()
        cleaned = re.sub(r"\D", "", str(query))

        pos_list = None
        id_type = "STIR"

        if len(cleaned) == 9:
            id_type = "STIR / INN"
            pos_list = self.cache_by_inn.get(cleaned)
        elif len(cleaned) == 14:
            id_type = "JSHSHIR"
            pos_list = self.cache_by_jshshir.get(cleaned)
        else:
            # Agar 9 ham 14 ham bo'lmasa, ikkalasidan ham qidirib ko'ramiz
            pos_list = self.cache_by_inn.get(cleaned) or self.cache_by_jshshir.get(cleaned)

        if not pos_list:
            return None

        org_name = pos_list[0]["org_name"]
        total_pos_count = len(pos_list)
        active_pos_list = [p for p in pos_list if p.get("is_active")]
        active_count = len(active_pos_list)
        inactive_count = total_pos_count - active_count

        # Qizil (ro'yxatdan chiqarilgan) qatorlardagi balans hisoblanmaydi
        # Chunki u apparat ro'yxatdan chiqarilgan va butunlay hisob-kitobdan chiqarilgan hisoblanadi
        if active_count > 0:
            total_qoldiq = sum(p.get("qoldiq_raw", 0.0) for p in active_pos_list)
        else:
            total_qoldiq = 0.0

        total_debt = max(0.0, total_qoldiq)
        has_debt = total_qoldiq > 0.01
        has_advance = total_qoldiq < -0.01
        advance_amount = abs(total_qoldiq) if has_advance else 0.0

        # Oylik abonent stavkasi: 1 apparat = 100 000 so'm/oy
        monthly_fee_per_pos = 100000
        shu_oylik_abonoment = (active_count if active_count > 0 else 1) * monthly_fee_per_pos

        now = datetime.now()
        current_month = now.month
        # Keyingi oydan boshlab yil oxirigacha bo'lgan oylar soni
        rem_months = list(range(current_month + 1, 13))
        next_months_count = len(rem_months)

        month_names = {
            1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
            5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
            9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"
        }

        advance_text = ""
        if has_advance:
            adv = advance_amount
            adv_str = f"{adv:,.0f}".replace(",", " ")
            temp_adv = adv
            covered = []
            partial_month = None
            partial_needed = 0.0

            for m in rem_months:
                if temp_adv >= shu_oylik_abonoment:
                    covered.append(month_names[m])
                    temp_adv -= shu_oylik_abonoment
                elif temp_adv > 0:
                    partial_month = month_names[m]
                    partial_needed = shu_oylik_abonoment - temp_adv
                    temp_adv = 0.0
                    break
                else:
                    break

            if len(covered) == len(rem_months) and len(rem_months) > 0:
                leftover = temp_adv
                covered_str = " va ".join(covered) if len(covered) <= 2 else f"{covered[0]}–{covered[-1]}"
                if leftover > 0:
                    leftover_str = f"{leftover:,.0f}".replace(",", " ")
                    advance_text = (
                        f"💰 *Hisobingizda:* *{adv_str} so'm* ortiqcha to'lov (avans) mavjud.\n"
                        f"Bu summa joriy yil oxirigacha (*{covered_str}* oylari uchun) to'liq yetadi va 2027-yilga *{leftover_str} so'm* o'tadi.\n"
                        f"✅ *Yil oxirigacha boshqa to'lov qilishingiz shart emas.*"
                    )
                else:
                    advance_text = (
                        f"💰 *Hisobingizda:* *{adv_str} so'm* ortiqcha to'lov (avans) mavjud.\n"
                        f"Bu summa joriy yil oxirigacha (*{covered_str}* oylari uchun) to'liq yetadi.\n"
                        f"✅ *Yil oxirigacha boshqa to'lov qilishingiz shart emas.*"
                    )
            elif covered:
                next_pay_idx = rem_months[len(covered)]
                next_pay_m = month_names[next_pay_idx]
                uncovered_count = len(rem_months) - len(covered)
                yil_needed = (uncovered_count * shu_oylik_abonoment) - temp_adv
                yil_needed_str = f"{yil_needed:,.0f}".replace(",", " ")
                covered_str = " va ".join(covered)
                advance_text = (
                    f"💰 *Hisobingizda:* *{adv_str} so'm* ortiqcha to'lov (avans) mavjud.\n"
                    f"Bu summa *{covered_str}* oyi uchun yetadi. *{next_pay_m}* oyidan boshlab yana to'lov qilasiz (yil oxirigacha to'lash uchun: *{yil_needed_str} so'm*)."
                )
            elif partial_month:
                uncovered_rest = (len(rem_months) - 1) * shu_oylik_abonoment
                total_yil_needed = partial_needed + uncovered_rest
                advance_text = (
                    f"💰 *Hisobingizda:* *{adv_str} so'm* ortiqcha to'lov (avans) mavjud.\n"
                    f"*{partial_month}* oyi to'liq yopilishi uchun yana *{partial_needed:,.0f} so'm* to'lashingiz kerak (yil oxirigacha: *{total_yil_needed:,.0f} so'm*).".replace(",", " ")
                )
            else:
                advance_text = f"💰 *Hisobingizda:* *{adv_str} so'm* ortiqcha to'lov (avans) mavjud."

        if total_debt > 0:
            shu_oy_oxirigacha_tolov = total_debt
            yil_oxirigacha_tolov = total_debt + (next_months_count * shu_oylik_abonoment)
        else:
            shu_oy_oxirigacha_tolov = 0
            yil_oxirigacha_tolov = next_months_count * shu_oylik_abonoment

        return {
            "query": cleaned,
            "id_type": id_type,
            "org_name": org_name,
            "total_pos_count": total_pos_count,
            "active_count": active_count,
            "inactive_count": inactive_count,
            "pos_list": pos_list,
            "has_debt": has_debt,
            "has_advance": has_advance,
            "advance_amount": advance_amount,
            "advance_text": advance_text,
            "total_debt": total_debt,
            "total_debt_text": f"{total_debt:,.0f}".replace(",", " "),
            "shu_oy_oxirigacha": shu_oy_oxirigacha_tolov,
            "shu_oy_oxirigacha_text": f"{shu_oy_oxirigacha_tolov:,.0f}".replace(",", " "),
            "yil_oxirigacha": yil_oxirigacha_tolov,
            "yil_oxirigacha_text": f"{yil_oxirigacha_tolov:,.0f}".replace(",", " "),
            "next_months_count": next_months_count,
            "monthly_fee_per_pos": monthly_fee_per_pos
        }

    def find_by_inn(self, inn_or_jshshir):
        return self.find_by_identifier(inn_or_jshshir)

    def get_payment_history_text(self, info):
        """Mijoz uchun oylar kesimida to'lovlar tarixi va FIFO hisob-kitob hisoboti"""
        if not info or not info.get("pos_list"):
            return "Tashkilot bo'yicha to'lov ma'lumotlari topilmadi."

        pos_list = info["pos_list"]
        org_name = info["org_name"]
        id_type = info["id_type"]
        query = info["query"]
        total_pos_count = info["total_pos_count"]
        active_count = info.get("active_count", total_pos_count)

        month_keys = [
            ("Yanvar", 1), ("Fevral", 2), ("Mart", 3), ("Aprel", 4),
            ("May", 5), ("Iyun", 6), ("Iyul", 7), ("Avgust", 8),
            ("Sentabr", 9), ("Oktabr", 10), ("Noyabr", 11), ("Dekabr", 12)
        ]

        # Agar barcha apparatlar ro'yxatdan chiqarilgan bo'lsa
        if active_count == 0:
            return (
                f"📊 *{org_name} bo'yicha to'lovlar hisoboti:*\n"
                f"📑 {id_type}: `{query}`\n"
                f"📌 Kassa apparatlari soni: *{total_pos_count} ta* (barchasi ro'yxatdan chiqarilgan)\n\n"
                f"❌ *Barcha kassa apparatlari ro'yxatdan chiqarilgan va butunlay hisob-kitobdan to'xtatilgan.*"
            )

        # Barcha faol apparatlar bo'yicha ma'lumotlarni jamlash (qizil qatorlar butunlay chiqarilgan)
        earliest_reg = None
        total_prev_year_balance = 0.0
        total_qoldiq_raw = 0.0
        agg_calc = {m: 0.0 for m, _ in month_keys}
        agg_paid = {m: 0.0 for m, _ in month_keys}

        for p in pos_list:
            if p.get("color_type") == "red" or not p.get("is_active"):
                continue
            rd = p.get("reg_date")
            if rd:
                if earliest_reg is None or rd < earliest_reg:
                    earliest_reg = rd
            total_prev_year_balance += p.get("prev_year_balance", 0.0)
            total_qoldiq_raw += p.get("qoldiq_raw", 0.0)
            for m, _ in month_keys:
                agg_calc[m] += p.get("months_calc", {}).get(m, 0.0)
                agg_paid[m] += p.get("months_paid", {}).get(m, 0.0)

        header = (
            f"📊 *{org_name} bo'yicha to'lovlar hisoboti:*\n"
            f"📑 {id_type}: `{query}`\n"
            f"📌 Kassa apparatlari soni: *{total_pos_count} ta*\n"
        )

        now = datetime.now()
        current_month = now.month

        # Ro'yxatga olingan sana va boshlang'ich oyni aniqlash
        show_prev_year = False
        if earliest_reg and earliest_reg.year == 2026:
            start_month = earliest_reg.month
        elif earliest_reg and earliest_reg.year < 2026:
            start_month = 1
            show_prev_year = True
        else:
            first_m = 1
            for m_name, m_num in month_keys:
                if agg_calc[m_name] > 0 or agg_paid[m_name] > 0:
                    first_m = m_num
                    break
            start_month = first_m if first_m > 1 else 1
            show_prev_year = (start_month == 1 and total_prev_year_balance != 0)

        # Apparat(lar) ro'yxatga olingan sanasi
        if total_pos_count == 1:
            rd = pos_list[0].get("reg_date")
            rd_str = rd.strftime("%d.%m.%Y") if rd else "Ko'rsatilmagan"
            header += f"📅 Apparat ro'yxatga olingan sana: *{rd_str}*\n"
        else:
            header += "📅 *Apparatlar ro'yxatga olingan sanalari:*\n"
            for idx, p in enumerate(pos_list, 1):
                rd = p.get("reg_date")
                rd_str = rd.strftime("%d.%m.%Y") if rd else "Ko'rsatilmagan"
                status_suffix = " (❌ ro'yxatdan chiqarilgan, hisoblanmaydi)" if p.get("color_type") == "red" else ""
                header += f"  • {idx}-aparat{status_suffix}: *{rd_str}*\n"

        lines = ["\n🗓 *Oylik to'lovlar holati:*"]
        for m_name, m_idx in month_keys:
            if m_idx < start_month:
                continue
            paid = agg_paid[m_name]
            if paid > 0:
                paid_str = f"{paid:,.0f}".replace(",", " ")
                lines.append(f"  • *{m_name}:* ✅ *{paid_str} so'm* to'langan")
            elif m_idx < current_month:
                lines.append(f"  • *{m_name}:* ❌ To'lanmagan (0 so'm)")
            elif m_idx == current_month:
                lines.append(f"  • *{m_name}:* ⚠️ To'lanmagan (0 so'm)")
            else:
                lines.append(f"  • *{m_name}:* ⏳ Kelgusi oy (0 so'm)")

        # Umumiy hisob-kitob ko'rsatkichlari (qisqa, aniq va tushunarli xulosa)
        jami_tolangan = sum(agg_paid.values())
        jami_tolangan_str = f"{jami_tolangan:,.0f}".replace(",", " ")

        pos_rate = (active_count if active_count > 0 else 1) * 100000.0
        # Joriy yil bo'yicha hisoblangan summa
        calc_total = sum(agg_calc[m_name] for m_name, m_idx in month_keys if m_idx >= start_month)
        if calc_total == 0.0 and start_month <= current_month:
            calc_total = (current_month - start_month + 1) * pos_rate
        calc_total_str = f"{calc_total:,.0f}".replace(",", " ")

        summary_lines = ["\n📋 *Hisob-kitob xulosasi:*"]

        # 1. Eski yildan o'tgan avans yoki qarz
        if total_prev_year_balance > 0:
            summary_lines.append(f"• *O'tgan yildan qolgan qarz:* {total_prev_year_balance:,.0f} so'm".replace(",", " "))
        elif total_prev_year_balance < 0:
            summary_lines.append(f"• *O'tgan yildan o'tgan haqdorlik (avans):* {abs(total_prev_year_balance):,.0f} so'm".replace(",", " "))
        else:
            summary_lines.append("• *O'tgan yildan:* Qarzdorlik yoki avans yo'q (0 so'm)")

        # 2. Joriy yil bo'yicha to'lanishi kerak bo'lgan summa
        summary_lines.append(f"• *Joriy yil bo'yicha hozirgi oygacha to'lanishi kerak bo'lgan summa:* {calc_total_str} so'm")

        # 3. Jami to'langan summa
        summary_lines.append(f"• *Jami to'langan summa:* {jami_tolangan_str} so'm")
        summary_lines.append("────────────────────────────")

        # 4. Hozirgi yakuniy qoldiq (qarz yoki avans)
        if total_qoldiq_raw > 0:
            qoldiq_str = f"{total_qoldiq_raw:,.0f}".replace(",", " ")
            summary_lines.append(f"⚠️ *Hozirgi qarzdorlik:* *{qoldiq_str} so'm*")
            summary_lines.append("Iltimos, kassa apparatlaringiz uzluksiz ishlashi uchun to'lovni amalga oshiring.")
        elif total_qoldiq_raw < 0:
            avans_str = f"{abs(total_qoldiq_raw):,.0f}".replace(",", " ")
            summary_lines.append(f"💰 *Hisobingizdagi ortiqcha to'lov (avans):* *{avans_str} so'm*")
            summary_lines.append("✅ *Eslatma:* Qarzdorlik mavjud emas, apparatingiz oylik abonent tomonlama faol holatda.")
        else:
            summary_lines.append("📌 *Hozirgi qoldiq:* *0 so'm*")
            summary_lines.append("✅ *Eslatma:* Barcha to'lovlar to'liq to'langan, apparatingiz oylik abonent tomonlama faol holatda.")

        return header + "\n".join(lines) + "\n" + "\n".join(summary_lines)

    def find_by_fm(self, fm_number):
        """FM raqami bo'yicha qidirish"""
        self.load_data()
        cleaned = re.sub(r"\s+", "", str(fm_number)).upper()
        for pos_list in self.cache_by_inn.values():
            for p in pos_list:
                if p.get("pos_id") and cleaned in str(p["pos_id"]).upper():
                    return p
        return None

    def find_by_org_name(self, org_name):
        """Tashkilot nomi bo'yicha qidirish"""
        if not org_name:
            return None
        self.load_data()
        norm_target = re.sub(r"[^\w\s]", "", str(org_name)).strip().lower()
        if len(norm_target) < 3:
            return None
        for inn, pos_list in self.cache_by_inn.items():
            if pos_list and pos_list[0].get("org_name"):
                cand = re.sub(r"[^\w\s]", "", str(pos_list[0]["org_name"])).strip().lower()
                if norm_target in cand or cand in norm_target:
                    return self.find_by_identifier(inn)
        return None

    def update_excel_file(self, new_file_path):
        """Yangi kelgan Excel faylni o'rnatish va zaxiralash"""
        os.makedirs(config.BACKUP_DIR, exist_ok=True)
        if os.path.exists(self.excel_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(config.BACKUP_DIR, f"abonent_{timestamp}.xlsx")
            try:
                shutil.copy2(self.excel_path, backup_path)
            except Exception:
                pass

        target_path = os.path.join(config.DATA_DIR, "abonent_jadvali.xlsx")
        shutil.copy2(new_file_path, target_path)
        self.excel_path = target_path
        self.load_data()
        return len(self.cache_by_inn)

# Global servis
excel_service = ExcelService()
