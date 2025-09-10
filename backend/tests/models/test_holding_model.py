import pytest
from app.models import Holding, Security, Platform
from decimal import Decimal

@pytest.fixture
def test_security(db_session):
    security = Security(
        ticker='AAPL',
        name='Apple Inc.',
        instrument_type='stock',
        currency='USD'
    )
    db_session.add(security)
    db_session.commit()
    return security

@pytest.fixture
def test_platform(db_session):
    platform = Platform(
        name='Test Platform',
        account_type='Trading',
        currency='GBP'
    )
    db_session.add(platform)
    db_session.commit()
    return platform

def test_create_holding(db_session, test_portfolio, test_security, test_platform):
    """Test holding creation"""
    holding = Holding(
        portfolio=test_portfolio,
        security=test_security,
        platform=test_platform,
        quantity=Decimal('10.0'),
        currency=test_platform.currency,  # Use the platform's currency
        average_cost=Decimal('150.00'),
        total_cost=Decimal('1500.00')
    )
    db_session.add(holding)
    db_session.commit()
    
    assert holding.id is not None
    assert holding.quantity == Decimal('10.0')
    assert holding.average_cost == Decimal('150.00')

def test_holding_value_calculation(db_session, test_portfolio, test_security, test_platform):
    """Test holding value calculations with trading fees"""
    print("\nDEBUG: Starting holding value calculation test")
    
    # Create a holding with total cost including £20 trading fees (£1500 + £20)
    holding = Holding(
        portfolio=test_portfolio,
        security=test_security,
        platform=test_platform,
        quantity=Decimal('10.0'),
        currency=test_platform.currency,  # Use the platform's currency
        average_cost=Decimal('150.00'),
        total_cost=Decimal('1520.00'),  # Includes trading fees
        current_price=Decimal('160.00')
    )
    print(f"\nDEBUG: Created holding with:")
    print(f"DEBUG: Quantity: {holding.quantity}")
    print(f"DEBUG: Average Cost: {holding.average_cost}")
    print(f"DEBUG: Total Cost: {holding.total_cost}")
    print(f"DEBUG: Current Price: {holding.current_price}")
    
    db_session.add(holding)
    db_session.commit()
    
    # Test current value calculation
    print(f"\nDEBUG: Expected current value: 1600.00")
    print(f"DEBUG: Actual current value: {holding.current_value}")
    assert holding.current_value == Decimal('1600.00')
    
    # Test unrealized gain/loss (should account for fees)
    print(f"\nDEBUG: Expected unrealized gain/loss: 80.00")
    print(f"DEBUG: Actual unrealized gain/loss: {holding.unrealized_gain_loss}")
    assert holding.unrealized_gain_loss == Decimal('80.00')  # 1600 - 1520
    
    # Test percentage gain/loss
    print(f"\nDEBUG: Expected unrealized gain/loss %: 5.26")
    print(f"DEBUG: Actual unrealized gain/loss %: {holding.unrealized_gain_loss_pct}")
    assert holding.unrealized_gain_loss_pct == Decimal('5.26')  # (80/1520) * 100
