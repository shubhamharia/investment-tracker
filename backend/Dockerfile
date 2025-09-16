# backend/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# IMPORTANT: Make the entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app

# Add entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 portfolio && chown -R portfolio:portfolio /app
USER portfolio

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Default command
ENTRYPOINT ["./docker-entrypoint.sh"]

