import re
import fitz
from PIL import Image

def open_pdf(file_bytes):
    return fitz.open(stream=file_bytes, filetype="pdf")

def get_page_dimensions(doc, page_number):
    page = doc[page_number]
    rect = page.rect
    return rect.width, rect.height

def render_page_to_image(doc, page_number, dpi=300):
    page = doc[page_number]
    pix = page.get_pixmap(dpi=dpi)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

def crop_bbox(image, bbox):
    x, y, w, h = bbox
    return image.crop((x, y, x + w, y + h))

def get_stamp_bboxes_from_pdf(doc, page_number, dpi=150):
    """
    Use the PDF text layer to find stamp positions and engineer names.
    Returns list of dicts: {bbox: (x,y,w,h), license: str, name: str|None}
    Falls back to image-based detection if no licenses found.
    """
    page = doc[page_number]
    scale = dpi / 72.0
    rotation = page.rotation
    mb = page.mediabox

    def to_screen(x_nat, y_nat):
        if rotation == 270:
            return y_nat * scale, (mb.width - x_nat) * scale
        elif rotation == 90:
            return (mb.height - y_nat) * scale, x_nat * scale
        elif rotation == 180:
            return (mb.width - x_nat) * scale, (mb.height - y_nat) * scale
        else:
            return x_nat * scale, y_nat * scale

    words = page.get_text("words")
    license_pattern = re.compile(r'^\d{5}$')
    skip_licenses = {'01085', '01086'}  # Skip town permit numbers, not engineer stamps

    # Build a list of all words with screen coordinates
    word_list = []
    for w in words:
        sx, sy = to_screen((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)
        word_list.append({"text": w[4].strip(), "sx": sx, "sy": sy})

    name_blacklist = {
        'CIVIL', 'ENGINEER', 'PROFESSIONAL', 'REGISTERED', 'LICENSE',
        'STRUCTURAL', 'ENVIRONMENTAL', 'COMMONWEALTH', 'MASSACHUSETTS',
        'NO.', 'NO', 'PE', 'OF', 'THE', 'AND', 'FOR',
    }

    found = []
    seen_licenses = set()

    for w in word_list:
        lic = w["text"]
        if not license_pattern.match(lic):
            continue
        if lic.startswith('19') or lic.startswith('20') or lic in skip_licenses:
            continue
        if lic in seen_licenses:
            continue
        seen_licenses.add(lic)

        cx, cy = w["sx"], w["sy"]
        radius = int(280 * (dpi / 150))
        bx = max(0, int(cx) - radius)
        by = max(0, int(cy) - radius)
        bbox = (bx, by, radius * 2, radius * 2)

        # Find name words near this license (within ~200px in screen space)
        nearby_names = []
        for ww in word_list:
            if ww is w:
                continue
            dist = ((ww["sx"] - cx) ** 2 + (ww["sy"] - cy) ** 2) ** 0.5
            if dist > 200:
                continue
            txt = re.sub(r'[^A-Z\s\.]', '', ww["text"].upper()).strip()
            if not txt or len(txt) < 2:
                continue
            if txt in name_blacklist or txt.isdigit():
                continue
            if re.search(r'\bOF\b', txt):
                continue
            nearby_names.append((dist, txt))

        nearby_names.sort(key=lambda x: x[0])
        unique_names = list(dict.fromkeys(n[1] for n in nearby_names))
        name = " ".join(unique_names[:3]) if unique_names else None

        found.append({"bbox": bbox, "license": lic, "name": name})

    return found
