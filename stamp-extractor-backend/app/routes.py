import base64
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.pdf_handler import open_pdf, render_page_to_image, crop_bbox
from app.core.layout_detector import detect_stamp_region
from app.core.ocr_pipeline import preprocess_for_ocr
from app.core.extractor import extract_fields_with_boxes
from app.schemas import StampResponse, StampInfo
from PIL import Image

router = APIRouter()
RENDER_DPI = 150

@router.get("/")
async def root():
    return {"message": "Stamp Extractor API - Precise Multi-Stamp Ready", "status": "ok"}

@router.post("/get-info")
async def get_pdf_info(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        doc = open_pdf(contents)
        return {"page_count": len(doc)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get-page-image")
async def get_page_image(file: UploadFile = File(...), page: int = Form(...)):
    try:
        contents = await file.read()
        doc = open_pdf(contents)
        if page < 0 or page >= len(doc): raise HTTPException(status_code=400, detail="Invalid page number")
        page_img = render_page_to_image(doc, page, dpi=RENDER_DPI)
        buffered = BytesIO()
        page_img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return {"image": f"data:image/jpeg;base64,{img_str}", "width": page_img.width, "height": page_img.height}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-stamp", response_model=StampResponse)
async def extract_stamp(file: UploadFile = File(...), page: int = Form(...)):
    try:
        contents = await file.read()
        doc = open_pdf(contents)
        if page < 0 or page >= len(doc): raise HTTPException(status_code=400, detail="Invalid page number")

        page_img = render_page_to_image(doc, page, dpi=RENDER_DPI)
        bboxes = detect_stamp_region(page_img)
        
        stamps_found = []
        for region_bbox in bboxes:
            rx, ry, rw, rh = region_bbox
            cropped = crop_bbox(page_img, region_bbox)
            
            # Use original grayscale but upscaled for image_to_data
            # We don't use the binary thresh because it might break character shapes for Tesseract
            import cv2
            import numpy as np
            img_arr = np.array(cropped.convert("L"))
            h, w = img_arr.shape
            scale = 300 / min(h, w) if min(h, w) < 300 else 1.0
            if scale > 1.0:
                img_arr = cv2.resize(img_arr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
            
            processed_pil = Image.fromarray(img_arr)
            
            engineers = extract_fields_with_boxes(processed_pil)
            
            for eng in engineers:
                rel_x, rel_y, rel_w, rel_h = eng["relative_bbox"]
                
                # Scale coordinates back
                rel_x_orig = rel_x / scale
                rel_y_orig = rel_y / scale
                rel_w_orig = rel_w / scale
                rel_h_orig = rel_h / scale
                
                global_x = rx + rel_x_orig
                global_y = ry + rel_y_orig
                
                stamps_found.append(StampInfo(
                    symbol_type="approval_stamp",
                    bounding_box=[int(global_x), int(global_y), int(rel_w_orig), int(rel_h_orig)],
                    engineer_name=eng["engineer_name"],
                    license_number=eng["license_number"]
                ))

        return {
            "page": page,
            "stamps": stamps_found,
            "raw_text": "Check logs",
            "units": "pixels"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
