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
    Uses HoughCircles to detect circular stamp seals in the right title block.
    Falls back to contour detection if no circles found.
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

    # First try: Detect circular stamps using HoughCircles
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=200,  # Stamps should be at least 200px apart
        param1=50,
        param2=30,
        minRadius=80,  # Stamps are typically 160-600px diameter
        maxRadius=300
    )

    # If circles found, use them
    if circles is not None:
        circles = np.uint16(np.around(circles))
        result = []
        for circle in circles[0, :]:
            cx, cy, radius = circle
            # Convert circle to bounding box
            bx = max(0, sx + cx - radius - BBOX_MARGIN)
            by = max(0, sy + cy - radius - BBOX_MARGIN)
            size = (radius + BBOX_MARGIN) * 2
            bw = min(size, img_w - bx)
            bh = min(size, img_h - by)
            result.append((bx, by, bw, bh))

        if result:
            return result[:4]  # Return up to 4 stamps

    # No circles found - use heuristic fallback
    return [_heuristic_fallback(img_w, img_h)]


def _heuristic_fallback(page_width: int, page_height: int):
    aspect = page_width / page_height
    if aspect > LANDSCAPE_ASPECT_THRESHOLD:
        return int(page_width * 0.77), int(page_height * 0.05), int(page_width * 0.22), int(page_height * 0.60)
    else:
        return int(page_width * 0.58), int(page_height * 0.65), int(page_width * 0.37), int(page_height * 0.30)
