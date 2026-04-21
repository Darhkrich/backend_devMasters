FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (optional, but good for production)
RUN python manage.py collectstatic --noinput

# Create non-root user (optional but good practice)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port that Railway will use
EXPOSE $PORT

# Run migrations on startup, then start Gunicorn
CMD sh -c "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"