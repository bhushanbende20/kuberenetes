FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY app/ app/

# Environment configuration
ENV HOST=0.0.0.0
ENV PORT=8000
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV DEFAULT_MODEL=qwen3.5:4b

EXPOSE 8000

CMD ["python", "main.py"]
