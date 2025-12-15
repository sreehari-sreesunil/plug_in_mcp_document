FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for potential OCR (e.g. tesseract-ocr) if needed later
# RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY configs/ configs/
# Create data dir
RUN mkdir data

# Environment variables
ENV CONFIG_PATH=/app/configs
ENV DATA_PATH=/app/data
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "src/server.py"]
