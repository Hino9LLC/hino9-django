# Builder stage
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Tailwind CSS build
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user early to ensure correct permissions
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies as appuser to avoid root-owned venv
RUN --mount=type=cache,target=/home/appuser/.cache/uv \
    mkdir -p /home/appuser/.cache/uv && \
    chown -R appuser:appuser /app /home/appuser/.cache && \
    su appuser -c "cd /app && uv sync --frozen --no-dev"

# Copy application code
COPY --chown=appuser:appuser . .

# Build Tailwind CSS as appuser
RUN su appuser -c "cd /app/theme/static_src && npm install && npm run build"

# Collect static files as appuser
RUN su appuser -c "cd /app && uv run python manage.py collectstatic --noinput"

# Production stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy installed dependencies and application from builder
COPY --from=builder --chown=appuser:appuser /app /app

# Run as non-root user
USER appuser

EXPOSE 8300

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8300/health || exit 1

# Start Gunicorn with dynamic worker scaling
CMD ["sh", "-c", "uv run gunicorn ainews.wsgi:application --bind 0.0.0.0:8300 --workers ${WORKERS:-4} --timeout 60 --access-logfile - --error-logfile -"]
