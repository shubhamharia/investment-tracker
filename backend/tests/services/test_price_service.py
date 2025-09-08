import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock
import pandas as pd
from app.models import Security, PriceHistory
from app.services.price_service import PriceService

@pytest.fixture
def mock_yahoo_finance():
    with patch('yfinance.Ticker') as mock_ticker:
        # Create mock price data
        mock_data = pd.DataFrame({
            'Open': [100.0],
            'High': [105.0],
            'Low': [98.0],
            'Close': [102.0],
            'Volume': [1000000]
        }, index=pd.date_range('2025-01-01', periods=1))
        
        mock_ticker.return_value.history.return_value = mock_data
        yield mock_ticker

def test_fetch_latest_prices(db_session, mock_yahoo_finance):
    """Test fetching latest price data from Yahoo Finance"""
    security = Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL')
    db_session.add(security)
    db_session.commit()
    
    price_history = PriceService.fetch_latest_prices(security)
    
    assert price_history is not None
    assert price_history.security_id == security.id
    assert price_history.open_price == Decimal('100.0')
    assert price_history.close_price == Decimal('102.0')
    assert price_history.currency == 'USD'

def test_update_all_prices(db_session, mock_yahoo_finance):
    """Test updating prices for all securities"""
    securities = [
        Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL'),
        Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT')
    ]
    for security in securities:
        db_session.add(security)
    db_session.commit()
    
    updated_count = PriceService.update_all_prices()
    
    assert updated_count == 2
    
    # Verify price histories in database
    for security in securities:
        price = PriceHistory.query.filter_by(security_id=security.id).first()
        assert price is not None
        assert price.close_price == Decimal('102.0')

def test_price_update_with_error(db_session):
    """Test price update handling when Yahoo Finance raises an error"""
    security = Security(ticker='ERROR', name='Error Test', currency='USD', yahoo_symbol='ERROR')
    db_session.add(security)
    db_session.commit()
    
    with patch('yfinance.Ticker') as mock_ticker:
        mock_ticker.return_value.history.side_effect = Exception('API Error')
        
        price_history = PriceService.fetch_latest_prices(security)
        assert price_history is None
        
        # Verify no price history was created
        assert PriceHistory.query.filter_by(security_id=security.id).first() is None

def test_price_update_with_empty_data(db_session):
    """Test price update handling when no data is returned"""
    security = Security(ticker='EMPTY', name='Empty Test', currency='USD', yahoo_symbol='EMPTY')
    db_session.add(security)
    db_session.commit()
    
    with patch('yfinance.Ticker') as mock_ticker:
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        
        price_history = PriceService.fetch_latest_prices(security)
        assert price_history is None
        
        # Verify no price history was created
        assert PriceHistory.query.filter_by(security_id=security.id).first() is None

def test_price_decimal_precision(db_session, mock_yahoo_finance):
    """Test that price decimals are handled with proper precision"""
    security = Security(ticker='TEST', name='Test Inc.', currency='USD', yahoo_symbol='TEST')
    db_session.add(security)
    db_session.commit()
    
    # Mock data with more decimal places
    mock_yahoo_finance.return_value.history.return_value = pd.DataFrame({
        'Open': [100.123456],
        'High': [105.123456],
        'Low': [98.123456],
        'Close': [102.123456],
        'Volume': [1000000]
    }, index=pd.date_range('2025-01-01', periods=1))
    
    price_history = PriceService.fetch_latest_prices(security)
    
    assert price_history is not None
    # Verify decimal precision is maintained correctly
    assert str(price_history.close_price) == '102.12345600'
