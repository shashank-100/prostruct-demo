# Structural Drawing Approval Stamp Extractor

A full-stack web application that automatically detects and extracts engineer approval stamps from structural drawings (PDF files) using OCR technology.

## Features

- **PDF Upload & Processing**: Upload structural drawings in PDF format
- **Page Navigation**: Browse through multi-page PDF documents
- **Automatic Stamp Detection**: Heuristic-based detection of engineer approval stamps
- **Visual Bounding Box**: Real-time visualization of detected stamp regions
- **OCR Extraction**: Extracts engineer name and license number using Tesseract OCR
- **JSON Output**: Structured data output for integration with other systems
- **Modern UI**: Clean, dark-themed interface with responsive design

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **PyMuPDF (fitz)**: PDF processing and rendering
- **OpenCV**: Image preprocessing
- **Tesseract OCR**: Optical character recognition
- **Python 3.11**: Core programming language

### Frontend
- **React 19**: Modern UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client for API requests
- **Lucide React**: Beautiful icon library

## Project Structure

```
prostruct/
├── stamp-extractor-backend/     # FastAPI Backend
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── routes.py            # API endpoints
│   │   ├── schemas.py           # Pydantic models
│   │   └── core/
│   │       ├── pdf_handler.py   # PDF processing
│   │       ├── layout_detector.py # Stamp region detection
│   │       ├── ocr_pipeline.py  # OCR preprocessing
│   │       └── extractor.py     # Field extraction
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .gitignore
└── stamp-extractor-ui/          # React Frontend
    ├── src/
    │   ├── App.tsx              # Main application component
    │   ├── App.css              # Styling
    │   └── main.tsx             # Entry point
    ├── package.json
    ├── vite.config.ts
    ├── .env.example
    └── .gitignore
```

## Getting Started

### Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **Tesseract OCR** installed on your system

#### Installing Tesseract

**macOS**:
```bash
brew install tesseract
```

**Ubuntu/Debian**:
```bash
sudo apt-get install tesseract-ocr libtesseract-dev
```

**Windows**:
Download from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)

### Backend Setup

1. Navigate to backend directory:
```bash
cd stamp-extractor-backend
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd stamp-extractor-ui
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

4. Run development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## API Documentation

### Endpoints

#### GET `/` (Root)
Health check endpoint

#### POST `/get-info`
Get PDF information (page count)

**Request**:
- `file`: PDF file (multipart/form-data)

**Response**:
```json
{
  "page_count": 4
}
```

#### POST `/get-page-image`
Render a specific page as an image

**Request**:
- `file`: PDF file (multipart/form-data)
- `page`: Page number (integer, 0-indexed)

**Response**:
```json
{
  "image": "data:image/jpeg;base64,...",
  "width": 5100,
  "height": 3300
}
```

#### POST `/extract-stamp`
Extract stamp information from a specific page

**Request**:
- `file`: PDF file (multipart/form-data)
- `page`: Page number (integer, 0-indexed)

**Response**:
```json
{
  "page": 0,
  "symbol_type": "approval_stamp",
  "bounding_box": [6630, 2970, 3060, 990],
  "engineer_name": "THOMAS MAHANNA",
  "license_number": "39479",
  "units": "pixels"
}
```

## How It Works

### Stamp Detection Algorithm

1. **PDF Processing**: Upload PDF is loaded using PyMuPDF
2. **Page Rendering**: Selected page is rendered to high-resolution image (300 DPI)
3. **Region Detection**: Heuristic algorithm identifies likely stamp location:
   - Horizontal: 65% from left edge
   - Vertical: 45% from top edge
   - Size: 30% width × 15% height
4. **Image Preprocessing**:
   - Convert to grayscale
   - Apply Otsu's thresholding for binarization
5. **OCR Execution**: Tesseract OCR with PSM mode 6 (uniform text block)
6. **Field Extraction**:
   - Engineer Name: Regex pattern matching for 2-3 uppercase words
   - License Number: Pattern matching for 4-6 digit numbers with common prefixes (No., PE, etc.)

### Key Design Decisions

- **Focused Region**: Instead of full-page OCR, we target a specific region where stamps typically appear in structural drawings (middle-right area of title block)
- **Preprocessing**: Grayscale conversion and thresholding improve OCR accuracy on stamps with complex backgrounds
- **Flexible Patterns**: Regex-based extraction handles variations in stamp formats
- **Visual Feedback**: Bounding box overlay helps users verify correct region detection

## Deployment

### Backend Deployment (Railway/Render)

1. Push code to GitHub
2. Connect repository to Railway/Render
3. Platform will auto-detect Dockerfile
4. Set environment variables if needed
5. Deploy

**Environment Variables**:
- `PORT`: Server port (default: 8000)

### Frontend Deployment (Vercel/Netlify)

1. Push code to GitHub
2. Connect repository to Vercel/Netlify
3. Configure build settings:
   - Build command: `npm run build`
   - Output directory: `dist`
4. Set environment variable:
   - `VITE_API_BASE_URL`: Your backend URL (e.g., `https://your-backend.railway.app`)
5. Deploy

## Development

### Running Tests

Backend:
```bash
cd stamp-extractor-backend
source venv/bin/activate
python -m pytest  # (if tests are added)
```

Frontend:
```bash
cd stamp-extractor-ui
npm run lint
```

### Building for Production

Backend (Docker):
```bash
cd stamp-extractor-backend
docker build -t stamp-extractor-backend .
docker run -p 8000:8000 stamp-extractor-backend
```

Frontend:
```bash
cd stamp-extractor-ui
npm run build
```

## Limitations & Future Improvements

### Current Limitations

- **OCR Accuracy**: Curved text in circular stamps can be challenging for Tesseract
- **Fixed Region**: Stamp detection uses a fixed heuristic (works for standard structural drawings)
- **Single Stamp**: Currently extracts first detected stamp (may miss multiple stamps)

### Potential Improvements

- Machine learning-based stamp detection for better accuracy
- Support for multiple stamp detection on single page
- Advanced OCR preprocessing (deskewing, rotation correction)
- Batch processing for multiple PDFs
- Database storage for extracted data
- User feedback mechanism to improve extraction patterns

## License

This project is for educational and demonstration purposes.

## Contact & Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ for PROSTRUCT**
