import pytest
from decimal import Decimal
from datetime import date, timedelta
from app.models import PriceHistory, Security
from app.constants import DECIMAL_PLACES

def test_price_history_creation(db_session):
    """Test basic price history creation."""
    # Create test security
    security = Security(ticker='AAPL', name='Apple Inc.', currency='USD')
    db_session.add(security)
    db_session.commit()
    
    # Create price history
    price = PriceHistory(
        security_id=security.id,
        price_date=date(2025, 1, 1),
        open_price=Decimal('150.00'),
        high_price=Decimal('155.00'),
        low_price=Decimal('148.00'),
        close_price=Decimal('152.50'),
        volume=1000000,
        currency='USD',
        data_source='YAHOO'
    )
    
    db_session.add(price)
    db_session.commit()
    
    assert price.id is not None
    assert price.security_id == security.id
    assert price.close_price == Decimal('152.50')

def test_daily_change_calculation(db_session):
    """Test daily price change calculations."""
    # Create test security
    security = Security(ticker='MSFT', name='Microsoft Corp', currency='USD')
    db_session.add(security)
    db_session.commit()
    
    # Create price history with gain
    price = PriceHistory(
        security_id=security.id,
        price_date=date(2025, 1, 1),
        open_price=Decimal('200.00'),
        close_price=Decimal('220.00'),
        currency='USD'
    )
    
    change, change_pct = price.calculate_daily_change()
    
    expected_change = Decimal('20.00')
    expected_pct = Decimal('10.00')  # 10% gain
    
    assert change.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}')) == expected_change
    assert change_pct.quantize(Decimal('0.01')) == expected_pct

def test_volatility_calculation(db_session):
    """Test price volatility calculations."""
    # Create test security
    security = Security(ticker='TEST', name='Test Corp', currency='USD')
    db_session.add(security)
    db_session.commit()
    
    # Create price history for 10 days
    base_price = Decimal('100.00')
    base_date = date(2025, 1, 1)
    
    for i in range(10):
        price = PriceHistory(
            security_id=security.id,
            price_date=base_date + timedelta(days=i),
            close_price=base_price + Decimal(str(i)),  # Linear price increase
            currency='USD'
        )
        db_session.add(price)
    
    db_session.commit()
    
    # Get the last price
    latest_price = PriceHistory.query.filter_by(security_id=security.id).order_by(PriceHistory.price_date.desc()).first()
    
    # Calculate volatility
    volatility = latest_price.calculate_volatility(days=10)
    
    # Verify volatility is calculated
    assert volatility is not None
    assert isinstance(volatility, Decimal)

def test_price_at_date(db_session):
    """Test getting price at specific date."""
    # Create test security
    security = Security(ticker='VOD', name='Vodafone Group', currency='GBP')
    db_session.add(security)
    db_session.commit()
    
    # Create multiple price points
    dates = [
        date(2025, 1, 1),
        date(2025, 1, 2),
        date(2025, 1, 3)
    ]
    
    prices = [
        Decimal('100.00'),
        Decimal('102.00'),
        Decimal('101.00')
    ]
    
    for test_date, price in zip(dates, prices):
        price_history = PriceHistory(
            security_id=security.id,
            price_date=test_date,
            close_price=price,
            currency='GBP'
        )
        db_session.add(price_history)
    
    db_session.commit()
    
    # Test getting price at specific date
    price_at_date = PriceHistory.get_price_at_date(security.id, date(2025, 1, 2))
    assert price_at_date.close_price == Decimal('102.00')
    
    # Test getting price at date before first price
    price_at_early_date = PriceHistory.get_price_at_date(security.id, date(2024, 12, 31))
    assert price_at_early_date is None
    
    # Test getting price at date after last price
    price_at_late_date = PriceHistory.get_price_at_date(security.id, date(2025, 1, 4))
    assert price_at_late_date.close_price == Decimal('101.00')  # Should get last available price

def test_price_history_to_dict(db_session):
    """Test price history to_dict method."""
    # Create test security
    security = Security(ticker='BT', name='BT Group', currency='GBP')
    db_session.add(security)
    db_session.commit()
    
    test_date = date(2025, 1, 1)
    
    # Create price history
    price = PriceHistory(
        security_id=security.id,
        price_date=test_date,
        open_price=Decimal('100.00'),
        high_price=Decimal('105.00'),
        low_price=Decimal('98.00'),
        close_price=Decimal('103.00'),
        volume=500000,
        currency='GBP',
        data_source='TEST'
    )
    
    db_session.add(price)
    db_session.commit()
    
    # Get dictionary representation
    price_dict = price.to_dict()
    
    # Verify dictionary content
    assert price_dict['security_id'] == security.id
    assert price_dict['price_date'] == test_date.isoformat()
    assert Decimal(price_dict['open_price']) == Decimal('100.00')
    assert Decimal(price_dict['high_price']) == Decimal('105.00')
    assert Decimal(price_dict['low_price']) == Decimal('98.00')
    assert Decimal(price_dict['close_price']) == Decimal('103.00')
    assert price_dict['volume'] == 500000
    assert price_dict['currency'] == 'GBP'
    assert price_dict['data_source'] == 'TEST'
    
    # Verify daily change calculations in dictionary
    assert Decimal(price_dict['daily_change']) == Decimal('3.00')
    assert Decimal(price_dict['daily_change_pct']) == Decimal('3.00')
