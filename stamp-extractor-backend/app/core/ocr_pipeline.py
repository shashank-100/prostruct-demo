import cv2
import numpy as np
import pytesseract
from PIL import Image

def preprocess_for_ocr(image):
    img = np.array(image)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    
    # Simple thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def run_ocr(image):
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=config)
    return text
