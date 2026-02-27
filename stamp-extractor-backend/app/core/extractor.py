import re
import pytesseract

def clean_scattered_text(text):
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if re.match(r'^([A-Z]\s+){2,}[A-Z]$', line.strip()):
            cleaned_line = line.replace(' ', '')
            cleaned_lines.append(cleaned_line)
        else:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def get_blacklist_and_titles():
    blacklist = [
        'NOT FOR', 'CONSTRUCTION', 'RECORD ONLY', 'PRELIMINARY', 'FOR REVIEW', 
        'PLANS', 'ISSUED', 'DOCUMENT', 'INCOMPLETE', 'RELEASED', 'TEMPORARILY',
        'PROGRESS', 'INTENDED', 'INTENDICD', 'BIDDING', 'PURPOSES', 'DRAWINGS', 'PERMIT',
        'REVIEW', 'ONLY', 'HARVARD', 'WATER', 'SYSTEM', 'PROJECT', 'PUBLIC', 'THIS', 'NOT',
        'AUF', 'MASS', 'STAMP', 'SEAL', 'DATE', 'SIGNED', 'SIGNATURE', 'YSTEM', 'ECT',
        'ANY', 'OND', 'OF', 'THE', 'AND', 'FOR', 'HIS', 'PROJECT', 'DESCRIPTION', 'INTERCONNECTION',
        'DITHLIC', 'HARVARDDEVEN', 'HARVARD-DEVEN', 'PEMES', 'MAG', 'MAS', 'ATH', 'KN', 'KOS', 'OAK'
    ]
    titles = [
        'CIVIL', 'ENGINEER', 'PROFESSIONAL', 'REGISTERED', 'LICENSE', 
        'CERTIFICATE', 'STRUCTURAL', 'STATE', 'OF', 'COMMONWEALTH',
        'ENVIRONMENTAL', 'ENVIRONMENTAL]', 'NATIONAL', 'BOARD', 'REGISTRATION',
        'MENTAL', 'MENTAL]', 'EN', 'WY', 'AL', 'S|', 'OS', 'FIC', 'AOS', 'II', 'O/', 'ENVI', 'RONMENTAL'
    ]
    return blacklist, titles

def extract_engineer_name_near_idx(lines, anchor_idx):
    blacklist, titles = get_blacklist_and_titles()
    candidates = []
    for offset in range(1, 9):
        for i in [anchor_idx - offset, anchor_idx + offset]:
            if i < 0 or i >= len(lines): continue
            line = lines[i]
            clean_l = re.sub(r'[^A-Z\s\.]', '', line.upper()).strip()
            if (len(clean_l) >= 3 or (len(clean_l) == 2 and clean_l.endswith('.'))) and not re.search(r'\d', clean_l):
                if clean_l not in titles and not any(b == clean_l for b in blacklist):
                    if clean_l not in [c[1] for c in candidates]:
                        candidates.append((offset, clean_l, i))
        if len(candidates) >= 2: break
    if not candidates: return None
    sorted_by_idx = sorted(candidates[:2], key=lambda x: x[2])
    return " ".join([c[1] for c in sorted_by_idx])

def extract_fields_multi(image):
    # OCR with boxes
    data = pytesseract.image_to_data(image, config=r'--oem 3 --psm 12')
    rows = data.split('\n')
    if not rows: return []
    header = rows[0].split('\t')
    try:
        idx_text, idx_left, idx_top, idx_width, idx_height, idx_line, idx_block = \
            header.index('text'), header.index('left'), header.index('top'), \
            header.index('width'), header.index('height'), header.index('line_num'), header.index('block_num')
    except ValueError: return []

    line_map = {}
    for row in rows[1:]:
        cols = row.split('\t')
        if len(cols) <= idx_text: continue
        text = cols[idx_text].strip()
        if not text: continue
        key = (cols[idx_block], cols[idx_line])
        word_info = {"text": text, "left": int(cols[idx_left]), "top": int(cols[idx_top]), "width": int(cols[idx_width]), "height": int(cols[idx_height])}
        if key not in line_map: line_map[key] = []
        line_map[key].append(word_info)

    lines_data = []
    for key in sorted(line_map.keys()):
        words = line_map[key]
        full_text = " ".join([w["text"] for w in words])
        lx, ly = min([w["left"] for w in words]), min([w["top"] for w in words])
        lw, lh = sum([w["width"] for w in words]), max([w["height"] for w in words])
        lines_data.append({"text": full_text, "bbox": (lx, ly, lw, lh)})

    cleaned_lines = [clean_scattered_text(ld["text"]) for ld in lines_data]
    
    results = []
    processed_licenses = set()
    license_pattern = r'\b\d{4,6}\b'
    
    for i, line_text in enumerate(cleaned_lines):
        matches = re.findall(license_pattern, line_text)
        for lic in matches:
            if lic.startswith('19') or lic.startswith('20'): continue
            if lic in processed_licenses: continue
            
            name = extract_engineer_name_near_idx(cleaned_lines, i)
            lx, ly, lw, lh = lines_data[i]["bbox"]
            
            results.append({
                "engineer_name": name,
                "license_number": lic,
                "relative_bbox": [lx - 50, ly - 200, lw + 100, lh + 400]
            })
            processed_licenses.add(lic)
            
    return results
