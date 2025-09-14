# Investment Tracker - Raspberry Pi Deployment Guide

This guide provides step-by-step instructions for deploying and testing the Investment Tracker application on a Raspberry Pi using Docker.

## Prerequisites

1. A Raspberry Pi 4 (4GB or 8GB RAM recommended)
2. Raspberry Pi OS (64-bit recommended) installed and updated
3. SSH access to your Raspberry Pi
4. Docker and Docker Compose installed

## Initial Setup

1. Install required packages:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install -y git curl vim
   ```

2. Install Docker:
   ```bash
   # Install Docker
   curl -sSL https://get.docker.com | sh
   
   # Add current user to docker group
   sudo usermod -aG docker $USER
   
   # Start Docker service
   sudo systemctl enable docker
   sudo systemctl start docker
   
   # Verify installation
   docker --version
   ```

3. Install Docker Compose:
   ```bash
   # Install Docker Compose
   sudo apt install -y python3-pip libffi-dev
   pip3 install docker-compose
   
   # Verify installation
   docker-compose --version
   ```

## Clone and Configure

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/investment-tracker.git
   cd investment-tracker
   ```

2. Create environment files:
   ```bash
   # Create .env file for backend
   cat > backend/.env << EOL
   FLASK_APP=run.py
   FLASK_ENV=development
   DATABASE_URL=postgresql://postgres:postgres@db:5432/investment_tracker
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   EOL
   
   # Create .env file for database
   cat > .env << EOL
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=investment_tracker
   EOL
   ```

## Docker Configuration

1. Update `docker-compose.yml` for ARM architecture:
```yaml
version: '3.8'

services:
  db:
    image: postgres:13-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=investment_tracker
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.arm
    environment:
      - FLASK_APP=run.py
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/investment_tracker
    depends_on:
      - db
      - redis
    ports:
      - "5000:5000"

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.arm
    command: celery -A app.tasks.celery_tasks worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - backend

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.arm
    command: celery -A app.tasks.celery_tasks beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - backend

volumes:
  postgres_data:
```

2. Create ARM-specific Dockerfile (Dockerfile.arm):
```dockerfile
FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Set the default command
CMD ["python", "run.py"]
```

## Building and Running

1. Build the Docker images:
   ```bash
   docker-compose build
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. Monitor the logs:
   ```bash
   docker-compose logs -f
   ```

## Running Tests

1. Create a test environment:
   ```bash
   docker-compose -f docker-compose.test.yml build
   ```

2. Run the test suite:
   ```bash
   docker-compose -f docker-compose.test.yml run --rm backend pytest tests/ -v
   ```

3. Run tests with coverage:
   ```bash
   docker-compose -f docker-compose.test.yml run --rm backend pytest --cov=app tests/ -v
   ```

## Performance Considerations

1. Memory Management:
   - Monitor memory usage: `free -h`
   - Adjust Docker memory limits in `docker-compose.yml`:
     ```yaml
     services:
       backend:
         deploy:
           resources:
             limits:
               memory: 512M
     ```

2. Storage Management:
   - Monitor disk space: `df -h`
   - Consider using external storage for database volumes
   - Regularly clean up old Docker images and containers:
     ```bash
     docker system prune -a
     ```

3. CPU Usage:
   - Monitor CPU usage: `top` or `htop`
   - Consider adding CPU limits in `docker-compose.yml`:
     ```yaml
     services:
       backend:
         deploy:
           resources:
             limits:
               cpus: '0.5'
     ```

## Monitoring

1. Basic Monitoring:
   ```bash
   # Monitor containers
   docker stats
   
   # Check container logs
   docker-compose logs -f backend
   
   # Check application logs
   docker-compose exec backend tail -f /app/logs/app.log
   ```

2. Resource Usage:
   ```bash
   # System resources
   htop
   
   # Disk usage
   df -h
   
   # Memory usage
   free -h
   ```

## Troubleshooting

1. Container Issues:
   ```bash
   # Restart services
   docker-compose restart
   
   # Rebuild services
   docker-compose up -d --build
   
   # Check container status
   docker-compose ps
   ```

2. Database Issues:
   ```bash
   # Connect to database
   docker-compose exec db psql -U postgres -d investment_tracker
   
   # Check database logs
   docker-compose logs db
   ```

3. Application Issues:
   ```bash
   # Check application logs
   docker-compose logs backend
   
   # Access container shell
   docker-compose exec backend bash
   ```

## Backup and Restore

1. Database Backup:
   ```bash
   docker-compose exec db pg_dump -U postgres investment_tracker > backup.sql
   ```

2. Database Restore:
   ```bash
   cat backup.sql | docker-compose exec -T db psql -U postgres investment_tracker
   ```

## Security Considerations

1. Environment Variables:
   - Store sensitive data in `.env` files
   - Never commit `.env` files to version control
   - Use strong passwords and secret keys

2. Network Security:
   - Use internal Docker network for service communication
   - Expose only necessary ports
   - Configure firewall rules:
     ```bash
     sudo ufw allow 22
     sudo ufw allow 80
     sudo ufw allow 443
     sudo ufw enable
     ```

3. Regular Updates:
   ```bash
   # Update system packages
   sudo apt update
   sudo apt upgrade -y
   
   # Update Docker images
   docker-compose pull
   docker-compose up -d
   ```

## Additional Notes

1. CPU Architecture:
   - Raspberry Pi uses ARM architecture
   - Use ARM-compatible Docker images
   - Build custom images when ARM versions aren't available

2. Memory Management:
   - Monitor swap usage
   - Consider increasing swap if needed:
     ```bash
     # Add 2GB swap
     sudo fallocate -l 2G /swapfile
     sudo chmod 600 /swapfile
     sudo mkswap /swapfile
     sudo swapon /swapfile
     ```

3. Performance Optimization:
   - Use production settings in Flask
   - Enable PostgreSQL optimizations
   - Configure appropriate worker counts for Celery

4. Logging:
   - Configure log rotation
   - Monitor log sizes
   - Set appropriate log levels