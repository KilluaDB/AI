# ============================================
# SchemaAgent - Multi-stage Docker Build
# ============================================
# This Dockerfile creates a production-ready image for the SchemaAgent API

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-dev \
    libcairo2-dev \
    libgirepository1.0-dev \
    gcc \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*
# ============================================
# Builder stage - install Python dependencies
# ============================================
FROM base as builder

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --user -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Download NLTK data
RUN python -c "import nltk; nltk.download('wordnet', download_dir='/root/nltk_data'); nltk.download('omw-1.4', download_dir='/root/nltk_data')"

# ============================================
# Production stage
# ============================================
FROM base as production

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /root/nltk_data /root/nltk_data

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV NLTK_DATA=/root/nltk_data

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/physical_design/er_data \
    /app/physical_design/saved_files \
    /app/outputs/DBdesign_domain/text

# Expose port for FastAPI
EXPOSE 8080

# Default command - run FastAPI server
CMD ["python", "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080"]
