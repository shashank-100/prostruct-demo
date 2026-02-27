import cv2
import numpy as np
import pytesseract
from PIL import Image

def preprocess_for_ocr(image: Image.Image):
    """
    Returns (processed_image_ndarray, scale_factor)
    """
    img = np.array(image)

    # Grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    # Upscale: make sure shorter dimension >= 300 px
    h, w = gray.shape
    min_dim = min(h, w)
    scale = 1.0
    if min_dim < 300:
        scale = 300 / min_dim
        new_w = int(w * scale)
        new_h = int(h * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10,
    )

    # Slight dilation
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.dilate(thresh, kernel, iterations=1)

    return processed, scale

def run_ocr(image: np.ndarray) -> str:
    config = r'--oem 3 --psm 11'
    text = pytesseract.image_to_string(image, config=config)
    return text
