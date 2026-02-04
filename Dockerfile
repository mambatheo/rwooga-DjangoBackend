FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files with all required environment variables
RUN SECRET_KEY=build-time-placeholder \
    DEBUG=False \
    ALLOWED_HOSTS=* \
    DATABASE_URL=postgresql://stub:stub@stub:5432/stub \
    DB_NAME=stub \
    DB_USER=stub \
    DB_PASSWORD=stub \
    DB_HOST=stub \
    DB_PORT=5432 \
    EMAIL_HOST=smtp.gmail.com \
    EMAIL_PORT=587 \
    EMAIL_USE_TLS=True \
    EMAIL_HOST_USER=stub@stub.com \
    EMAIL_HOST_PASSWORD=stub \
    DEFAULT_FROM_EMAIL=stub@stub.com \
    SITE_URL=http://localhost:3000 \
    COMPANY_NAME=Stub \
    SUPPORT_EMAIL=stub@stub.com \
    VERIFICATION_CODE_EXPIRY_MINUTES=10 \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Run gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT --workers=2 --threads=2 --timeout=60 --access-logfile - --error-logfile - rwoogaBackend.wsgi:application