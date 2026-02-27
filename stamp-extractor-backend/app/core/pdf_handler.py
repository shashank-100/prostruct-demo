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
