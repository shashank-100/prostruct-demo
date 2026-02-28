import cv2
import numpy as np
from PIL import Image

LANDSCAPE_ASPECT_THRESHOLD = 1.3
# 0.77 keeps us inside the title block column, away from the drawing area
LANDSCAPE_SEARCH_X_START = 0.77
PORTRAIT_SEARCH_X_START = 0.55
PORTRAIT_SEARCH_Y_START = 0.55

BBOX_MARGIN = 40


def detect_stamp_region(page_image: Image.Image):
    """
    Returns a LIST of bounding boxes for all detected stamps.
    Uses Canny edge detection to find stamp box borders.
    Falls back to heuristic if nothing found.
    """
    img_w, img_h = page_image.size
    aspect = img_w / img_h

    if aspect > LANDSCAPE_ASPECT_THRESHOLD:
        sx, sy = int(img_w * LANDSCAPE_SEARCH_X_START), 0
    else:
        sx, sy = int(img_w * PORTRAIT_SEARCH_X_START), int(img_h * PORTRAIT_SEARCH_Y_START)

    search_crop = page_image.crop((sx, sy, img_w, img_h))
    gray = np.array(search_crop.convert("L"))
    rw, rh = search_crop.size

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for cnt in contours:
        bx, by, bw, bh = cv2.boundingRect(cnt)
        area_frac = (bw * bh) / (rw * rh)
        box_aspect = bw / bh if bh > 0 else 0
        if area_frac < 0.01 or area_frac > 0.65:
            continue
        if box_aspect < 0.3 or box_aspect > 5.0:
            continue
        candidates.append((sx + bx, sy + by, bw, bh))

    if not candidates:
        return [_heuristic_fallback(img_w, img_h)]

    candidates.sort(key=lambda c: c[2] * c[3], reverse=True)

    result = []
    seen = []
    for (fx, fy, fw, fh) in candidates[:6]:
        if any(abs(fx - s[0]) < 200 and abs(fy - s[1]) < 200 for s in seen):
            continue
        seen.append((fx, fy))

        bx = max(0, fx - BBOX_MARGIN)
        by = max(0, fy - BBOX_MARGIN)
        bw = min(fw + 2 * BBOX_MARGIN, img_w - bx)
        bh = min(fh + 2 * BBOX_MARGIN, img_h - by)

        # Wide box = two stamps side by side → split in half
        if bw > 1.4 * bh:
            half = bw // 2
            result.append((bx, by, half, bh))
            result.append((bx + half, by, bw - half, bh))
        else:
            result.append((bx, by, bw, bh))

        if len(result) >= 4:
            break

    return result if result else [_heuristic_fallback(img_w, img_h)]


def _heuristic_fallback(page_width: int, page_height: int):
    aspect = page_width / page_height
    if aspect > LANDSCAPE_ASPECT_THRESHOLD:
        return int(page_width * 0.77), int(page_height * 0.05), int(page_width * 0.22), int(page_height * 0.60)
    else:
        return int(page_width * 0.58), int(page_height * 0.65), int(page_width * 0.37), int(page_height * 0.30)
