from celery import Celery
from celery.schedules import crontab
from app import create_app
from app.services.price_service import PriceService
from app.services.dividend_service import DividendService
import logging

celery = Celery('tasks')

# Configure Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    task_acks_late=True
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
        for security in securities:
            try:
                price_data = service.fetch_latest_prices(security)
                if price_data:
                    if isinstance(price_data, list):
                        for price in price_data:
                            db.session.add(price)
                    else:
                        db.session.add(price_data)
            except Exception as exc:
                success = False
                app.logger.error(f"Error updating prices for {security.ticker}: {str(exc)}")
                continue
                
        try:
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
        for security in securities:
            try:
                dividend_data = service.fetch_dividend_data(security)
                if dividend_data:
                    if isinstance(dividend_data, list):
                        for dividend in dividend_data:
                            db.session.add(dividend)
                    else:
                        db.session.add(dividend_data)
            except Exception as exc:
                success = False
                app.logger.error(f"Error updating dividends for {security.ticker}: {str(exc)}")
                continue
                
        try:
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