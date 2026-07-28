# Multi-stage build for Python FastAPI application

# Stage 1: Builder
FROM python:3.13-slim as builder

WORKDIR /tmp

# Install build dependencies for pymssql and other compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    freetds-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Install the FreeTDS runtime used by pymssql
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsybdb5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security before copying files
RUN useradd -m -u 1000 appuser

# Copy Python dependencies from builder to app home
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./alembic ./alembic
COPY --chown=appuser:appuser ./alembic.ini ./alembic.ini
COPY --chown=appuser:appuser ./scripts ./scripts

USER appuser

# Make entrypoint executable
RUN chmod +x /app/scripts/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Entrypoint script handles migrations and startup
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
