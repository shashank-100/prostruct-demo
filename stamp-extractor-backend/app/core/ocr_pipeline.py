import cv2
import numpy as np
import pytesseract
from PIL import Image

def preprocess_for_ocr(image):
    img = np.array(image)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img.copy()

    # Upscale for better OCR on small stamps
    scale = 2
    gray = cv2.resize(gray, (gray.shape[1] * scale, gray.shape[0] * scale), interpolation=cv2.INTER_CUBIC)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # Adaptive threshold works better than global Otsu for stamps with uneven lighting
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10
    )

    # Morphological cleanup to close small gaps in characters
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return thresh

def run_ocr(image):
    # PSM 11: sparse text (good for stamps where text is not in neat blocks)
    # Also try PSM 6 as fallback and merge results
    config_sparse = r'--oem 3 --psm 11'
    config_block  = r'--oem 3 --psm 6'

    text_sparse = pytesseract.image_to_string(image, config=config_sparse)
    text_block  = pytesseract.image_to_string(image, config=config_block)

    # Merge: use whichever has more content; also return both so extractor can use both
    if len(text_sparse.strip()) >= len(text_block.strip()):
        combined = text_sparse + '\n' + text_block
    else:
        combined = text_block + '\n' + text_sparse

    return combined
