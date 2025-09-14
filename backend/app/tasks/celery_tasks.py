"""Celery tasks for the application."""
from celery import Celery
from celery.schedules import crontab
from datetime import datetime
import time
import random
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

@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def update_single_security_price(self, security_id):
    """Update price for a single security - distributed task"""
    print(f"\n=== Single Security Price Update ===")
    print(f"Security ID: {security_id}")
    app = setup_app_context()
    is_testing = os.environ.get("FLASK_ENV") == "testing"
    
    with app.app_context():
        from app.models import Security, PriceHistory
        from app.extensions import db
        
        try:
            # Get the specific security
            security = Security.query.get(security_id)
            if not security:
                print(f"Security {security_id} not found")
                return {"status": "error", "message": f"Security {security_id} not found"}
            
            print(f"Processing security: {security.ticker}")
            
            # Add random delay to avoid rate limiting
            import random
            delay = random.uniform(1, 5)  # 1-5 second random delay
            print(f"Applying rate limiting delay: {delay:.2f}s")
            time.sleep(delay)
            
            # Get price service
            service = get_price_service()
            price_data = service.get_current_price(security)
            
            if price_data is not None:
                print(f"Received price data: {price_data}")
                
                # Create price history record
                price_history = PriceHistory(
                    security_id=security.id,
                    close_price=price_data['Close'],
                    open_price=price_data['Open'],
                    high_price=price_data['High'],
                    low_price=price_data['Low'],
                    volume=price_data['Volume'],
                    price_date=datetime.utcnow().date(),
                    currency=security.currency or "USD",
                    data_source="yahoo"
                )
                
                # Check for existing record and update or create
                existing = PriceHistory.query.filter_by(
                    security_id=security.id,
                    price_date=price_history.price_date
                ).first()
                
                if existing:
                    existing.close_price = price_history.close_price
                    existing.open_price = price_history.open_price
                    existing.high_price = price_history.high_price
                    existing.low_price = price_history.low_price
                    existing.volume = price_history.volume
                    existing.currency = price_history.currency
                    existing.data_source = price_history.data_source
                    print(f"Updated existing price record for {security.ticker}")
                else:
                    db.session.add(price_history)
                    print(f"Created new price record for {security.ticker}")
                
                db.session.commit()
                
                return {
                    "status": "success", 
                    "security_id": security_id,
                    "ticker": security.ticker,
                    "price": float(price_data['Close'])
                }
            else:
                print(f"No price data received for {security.ticker}")
                return {
                    "status": "no_data", 
                    "security_id": security_id,
                    "ticker": security.ticker
                }
                
        except Exception as e:
            print(f"Error updating price for security {security_id}: {str(e)}")
            db.session.rollback()
            
            # In test mode, always propagate
            if is_testing:
                raise e
            
            # In production, retry with exponential backoff
            retry_count = getattr(self.request, "retries", 0)
            if retry_count >= self.max_retries:
                return {
                    "status": "error", 
                    "security_id": security_id,
                    "message": str(e)
                }
            
            # Exponential backoff: 30s, 60s, 120s
            retry_delay = self.default_retry_delay * (2 ** retry_count)
            print(f"Retrying in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=retry_delay)

@celery.task(bind=True, max_retries=2, default_retry_delay=60)
def update_security_prices_coordinator(self):
    """Coordinator task that dispatches individual security price update tasks"""
    print("\n=== Price Update Coordinator Start ===")
    app = setup_app_context()
    
    with app.app_context():
        from app.models import Security
        from app.extensions import db
        
        try:
            securities = Security.query.all()
            print(f"Found {len(securities)} securities to process")
            
            if not securities:
                print("No securities found to update")
                return {"status": "no_securities", "processed": 0}
            
            # Dispatch individual tasks with staggered timing
            task_results = []
            batch_size = 5  # Process in batches to avoid overwhelming
            
            for i, security in enumerate(securities):
                # Calculate delay for this task (stagger dispatching)
                dispatch_delay = (i % batch_size) * 10  # 10 second intervals within batch
                batch_delay = (i // batch_size) * 30    # 30 second delay between batches
                total_delay = dispatch_delay + batch_delay
                
                print(f"Scheduling {security.ticker} with {total_delay}s delay")
                
                # Dispatch task with delay
                task = update_single_security_price.apply_async(
                    args=[security.id],
                    countdown=total_delay
                )
                task_results.append({
                    "security_id": security.id,
                    "ticker": security.ticker,
                    "task_id": task.id,
                    "delay": total_delay
                })
            
            print(f"Dispatched {len(task_results)} individual price update tasks")
            
            return {
                "status": "dispatched",
                "total_securities": len(securities),
                "dispatched_tasks": len(task_results),
                "task_ids": [t["task_id"] for t in task_results]
            }
            
        except Exception as e:
            print(f"Coordinator error: {str(e)}")
            raise

@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def update_single_security_dividend(self, security_id):
    """Update dividend for a single security - distributed task"""
    print(f"\n=== Single Security Dividend Update ===")
    print(f"Security ID: {security_id}")
    app = setup_app_context()
    is_testing = os.environ.get("FLASK_ENV") == "testing"
    
    with app.app_context():
        from app.models import Security, Dividend
        from app.extensions import db
        
        try:
            # Get the specific security
            security = Security.query.get(security_id)
            if not security:
                print(f"Security {security_id} not found")
                return {"status": "error", "message": f"Security {security_id} not found"}
            
            print(f"Processing dividend for: {security.ticker}")
            
            # Add random delay to avoid rate limiting
            delay = random.uniform(2, 8)  # 2-8 second random delay
            print(f"Applying rate limiting delay: {delay:.2f}s")
            time.sleep(delay)
            
            # Get dividend service
            service = get_dividend_service()
            dividend_data = service.fetch_dividend_data(security)
            
            if dividend_data:
                if isinstance(dividend_data, list):
                    added_count = 0
                    for dividend in dividend_data:
                        db.session.add(dividend)
                        added_count += 1
                    print(f"Added {added_count} dividend records for {security.ticker}")
                else:
                    db.session.add(dividend_data)
                    print(f"Added 1 dividend record for {security.ticker}")
                
                db.session.commit()
                
                return {
                    "status": "success",
                    "security_id": security_id,
                    "ticker": security.ticker,
                    "dividends_added": added_count if isinstance(dividend_data, list) else 1
                }
            else:
                print(f"No dividend data found for {security.ticker}")
                return {
                    "status": "no_data",
                    "security_id": security_id,
                    "ticker": security.ticker
                }
                
        except Exception as e:
            print(f"Error updating dividend for security {security_id}: {str(e)}")
            db.session.rollback()
            
            # In test mode, always propagate
            if is_testing:
                raise e
            
            # In production, retry with exponential backoff
            retry_count = getattr(self.request, "retries", 0)
            if retry_count >= self.max_retries:
                return {
                    "status": "error",
                    "security_id": security_id,
                    "message": str(e)
                }
            
            # Exponential backoff: 30s, 60s, 120s
            retry_delay = self.default_retry_delay * (2 ** retry_count)
            print(f"Retrying in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=retry_delay)

@celery.task(bind=True, max_retries=2, default_retry_delay=60)
def update_security_dividends_coordinator(self):
    """Coordinator task that dispatches individual security dividend update tasks"""
    print("\n=== Dividend Update Coordinator Start ===")
    app = setup_app_context()
    
    with app.app_context():
        from app.models import Security
        from app.extensions import db
        
        try:
            securities = Security.query.all()
            print(f"Found {len(securities)} securities to process for dividends")
            
            if not securities:
                print("No securities found to update dividends")
                return {"status": "no_securities", "processed": 0}
            
            # Dispatch individual tasks with staggered timing
            task_results = []
            batch_size = 3  # Smaller batches for dividends (less frequent updates)
            
            for i, security in enumerate(securities):
                # Calculate delay for this task (stagger dispatching)
                dispatch_delay = (i % batch_size) * 15  # 15 second intervals within batch
                batch_delay = (i // batch_size) * 60    # 60 second delay between batches
                total_delay = dispatch_delay + batch_delay
                
                print(f"Scheduling dividend update for {security.ticker} with {total_delay}s delay")
                
                # Dispatch task with delay
                task = update_single_security_dividend.apply_async(
                    args=[security.id],
                    countdown=total_delay
                )
                task_results.append({
                    "security_id": security.id,
                    "ticker": security.ticker,
                    "task_id": task.id,
                    "delay": total_delay
                })
            
            print(f"Dispatched {len(task_results)} individual dividend update tasks")
            
            return {
                "status": "dispatched",
                "total_securities": len(securities),
                "dispatched_tasks": len(task_results),
                "task_ids": [t["task_id"] for t in task_results]
            }
            
        except Exception as e:
            print(f"Dividend coordinator error: {str(e)}")
            raise

@celery.task(bind=True, max_retries=3, default_retry_delay=1)
def update_security_dividends(self):
    """Legacy bulk dividend update task - kept for backward compatibility"""
    print("\n=== Legacy Dividend Update (Deprecated) ===")
    print("This task is deprecated. Use update_security_dividends_coordinator instead.")
    
    # Delegate to the new coordinator
    return update_security_dividends_coordinator.delay()

# Schedule periodic tasks

@celery.task
def setup_periodic_tasks(sender):
    """Setup periodic Celery tasks"""
    # Schedule price updates during market hours (using coordinator)
    sender.add_periodic_task(
        crontab(
            minute="0",    # Once per hour
            hour="9-16",   # 9 AM to 4 PM
            day_of_week="1-5"  # Monday to Friday
        ),
        update_security_prices_coordinator.s(),
        name="update_security_prices_coordinator"
    )
    
    # Schedule dividend updates daily (using coordinator)
    sender.add_periodic_task(
        crontab(
            minute="0",
            hour="17",
            day_of_week="1-5"
        ),
        update_security_dividends_coordinator.s(),
        name="update_security_dividends_coordinator"
    )