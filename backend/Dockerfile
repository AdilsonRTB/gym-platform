FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libjpeg62-turbo zlib1g libwebp7 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN DJANGO_DEBUG=false DJANGO_SECRET_KEY=build \
    python manage.py collectstatic --noinput \
    && useradd --create-home app && mkdir -p /app/media && chown -R app /app/media

USER app
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 3 --timeout 60 --access-logfile -"]
