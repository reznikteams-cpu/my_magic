FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bot.py .
COPY database.py .
COPY robokassa_handler.py .
COPY webhook_server.py .

# Create logs directory
RUN mkdir -p /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${WEBHOOK_PORT:-5000}/health || exit 1

# Run both services
CMD ["sh", "-c", "python webhook_server.py & python bot.py"]
