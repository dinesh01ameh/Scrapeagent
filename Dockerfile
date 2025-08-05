# SwissKnife AI Scraper - Backend Dockerfile
# Multi-stage build for FastAPI application

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    gcc \
    g++ \
    # Network tools
    curl \
    wget \
    git \
    # Image processing
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # PDF processing
    poppler-utils \
    # Browser dependencies for Playwright
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    # PostgreSQL client
    libpq-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-minimal.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-minimal.txt

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data cache logs models temp

# Create non-root user
RUN useradd --create-home --shell /bin/bash swissknife && \
    chown -R swissknife:swissknife /app

# Switch to non-root user
USER swissknife

# Expose port
EXPOSE 8601

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8601/health || exit 1

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8601"]

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest-xdist \
    pytest-mock \
    httpx \
    factory-boy

# Enable hot reload for development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8601", "--reload"]

# Production stage
FROM base as production

# Set production environment
ENV ENVIRONMENT=production
ENV DEBUG=false

# Install gunicorn for production
RUN pip install --no-cache-dir gunicorn

# Use gunicorn for production
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8601"]
