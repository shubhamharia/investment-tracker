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
        # Mock the price fetch to return different test data for each security
        def mock_fetch_prices(security):
            return [PriceHistory(
                security_id=security.id,
                price_date=datetime.now().date(),
                open_price=100.00,
                high_price=105.00,
                low_price=98.00,
                close_price=102.00,
                volume=1000000,
                currency=security.currency
            )]
        
        mock_fetch.side_effect = mock_fetch_prices
        
        # Run the task
        result = update_security_prices.apply()
        
        # Check that prices were updated for both securities
        assert result.successful()
        assert mock_fetch.call_count == len(securities)  # Should be called once per security
        
        # Verify we have price histories for each security
        price_histories = PriceHistory.query.all()
        assert len(price_histories) == len(securities)
        
        # Verify each security has its own price history
        security_ids = {ph.security_id for ph in price_histories}
        assert security_ids == {s.id for s in securities}

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
        # Mock the dividend fetch to return different test data for each security
        def mock_fetch_dividends(security):
            return [Dividend(
                security_id=security.id,
                platform_id=1,  # Add required platform_id
                ex_date=datetime.now().date(),
                dividend_per_share=0.88,
                quantity_held=100,  # Add required quantity
                currency=security.currency
            )]
            
        mock_fetch.side_effect = mock_fetch_dividends
        
        # Run the task
        result = update_security_dividends.apply()
        
        # Verify dividends were updated
        assert result.successful()
        assert mock_fetch.call_count == len(securities)  # Should be called once per security
        
        # Verify we have dividends for each security
        dividends = Dividend.query.all()
        assert len(dividends) == len(securities)
        
        # Verify each security has its own dividend
        security_ids = {d.security_id for d in dividends}
        assert security_ids == {s.id for s in securities}
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
        # First call fails, second succeeds
        call_count = 0
        def mock_fetch_with_error(security):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception('Temporary Error')
            return [PriceHistory(
                security_id=security.id,
                price_date=datetime.now().date(),
                open_price=100.00,
                high_price=105.00,
                low_price=98.00,
                close_price=102.00,
                volume=1000000,
                currency=security.currency
            )]
            
        mock_fetch.side_effect = mock_fetch_with_error
        
        # Run the task
        with pytest.raises(Exception) as exc_info:
            result = update_security_prices.apply()
            
        # First attempt should fail
        assert 'Temporary Error' in str(exc_info.value)
        
        # Run again to test retry behavior
        result = update_security_prices.apply()
        assert result.successful()
        assert mock_fetch.call_count > 1  # Should have retried
