# ============================================
# Multi-stage Dockerfile untuk FastAPI Backend
# Target: Python 3.11 Slim, image < 500MB
# ============================================

# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies (libpq untuk asyncpg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/* && \
    # Buat user non-root untuk keamanan
    adduser --disabled-password --gecos "" appuser

# Copy installed packages dari builder stage
COPY --from=builder /install /usr/local

# Copy source code aplikasi
COPY . .

# Gunakan user non-root
USER appuser

# Expose port backend
EXPOSE 8000

# Health check menggunakan curl
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8000/health || exit 1

# Jalankan FastAPI dengan uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
