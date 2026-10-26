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
    fills_elem = sroot.find('ns:fills', ns)
    if fills_elem is not None:
        for idx, f in enumerate(fills_elem.findall('ns:fill', ns)):
            pat = f.find('ns:patternFill', ns)
            info = {'idx': idx, 'pattern': pat.get('patternType') if pat is not None else None}
            if pat is not None:
                fg = pat.find('ns:fgColor', ns)
                if fg is not None:
                    info['rgb'] = fg.get('rgb')
                    info['indexed'] = fg.get('indexed')
                    info['theme'] = fg.get('theme')
                    info['tint'] = fg.get('tint')
            fills.append(info)
            if info.get('rgb') or info.get('indexed') or info.get('theme'):
                print(f'Fill {idx}: {info}')
                
    cell_xfs = sroot.find('ns:cellXfs', ns)
    xfs = []
    if cell_xfs is not None:
        for idx, xf in enumerate(cell_xfs.findall('ns:xf', ns)):
            fill_id = int(xf.get('fillId', 0))
            apply_fill = xf.get('applyFill')
            xfs.append({'fillId': fill_id, 'applyFill': apply_fill, 'fill': fills[fill_id] if fill_id < len(fills) else None})

    print(f'Total fills: {len(fills)}, total cellXfs: {len(xfs)}')
    
    # 6473 qatoridagi kataklarning stillari
    stree2 = ET.parse(z.open('xl/worksheets/sheet1.xml'))
    sroot2 = stree2.getroot()
    row6473 = sroot2.find('.//ns:row[@r="6473"]', ns)
    print(f'Row 6473 s attribute: {row6473.get("s")}')
    for c in row6473.findall('ns:c', ns)[:6]:
        s_id = int(c.get('s', 0))
        xf_info = xfs[s_id] if s_id < len(xfs) else None
        print(f'  Cell {c.get("r")} s={s_id} -> {xf_info}')

    # Jadvaldagi qizil va sariq qatorlarni topib tekshiramiz
    print("\n--- Namuna qizil va sariq qatorlarni qidiramiz ---")
    colored_found = {}
    for r in sroot2.findall('.//ns:row', ns)[2:500]:
        r_num = r.get('r')
        row_s = r.get('s')
        cells = r.findall('ns:c', ns)
        for c in cells:
            s_id = int(c.get('s', 0))
            if s_id < len(xfs):
                f = xfs[s_id]['fill']
                if f and (f.get('rgb') or f.get('indexed') or f.get('theme')):
                    key = str(f.get('rgb') or f.get('indexed') or f.get('theme'))
                    if key not in colored_found:
                        colored_found[key] = (r_num, c.get('r'), f)
    for k, v in colored_found.items():
        print(f'Color key {k}: Row {v[0]}, Cell {v[1]}, Info: {v[2]}')
