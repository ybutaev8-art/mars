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
    yellow_rows = []
    for r in sroot2.findall('.//ns:row', ns)[2:500]:
        r_num = r.get('r')
        cells = r.findall('ns:c', ns)[:6]
        for c in cells:
            s_id = int(c.get('s', 0))
            f_id = xfs[s_id] if s_id < len(xfs) else 0
            rgb = fills[f_id] if f_id < len(fills) else None
            if rgb in ['FFFFFF00', 'FFFFEB9C', 'FFFFC000', 'FFFFFFCC', 'FFFFCC99']:
                yellow_rows.append((r_num, c.get('r'), rgb))
                break
    print(f'Found {len(yellow_rows)} yellow rows in first 500 rows:')
    for yr in yellow_rows[:10]:
        print(f'  Row {yr[0]}: {yr[1]} with color {yr[2]}')
