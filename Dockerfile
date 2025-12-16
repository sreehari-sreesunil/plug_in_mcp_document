# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies if needed (e.g. for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install Runtime Dependencies
# - tesseract-ocr for OCR support
# - libgl1 for some CV libraries if needed by Pillow/others, though usually optional for basic usage
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

COPY src/ src/
COPY configs/ configs/

# Create data dir
RUN mkdir data

# Environment variables
ENV CONFIG_PATH=/app/configs
ENV DATA_PATH=/app/data
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health Check: Check root, if we get a response (even 404), the server is up.
# python's urlopen raises HTTPError for 404, so we catch it.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request, sys; \
    try: \
        urllib.request.urlopen('http://localhost:8000/'); \
    except urllib.error.HTTPError as e: \
        sys.exit(0) if e.code == 404 else sys.exit(1); \
    except Exception: \
        sys.exit(1)" || exit 1

CMD ["python", "src/server.py"]
