"""
Rangli qatorlarga ega haqiqiy .xlsx fayl yaratuvchi skript
OpenXML formatida (qizil, sariq, rangsiz qatorlar)
"""
import zipfile
import io
import os

def create_styled_excel(output_path):
    # XML larni tayyorlaymiz
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    wb_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>"""

    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    # Styles:
    # fill 0: none
    # fill 1: gray125
    # fill 2: RED (FFFF0000)
    # fill 3: YELLOW (FFFFFF00)
    # xf 0: default
    # xf 1: red fill
    # xf 2: yellow fill
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="4">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFF0000"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFFF00"/></patternFill></fill>
  </fills>
  <borders count="1"><border><left/><right/><top/><bottom/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="0" fillId="2" borderId="0" xfId="0" applyFill="1"/>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1"/>
  </cellXfs>
</styleSheet>"""

    # Shared Strings
    strings = [
        "INN/JSHSHIR", "Tashkilot Nomi", "Oylik Qarzdorlik", "FM Raqami", "Yillik Muddati",
        "123456789", "MARS TEST SAVDO MCHJ (1-aparat)", "150000", "FM123456789012", "01.05.2026", # row 2: yellow (P3)
        "MARS TEST SAVDO MCHJ (2-aparat)", "0", "FM123456789013", "10.06.2026", # row 3: white (SmartOne)
        "987654321", "BARAKA NON YATT", "FM987654321098", "15.11.2026", # row 4: yellow (P3)
        "777888999", "FAOLIYATI TO'XTATILGAN MCHJ", "FM777888999000", "01.01.2025", # row 5: red (Ro'yxatdan chiqarilgan)
        "305123456", "MEGA MARKET MCHJ", "FM305123456001", "20.12.2026" # row 6: white (SmartOne)
    ]
    str_xml_items = "".join(f"<si><t>{s}</t></si>" for s in strings)
    shared_strings = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">
  {str_xml_items}
</sst>"""

    # Sheet1
    # row 1: Header (s=0)
    # row 2: 123456789 (s=2 - yellow -> P3)
    # row 3: 123456789 (s=0 - white -> SmartOne)
    # row 4: 987654321 (s=2 - yellow -> P3)
    # row 5: 777888999 (s=1 - red -> Ro'yxatdan chiqarilgan)
    # row 6: 305123456 (s=0 - white -> SmartOne)
    sheet1 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="s"><v>0</v></c>
      <c r="B1" t="s"><v>1</v></c>
      <c r="C1" t="s"><v>2</v></c>
      <c r="D1" t="s"><v>3</v></c>
      <c r="E1" t="s"><v>4</v></c>
    </row>
    <row r="2" s="2">
      <c r="A2" s="2" t="s"><v>5</v></c>
      <c r="B2" s="2" t="s"><v>6</v></c>
      <c r="C2" s="2" t="s"><v>7</v></c>
      <c r="D2" s="2" t="s"><v>8</v></c>
      <c r="E2" s="2" t="s"><v>9</v></c>
    </row>
    <row r="3" s="0">
      <c r="A3" s="0" t="s"><v>5</v></c>
      <c r="B3" s="0" t="s"><v>10</v></c>
      <c r="C3" s="0" t="s"><v>11</v></c>
      <c r="D3" s="0" t="s"><v>12</v></c>
      <c r="E3" s="0" t="s"><v>13</v></c>
    </row>
    <row r="4" s="2">
      <c r="A4" s="2" t="s"><v>14</v></c>
      <c r="B4" s="2" t="s"><v>15</v></c>
      <c r="C4" s="2" t="s"><v>11</v></c>
      <c r="D4" s="2" t="s"><v>16</v></c>
      <c r="E4" s="2" t="s"><v>17</v></c>
    </row>
    <row r="5" s="1">
      <c r="A5" s="1" t="s"><v>18</v></c>
      <c r="B5" s="1" t="s"><v>19</v></c>
      <c r="C5" s="1" t="s"><v>11</v></c>
      <c r="D5" s="1" t="s"><v>20</v></c>
      <c r="E5" s="1" t="s"><v>21</v></c>
    </row>
    <row r="6" s="0">
      <c r="A6" s="0" t="s"><v>22</v></c>
      <c r="B6" s="0" t="s"><v>23</v></c>
      <c r="C6" s="0" t="s"><v>11</v></c>
      <c r="D6" s="0" t="s"><v>24</v></c>
      <c r="E6" s="0" t="s"><v>25</v></c>
    </row>
  </sheetData>
</worksheet>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/sharedStrings.xml", shared_strings)
        z.writestr("xl/worksheets/sheet1.xml", sheet1)

    print(f"[OK] Haqiqiy rangli test .xlsx fayli yaratildi: {output_path}")

if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "data", "abonent_jadvali.xlsx")
    create_styled_excel(target)
