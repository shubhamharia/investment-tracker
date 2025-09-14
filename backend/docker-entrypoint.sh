#!/bin/sh

# Wait for the database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database is ready!"

# Initialize the database
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

# Check if CSV data should be imported automatically
if [ "$AUTO_IMPORT_CSV" = "true" ] && [ -f "/app/data/combined_transactions_updated.csv" ]; then
    echo "Auto-importing CSV data..."
    python import_data.py import
else
    echo "Skipping CSV import (AUTO_IMPORT_CSV not set or CSV file not found)"
    echo "To import data manually, run: docker-compose exec backend python import_data.py import"
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 wsgi:app
