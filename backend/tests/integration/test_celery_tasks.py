import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.tasks.celery_tasks import update_security_prices, update_security_dividends
from app.models import Security, PriceHistory, Dividend

def test_price_update_task(db_session):
    """Test the price update Celery task"""
    # Setup test securities
    securities = [
        Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL'),
        Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT')
    ]
    for security in securities:
        db_session.add(security)
    db_session.commit()
    
    with patch('app.services.price_service.PriceService.fetch_latest_prices') as mock_fetch:
        # Mock the price fetch to return test data
        mock_data = PriceHistory(
            security_id=1,
            price_date=datetime.now().date(),
            open_price=100.00,
            high_price=105.00,
            low_price=98.00,
            close_price=102.00,
            volume=1000000,
            currency='USD'
        )
        mock_fetch.return_value = [mock_data]
        
        # Run the task
        result = update_security_prices.apply()
        
        # Check that prices were updated for both securities
        assert result.successful()
        assert mock_fetch.call_count == len(securities)
        assert len(PriceHistory.query.all()) == len(securities)

def test_dividend_update_task(db_session):
    """Test the dividend update Celery task"""
    # Setup test securities
    securities = [
        Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL'),
        Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT')
    ]
    for security in securities:
        db_session.add(security)
    db_session.commit()
    
    with patch('app.services.dividend_service.DividendService.fetch_dividend_data') as mock_fetch:
        # Mock the dividend fetch to return test data
        mock_data = [Dividend(
            security_id=1,
            platform_id=1,  # Add required platform_id
            ex_date=datetime.now().date(),
            dividend_per_share=0.88,
            quantity_held=100,  # Add required quantity
            currency='USD'
        )]
        mock_fetch.return_value = mock_data
        
        # Run the task
        result = update_security_dividends.apply()
        
        # Verify dividends were updated
        assert result.successful()
        assert mock_fetch.call_count == len(securities)
        assert len(Dividend.query.all()) == 1

@patch('celery.app.task.Task.apply_async')
def test_task_scheduling(mock_apply_async):
    """Test that tasks are scheduled correctly"""
    from app.tasks.celery_tasks import setup_periodic_tasks
    
    # Create mock sender
    sender = MagicMock()
    sender.add_periodic_task = MagicMock()
    
    # Call setup function
    setup_periodic_tasks(sender)
    
    # Verify price updates scheduled every 5 minutes
    assert sender.add_periodic_task.call_args_list[0][0][0] == 300.0
    
    # Verify dividend updates scheduled daily
    assert 'crontab' in str(sender.add_periodic_task.call_args_list[1])

def test_task_error_handling(db_session):
    """Test error handling in Celery tasks"""
    security = Security(ticker='ERROR', name='Error Test', currency='USD', yahoo_symbol='ERROR')
    db_session.add(security)
    db_session.commit()
    
    with patch('app.services.price_service.PriceService.fetch_latest_prices') as mock_fetch:
        # Simulate an error
        mock_fetch.side_effect = Exception('API Error')
        
        # Run the task
        result = update_security_prices.apply()
        
        # Task should complete despite error
        assert result.successful()
        
        # Verify error was logged
        # Note: In a real environment, you'd verify this in the Celery logs

def test_task_retry_mechanism(db_session):
    """Test that tasks properly implement retry mechanism"""
    security = Security(ticker='RETRY', name='Retry Test', currency='USD', yahoo_symbol='RETRY')
    db_session.add(security)
    db_session.commit()
    
    with patch('app.services.price_service.PriceService.fetch_latest_prices') as mock_fetch:
        # Simulate temporary failure
        mock_fetch.side_effect = [
            Exception('Temporary Error'),
            PriceHistory(
                security_id=1,
                price_date=datetime.now().date(),
                close_price=100.00,
                currency='USD'
            )
        ]
        
        # Run the task
        result = update_security_prices.apply()
        
        assert result.successful()
        assert mock_fetch.call_count == 2  # Verify retry occurred
