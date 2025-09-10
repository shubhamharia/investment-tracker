from celery import Celery
from celery.schedules import crontab
from app import create_app
from app.services.price_service import PriceService
from app.services.dividend_service import DividendService

celery = Celery('tasks')

@celery.task
def update_security_prices():
    """Update security prices from external API"""
    app = create_app()
    with app.app_context():
        from app.models import Security
        price_service = PriceService()
        securities = Security.query.all()
        for security in securities:
            price_service.fetch_latest_prices(security)

@celery.task
def update_security_dividends():
    """Update security dividends from external API"""
    app = create_app()
    with app.app_context():
        from app.models import Security
        dividend_service = DividendService()
        securities = Security.query.all()
        for security in securities:
            dividend_service.fetch_dividend_data(security)

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