import cv2
import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------

# Aspect ratio threshold: pages wider than this are treated as landscape
# drawings with a RIGHT-SIDE vertical title block strip.
LANDSCAPE_ASPECT_THRESHOLD = 1.3

# --- Landscape (right-strip) search window ---
# The title block is a narrow vertical strip on the right edge.
# Search the rightmost 28% of the page, full height.
LANDSCAPE_SEARCH_X_START = 0.72   # 72 % from left → covers right strip
LANDSCAPE_SEARCH_Y_START = 0.00   # full height (stamp can be anywhere in strip)

# --- Portrait / near-square search window ---
# Title block is at the bottom; stamp is in bottom-right corner.
PORTRAIT_SEARCH_X_START = 0.55
PORTRAIT_SEARCH_Y_START = 0.55

# Stamp size bounds as fraction of the FULL page pixel area
MIN_STAMP_AREA_FRAC = 0.0005   # at least 0.05 % of page
MAX_STAMP_AREA_FRAC = 0.06     # no more than 6 %

# Bounding-rect aspect ratio: 1.0 = perfect square (circle).
# We allow a generous range because engineer seals vary slightly.
MIN_SQUARENESS = 0.60
MAX_SQUARENESS = 1.60

# Padding added around the winning bounding rect (pixels at 150 DPI)
BBOX_MARGIN = 14


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_stamp_region(page_image: Image.Image):
    """
    Locate the circular engineer/approval stamp without using Hough circles.

    For LANDSCAPE drawings (aspect > 1.3) the search is restricted to the
    right-side vertical title block strip (rightmost ~28 %, full height).
    For PORTRAIT drawings the search covers the bottom-right corner.

    Detection pipeline (contour-based, no Hough):
      1. Crop the layout-aware search sub-region.
      2. Adaptive-threshold → dilate to close the circular border ring.
      3. Score every external contour by:
           • near-square bounding rect  (circles fit in a square)
           • area in plausible range     (not a stray mark or whole block)
           • fill ratio ≈ 0.15–0.97     (hollow ring with text inside)
           • convex-hull ratio ≥ 0.35   (roughly convex shape)
      4. Return best candidate's bbox (x, y, w, h) in full-image px coords.
      5. Fall back to the heuristic strip / corner if nothing passes.

    Parameters
    ----------
    page_image : PIL.Image
        Full rendered page (RGB), at whatever DPI the caller uses.

    Returns
    -------
    (x, y, w, h) : tuple[int, int, int, int]
        Bounding box in page_image pixel coordinates.
    """
    img_w, img_h = page_image.size
    page_area = img_w * img_h
    aspect = img_w / img_h

    # ── 1. Choose search window based on layout ──────────────────────────────
    if aspect > LANDSCAPE_ASPECT_THRESHOLD:
        # Right-side vertical title block (landscape drawing)
        sx = int(img_w * LANDSCAPE_SEARCH_X_START)
        sy = int(img_h * LANDSCAPE_SEARCH_Y_START)
    else:
        # Bottom-right corner (portrait / near-square drawing)
        sx = int(img_w * PORTRAIT_SEARCH_X_START)
        sy = int(img_h * PORTRAIT_SEARCH_Y_START)

    search_crop = page_image.crop((sx, sy, img_w, img_h))

    # ── 2. Build binary image ─────────────────────────────────────────────────
    gray = np.array(search_crop.convert("L"))

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    binary = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,
        C=6,
    )

    # Dilate so a thin circular border becomes a closed solid ring
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated = cv2.dilate(binary, kernel, iterations=2)

    # ── 3. Contour scoring ────────────────────────────────────────────────────
    contours, _ = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    min_area = page_area * MIN_STAMP_AREA_FRAC
    max_area = page_area * MAX_STAMP_AREA_FRAC

    best_bbox  = None
    best_score = -1.0

    for cnt in contours:
        bx, by, bw, bh = cv2.boundingRect(cnt)
        bbox_area    = bw * bh
        contour_area = cv2.contourArea(cnt)

        if bbox_area < 1:
            continue

        # Area filter (bbox area approximates contour footprint)
        if bbox_area < min_area or bbox_area > max_area:
            continue

        # Squareness: circles have aspect ≈ 1
        sq = bw / bh if bh > 0 else 0
        if sq < MIN_SQUARENESS or sq > MAX_SQUARENESS:
            continue

        # Fill ratio: hollow ring ≈ 0.20–0.75; solid disc ≈ 0.75–0.97
        fill = contour_area / bbox_area if bbox_area > 0 else 0
        if fill < 0.15 or fill > 0.98:
            continue

        # Convexity: stamp shapes are broadly convex
        hull      = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        convexity = contour_area / hull_area if hull_area > 0 else 0
        if convexity < 0.35:
            continue

        # Composite score: reward squareness, convexity, larger size
        squareness_score = 1.0 - abs(1.0 - sq)
        score = squareness_score * convexity * (bbox_area / max_area)

        if score > best_score:
            best_score = score
            best_bbox  = (bx, by, bw, bh)

    # ── 4. Translate back to full-image coordinates ───────────────────────────
    if best_bbox is not None:
        bx, by, bw, bh = best_bbox
        fx = max(0, sx + bx - BBOX_MARGIN)
        fy = max(0, sy + by - BBOX_MARGIN)
        fw = min(bw + 2 * BBOX_MARGIN, img_w - fx)
        fh = min(bh + 2 * BBOX_MARGIN, img_h - fy)
        return fx, fy, fw, fh

    # ── 5. Heuristic fallback ─────────────────────────────────────────────────
    return _heuristic_fallback(img_w, img_h)


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def _heuristic_fallback(page_width: int, page_height: int):
    """
    Returns a generous region covering where the stamp almost certainly is,
    used only when contour detection finds no plausible candidate.
    """
    aspect = page_width / page_height

    if aspect > LANDSCAPE_ASPECT_THRESHOLD:
        # Landscape: right vertical strip, upper-mid section
        # (stamp commonly sits in the upper half of the title strip)
        x      = int(page_width  * 0.73)
        y      = int(page_height * 0.10)
        width  = int(page_width  * 0.25)
        height = int(page_height * 0.50)
    else:
        # Portrait: bottom-right corner
        x      = int(page_width  * 0.58)
        y      = int(page_height * 0.65)
        width  = int(page_width  * 0.37)
        height = int(page_height * 0.30)

    return x, y, width, height
