@echo off
REM Start Celery worker
start cmd /k "celery -A app.extensions.celery worker --loglevel=info"

REM Start Celery beat for scheduled tasks
start cmd /k "celery -A app.extensions.celery beat --loglevel=info"

from app.tasks import update_prices, update_portfolio

# Run tasks manually
update_prices.delay()  # Async call
update_portfolio.delay()  # Async call