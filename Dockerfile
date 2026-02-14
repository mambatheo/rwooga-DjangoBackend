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

# Set environment variables for collectstatic
ENV DJANGO_SETTINGS_MODULE=rwoogaBackend.settings
ENV SECRET_KEY=temporary-build-key-will-be-overridden
ENV DEBUG=False
ENV DATABASE_URL=sqlite:///dummy.db

# Collect static files (this will work now)
RUN python manage.py collectstatic --noinput

# Clean up build env vars (will be replaced by Koyeb's env vars at runtime)
ENV SECRET_KEY=
ENV DATABASE_URL=

# Bind to Koyeb's injected PORT
CMD ["sh", "-c", "gunicorn rwoogaBackend.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 4 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -"]
