import pytest
from decimal import Decimal
from datetime import datetime, date
from app.models import Transaction, Holding, Security, Platform, Portfolio
from app.services.portfolio_service import PortfolioService

def test_transaction_creates_holding(db_session, test_portfolio):
    """Test that creating a buy transaction creates a new holding"""
    # Setup
    security = Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create buy transaction
    transaction = Transaction(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        transaction_type='BUY',
        quantity=Decimal('100'),
        price=Decimal('150.00'),
        fee=Decimal('9.99'),
        currency='USD',
        transaction_date=date(2025, 1, 1)
    )
    db_session.add(transaction)
    db_session.commit()
    
    # Verify holding was created
    holding = Holding.query.filter_by(
        portfolio_id=test_portfolio.id,
        security_id=security.id
    ).first()
    
    assert holding is not None
    assert holding.quantity == Decimal('100')
    assert holding.currency == 'USD'

def test_multiple_transactions_update_holding(db_session, test_portfolio):
    """Test that multiple transactions correctly update holding quantity"""
    # Setup
    security = Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create transactions
    transactions = [
        Transaction(  # Buy 100
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price=Decimal('200.00'),
            fee=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 1)
        ),
        Transaction(  # Buy 50 more
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('50'),
            price=Decimal('210.00'),
            fee=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 2)
        ),
        Transaction(  # Sell 30
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='SELL',
            quantity=Decimal('30'),
            price=Decimal('220.00'),
            fee=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 3)
        )
    ]
    
    for transaction in transactions:
        db_session.add(transaction)
        db_session.commit()
    
    # Verify final holding quantity
    holding = Holding.query.filter_by(
        portfolio_id=test_portfolio.id,
        security_id=security.id
    ).first()
    
    assert holding is not None
    assert holding.quantity == Decimal('120')  # 100 + 50 - 30

def test_cost_basis_calculation(db_session, test_portfolio):
    """Test that cost basis is correctly calculated from transactions"""
    # Setup
    security = Security(ticker='GOOGL', name='Alphabet Inc.', currency='USD', yahoo_symbol='GOOGL')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create transactions
    transactions = [
        Transaction(  # Buy 100 at $100
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price=Decimal('100.00'),
            fee=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 1)
        ),
        Transaction(  # Buy 50 at $120
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('50'),
            price=Decimal('120.00'),
            fee=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 2)
        )
    ]
    
    for transaction in transactions:
        db_session.add(transaction)
        db_session.commit()
    
    holding = Holding.query.filter_by(
        portfolio_id=test_portfolio.id,
        security_id=security.id
    ).first()
    
    # Calculate expected cost basis
    expected_cost = (
        (Decimal('100') * Decimal('100.00')) +  # First purchase
        (Decimal('50') * Decimal('120.00')) +   # Second purchase
        (Decimal('9.99') * 2)                   # Total fees
    )
    
    assert holding is not None
    assert holding.total_cost == expected_cost

def test_portfolio_value_updates(db_session, test_portfolio):
    """Test that portfolio value is updated after transactions"""
    # Setup
    security = Security(ticker='VOD', name='Vodafone Group', currency='GBP', yahoo_symbol='VOD.L')
    platform = Platform(name='Test Platform', currency='GBP')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create transaction
    transaction = Transaction(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        transaction_type='BUY',
        quantity=Decimal('1000'),
        price=Decimal('1.00'),
        fee=Decimal('9.99'),
        currency='GBP',
        transaction_date=date(2025, 1, 1)
    )
    db_session.add(transaction)
    db_session.commit()
    
    # Update portfolio performance
    performance = test_portfolio.update_performance()
    
    # Verify portfolio value includes new holding
    assert performance.invested_value == Decimal('1009.99')  # 1000 shares * 1.00 + 9.99 fee

def test_transaction_validation(db_session, test_portfolio):
    """Test transaction validation rules"""
    security = Security(ticker='IBM', name='IBM Corp', currency='USD', yahoo_symbol='IBM')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Try to create invalid transaction
    with pytest.raises(ValueError):
        transaction = Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='SELL',
            quantity=Decimal('100'),  # Try to sell when no holdings exist
            price=Decimal('150.00'),
            fee=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 1)
        )
        db_session.add(transaction)
        db_session.commit()
