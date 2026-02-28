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
        'DITHLIC', 'HARVARDDEVEN', 'HARVARD-DEVEN', 'PEMES', 'MAG', 'MAS', 'ATH', 'KN', 'KOS', 'OAK',
        'COMMONWEALTH', 'MASSACHUSETTS', 'PE',
    ]
    titles = [
        'CIVIL', 'ENGINEER', 'PROFESSIONAL', 'REGISTERED', 'LICENSE',
        'CERTIFICATE', 'STRUCTURAL', 'STATE', 'OF', 'COMMONWEALTH',
        'ENVIRONMENTAL', 'ENVIRONMENTAL]', 'NATIONAL', 'BOARD', 'REGISTRATION',
        'MENTAL', 'MENTAL]', 'EN', 'WY', 'AL', 'S|', 'OS', 'FIC', 'AOS', 'II', 'O/', 'ENVI', 'RONMENTAL',
    ]
    return blacklist, titles


def _is_valid_name_fragment(clean_l):
    """Return True if text looks like part of an engineer name."""
    blacklist, titles = get_blacklist_and_titles()
    if not clean_l or len(clean_l) < 2:
        return False
    # Filter circular text artifacts: "XX OF XX", "XX OF MAS", etc.
    if re.search(r'\bOF\b', clean_l):
        return False
    # Filter if it contains digits
    if re.search(r'\d', clean_l):
        return False
    # Filter blacklist (exact match on whole line)
    if clean_l in blacklist or clean_l in titles:
        return False
    # Filter lines that are just 1-2 chars (noise)
    if len(re.sub(r'\s', '', clean_l)) < 3:
        return False
    return True


def extract_engineer_name_near_idx(lines, anchor_idx, lines_data=None):
    """Find engineer name lines near the license number line.
    Uses spatial proximity if lines_data (with bbox) is provided."""
    candidates = []

    # Prefer spatial search if we have bbox data
    if lines_data and anchor_idx < len(lines_data):
        anchor_y = lines_data[anchor_idx]["bbox"][1]  # top-y of license line
        anchor_x = lines_data[anchor_idx]["bbox"][0]

        for i, ld in enumerate(lines_data):
            if i == anchor_idx:
                continue
            lx, ly, lw, lh = ld["bbox"]
            # Must be above the license line (smaller y) and within stamp width
            dy = anchor_y - ly
            dx = abs(lx - anchor_x)
            if dy < 0 or dy > 400:  # above by up to 400px
                continue
            if dx > 300:  # horizontally close
                continue
            clean_l = re.sub(r'[^A-Z\s\.]', '', lines[i].upper()).strip()
            if _is_valid_name_fragment(clean_l):
                candidates.append((dy, clean_l, i))

        if candidates:
            # Sort by distance from license (closest first), take best 2
            candidates.sort(key=lambda x: x[0])
            best = sorted(candidates[:4], key=lambda x: x[2])  # sort by line index
            return " ".join(c[1] for c in best[:2])

    # Fallback: line-index proximity search
    for offset in range(1, 7):
        for i in [anchor_idx - offset, anchor_idx + offset]:
            if i < 0 or i >= len(lines):
                continue
            clean_l = re.sub(r'[^A-Z\s\.]', '', lines[i].upper()).strip()
            if _is_valid_name_fragment(clean_l):
                candidates.append((offset, clean_l, i))
        if len(candidates) >= 2:
            break

    if not candidates:
        return None
    sorted_by_idx = sorted(candidates[:2], key=lambda x: x[2])
    return " ".join([c[1] for c in sorted_by_idx])


def extract_fields_multi(image):
    # OCR with word-level boxes
    # PSM 11 = sparse text, find as much text as possible (best for stamps with circular/rotated text)
    # OEM 1 = LSTM neural net mode (better accuracy for varied fonts)
    data = pytesseract.image_to_data(image, config=r'--oem 1 --psm 11', lang='eng')
    # Also get raw text for debugging
    raw_text = pytesseract.image_to_string(image, config=r'--oem 1 --psm 11', lang='eng')
    print(f"[OCR DEBUG] Raw text found: {raw_text[:200] if raw_text else 'NONE'}")
    rows = data.split('\n')
    if not rows:
        return []
    header = rows[0].split('\t')
    try:
        idx_text = header.index('text')
        idx_left = header.index('left')
        idx_top = header.index('top')
        idx_width = header.index('width')
        idx_height = header.index('height')
        idx_line = header.index('line_num')
        idx_block = header.index('block_num')
    except ValueError:
        return []

    line_map = {}
    for row in rows[1:]:
        cols = row.split('\t')
        if len(cols) <= idx_text:
            continue
        text = cols[idx_text].strip()
        if not text:
            continue
        key = (cols[idx_block], cols[idx_line])
        word_info = {
            "text": text,
            "left": int(cols[idx_left]),
            "top": int(cols[idx_top]),
            "width": int(cols[idx_width]),
            "height": int(cols[idx_height]),
        }
        if key not in line_map:
            line_map[key] = []
        line_map[key].append(word_info)

    lines_data = []
    for key in sorted(line_map.keys()):
        words = line_map[key]
        full_text = " ".join([w["text"] for w in words])
        lx = min(w["left"] for w in words)
        ly = min(w["top"] for w in words)
        lw = sum(w["width"] for w in words)
        lh = max(w["height"] for w in words)
        lines_data.append({"text": full_text, "bbox": (lx, ly, lw, lh)})

    cleaned_lines = [clean_scattered_text(ld["text"]) for ld in lines_data]

    results = []
    processed_licenses = set()
    # Match 4-6 digit license numbers; allow optional leading noise char
    license_pattern = r'\b\d{4,6}\b'

    for i, line_text in enumerate(cleaned_lines):
        # Clean line text: remove common OCR artifacts around numbers
        # "0, 39479" → "39479", "No. 39479" → "39479"
        cleaned_for_lic = re.sub(r'[Oo0][\s,\.]+', ' ', line_text)  # Remove leading O/0 with punctuation
        cleaned_for_lic = re.sub(r'[Nn][Oo0]\.?\s*', ' ', cleaned_for_lic)  # Remove "No." prefix

        matches = re.findall(license_pattern, cleaned_for_lic)
        for lic in matches:
            # Skip obvious years (19xx, 20xx) but only if exactly 4 digits
            # This allows partial reads like "1926" which might be "55926" with OCR error
            if len(lic) == 4 and (lic.startswith('19') or lic.startswith('20')):
                continue
            # Skip very small numbers (noise)
            if int(lic) < 1000:
                continue
            if lic in processed_licenses:
                continue

            name = extract_engineer_name_near_idx(cleaned_lines, i, lines_data)
            lx, ly, lw, lh = lines_data[i]["bbox"]

            results.append({
                "engineer_name": name,
                "license_number": lic,
                "relative_bbox": [lx - 50, ly - 200, lw + 100, lh + 400]
            })
            processed_licenses.add(lic)

    return results


# Alias for compatibility
extract_fields_with_boxes = extract_fields_multi
