import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
import pandas as pd
from app.models import Security, Platform, Holding, Dividend, Portfolio
from app.services.dividend_service import DividendService

@pytest.fixture
def mock_yahoo_finance():
    with patch('yfinance.Ticker') as mock_ticker:
        # Create mock dividend data
        dates = pd.date_range(start='2025-01-01', end='2025-12-31', periods=4)
        dividends = pd.Series([0.88, 0.88, 0.88, 0.88], index=dates)
        mock_ticker.return_value.actions = pd.DataFrame({'Dividends': dividends})
        yield mock_ticker

def test_fetch_dividend_data(db_session, mock_yahoo_finance):
    """Test fetching dividend data from Yahoo Finance"""
    # Create test data
    security = Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL')
    platform = Platform(name='Test Platform', currency='USD')
    
    # Create test user and portfolio
    from app.models.user import User
    user = User(username='testuser', email='test@example.com')
    user.set_password('testpass')
    portfolio = Portfolio(name='Test Portfolio', user=user)
    
    db_session.add_all([security, platform, user, portfolio])
    db_session.commit()
    
    # Create a holding
    holding = Holding(
        portfolio=portfolio,
        security=security,
        platform=platform,
        quantity=Decimal('100'),
        currency='USD',  # Set to match platform's currency
        average_cost=Decimal('150.00'),
        total_cost=Decimal('15000.00')
    )
    db_session.add(holding)
    db_session.commit()
    
    # Test dividend fetching
    dividends = DividendService.fetch_dividend_data(security)
    
    assert len(dividends) == 4
    for dividend in dividends:
        assert dividend.security_id == security.id
        assert dividend.platform_id == platform.id
        assert dividend.dividend_per_share == Decimal('0.88')
        assert dividend.quantity_held == Decimal('100')
        assert dividend.gross_dividend == Decimal('88.00')

def test_update_all_dividends(db_session, mock_yahoo_finance):
    """Test updating dividends for all securities"""
    # Create test data
    security1 = Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL')
    security2 = Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT')
    platform = Platform(name='Test Platform', currency='USD')
    
    # Create user and portfolio
    from app.models.user import User
    user = User(username='testuser2', email='test2@example.com')
    user.set_password('testpass')
    portfolio = Portfolio(name='Test Portfolio', user=user)
    
    db_session.add_all([security1, security2, platform, user, portfolio])
    db_session.commit()
    
    # Create holdings
    holding1 = Holding(
        portfolio=portfolio,
        security=security1,
        platform=platform,
        quantity=Decimal('100'),
        currency='USD',  # Set to match platform's currency
        average_cost=Decimal('150.00'),
        total_cost=Decimal('15000.00')
    )
    holding2 = Holding(
        portfolio=portfolio,
        security=security2,
        platform=platform,
        quantity=Decimal('50'),
        currency='USD',  # Set to match platform's currency
        average_cost=Decimal('200.00'),
        total_cost=Decimal('10000.00')
    )
    db_session.add_all([holding1, holding2])
    db_session.commit()
    
    # Test updating all dividends
    new_count = DividendService.update_all_dividends()
    
    assert new_count == 8  # 4 dividends each for 2 securities
    
    # Verify dividends in database
    dividends = Dividend.query.all()
    assert len(dividends) == 8

def test_duplicate_dividend_prevention(db_session, mock_yahoo_finance):
    """Test that duplicate dividends are not created"""
    # Create test data
    security = Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL')
    platform = Platform(name='Test Platform', currency='USD')
    
    # Create user and portfolio
    from app.models.user import User
    user = User(username='testuser3', email='test3@example.com')
    user.set_password('testpass')
    portfolio = Portfolio(name='Test Portfolio', user=user)
    
    db_session.add_all([security, platform, user, portfolio])
    db_session.commit()
    
    holding = Holding(
        portfolio=portfolio,
        security=security,
        platform=platform,
        quantity=Decimal('100'),
        currency='USD',  # Set to match platform's currency
        average_cost=Decimal('150.00'),
        total_cost=Decimal('15000.00')
    )
    db_session.add(holding)
    db_session.commit()
    
    # First update
    count1 = DividendService.update_all_dividends()
    assert count1 == 4
    
    # Second update should not create duplicates
    count2 = DividendService.update_all_dividends()
    assert count2 == 0
    
    # Verify total dividends in database
    assert len(Dividend.query.all()) == 4
