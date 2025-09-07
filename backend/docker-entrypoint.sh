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
app = create_app('development')
with app.app_context():
    db.create_all()
END

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 wsgi:app
