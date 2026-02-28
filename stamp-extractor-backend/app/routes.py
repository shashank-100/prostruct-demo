import base64
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.pdf_handler import open_pdf, render_page_to_image, crop_bbox, get_stamp_bboxes_from_pdf
from app.core.layout_detector import detect_stamp_region
from app.core.ocr_pipeline import preprocess_for_ocr
from app.core.extractor import extract_fields_with_boxes
from app.schemas import StampResponse, StampInfo
from PIL import Image

router = APIRouter()
DETECT_DPI = 150  # Low DPI for fast region detection
OCR_DPI = 600     # High DPI for accurate OCR on cropped regions only

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
    import traceback
    try:
        print(f"[IMAGE] Request for page {page}")
        contents = await file.read()
        print(f"[IMAGE] PDF loaded: {len(contents)/1024:.1f} KB")

        doc = open_pdf(contents)
        if page < 0 or page >= len(doc):
            raise HTTPException(status_code=400, detail="Invalid page number")

        print(f"[IMAGE] Rendering page {page} at {DETECT_DPI} DPI...")
        page_img = render_page_to_image(doc, page, dpi=DETECT_DPI)

        buffered = BytesIO()
        page_img.save(buffered, format="JPEG", quality=85, optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        print(f"[IMAGE] Success! Page {page}: {page_img.size}, {len(img_str)/1024:.1f} KB base64")
        return {"image": f"data:image/jpeg;base64,{img_str}", "width": page_img.width, "height": page_img.height}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[IMAGE ERROR] Page {page}: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-stamp", response_model=StampResponse)
async def extract_stamp(file: UploadFile = File(...), page: int = Form(...)):
    try:
        import time
        start = time.time()
        print(f"\n[EXTRACT] Starting extraction for page {page}...")

        contents = await file.read()
        print(f"[EXTRACT] PDF loaded ({len(contents)/1024:.1f} KB)")

        doc = open_pdf(contents)
        if page < 0 or page >= len(doc): raise HTTPException(status_code=400, detail="Invalid page number")

        import cv2
        import numpy as np
        import fitz

        stamps_found = []
        seen_licenses = set()

        # ── Step 1: PDF text layer — exact positions + names, no OCR needed ──
        print(f"[EXTRACT] Step 1: Checking PDF text layer...")
        pdf_stamps = get_stamp_bboxes_from_pdf(doc, page, dpi=DETECT_DPI)
        print(f"[EXTRACT] Found {len(pdf_stamps)} stamps in PDF text layer")

        for ps in pdf_stamps:
            rx, ry, rw, rh = ps["bbox"]
            lic = ps["license"]
            name = ps["name"]
            if lic in seen_licenses:
                continue
            seen_licenses.add(lic)
            stamps_found.append(StampInfo(
                symbol_type="approval_stamp",
                bounding_box=[rx, ry, rw, rh],
                engineer_name=name,
                license_number=lic
            ))

        # ── Step 2: Detect stamp regions at LOW DPI (fast) ──
        print(f"[EXTRACT] Step 2: Rendering page at {DETECT_DPI} DPI for region detection...")
        page_img_lowres = render_page_to_image(doc, page, dpi=DETECT_DPI)
        print(f"[EXTRACT] Low-res page: {page_img_lowres.size}")

        print(f"[EXTRACT] Step 3: Detecting stamp regions...")
        img_bboxes = detect_stamp_region(page_img_lowres)
        print(f"[EXTRACT] Found {len(img_bboxes)} regions")

        # ── Step 3: Render and OCR ONLY the detected regions at HIGH DPI ──
        print(f"[EXTRACT] Step 4: OCR on regions at {OCR_DPI} DPI...")
        pdf_page = doc[page]
        dpi_scale = OCR_DPI / DETECT_DPI

        for i, region_bbox in enumerate(img_bboxes):
            rx, ry, rw, rh = region_bbox

            # Scale bbox to high DPI coordinates
            rx_hd = int(rx * dpi_scale)
            ry_hd = int(ry * dpi_scale)
            rw_hd = int(rw * dpi_scale)
            rh_hd = int(rh * dpi_scale)

            # Render ONLY this region at high DPI
            # Convert pixels back to PDF coordinates
            scale_to_pdf = 72.0 / OCR_DPI
            pdf_rect = fitz.Rect(
                rx_hd * scale_to_pdf,
                ry_hd * scale_to_pdf,
                (rx_hd + rw_hd) * scale_to_pdf,
                (ry_hd + rh_hd) * scale_to_pdf
            )

            # Render cropped region at high DPI
            mat = fitz.Matrix(OCR_DPI / 72.0, OCR_DPI / 72.0)
            pix = pdf_page.get_pixmap(matrix=mat, clip=pdf_rect)
            cropped_hd = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            print(f"[EXTRACT]   Region {i+1}: {cropped_hd.size}")

            # Run OCR on high-res crop
            engineers = extract_fields_with_boxes(cropped_hd)
            print(f"[EXTRACT]   Region {i+1} OCR found {len(engineers)} stamps")
            for eng in engineers:
                lic = eng["license_number"]
                if lic in seen_licenses:
                    continue
                seen_licenses.add(lic)
                rel_x, rel_y, rel_w, rel_h = eng["relative_bbox"]

                # Bbox is relative to low-res coords (DETECT_DPI)
                stamps_found.append(StampInfo(
                    symbol_type="approval_stamp",
                    bounding_box=[rx, ry, rw, rh],  # Use region bbox at DETECT_DPI
                    engineer_name=eng["engineer_name"],
                    license_number=lic
                ))

        elapsed = time.time() - start
        print(f"[EXTRACT] Complete! Found {len(stamps_found)} total stamps in {elapsed:.2f}s\n")

        return {
            "page": page,
            "stamps": stamps_found,
            "raw_text": "Check logs",
            "units": "pixels"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
