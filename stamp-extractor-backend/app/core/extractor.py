import re

# Words that commonly appear in stamp areas but are NOT engineer names
EXCLUDE_PHRASES = [
    'PREPARED BY', 'TOWN OF', 'STATE OF', 'COMMONWEALTH', 'DEPARTMENT OF',
    'PUBLIC WORKS', 'PERMIT DRAWINGS', 'NOT FOR', 'COMPLETE SET',
    'THIS DOCUMENT', 'RELEASED TEMPORARILY', 'TIGHE BOND', 'ENVIRONMENTAL',
    'CIVIL', 'STRUCTURAL', 'ENGINEER', 'ENGINEERING', 'LICENSED', 'REGISTERED',
    'PROFESSIONAL', 'SEAL', 'SIGNATURE', 'DATE', 'SHEET', 'DRAWING',
    'PROJECT', 'SCALE', 'REVISION', 'APPROVED', 'CHECKED', 'DRAWN',
]

def _clean_ocr_line(line: str) -> str:
    """Remove common OCR noise characters from a line."""
    return re.sub(r'[|_~`@#$%^&*(){}\[\]<>]', '', line).strip()

def extract_engineer_name(text: str):
    lines = [_clean_ocr_line(l) for l in text.split('\n')]

    # Pattern: 2-3 ALL-CAPS words (each 2+ letters) with optional middle initial
    # e.g. "THOMAS A. MAHANNA" or "MARY DANIELSON"
    name_pattern = re.compile(
        r'\b([A-Z]{2,}(?:\s+[A-Z]\.?)?\s+[A-Z]{2,}(?:\s+[A-Z]{2,})?)\b'
    )

    for line in lines:
        upper = line.upper()

        # Skip lines that are clearly not names
        if any(excl in upper for excl in EXCLUDE_PHRASES):
            continue
        if re.search(r'\d', line):
            continue
        if len(line) < 4:
            continue

        matches = name_pattern.findall(upper)
        for name in matches:
            words = name.split()
            # Must be at least 2 words, none a single letter (unless middle initial)
            if len(words) < 2:
                continue
            # Filter single-letter non-initial words
            if any(len(w) == 1 and not w.endswith('.') for w in words):
                continue
            if any(excl in name for excl in EXCLUDE_PHRASES):
                continue
            return re.sub(r'\s+', ' ', name).strip()

    return None


def extract_license_number(text: str):
    # Priority: explicit label + number
    labeled_pattern = re.compile(
        r'(?:NO\.?|LICENSE|LIC\.?|REG\.?|PE|P\.E\.|S\.E\.|NUMBER|#)\s*[:#\-]?\s*(\d{4,8})',
        re.IGNORECASE
    )
    match = labeled_pattern.search(text)
    if match:
        return match.group(1)

    # Fallback: any standalone 4-6 digit number that doesn't look like a year or zip
    for m in re.finditer(r'\b(\d{4,6})\b', text):
        num = m.group(1)
        # Skip likely years
        if re.match(r'^(19|20)\d{2}$', num):
            continue
        return num

    return None


def extract_fields(text: str):
    return {
        "engineer_name": extract_engineer_name(text),
        "license_number": extract_license_number(text)
    }
