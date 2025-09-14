import os

# Use environment variables with fallback to Docker service names
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task routing configuration
task_routes = {
    'app.tasks.celery_tasks.update_security_prices': {'queue': 'prices'},
    'app.tasks.celery_tasks.update_security_dividends': {'queue': 'dividends'}
}

# Worker configuration
worker_prefetch_multiplier = 1
task_acks_late = True
task_reject_on_worker_lost = True

# Retry configuration
task_default_retry_delay = 60
task_max_retries = 3

# Task time limits
task_soft_time_limit = 600  # 10 minutes
task_time_limit = 900       # 15 minutes

# Beat schedule for periodic tasks
beat_schedule = {
    'update-prices-every-5-minutes': {
        'task': 'app.tasks.celery_tasks.update_security_prices',
        'schedule': 300.0,  # 5 minutes
    },
    'update-dividends-daily': {
        'task': 'app.tasks.celery_tasks.update_security_dividends',
        'schedule': 86400.0,  # 24 hours
    },
}