# ─── Stage 1: Install Python dependencies ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Stage 2: Final lean image ────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq2 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

# Stub env vars so Django can load settings during collectstatic at build time.
# Real values are injected by Koyeb at runtime.
RUN SECRET_KEY=build-time-placeholder \
    CORS_ALLOWED_ORIGINS=http://localhost:3000 \
    EMAIL_HOST=smtp.gmail.com \
    EMAIL_PORT=587 \
    EMAIL_HOST_USER=stub@stub.com \
    EMAIL_HOST_PASSWORD=stub \
    NAME=stub \
    USER=stub \
    PASSWORD=stub \
    HOST=stub \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD gunicorn --bind 0.0.0.0:${PORT:-8000} \
    --workers=2 \
    --threads=2 \
    --timeout=60 \
    --access-logfile - \
    --error-logfile - \
    rwoogaBackend.wsgi:application