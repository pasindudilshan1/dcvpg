# ────────────────────────────────────────────
# Stage 1: Build
# ────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build
# Copy the whole repo so pip install can find pyproject.toml + dcvpg/ package
COPY pyproject.toml .
COPY dcvpg/ dcvpg/
RUN pip install --upgrade pip build && \
    pip install .

# ────────────────────────────────────────────
# Stage 2: Runtime
# ────────────────────────────────────────────
FROM python:3.11-slim

LABEL org.opencontainers.image.title="DCVPG API"
LABEL org.opencontainers.image.description="Data Contract Validator & Pipeline Guardian"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install runtime OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed package from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source
COPY dcvpg/ /app/dcvpg/

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "dcvpg.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
