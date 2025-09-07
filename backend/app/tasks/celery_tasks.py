from celery import Celery
from app import create_app
from app.services.price_service import update_prices

celery = Celery('tasks')

@celery.task
def update_security_prices():
    """Update security prices from external API"""
    app = create_app()
    with app.app_context():
        update_prices()

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks"""
    sender.add_periodic_task(
        300.0,  # 5 minutes
        update_security_prices.s(),
        name='update prices every 5 minutes'
    )