FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agentic_fabric/providers/ /app/agentic_fabric/providers/

EXPOSE 8085
CMD ["uvicorn", "agentic_fabric.providers.main:app", "--host", "0.0.0.0", "--port", "8085"]
