# Structural Drawing Approval Stamp Extractor - Deployment Plan

## Project Overview
Building a full-stack application to extract engineer approval stamps from structural drawings (PDF files) using OCR technology.

**Goal**: Deploy a working public URL with both frontend and backend, with source code on GitHub.

---

## Current Project Status

### Backend (FastAPI) - COMPLETE ✓
**Location**: `stamp-extractor-backend/`

**Components**:
- FastAPI application with 3 endpoints:
  - `POST /get-info` - Returns PDF page count
  - `POST /get-page-image` - Returns page image as base64
  - `POST /extract-stamp` - Extracts stamp and returns JSON

**Core Modules**:
- `app/core/pdf_handler.py` - PDF processing using PyMuPDF
- `app/core/layout_detector.py` - Stamp region detection (bottom-right 40%)
- `app/core/ocr_pipeline.py` - OCR using Tesseract with preprocessing
- `app/core/extractor.py` - Name and license number extraction using regex

**Dependencies**:
- fastapi
- uvicorn
- pymupdf (PyMuPDF)
- pillow
- opencv-python-headless
- numpy
- pytesseract
- python-multipart

### Frontend (React + Vite) - COMPLETE ✓
**Location**: `stamp-extractor-ui/`

**Features**:
- PDF file upload interface
- Page navigation (previous/next)
- Visual page preview with bounding box overlay
- Extracted data display (engineer name, license number)
- JSON output display
- Modern UI with dark theme

**Tech Stack**:
- React 19 + TypeScript
- Vite build tool
- Axios for API calls
- Lucide React for icons

---

## Issues to Fix Before Deployment

### 1. Frontend API Configuration
**Issue**: API base URL is hardcoded to `http://127.0.0.1:8000`

**Fix**:
- Create environment variable support
- Add `.env` file for local development
- Configure production URL via environment variables

**Files to modify**:
- `stamp-extractor-ui/src/App.tsx` - Replace hardcoded API_BASE
- Create `stamp-extractor-ui/.env.example`
- Update `stamp-extractor-ui/vite.config.ts` for env loading

### 2. Backend Dockerfile
**Status**: Dockerfile exists but needs verification

**Needs**:
- Verify Python base image
- Ensure all dependencies are installed
- Confirm Tesseract OCR installation
- Set proper PORT environment variable handling

### 3. Backend CORS Configuration
**Current**: Allows all origins (`allow_origins=["*"]`)

**Action**:
- Keep as-is for initial deployment
- Consider restricting to specific frontend domain after deployment

### 4. Missing Configuration Files

**Backend needs**:
- `.gitignore` for Python (venv, __pycache__, *.pyc, etc.)
- `runtime.txt` (for some platforms to specify Python version)
- Health check endpoint for deployment platforms

**Frontend needs**:
- Build configuration verification
- Environment variable setup

### 5. Repository Setup
**Status**: Not a git repository

**Actions needed**:
- Initialize git repository
- Create `.gitignore` files
- Create comprehensive README.md
- Add LICENSE file (optional but recommended)

---

## Deployment Strategy

### Phase 1: Preparation (Pre-deployment)
1. **Fix environment variable handling in frontend**
2. **Add health check endpoint to backend** (`GET /health`)
3. **Create/verify Dockerfile for backend**
4. **Test backend locally with sample PDF**
5. **Test frontend locally connected to backend**
6. **Create comprehensive README**
7. **Initialize git repository**
8. **Create .gitignore files**

### Phase 2: Backend Deployment
**Recommended Platform**: Railway or Render (both support Docker and have free tiers)

**Railway Deployment**:
- Connect GitHub repository
- Auto-detect Dockerfile
- Set environment variables if needed
- Deploy from main branch
- Railway provides public URL automatically

**Render Deployment**:
- Connect GitHub repository
- Select "Web Service" type
- Use Docker deployment
- Configure start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add environment variable for PORT
- Deploy

**Deployment checklist**:
- [ ] Create account on deployment platform
- [ ] Connect GitHub repository
- [ ] Configure build settings
- [ ] Set environment variables
- [ ] Deploy backend
- [ ] Verify health endpoint responds
- [ ] Test API endpoints with curl/Postman
- [ ] Note the backend public URL

### Phase 3: Frontend Deployment
**Recommended Platform**: Vercel or Netlify (optimized for React/Vite)

**Vercel Deployment**:
- Connect GitHub repository
- Auto-detect Vite project
- Set environment variable: `VITE_API_BASE_URL=<backend-url>`
- Build command: `npm run build`
- Output directory: `dist`
- Deploy

**Netlify Deployment**:
- Connect GitHub repository
- Build command: `npm run build`
- Publish directory: `dist`
- Set environment variable: `VITE_API_BASE_URL=<backend-url>`
- Deploy

**Deployment checklist**:
- [ ] Create account on deployment platform
- [ ] Connect GitHub repository
- [ ] Configure build settings
- [ ] Set backend API URL as environment variable
- [ ] Deploy frontend
- [ ] Test the deployed application
- [ ] Verify CORS allows requests from frontend domain

