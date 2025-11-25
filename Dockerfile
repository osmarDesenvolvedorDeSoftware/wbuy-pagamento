FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/storage/webhooks

EXPOSE 5000

CMD [
    "gunicorn",
    "--workers",
    "2",
    "--worker-class",
    "sync",
    "--timeout",
    "120",
    "--keep-alive",
    "5",
    "--bind",
    "0.0.0.0:5000",
    "--log-level",
    "info",
    "app:app"
]
