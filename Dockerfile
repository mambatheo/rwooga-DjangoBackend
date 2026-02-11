FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Project files
COPY . .

# Collect static files (safe for build)
RUN python manage.py collectstatic --noinput || echo "Collectstatic skipped"

#bind to Koyeb's injected PORT
CMD ["sh", "-c", "gunicorn rwoogaBackend.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 1 \
  --threads 2 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -"]
