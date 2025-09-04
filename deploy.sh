#!/bin/bash

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting Investment Tracker deployment...${NC}"

# Generate random passwords if .env doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
POSTGRES_PASSWORD=$(openssl rand -base64 32)
FLASK_SECRET_KEY=$(openssl rand -base64 32)
EOF
fi

# Run tests before deployment
echo "Running backend tests..."
cd backend
python -m pytest
cd ..

# Build and start services
echo "Starting services..."
docker-compose build
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "Running database migrations..."
docker-compose exec backend flask db upgrade

# Import test data if specified
if [ "$1" = "--with-test-data" ]; then
    echo "Importing test data..."
    docker-compose exec backend python -m pytest tests/test_master.py
fi

echo -e "${GREEN}Deployment completed successfully!${NC}"

# Print access information
echo -e "\nAccess the application:"
echo "Frontend: http://localhost"
echo "API: http://localhost/api"
echo "Health check: http://localhost/health"