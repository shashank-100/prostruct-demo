import cv2
import numpy as np
import pytesseract
from PIL import Image

def preprocess_for_ocr(image: Image.Image):
    """
    Returns (processed_image_ndarray, scale_factor)
    Minimal preprocessing - upscale only, let Tesseract handle the rest.
    """
    img = np.array(image)

    # Grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    # Upscale: make sure shorter dimension >= 800 px for better OCR accuracy
    h, w = gray.shape
    min_dim = min(h, w)
    scale = 1.0
    if min_dim < 800:
        scale = 800 / min_dim
        new_w = int(w * scale)
        new_h = int(h * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # Apply slight sharpening to enhance text edges
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(gray, -1, kernel)

    return sharpened, scale

def run_ocr(image: np.ndarray) -> str:
    # PSM 11 = sparse text, find as much text as possible (best for stamps)
    # OEM 1 = LSTM neural net mode (better accuracy for varied fonts/rotation)
    config = r'--oem 1 --psm 11'
    text = pytesseract.image_to_string(image, config=config, lang='eng')
    return text
