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

ENV DJANGO_SETTINGS_MODULE=rwoogaBackend.settings
ENV SECRET_KEY=temporary-build-key-will-be-overridden
ENV DEBUG=False
ENV DATABASE_URL=sqlite:///dummy.db
ENV CORS_ALLOWED_ORIGINS=http://localhost:3000
ENV CSRF_TRUSTED_ORIGINS=http://localhost:3000

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port (Koyeb will inject the actual PORT at runtime)
EXPOSE 8000

# Start command - uses Koyeb's $PORT variable at runtime
CMD ["sh", "-c", "gunicorn rwoogaBackend.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 4 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -"]