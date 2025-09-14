"""Celery tasks for the application."""
from celery import Celery
from celery.schedules import crontab
from datetime import datetime
from app import create_app
from app.services.service_manager import get_price_service, get_dividend_service
import logging
import os

celery = Celery("tasks")

# Load Celery configuration based on environment
if os.environ.get("FLASK_ENV") == "testing":
    celery.config_from_object("tests.celeryconfig_test")
else:
    celery.config_from_object("celeryconfig")

# Additional task-specific configurations
celery.conf.update(
    task_track_started=True,
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    broker_pool_limit=None,  # Disable connection pool limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50  # Restart worker after 50 tasks
)

if os.environ.get("FLASK_ENV") == "testing":
    celery.conf.update(
        task_always_eager=True,  # For testing
        task_eager_propagates=True  # For testing
    )

def setup_app_context():
    """Create and configure Flask app context"""
    config_name = "testing" if os.environ.get("FLASK_ENV") == "testing" else "default"
    print(f"\n=== Setting up app context ===")
    print(f"Config name: {config_name}")
    
    # For testing, use the same app instance
    if config_name == "testing":
        from flask import current_app
        if current_app:
            print("Using existing Flask app")
            return current_app
    
    print("Creating new Flask app")
    app = create_app(config_name)
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    return app

@celery.task(bind=True, max_retries=3, default_retry_delay=1)
def update_security_prices(self):
    """Update security prices from external API"""
    print("\n=== Task Function Start ===")
    print(f"Current FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    app = setup_app_context()
    is_testing = os.environ.get("FLASK_ENV") == "testing"
    print(f"Testing mode: {is_testing}")
    
    with app.app_context():
        from app.models import Security, PriceHistory
        from app.extensions import db
        
        try:
            print("\n=== Task Execution Debug ===")
            print("Task instance:", self)
            print("Has retry method:", hasattr(self, "retry"))
            print("Max retries:", getattr(self, "max_retries", None))
            
            # Verify database state
            print("\n=== Database Check ===")
            print(f"Database tables: {db.metadata.tables.keys()}")
            print(f"Database engine: {db.engine.url}")
            
            # List all tables and their row counts
            for table in db.metadata.sorted_tables:
                count = db.session.query(table).count()
                print(f"Table {table.name}: {count} rows")
            
            # Ensure tables exist in test environment
            if is_testing:
                print("Ensuring tables exist in test mode")
                db.create_all()
            
            securities = Security.query.all()
            print(f"Found {len(securities)} securities to process")
            print(f"Securities: {[s.ticker for s in securities]}")
            if not securities:
                logging.info("No securities found to update")
                return True
            
            # Track failures
            failures = []
            failed_tickers = []
            
            # Process securities - in test mode, fail fast
            try:
                # Track price histories to be added
                new_price_histories = []
                for security in securities:
                    try:
                        print(f"\nProcessing security: {security.ticker}")
                        
                        # Get price service for each security to ensure we get the mocked version
                        service = get_price_service()
                        price = service.get_current_price(security)
                        
                        if price is not None:
                            print(f"Received price: {price}")
                            price_history = PriceHistory(
                                security_id=security.id,
                                close_price=price,
                                price_date=datetime.utcnow().date(),
                                currency="USD"  # Default currency
                            )
                            new_price_histories.append(price_history)
                    except Exception as e:
                        print(f"\n=== Error for {security.ticker} ===")
                        print(f"Error: {str(e)}")
                        
                        db.session.rollback()  # Rollback any pending changes
                        
                        # In test mode, always propagate
                        if is_testing:
                            print("Test mode: propagating error")
                            # Ensure all changes are rolled back 
                            raise e
                        
                        # In production, collect failures
                        failures.append((security.ticker, e))
                        failed_tickers.append(security.ticker)
            except Exception as e:
                print("\n=== Outer Exception ===")
                print(f"Error: {str(e)}")
                db.session.rollback()
                raise
                
            # Only commit if there were no failures
            if not failures:
                try:
                    for ph in new_price_histories:
                        db.session.add(ph)
                    db.session.commit()
                    print("Successfully committed all price updates")
                except Exception as e:
                    print("Failed to commit price updates")
                    db.session.rollback()
                    raise e
            else:
                error_msg = f"Failed to update prices for: {', '.join(failed_tickers)}"
                logging.error(error_msg)
                
                db.session.rollback()  # Ensure no partial commits
                
                if is_testing:
                    # Test mode - raise first failure
                    raise failures[0][1]
                elif len(failures) == len(securities):
                    # Complete failure - raise
                    raise failures[0][1]
                else:
                    # Production mode with partial failure - retry
                    self.retry(exc=failures[0][1])
            
            return True
            
        except Exception as e:
            # Log and propagate any errors
            logging.error(f"Task failed: {str(e)}", exc_info=True)
            raise  # Always propagate exceptions

@celery.task(bind=True, max_retries=3, default_retry_delay=1)
def update_security_dividends(self):
    """Update security dividends from external API"""
    app = setup_app_context()
    
    with app.app_context():
        from app.models import Security, Dividend
        from app.extensions import db
        
        # Ensure tables exist in test environment
        if os.environ.get("FLASK_ENV") == "testing":
            db.create_all()
        
        securities = Security.query.all()
        if not securities:
            logging.info("No securities found to update dividends")
            return True
        
        # Get service once at task start
        service = get_dividend_service()
        
        # Process each security
        for security in securities:
            try:
                dividend_data = service.fetch_dividend_data(security)
                if dividend_data:
                    if isinstance(dividend_data, list):
                        for dividend in dividend_data:
                            db.session.add(dividend)
                    else:
                        db.session.add(dividend_data)
                    db.session.commit()
            except Exception as e:
                logging.error(f"Error getting dividends for {security.ticker}: {str(e)}")
                db.session.rollback()
                retry_count = getattr(self.request, "retries", 0)
                if retry_count >= self.max_retries:
                    logging.error(f"Max retries ({self.max_retries}) reached. Final error: {str(e)}")
                    raise e
                logging.info(f"Attempting retry {retry_count + 1} of {self.max_retries}")
                raise self.retry(exc=e, countdown=0)
        return True

# Schedule periodic tasks

@celery.task
def setup_periodic_tasks(sender):
    """Setup periodic Celery tasks"""
    # Schedule price updates during market hours
    sender.add_periodic_task(
        crontab(
            minute="*/5",  # Every 5 minutes
            hour="9-16",   # 9 AM to 4 PM
            day_of_week="1-5"  # Monday to Friday
        ),
        update_security_prices.s(),
        name="update_security_prices"
    )
    
    # Schedule dividend updates daily
    sender.add_periodic_task(
        crontab(
            minute="0",
            hour="17",
            day_of_week="1-5"
        ),
        update_security_dividends.s(),
        name="update_security_dividends"
    )