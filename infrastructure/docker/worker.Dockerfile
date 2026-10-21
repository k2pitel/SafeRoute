FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Async Worker, target architecture (afsnit 4.3.4.5): Celery worker + Beat.
CMD ["celery", "-A", "app.worker.celery_app", "worker", "--beat", "-l", "info"]
