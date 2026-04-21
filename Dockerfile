FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Use the PORT environment variable provided by Railway
EXPOSE $PORT

# Run migrations and then start Gunicorn
CMD sh -c "python manage.py migrate && python manage.py ensure_superuser && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
