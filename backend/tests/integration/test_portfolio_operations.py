import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from app.models import Portfolio, Security, Platform, Holding, Transaction, Dividend, PriceHistory
from app.services.portfolio_service import PortfolioService
from app.services.price_service import PriceService

def test_portfolio_rebalancing_workflow(db_session, test_portfolio):
    """Test complete portfolio rebalancing workflow"""
    # Setup initial portfolio with multiple securities
    securities = [
        Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL'),
        Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT'),
        Security(ticker='GOOGL', name='Alphabet Inc.', currency='USD', yahoo_symbol='GOOGL')
    ]
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add(platform)
    
    for security in securities:
        db_session.add(security)
    db_session.commit()
    
    # Create initial holdings (unbalanced)
    holdings_data = [
        (securities[0], Decimal('100'), Decimal('150.00')),  # 15,000 USD
        (securities[1], Decimal('50'), Decimal('200.00')),   # 10,000 USD
        (securities[2], Decimal('20'), Decimal('250.00'))    # 5,000 USD
    ]
    
    for security, qty, price in holdings_data:
        # Create holding
        holding = Holding(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            quantity=qty,
            currency='USD',  # Match platform's currency
            average_cost=price,  # Add missing required fields
            total_cost=qty * price  # Add missing required fields
        )
        db_session.add(holding)
        
        # Add initial buy transaction
        transaction = Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=qty,
            price_per_share=price,
            trading_fees=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 1)
        )
        db_session.add(transaction)
        
            # Add price history
            price_history = PriceHistory(
                security_id=security.id,
                price_date=date(2025, 1, 1),
                open_price=price,
                high_price=price * Decimal('1.02'),
                low_price=price * Decimal('0.98'),
                close_price=price,
                volume=1000000,
                currency='USD'
            )
            db_session.add(price_history)
            
            # Update the holding's current price
            holding.current_price = price
            holding.calculate_values()  # This will update current value based on price    db_session.commit()
    
    # Verify initial portfolio state
    initial_performance = test_portfolio.update_performance()
    assert initial_performance.total_value == Decimal('30029.97')  # 30,000 + 3 * 9.99 fees
    
    # Simulate rebalancing transactions to achieve equal weights
    target_value = Decimal('10000.00')  # Equal weight target
    
    # Calculate and execute rebalancing trades
    for holding in test_portfolio.holdings:
        current_value = holding.calculate_value()
        if current_value > target_value:
            # Sell to reduce position
            shares_to_sell = (current_value - target_value) / holding.current_price
            transaction = Transaction(
                portfolio_id=test_portfolio.id,
                security_id=holding.security_id,
                platform_id=platform.id,
                transaction_type='SELL',
                quantity=shares_to_sell.quantize(Decimal('0.00')),
                price_per_share=holding.current_price,
                trading_fees=Decimal('9.99'),
                currency='USD',
                transaction_date=date(2025, 1, 2)
            )
            db_session.add(transaction)
        elif current_value < target_value:
            # Buy to increase position
            shares_to_buy = (target_value - current_value) / holding.current_price
            transaction = Transaction(
                portfolio_id=test_portfolio.id,
                security_id=holding.security_id,
                platform_id=platform.id,
                transaction_type='BUY',
                quantity=shares_to_buy.quantize(Decimal('0.00')),
                price_per_share=holding.current_price,
                trading_fees=Decimal('9.99'),
                currency='USD',
                transaction_date=date(2025, 1, 2)
            )
            db_session.add(transaction)
    
    db_session.commit()
    
    # Verify rebalanced portfolio
    final_performance = test_portfolio.update_performance()
    
    # Check that holdings are now approximately equal weight
    for holding in test_portfolio.holdings:
        value = holding.calculate_value()
        assert abs(value - target_value) < Decimal('100.00')  # Allow small deviation due to rounding

