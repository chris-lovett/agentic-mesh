FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY upstream_service/ /app/upstream_service/

EXPOSE 8080
CMD ["uvicorn", "upstream_service.main:app", "--host", "0.0.0.0", "--port", "8080"]
