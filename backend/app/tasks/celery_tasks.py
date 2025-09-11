from celery import Celery
from celery.schedules import crontab
from app import create_app
from app.services.price_service import PriceService
from app.services.dividend_service import DividendService
import logging

celery = Celery('tasks')

# Load Celery configuration from celeryconfig.py
celery.config_from_object('celeryconfig')

# Additional task-specific configurations
celery.conf.update(
    task_track_started=True,
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    broker_pool_limit=None,  # Disable connection pool limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50  # Restart worker after 50 tasks
)

# Removed misplaced import after decorator

@celery.task(bind=True, max_retries=3, default_retry_delay=60)  # 1 minute delay between retries
def update_security_prices(self):
    """Update security prices from external API"""
    app = create_app()
    with app.app_context():
        from app.models import Security
        from app.extensions import db
        
        service = PriceService()
        securities = Security.query.all()
        
        success = True
        all_price_data = []

        # Batch fetch prices
        for security in securities:
            try:
                price_data = service.fetch_latest_prices(security)
                if price_data:
                    if isinstance(price_data, list):
                        all_price_data.extend(price_data)
                    else:
                        all_price_data.append(price_data)
            except Exception as exc:
                success = False
                app.logger.error(f"Error updating prices for {security.ticker}: {str(exc)}")
                
        # Batch commit all prices
        try:
            if all_price_data:
                for price in all_price_data:
                    db.session.add(price)
                db.session.commit()
        except Exception as exc:
            db.session.rollback()
            success = False
            app.logger.error(f"Error committing price updates: {str(exc)}")
            
        if not success:
            # Only retry if we had any failures
            raise self.retry(exc=Exception("Some price updates failed"))

@celery.task(bind=True, max_retries=3, default_retry_delay=60)  # 1 minute delay between retries
def update_security_dividends(self):
    """Update security dividends from external API"""
    app = create_app()
    with app.app_context():
        from app.models import Security
        from app.extensions import db
        
        service = DividendService()
        securities = Security.query.all()
        
        success = True
        all_dividend_data = []

        # Batch fetch dividends
        for security in securities:
            try:
                dividend_data = service.fetch_dividend_data(security)
                if dividend_data:
                    if isinstance(dividend_data, list):
                        all_dividend_data.extend(dividend_data)
                    else:
                        all_dividend_data.append(dividend_data)
            except Exception as exc:
                success = False
                app.logger.error(f"Error updating dividends for {security.ticker}: {str(exc)}")
                
        # Batch commit all dividends
        try:
            if all_dividend_data:
                for dividend in all_dividend_data:
                    db.session.add(dividend)
                db.session.commit()
        except Exception as exc:
            db.session.rollback()
            success = False
            app.logger.error(f"Error committing dividend updates: {str(exc)}")
            
        if not success:
            # Only retry if we had any failures
            raise self.retry(exc=Exception("Some dividend updates failed"))

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks"""
    # Update prices every 5 minutes during market hours
    sender.add_periodic_task(
        crontab(minute='*/5', hour='9-16', day_of_week='1-5'),  # Every 5 mins, 9 AM-4 PM, Mon-Fri
        update_security_prices.s(),
        name='update_security_prices'
    )
    
    # Update dividends once per day at 6 AM
    sender.add_periodic_task(
        crontab(hour=6, minute=0),  # 6 AM every day
        update_security_dividends.s(),
        name='update_security_dividends'
    )