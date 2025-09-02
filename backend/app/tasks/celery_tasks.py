from ..extensions import celery
from ..services.price_service import PriceService
from ..services.portfolio_service import PortfolioService
from celery.schedules import crontab
import logging

@celery.task(name='tasks.update_prices')
def update_prices():
    """Task to update security prices"""
    try:
        updated_count = PriceService.update_all_prices()
        logging.info(f"Updated prices for {updated_count} securities")
        return updated_count
    except Exception as e:
        logging.error(f"Error updating prices: {str(e)}")
        raise

@celery.task(name='tasks.update_portfolio')
def update_portfolio():
    """Task to update portfolio holdings with latest prices"""
    try:
        PortfolioService.update_holdings()
        logging.info("Portfolio holdings updated successfully")
    except Exception as e:
        logging.error(f"Error updating portfolio: {str(e)}")
        raise

# Schedule periodic tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Update prices every day at market close (4:30 PM UTC)
    sender.add_periodic_task(
        crontab(hour=16, minute=30),
        update_prices.s(),
        name='update_prices_daily'
    )
    
    # Update portfolio 5 minutes after price updates
    sender.add_periodic_task(
        crontab(hour=16, minute=35),
        update_portfolio.s(),
        name='update_portfolio_daily'
    )