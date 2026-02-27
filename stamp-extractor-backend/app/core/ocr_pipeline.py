import cv2
import numpy as np
import pytesseract
from PIL import Image


def preprocess_for_ocr(image: Image.Image) -> np.ndarray:
    """
    Prepare a stamp crop for Tesseract.

    Steps:
      1. Convert to grayscale.
      2. Upscale to at least 300 px on the shorter axis — Tesseract works
         best at effective resolutions ≥ 300 DPI; our render is 150 DPI so
         the stamp crop is small and needs a 2× boost.
      3. Adaptive threshold (handles uneven ink / background in stamps).
      4. Light dilation to thicken thin strokes.
    """
    img = np.array(image)

    # Grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    # Upscale: make sure shorter dimension ≥ 300 px
    h, w = gray.shape
    min_dim = min(h, w)
    if min_dim < 300:
        scale = 300 / min_dim
        new_w = int(w * scale)
        new_h = int(h * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # Adaptive threshold — better than a global threshold for stamps with
    # curved text, vector borders, and varying ink density
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10,
    )

    # Slight dilation to reconnect broken strokes after thresholding
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.dilate(thresh, kernel, iterations=1)

    return processed


def run_ocr(image: np.ndarray) -> str:
    """
    Run Tesseract on a preprocessed stamp image.

    PSM 11 (sparse text) is ideal for engineer stamps: text appears at
    multiple orientations (curved, rotated) with large gaps between words.
    OEM 3 uses the LSTM engine for best accuracy.
    """
    config = r'--oem 3 --psm 11'
    text = pytesseract.image_to_string(image, config=config)
    return text
