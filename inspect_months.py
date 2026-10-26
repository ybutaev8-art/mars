import zipfile
import xml.etree.ElementTree as ET
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with zipfile.ZipFile('data/abonent_jadvali.xlsx', 'r') as z:
    tree = ET.parse(z.open('xl/sharedStrings.xml'))
    root = tree.getroot()
    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    shared_strings = [''.join(t.text or '' for t in si.findall('.//ns:t', ns)) for si in root.findall('.//ns:si', ns)]
    
    stree = ET.parse(z.open('xl/worksheets/sheet1.xml'))
    sroot = stree.getroot()
    
    row1 = sroot.find('.//ns:row[@r="1"]', ns)
    row2 = sroot.find('.//ns:row[@r="2"]', ns)
    
    row1_dict = {}
    if row1 is not None:
        for c in row1.findall('ns:c', ns):
            v = c.find('ns:v', ns)
            val = v.text if v is not None else ''
            if c.get('t') == 's' and val.isdigit():
                val = shared_strings[int(val)]
            col = ''.join(filter(str.isalpha, c.get('r')))
            if val:
                row1_dict[col] = val

    row2_dict = {}
    if row2 is not None:
        for c in row2.findall('ns:c', ns):
            v = c.find('ns:v', ns)
            val = v.text if v is not None else ''
            if c.get('t') == 's' and val.isdigit():
                val = shared_strings[int(val)]
            col = ''.join(filter(str.isalpha, c.get('r')))
            row2_dict[col] = val

    print("=== Row 1 Sarlavhalari (Guruhlar) ===")
    for col, val in row1_dict.items():
        print(f"Col {col}: {val}")

    print("\n=== Row 2 Sarlavhalari (Oylar) va Row 1 dagi guruhi ===")
    current_group = ""
    for col, val in row2_dict.items():
        if col in row1_dict:
            current_group = row1_dict[col]
        if val:
            print(f"Col {col} ({current_group}): {val}")

    print("\n=== Row 6473 (312420017) dagi barcha qiymatlar ===")
    row6473 = sroot.find('.//ns:row[@r="6473"]', ns)
    for c in row6473.findall('ns:c', ns):
        v = c.find('ns:v', ns)
        val = v.text if v is not None else ''
        if c.get('t') == 's' and val.isdigit():
            val = shared_strings[int(val)]
        col = ''.join(filter(str.isalpha, c.get('r')))
        h2 = row2_dict.get(col, '')
        print(f"  {col} ({h2}): {val}")
