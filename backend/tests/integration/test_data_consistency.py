import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from app.models import Portfolio, Security, Platform, Holding, Transaction, PriceHistory, Dividend
from app.services.portfolio_service import PortfolioService
from app.services.price_service import PriceService
from app.services.dividend_service import DividendService
from sqlalchemy import func
  
def test_portfolio_holding_transaction_consistency(db_session, test_portfolio):
    """Test data consistency between portfolios, holdings, and transactions"""
    # Setup
    security = Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create transactions
    transactions = [
        # Buy 100
        Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price_per_share=Decimal('150.00'),
            trading_fees=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 1)
        ),
        # Buy 50 more
        Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('50'),
            price_per_share=Decimal('160.00'),
            trading_fees=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 2)
        ),
        # Sell 30
        Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='SELL',
            quantity=Decimal('30'),
            price_per_share=Decimal('170.00'),
            trading_fees=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 3)
        )
    ]
    
    for transaction in transactions:
        db_session.add(transaction)
    db_session.commit()
    
    # Get holding
    holding = Holding.query.filter_by(
        portfolio_id=test_portfolio.id,
        security_id=security.id
    ).first()
    
    # Verify holding quantity matches transaction history
    total_quantity = sum(
        t.quantity if t.transaction_type == 'BUY' else -t.quantity
        for t in transactions
    )
    assert holding.quantity == total_quantity
    
    # Verify cost basis calculation
    expected_cost = sum(
        (t.quantity * t.price_per_share + t.trading_fees) if t.transaction_type == 'BUY'
        else -(t.quantity * t.price_per_share - t.trading_fees)
        for t in transactions
    )
    assert holding.total_cost == expected_cost.quantize(Decimal(f'0.{"0" * 4}'))

def test_price_dividend_consistency(db_session, test_portfolio):
    """Test consistency between price history and dividend payments"""
    # Setup
    security = Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create holding through transaction
    transaction = Transaction(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        transaction_type='BUY',
        quantity=Decimal('100'),
        price_per_share=Decimal('100.00'),
        trading_fees=Decimal('9.99'),
        currency='USD',
        transaction_date=date(2025, 1, 1)
    )
    db_session.add(transaction)
    db_session.commit()
    
    holding = Holding.query.filter_by(
        portfolio_id=test_portfolio.id,
        security_id=security.id
    ).first()
    
    # Add price history
    dates = [date(2025, 1, 1) + timedelta(days=x) for x in range(10)]
    prices = [
        PriceHistory(
            security_id=security.id,
            price_date=d,
            open_price=Decimal('100.00'),
            high_price=Decimal('105.00'),
            low_price=Decimal('95.00'),
            close_price=Decimal('102.00'),
            volume=1000000,
            currency='USD'
        )
        for d in dates
    ]
    db_session.add_all(prices)
    
    # Add dividend
    dividend = Dividend(
        security_id=security.id,
        platform_id=platform.id,
        ex_date=dates[5],  # Middle of price history
        dividend_per_share=Decimal('0.88'),
        quantity_held=Decimal('100'),
        currency='USD'
    )
    dividend.calculate_amounts()
    db_session.add(dividend)
    db_session.commit()
    
    # Verify dividend date has corresponding price history
    dividend_date_price = PriceHistory.query.filter_by(
        security_id=security.id,
        price_date=dividend.ex_date
    ).first()
    
    assert dividend_date_price is not None
    
    # Verify dividend amount is reasonable compared to share price
    dividend_yield = (dividend.dividend_per_share * 4) / dividend_date_price.close_price * 100
    assert dividend_yield < 10  # Dividend yield should be reasonable

