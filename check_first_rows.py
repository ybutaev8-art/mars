import zipfile
import xml.etree.ElementTree as ET
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with zipfile.ZipFile('data/abonent_jadvali.xlsx', 'r') as z:
    stree = ET.parse(z.open('xl/styles.xml'))
    sroot = stree.getroot()
    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    fills = []
    for f in sroot.find('ns:fills', ns).findall('ns:fill', ns):
        pat = f.find('ns:patternFill', ns)
        fg = pat.find('ns:fgColor', ns) if pat is not None else None
        fills.append(fg.get('rgb') if fg is not None else None)
    
    xfs = [int(xf.get('fillId', 0)) for xf in sroot.find('ns:cellXfs', ns).findall('ns:xf', ns)]
    
    stree2 = ET.parse(z.open('xl/worksheets/sheet1.xml'))
    sroot2 = stree2.getroot()
    for r_num in ['3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']:
        row = sroot2.find(f'.//ns:row[@r="{r_num}"]', ns)
        if row is not None:
            c_colors = []
            for c in row.findall('ns:c', ns)[:6]:
                s_id = int(c.get('s', 0))
                f_id = xfs[s_id] if s_id < len(xfs) else 0
                rgb = fills[f_id] if f_id < len(fills) else None
                c_colors.append((c.get('r'), rgb))
            print(f'Row {r_num}: {c_colors}')
