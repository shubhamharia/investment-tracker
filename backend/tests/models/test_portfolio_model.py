import pytest
from app.models import Portfolio
from decimal import Decimal

def test_create_portfolio(db_session, test_user):
    """Test portfolio creation"""
    portfolio = Portfolio(
        name='Test Portfolio',
        description='Test Description',
        user=test_user
    )
    db_session.session.add(portfolio)
    db_session.session.commit()
    
    assert portfolio.id is not None
    assert portfolio.name == 'Test Portfolio'
    assert portfolio.user_id == test_user.id

def test_portfolio_holdings(db_session, test_user):
    """Test adding holdings to portfolio"""
    portfolio = Portfolio(
        name='Investment Portfolio',
        description='Long-term investments',
        user=test_user
    )
    db_session.session.add(portfolio)
    db_session.session.commit()
    
    # Test will be expanded when we implement holdings

def test_portfolio_value_calculation(db_session, test_user):
    """Test portfolio value calculations"""
    portfolio = Portfolio(
        name='Value Test Portfolio',
        description='Testing value calculations',
        user=test_user
    )
    db_session.session.add(portfolio)
    db_session.session.commit()
    
    # Test will be expanded when we implement value calculations

def test_user_portfolios_relationship(db_session, test_user):
    """Test relationship between user and portfolios"""
    portfolio1 = Portfolio(name='Portfolio 1', user=test_user)
    portfolio2 = Portfolio(name='Portfolio 2', user=test_user)
    
    db_session.session.add_all([portfolio1, portfolio2])
    db_session.session.commit()
    
    assert len(test_user.portfolios) == 2
    assert test_user.portfolios[0].name in ['Portfolio 1', 'Portfolio 2']
