import base64
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.pdf_handler import open_pdf, get_page_dimensions, render_page_to_image, crop_bbox
from app.core.layout_detector import detect_stamp_region
from app.core.ocr_pipeline import preprocess_for_ocr, run_ocr
from app.core.extractor import extract_fields
from app.schemas import StampResponse

router = APIRouter()

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
        
        if page < 0 or page >= len(doc):
            raise HTTPException(status_code=400, detail="Invalid page number")
            
        # Render at lower DPI for preview to keep it fast
        page_img = render_page_to_image(doc, page, dpi=150)
        
        buffered = BytesIO()
        page_img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            "image": f"data:image/jpeg;base64,{img_str}",
            "width": page_img.width,
            "height": page_img.height
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-stamp", response_model=StampResponse)
async def extract_stamp(file: UploadFile = File(...), page: int = Form(...)):
    try:
        contents = await file.read()
        doc = open_pdf(contents)

        if page < 0 or page >= len(doc):
            raise HTTPException(status_code=400, detail="Invalid page number")

        page_img = render_page_to_image(doc, page)

        width, height = get_page_dimensions(doc, page)
        
        # Rendered image dimensions (at 300 DPI)
        img_width, img_height = page_img.size
        
        # Detect region based on original page dimensions
        bbox = detect_stamp_region(img_width, img_height)

        cropped = crop_bbox(page_img, bbox)

        processed = preprocess_for_ocr(cropped)
        text = run_ocr(processed)

        extracted = extract_fields(text)

        return {
            "page": page,
            "symbol_type": "approval_stamp",
            "bounding_box": list(bbox),
            "engineer_name": extracted["engineer_name"],
            "license_number": extracted["license_number"],
            "units": "pixels"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
