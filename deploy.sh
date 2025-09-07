#!/bin/bash

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0;31m'

echo -e "${GREEN}Starting Investment Tracker deployment...${NC}"

# Generate random passwords if .env doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
POSTGRES_PASSWORD=$(openssl rand -base64 32)
FLASK_SECRET_KEY=$(openssl rand -base64 32)
EOF
fi

# Load environment variables
export $(cat .env | xargs)

# Build and start services
echo "Starting services..."
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 20

# Run backend tests inside the container
echo "Running backend tests inside the container..."
docker-compose exec backend python -m pytest

echo -e "${GREEN}Deployment completed successfully!${NC}"

# Print access information
echo -e "\nAccess the application:"
echo "Frontend: http://localhost"
echo "API: http://localhost/api"
echo "Health check: http://localhost/api/health"