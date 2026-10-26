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
    
    row2 = sroot.find('.//ns:row[@r="2"]', ns)
    if row2 is not None:
        for c in row2.findall('ns:c', ns):
            v = c.find('ns:v', ns)
            val = v.text if v is not None else ''
            if c.get('t') == 's' and val.isdigit():
                val = shared_strings[int(val)]
            col_letter = ''.join(filter(str.isalpha, c.get('r')))
            print(f'{col_letter}: {val}')
