from celery import Celery
from celery.schedules import crontab
from app import create_app
from app.services.price_service import PriceService
from app.services.dividend_service import DividendService

celery = Celery('tasks')

@celery.task(bind=True, max_retries=3, default_retry_delay=1)
def update_security_prices(self):
    """Update security prices from external API"""
    app = create_app()
    with app.app_context():
        from app.models import Security
        service = PriceService()
        securities = Security.query.all()
        
        # Call the service once with all securities
        try:
            service.fetch_latest_prices(securities)
        except Exception as exc:
            self.retry(exc=exc)

@celery.task(bind=True, max_retries=3, default_retry_delay=1)
def update_security_dividends(self):
    """Update security dividends from external API"""
    app = create_app()
    with app.app_context():
        from app.models import Security
        service = DividendService()
        securities = Security.query.all()
        
        # Call the service once with all securities
        try:
            service.fetch_dividend_data(securities)
        except Exception as exc:
            self.retry(exc=exc)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks"""
    # Update prices every 5 minutes
    sender.add_periodic_task(
        300.0,
        update_security_prices.s(),
        name='update prices every 5 minutes'
    )
    
    # Update dividends daily at midnight
    sender.add_periodic_task(
        crontab(minute=0, hour=0),
        update_security_dividends.s(),
        name='update dividends daily'
    )