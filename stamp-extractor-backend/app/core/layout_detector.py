import cv2
import numpy as np
from PIL import Image


def detect_stamp_region(page_width, page_height):
    """
    Adaptive stamp region detection for structural drawings.

    Returns (x, y, width, height) in pixels relative to the full rendered image.

    Handles two common title block layouts:
    1. Wide landscape (aspect > 1.4):  right-side vertical title block
       - stamp near top-right strip
    2. Portrait / square / mild landscape: bottom-right title block
       - stamp in bottom-right quadrant
    """
    aspect_ratio = page_width / page_height

    if aspect_ratio > 1.4:
        # Right-side vertical title block — stamp near top-right
        x = int(page_width * 0.72)
        y = int(page_height * 0.20)
        width  = int(page_width * 0.26)
        height = int(page_height * 0.30)
    else:
        # Bottom horizontal title block — stamp in bottom-right quadrant
        x = int(page_width * 0.60)
        y = int(page_height * 0.65)
        width  = int(page_width * 0.38)
        height = int(page_height * 0.33)

    return x, y, width, height


def refine_with_circle_detection(full_image: Image.Image, coarse_bbox):
    """
    Given a coarse bounding box (x, y, w, h) within a PIL image, try to
    detect a circular engineer stamp inside that region using Hough circles.

    Returns a refined (x, y, w, h) bbox if a circle is confidently found,
    otherwise returns the original coarse_bbox unchanged.
    """
    cx, cy, cw, ch = coarse_bbox

    # Crop the candidate region
    region = full_image.crop((cx, cy, cx + cw, cy + ch))
    img = np.array(region)

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img.copy()

    # Blur to reduce noise before circle detection
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    # Hough circle detection
    # min/max radius: stamps are typically 15–40% of the shorter dimension
    short_side = min(cw, ch)
    min_radius = int(short_side * 0.12)
    max_radius = int(short_side * 0.50)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=short_side * 0.4,   # only one stamp expected
        param1=60,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius,
    )

    if circles is not None:
        circles = np.round(circles[0, :]).astype(int)
        # Pick the circle with highest accumulator (first one, already sorted)
        best = circles[0]
        rx, ry, r = int(best[0]), int(best[1]), int(best[2])

        # Convert circle centre back to full-image coords and make a square bbox
        margin = int(r * 0.15)  # small padding around the circle
        bx = cx + rx - r - margin
        by = cy + ry - r - margin
        bw = (r + margin) * 2
        bh = (r + margin) * 2

        # Clamp to image bounds
        img_w, img_h = full_image.size
        bx = max(0, bx)
        by = max(0, by)
        bw = min(bw, img_w - bx)
        bh = min(bh, img_h - by)

        return bx, by, bw, bh

    # No circle found — return original
    return coarse_bbox
