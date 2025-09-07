# Backend - Investment Tracker

## Overview

The backend provides a RESTful API for managing user accounts, portfolios, securities, transactions, and other investment-related data.

## Tech Stack

*   Python 3.11+
*   Flask
*   Flask-SQLAlchemy
*   psycopg2
*   Redis
*   Celery
*   pytest

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd backend
    ```
2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate   # Linux/Mac
    venv\Scripts\activate  # Windows
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Database

1.  **Install PostgreSQL:**
    *   Ubuntu: `sudo apt-get install postgresql postgresql-contrib`
    *   macOS: `brew install postgres`
2.  **Create a database:**
    ```bash
    sudo -u postgres psql
    postgres=# CREATE DATABASE investment_tracker;
    postgres=# CREATE USER investment_tracker WITH PASSWORD 'your_password';
    postgres=# GRANT ALL PRIVILEGES ON DATABASE investment_tracker TO investment_tracker;
    postgres=# \q
    ```

## Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```
SECRET_KEY=<your-secret-key>
DATABASE_URL=postgresql://investment_tracker:your_password@localhost/investment_tracker
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Running the Application

1.  **Start Redis:**
    ```bash
    redis-server
    ```
2.  **Start Celery worker:**
    ```bash
    celery -A app.tasks.celery_tasks.celery worker --loglevel=info
    ```
3.  **Run the Flask application:**
    ```bash
    flask run
    ```

## Testing

1.  **Install pytest:**
    ```bash
    pip install pytest
    ```
2.  **Run tests:**
    ```bash
    cd backend
    pytest
    ```