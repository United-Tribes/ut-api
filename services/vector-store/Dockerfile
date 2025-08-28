FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY sample_knowledge_graph.json* ./
COPY knowledge_graph_enhanced_*.json* ./

# Set environment variables
ENV PORT=8000
ENV AWS_REGION=us-east-1
ENV SERVICE_NAME=ut-vector-store
ENV USE_MOCK=false

# Expose port
EXPOSE 8000

# Start command
CMD ["python3", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]