def test_multi_currency_data_consistency(db_session, test_portfolio):
    """Test data consistency across multiple currencies"""
    # Setup securities in different currencies
    securities = [
        Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL'),
        Security(ticker='VOD', name='Vodafone Group', currency='GBP', yahoo_symbol='VOD.L'),
        Security(ticker='SAP', name='SAP SE', currency='EUR', yahoo_symbol='SAP.DE')
    ]
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all(securities + [platform])
    db_session.commit()
    
    # Create holdings and transactions in different currencies
    for security in securities:
        # Create holding with initial cost data
        holding = Holding(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            quantity=Decimal('100'),
            currency=security.currency,
            average_cost=Decimal('100.00'),  # Set initial cost
            total_cost=Decimal('10000.00')  # 100 shares * $100.00
        )
        db_session.add(holding)
        
        # Add transaction
        transaction = Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price_per_share=Decimal('100.00'),
            trading_fees=Decimal('9.99'),
            currency=security.currency,
            transaction_date=date(2025, 1, 1)
        )
        db_session.add(transaction)
        
        # Add dividend
        dividend = Dividend(
            security_id=security.id,
            platform_id=platform.id,
            ex_date=date(2025, 1, 1),
            dividend_per_share=Decimal('0.50'),
            quantity_held=Decimal('100'),
            currency=security.currency
        )
        dividend.calculate_amounts()
        db_session.add(dividend)
    
    db_session.commit()
    
    # Verify currency consistency
    for security in securities:
        # Check holding currency matches security
        holding = Holding.query.filter_by(
            portfolio_id=test_portfolio.id,
            security_id=security.id
        ).first()
        assert holding.currency == security.currency
        
        # Check transaction currency matches security
        transaction = Transaction.query.filter_by(
            portfolio_id=test_portfolio.id,
            security_id=security.id
        ).first()
        assert transaction.currency == security.currency
        
        # Check dividend currency matches security
        dividend = Dividend.query.filter_by(
            security_id=security.id
        ).first()
        assert dividend.currency == security.currency

def test_historical_data_consistency(db_session, test_portfolio):
    """Test consistency of historical data over time"""
    # Setup
    security = Security(ticker='TSLA', name='Tesla Inc.', currency='USD', yahoo_symbol='TSLA')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create one year of daily price history
    dates = [date(2024, 1, 1) + timedelta(days=x) for x in range(365)]
    base_price = Decimal('100.00')
    
    for i, d in enumerate(dates):
        # Simulate price movement
        price_mod = Decimal(str(1 + (i % 10 - 5) / 100))  # -5% to +5% variation
        price = base_price * price_mod
        
        price_history = PriceHistory(
            security_id=security.id,
            price_date=d,
            open_price=price,
            high_price=price * Decimal('1.02'),
            low_price=price * Decimal('0.98'),
            close_price=price,
            volume=1000000,
            currency='USD'
        )
        db_session.add(price_history)
        
        # Add quarterly dividends (exactly 4 per year)
        if i in [0, 91, 182, 273]:  # Space dividends evenly throughout the year
            dividend = Dividend(
                security_id=security.id,
                platform_id=platform.id,
                ex_date=d,
                dividend_per_share=price * Decimal('0.01'),  # 1% dividend yield
                quantity_held=Decimal('100'),
                currency='USD'
            )
            dividend.calculate_amounts()
            db_session.add(dividend)
    
    db_session.commit()
    
    # Verify data consistency
    # Check price continuity
    prices = PriceHistory.query.filter_by(security_id=security.id).order_by(PriceHistory.price_date).all()
    for i in range(1, len(prices)):
        # Price shouldn't change more than 10% day-over-day
        price_change = abs(prices[i].close_price - prices[i-1].close_price) / prices[i-1].close_price
        assert price_change <= Decimal('0.10')
    
    # Verify dividend consistency
    dividends = Dividend.query.filter_by(security_id=security.id).order_by(Dividend.ex_date).all()
    assert len(dividends) == 4  # Quarterly dividends
    
    for dividend in dividends:
        # Get price on ex-date
        price = PriceHistory.query.filter_by(
            security_id=security.id,
            price_date=dividend.ex_date
        ).first()
        
        # Verify dividend yield is reasonable
        dividend_yield = (dividend.dividend_per_share * 4) / price.close_price * 100
        assert dividend_yield <= Decimal('5')  # Annual yield should be reasonable
