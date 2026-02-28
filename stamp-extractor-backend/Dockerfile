FROM python:3.11-slim

# Install system dependencies for OpenCV and Tesseract
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libgomp1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
