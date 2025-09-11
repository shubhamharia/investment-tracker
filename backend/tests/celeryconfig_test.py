CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
broker_url = 'memory://'
result_backend = 'cache+memory://'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

task_routes = {
    'app.tasks.update_security_prices': {'queue': 'prices'},
    'app.tasks.update_security_dividends': {'queue': 'dividends'}
}