FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", \
     "-w", "2", \
     "-k", "sync", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "-b", "0.0.0.0:5000", \
     "--log-level", "info", \
     "app:app"]
