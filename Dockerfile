# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# System packages needed to build psycopg2 / other C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
# The BuildKit cache mount keeps the pip wheel cache between builds so
# subsequent builds skip re-downloading unchanged packages.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Download spaCy model (also benefits from pip cache on re-builds)
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m spacy download en_core_web_sm

# Download NLTK data
RUN python -c "import nltk; nltk.download('wordnet', quiet=True); nltk.download('omw-1.4', quiet=True)"

# Copy application code (last — changes here don't invalidate dep layers)
COPY . .

RUN mkdir -p /app/design/er_data \
             /app/design/saved_files \
             /app/outputs/DBdesign_domain/text

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080"]
