FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY prompts/ ./prompts/

# Set environment variables
ENV PORT=8000
ENV AWS_REGION=us-east-1
ENV SERVICE_NAME=ut-query-service
ENV USE_MOCK=false
ENV VECTOR_STORE_URL=https://ut-vector-store.apprunner.us-east-1.amazonaws.com

# Expose port
EXPOSE 8000

# Start command
CMD ["python3", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]