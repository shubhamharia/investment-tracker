# backend/celery_config.py
from celery.schedules import crontab

# Celery configuration
broker_url = 'redis://redis:6379/0'
result_backend = 'redis://redis:6379/0'
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'Europe/London'
enable_utc = True

# Task routing
task_routes = {
    'app.update_prices': {'queue': 'price_updates'},
    'app.import_historical_data': {'queue': 'data_import'},
}

# Scheduled tasks
beat_schedule = {
    # Update prices every 5 minutes during market hours
    'update-prices-market-hours': {
        'task': 'app.update_prices',
        'schedule': crontab(minute='*/5', hour='8-16', day_of_week='1-5'),
    },
    # Update prices every hour outside market hours
    'update-prices-after-hours': {
        'task': 'app.update_prices',
        'schedule': crontab(minute=0),
    },
    # Daily backup at 2 AM
    'daily-backup': {
        'task': 'app.backup_database',
        'schedule': crontab(hour=2, minute=0),
    },
}
