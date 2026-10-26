import zipfile
import xml.etree.ElementTree as ET
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with zipfile.ZipFile('data/abonent_jadvali.xlsx', 'r') as z:
    # Shared strings
    tree = ET.parse(z.open('xl/sharedStrings.xml'))
    root = tree.getroot()
    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    shared_strings = []
    for si in root.findall('.//ns:si', ns):
        texts = si.findall('.//ns:t', ns)
        shared_strings.append(''.join(t.text or '' for t in texts))
    
    print(f'Total shared strings: {len(shared_strings)}')
    
    # 312420017 qaysi indekslarda?
    target_indices = set()
    for idx, s in enumerate(shared_strings):
        if '312420017' in s:
            print(f'Found in shared_strings[{idx}]: {repr(s)}')
            target_indices.add(str(idx))
            
    # Varaqlarni tekshiramiz
    wb_tree = ET.parse(z.open('xl/workbook.xml'))
    rels_tree = ET.parse(z.open('xl/_rels/workbook.xml.rels'))
    rel_ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
    id_to_target = {r.get('Id'): r.get('Target') for r in rels_tree.getroot().findall('.//r:Relationship', rel_ns)}
    
    for s in wb_tree.getroot().findall('.//ns:sheet', ns):
        name = s.get('name')
        r_id = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = 'xl/' + id_to_target[r_id]
        print(f'\nChecking Sheet: {name} ({target})')
        
        stree = ET.parse(z.open(target))
        sroot = stree.getroot()
        
        # Sarlavhalarni topish (birinchi 5 qator)
        for r_idx, row in enumerate(sroot.findall('.//ns:row', ns)[:5]):
            r_vals = []
            for c in row.findall('ns:c', ns):
                v = c.find('ns:v', ns)
                val = v.text if v is not None else ''
                t = c.get('t')
                if t == 's' and val.isdigit():
                    val = shared_strings[int(val)]
                r_vals.append(val)
            print(f'  Row {row.get("r")}: {r_vals[:12]}')

        # Qidirish
        for row in sroot.findall('.//ns:row', ns):
            row_num = row.get('r')
            for c in row.findall('ns:c', ns):
                v = c.find('ns:v', ns)
                if v is not None and v.text in target_indices:
                    print(f'  ===> MATCH in row {row_num}, cell {c.get("r")}!')
                    # Butun qatorni ko'rsatamiz
                    full_row = []
                    for rc in row.findall('ns:c', ns):
                        rv = rc.find('ns:v', ns)
                        rval = rv.text if rv is not None else ''
                        if rc.get('t') == 's' and rval.isdigit():
                            rval = shared_strings[int(rval)]
                        full_row.append((rc.get('r'), rval, rc.get('s')))
                    print(f'  Full row content: {full_row}')