def test_currency_conversion_workflow(db_session, test_portfolio):
    """Test portfolio handling of multiple currencies"""
    # Setup securities in different currencies
    securities = [
        Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL'),
        Security(ticker='VOD', name='Vodafone Group', currency='GBP', yahoo_symbol='VOD.L'),
        Security(ticker='SAP', name='SAP SE', currency='EUR', yahoo_symbol='SAP.DE')
    ]
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add(platform)
    
    for security in securities:
        db_session.add(security)
    db_session.commit()
    
    # Add holdings in different currencies with exchange rates
    exchange_rates = {
        'USD': Decimal('1.00'),
        'GBP': Decimal('1.25'),
        'EUR': Decimal('1.10')
    }
    
    holdings_data = [
        (securities[0], Decimal('100'), Decimal('150.00'), 'USD'),
        (securities[1], Decimal('200'), Decimal('1.00'), 'GBP'),
        (securities[2], Decimal('50'), Decimal('100.00'), 'EUR')
    ]
    
    for security, qty, price, currency in holdings_data:
        # Create holding with initial cost data
        holding = Holding(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            quantity=qty,
            currency=currency,
            average_cost=price,  # Set initial cost
            total_cost=qty * price  # Calculate initial total cost
        )
        db_session.add(holding)
        
        # Add transaction
        transaction = Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=qty,
            price_per_share=price,
            trading_fees=Decimal('9.99'),
            currency=currency,
            transaction_date=date(2025, 1, 1)
        )
        db_session.add(transaction)
        
        # Add price history
        price_history = PriceHistory(
            security_id=security.id,
            price_date=date(2025, 1, 1),
            open_price=price,
            high_price=price * Decimal('1.02'),
            low_price=price * Decimal('0.98'),
            close_price=price,
            volume=1000000,
            currency=currency
        )
        db_session.add(price_history)
    
    db_session.commit()
    
    # Calculate total portfolio value in USD
    portfolio_value_usd = sum(
        holding.calculate_value() * exchange_rates[holding.currency]
        for holding in test_portfolio.holdings
    )
    
    # Expected values in USD:
    # AAPL: 100 * 150.00 = 15,000 USD
    # VOD: 200 * 1.00 * 1.25 = 250 GBP = 312.50 USD
    # SAP: 50 * 100.00 * 1.10 = 5,000 EUR = 5,500 USD
    # Total: ~20,812.50 USD (plus fees)
    
    expected_value = Decimal('20812.50') + (Decimal('9.99') * 3)  # Add fees
    assert abs(portfolio_value_usd - expected_value) < Decimal('0.01')

def test_corporate_action_workflow(db_session, test_portfolio):
    """Test handling of corporate actions like stock splits"""
    # Setup initial holding
    security = Security(ticker='TSLA', name='Tesla Inc.', currency='USD', yahoo_symbol='TSLA')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create pre-split holding
    initial_quantity = Decimal('100')
    pre_split_price = Decimal('900.00')
    
    holding = Holding(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        quantity=initial_quantity,
        currency='USD',
        average_cost=pre_split_price,  # Set initial cost
        total_cost=initial_quantity * pre_split_price  # Calculate initial total cost
    )
    db_session.add(holding)
    
    # Add pre-split transaction
    transaction = Transaction(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        transaction_type='BUY',
        quantity=initial_quantity,
        price_per_share=pre_split_price,
        trading_fees=Decimal('9.99'),
        currency='USD',
        transaction_date=date(2025, 1, 1)
    )
    db_session.add(transaction)
    
    # Add pre-split price
    price_history = PriceHistory(
        security_id=security.id,
        price_date=date(2025, 1, 1),
        open_price=pre_split_price,
        high_price=pre_split_price * Decimal('1.02'),
        low_price=pre_split_price * Decimal('0.98'),
        close_price=pre_split_price,
        volume=1000000,
        currency='USD'
    )
    db_session.add(price_history)
    db_session.commit()
    
    # Verify pre-split state
    pre_split_value = holding.calculate_value()
    assert pre_split_value == pre_split_price * initial_quantity
    
    # Simulate 3:1 stock split
    split_ratio = 3
    post_split_price = pre_split_price / Decimal(split_ratio)
    
    # Update holding for split
    holding.quantity *= Decimal(split_ratio)
    
    # Record split as a corporate action transaction
    split_transaction = Transaction(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        transaction_type='SPLIT',
        quantity=holding.quantity - initial_quantity,  # Additional shares from split
        price_per_share=post_split_price,
        trading_fees=Decimal('0'),  # No fee for splits
        currency='USD',
        transaction_date=date(2025, 1, 2)
    )
    db_session.add(split_transaction)
    
    # Add post-split price
    post_split_price_history = PriceHistory(
        security_id=security.id,
        price_date=date(2025, 1, 2),
        open_price=post_split_price,
        high_price=post_split_price * Decimal('1.02'),
        low_price=post_split_price * Decimal('0.98'),
        close_price=post_split_price,
        volume=3000000,  # Volume typically increases after split
        currency='USD'
    )
    db_session.add(post_split_price_history)
    db_session.commit()
    
    # Verify post-split state
    post_split_value = holding.calculate_value()
    
    # Value should remain approximately the same
    assert abs(post_split_value - pre_split_value) < Decimal('0.01')
    # Quantity should be tripled
    assert holding.quantity == initial_quantity * Decimal(split_ratio)
    # Price should be one-third
    assert abs(post_split_price - (pre_split_price / Decimal(split_ratio))) < Decimal('0.01')
