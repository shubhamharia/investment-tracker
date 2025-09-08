import pytest
from app.models import Holding, Security, Platform
from decimal import Decimal

@pytest.fixture
def test_security(db_session):
    security = Security(
        ticker='AAPL',
        name='Apple Inc.',
        instrument_type='stock'
    )
    db_session.session.add(security)
    db_session.session.commit()
    return security

@pytest.fixture
def test_platform(db_session):
    platform = Platform(
        name='Test Platform',
        description='Test trading platform'
    )
    db_session.session.add(platform)
    db_session.session.commit()
    return platform

def test_create_holding(db_session, test_portfolio, test_security, test_platform):
    """Test holding creation"""
    holding = Holding(
        portfolio=test_portfolio,
        security=test_security,
        platform=test_platform,
        quantity=Decimal('10.0'),
        average_cost=Decimal('150.00'),
        total_cost=Decimal('1500.00')
    )
    db_session.session.add(holding)
    db_session.session.commit()
    
    assert holding.id is not None
    assert holding.quantity == Decimal('10.0')
    assert holding.average_cost == Decimal('150.00')

def test_holding_value_calculation(db_session, test_portfolio, test_security, test_platform):
    """Test holding value calculations"""
    holding = Holding(
        portfolio=test_portfolio,
        security=test_security,
        platform=test_platform,
        quantity=Decimal('10.0'),
        average_cost=Decimal('150.00'),
        total_cost=Decimal('1500.00'),
        current_price=Decimal('160.00')
    )
    db_session.session.add(holding)
    db_session.session.commit()
    
    # Test current value calculation
    assert holding.current_value == Decimal('1600.00')
    # Test unrealized gain/loss
    assert holding.unrealized_gain_loss == Decimal('100.00')
    # Test percentage gain/loss
    assert holding.unrealized_gain_loss_pct == Decimal('6.67')
