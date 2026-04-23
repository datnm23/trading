# syntax=docker/dockerfile:1

# ============================================================
# Stage 1: Builder
# ============================================================
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

# ============================================================
# Stage 2: Runtime
# ============================================================
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r trader && useradd -r -g trader -u 1000 trader

WORKDIR /app

# Copy application code
COPY --chown=trader:trader . .

# Create data directories
RUN mkdir -p /app/data/raw /app/data/processed /app/data/exports /app/data/logs \
    /app/ml/models /app/journal /app/logs && \
    chown -R trader:trader /app/data /app/logs /app/journal

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Switch to non-root user
USER trader

# Health check (uses curl which is lightweight)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8080/health > /dev/null || exit 1

# Default command (overridden by docker-compose per service)
CMD ["/app/scripts/run_bot.sh"]
