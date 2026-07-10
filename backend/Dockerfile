FROM python:3.13-slim

WORKDIR /app/saastoagent-v0.1/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY vendor/routedeck-v0-compat /app/saastoagent-v0.1/vendor/routedeck-v0-compat
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/saastoagent-v0.1
COPY backend/ ./backend/

RUN mkdir -p /app/saastoagent-v0.1/uploads

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