### Phase 4: Testing & Validation
1. **Upload the sample PDF** (`Stamped_Plans (1).pdf`)
2. **Navigate through pages**
3. **Run extraction on pages with stamps**
4. **Verify bounding box display**
5. **Check JSON output format**
6. **Test on different pages**
7. **Verify error handling** (invalid files, etc.)

### Phase 5: GitHub Repository Setup
1. **Create public repository** (e.g., `structural-stamp-extractor`)
2. **Push all source code**
3. **Create detailed README** with:
   - Project description
   - Features
   - Tech stack
   - Setup instructions (local development)
   - Deployment instructions
   - API documentation
   - Screenshots
   - Live demo links
4. **Add project documentation**
5. **Ensure .gitignore excludes sensitive files**

---

## File Structure After Changes

```
prostruct/
├── DEPLOYMENT_PLAN.md (this file)
├── stamp-extractor-backend/
│   ├── .gitignore
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── runtime.txt (optional)
│   ├── app/
│   │   ├── main.py (add /health endpoint)
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── core/
│   │       ├── pdf_handler.py
│   │       ├── layout_detector.py
│   │       ├── ocr_pipeline.py
│   │       └── extractor.py
│   └── Stamped_Plans (1).pdf (for testing)
├── stamp-extractor-ui/
│   ├── .gitignore (exists)
│   ├── .env.example (create)
│   ├── package.json
│   ├── vite.config.ts (update)
│   ├── src/
│   │   └── App.tsx (update API_BASE)
│   └── ...other frontend files
└── README.md (create comprehensive one)
```

---

## Environment Variables Reference

### Backend
- `PORT` - Port to run the server (default: 8000)
- No other env vars needed initially

### Frontend
- `VITE_API_BASE_URL` - Backend API URL
  - Local: `http://localhost:8000`
  - Production: `https://your-backend.railway.app` (or Render URL)

---

## Expected JSON Output Format

```json
{
  "page": 3,
  "symbol_type": "approval_stamp",
  "bounding_box": [1200, 2400, 800, 600],
  "engineer_name": "THOMAS MAHANNA",
  "license_number": "39479",
  "units": "pixels"
}
```

---

## Submission Checklist

Before submitting, ensure you have:

- [ ] Working public URL for the application
- [ ] Public GitHub repository with all source code
- [ ] Comprehensive README.md with:
  - [ ] Project description
  - [ ] Setup instructions
  - [ ] Tech stack details
  - [ ] Screenshots/demo
  - [ ] Live demo link
- [ ] Email prepared with:
  - [ ] Working URL
  - [ ] GitHub repository link
  - [ ] Short summary of approach (2-3 paragraphs)

---

## Approach Summary (for submission email)

**Technical Approach**:

The application uses a two-tier architecture with a FastAPI backend and React frontend. The backend processes PDF files using PyMuPDF to extract page images at 300 DPI for optimal OCR accuracy. A heuristic-based layout detector identifies the likely stamp region (bottom-right 40% of the page, typical location for approval stamps in structural drawings).

The OCR pipeline preprocesses the cropped region using OpenCV (grayscale conversion, Otsu thresholding) before applying Tesseract OCR with PSM mode 6 (uniform text block). Field extraction uses regex patterns to identify engineer names (2-3 uppercase words) and license numbers (4-6 digit patterns with common prefixes like "No.", "PE", etc.).

The React frontend provides an intuitive interface for PDF upload, page navigation, and visual feedback with bounding box overlays. The application displays both structured field data and raw JSON output for integration purposes.

---

## Risk Assessment & Mitigation

### Risk 1: Tesseract installation on deployment platform
**Mitigation**: Use Docker with Tesseract pre-installed, or use platforms that support buildpacks with system dependencies.

### Risk 2: Large PDF file uploads timing out
**Mitigation**: Current implementation handles files in memory. For production, consider adding file size limits or streaming uploads.

### Risk 3: OCR accuracy varies with stamp quality
**Mitigation**: Current preprocessing handles typical cases. Can be enhanced with additional image processing techniques if needed.

### Risk 4: CORS issues between deployed frontend and backend
**Mitigation**: Properly configure CORS on backend to allow frontend domain. Test thoroughly after deployment.

---

## Timeline

**Estimated time to complete**: 2-3 hours

1. **Code fixes and configuration** (45 min)
2. **Backend deployment** (30 min)
3. **Frontend deployment** (30 min)
4. **Testing and debugging** (30 min)
5. **Documentation and README** (30 min)
6. **Final submission preparation** (15 min)

---

## Next Steps

1. Review this plan
2. Make code modifications as outlined
3. Test locally
4. Set up GitHub repository
5. Deploy backend
6. Deploy frontend
7. Test end-to-end
8. Prepare submission

---

**Document Version**: 1.0
**Last Updated**: 2026-02-27
**Status**: Ready for Implementation
