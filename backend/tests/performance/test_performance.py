import pytest
import time
from decimal import Decimal
from datetime import datetime, timedelta
from app.models import Security, Platform, Portfolio, Holding, Transaction, PriceHistory
from app.services.portfolio_service import PortfolioService
from sqlalchemy import text

def create_test_data(db_session, scale=100):
    """Create test data for performance testing"""
    # Create test user first
    from app.models.user import User
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    # Create securities
    securities = []
    for i in range(scale):
        security = Security(
            ticker=f'TEST{i}',
            name=f'Test Company {i}',
            currency='USD',
            yahoo_symbol=f'TEST{i}'
        )
        db_session.add(security)
        securities.append(security)
    
    # Create platforms
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add(platform)
    
    # Create portfolio with user
    portfolio = Portfolio(
        name='Test Portfolio',
        description='Performance Test Portfolio',
        user=user,
        base_currency='USD'
    )
    db_session.add(portfolio)
    
    db_session.commit()
    
    # Create holdings and transactions
    for security in securities:
        # Create holding
        holding = Holding(
            portfolio_id=portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            quantity=Decimal('100'),
            currency='USD',
            average_cost=Decimal('100.00'),
            total_cost=Decimal('10000.00')
        )
        db_session.add(holding)
        
        # Create transactions
        for j in range(10):  # 10 transactions per security
            transaction = Transaction(
                portfolio_id=portfolio.id,
                security_id=security.id,
                platform_id=platform.id,
                transaction_type='BUY',
                quantity=Decimal('10'),
                price_per_share=Decimal('100.00'),
                trading_fees=Decimal('9.99'),
                currency='USD',
                transaction_date=datetime.now().date() - timedelta(days=j)
            )
            db_session.add(transaction)
        
        # Create price history
        for j in range(365):  # One year of daily prices
            price = PriceHistory(
                security_id=security.id,
                price_date=datetime.now().date() - timedelta(days=j),
                open_price=Decimal('100.00'),
                high_price=Decimal('105.00'),
                low_price=Decimal('95.00'),
                close_price=Decimal('102.00'),
                volume=1000000,
                currency='USD'
            )
            db_session.add(price)
    
    db_session.commit()
    return portfolio

def test_portfolio_value_calculation_performance(db_session):
    """Test performance of portfolio value calculations"""
    portfolio = create_test_data(db_session)
    
    start_time = time.time()
    portfolio.calculate_total_value()
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 1.0  # Should complete in less than 1 second

def test_transaction_history_query_performance(db_session):
    """Test performance of transaction history queries"""
    portfolio = create_test_data(db_session)
    
    start_time = time.time()
    transactions = Transaction.query.filter_by(portfolio_id=portfolio.id).all()
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 0.5  # Should complete in less than 0.5 seconds
    assert len(transactions) == 1000  # 100 securities * 10 transactions

def test_price_history_query_performance(db_session):
    """Test performance of price history queries"""
    portfolio = create_test_data(db_session)
    
    start_time = time.time()
    prices = db_session.execute(text("""
        SELECT ph.* 
        FROM price_history ph
        JOIN holdings h ON h.security_id = ph.security_id
        WHERE h.portfolio_id = :portfolio_id
        AND ph.price_date >= :start_date
    """), {
        'portfolio_id': portfolio.id,
        'start_date': datetime.now().date() - timedelta(days=30)
    }).fetchall()
    
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 0.5  # Should complete in less than 0.5 seconds

def test_portfolio_performance_calculation_performance(db_session):
    """Test performance of portfolio performance calculations"""
    portfolio = create_test_data(db_session)
    
    start_time = time.time()
    portfolio.update_performance()
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 2.0  # Should complete in less than 2 seconds

def test_concurrent_transaction_processing(db_session, app):
    """Test performance of concurrent transaction processing"""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    # Create test data within app context
    with app.app_context():
        portfolio = create_test_data(db_session, scale=10)  # Smaller scale for concurrent test
        security = Security.query.first()
        platform = Platform.query.first()
        
        # Store IDs for use in threads
        portfolio_id = portfolio.id
        security_id = security.id
        platform_id = platform.id

        # Create a new engine and session factory for threads
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
        
        # Create all tables in the new engine
        from app.extensions import db
        db.drop_all()  # Clean start
        db.create_all()  # Create all tables
        
        def create_transaction(i):
            """Create a single transaction"""
            with app.app_context():
                session = Session()
                try:
                    with Lock():
                        transaction = Transaction(
                            portfolio_id=portfolio_id,
                            security_id=security_id,
                            platform_id=platform_id,
                            transaction_type='BUY',
                            quantity=Decimal('10'),
                            price_per_share=Decimal('100.00'),
                            trading_fees=Decimal('9.99'),
                            currency='USD',
                            transaction_date=datetime.now().date()
                        )
                        session.add(transaction)
                        session.commit()
                except Exception as e:
                    session.rollback()
                    raise e
                finally:
                    Session.remove()

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(create_transaction, i) for i in range(100)]
        for future in futures:
            future.result()
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 5.0  # Should complete in less than 5 seconds
