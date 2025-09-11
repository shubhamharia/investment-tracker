import pytest
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.portfolio import Portfolio
from sqlalchemy.sql import text
from app.models.security import Security
from app.models.platform import Platform
from app.models.holding import Holding

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

# Create a new application context for each test
@pytest.fixture
def app_context(app):
    with app.app_context() as ctx:
        yield ctx

@pytest.fixture
def db_session(app, app_context):
    db.drop_all()  # Clean start
    db.create_all()
    
    # Initialize required data
    db_session = db.session
    yield db_session
    
    # Cleanup
    db_session.remove()
    db.drop_all()

@pytest.fixture
def test_user(db_session):
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_token(test_user):
    """Generate authentication token for test user"""
    return test_user.generate_auth_token()

@pytest.fixture
def test_portfolio(db_session, test_user):
    portfolio = Portfolio(
        name='Test Portfolio',
        description='Test Description',
        user=test_user
    )
    db_session.add(portfolio)
    db_session.commit()
    return portfolio

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

@pytest.fixture
def test_holding(db_session, test_portfolio, test_security, test_platform):
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
    return holding