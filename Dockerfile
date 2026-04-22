# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" || pip install -e .

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/raw /app/data/processed /app/ml/models /app/journal /app/logs

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Default command
CMD ["/app/scripts/run_bot.sh"]
