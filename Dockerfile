FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

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

CMD gunicorn --bind 0.0.0.0:8000 --workers=2 --threads=2 --timeout=60 --access-logfile - --error-logfile - rwoogaBackend.wsgi:application