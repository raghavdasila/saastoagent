FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn[standard]==0.34.0 pydantic==2.10.4

COPY routedeck_framework /app/routedeck_framework

EXPOSE 8096
CMD ["python", "-m", "uvicorn", "routedeck_framework.examples.minimal-fastapi-react.backend.app:app", "--host", "0.0.0.0", "--port", "8096"]
