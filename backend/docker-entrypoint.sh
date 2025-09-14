#!/bin/sh

# Function to wait for services
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    
    echo "Waiting for $service_name..."
    while ! nc -z $host $port; do
        sleep 1
    done
    echo "$service_name is ready!"
}

# Determine the startup mode based on command arguments
STARTUP_MODE=${1:-web}

# Wait for dependencies
wait_for_service db 5432 "database"
wait_for_service redis 6379 "Redis"

# Initialize the database (only for web and celery-beat modes)
if [ "$STARTUP_MODE" = "web" ] || [ "$STARTUP_MODE" = "celery-beat" ]; then
    echo "Initializing database..."
    python << END
from app import create_app, db
from app.models import User, Portfolio, Security, Platform, Holding
app = create_app('development')
with app.app_context():
    db.create_all()
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Created tables:", tables)
END
fi

# Check if CSV data should be imported automatically (only for web mode)
if [ "$STARTUP_MODE" = "web" ]; then
    if [ "$AUTO_IMPORT_CSV" = "true" ] && [ -f "/app/data/combined_transactions_updated.csv" ]; then
        echo "Auto-importing CSV data..."
        python import_data.py import
    else
        echo "Skipping CSV import (AUTO_IMPORT_CSV not set or CSV file not found)"
        echo "To import data manually, run: docker-compose exec backend python import_data.py import"
    fi
fi

# Start the appropriate service based on startup mode
case "$STARTUP_MODE" in
    "web")
        echo "Starting Gunicorn web server..."
        exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 wsgi:app
        ;;
    "celery-worker")
        echo "Starting Celery worker..."
        exec celery -A app.tasks.celery_tasks.celery worker --loglevel=info --concurrency=2
        ;;
    "celery-beat")
        echo "Starting Celery beat scheduler..."
        exec celery -A app.tasks.celery_tasks.celery beat --loglevel=info
        ;;
    *)
        echo "Unknown startup mode: $STARTUP_MODE"
        echo "Valid modes: web, celery-worker, celery-beat"
        exit 1
        ;;
esac
