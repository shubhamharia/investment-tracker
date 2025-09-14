"""import pytest

Test configuration and fixtures for the investment tracker backend.import os

"""from decimal import Decimal

import pytestfrom app import create_app

import tempfilefrom app.extensions import db

import osfrom datetime import datetime, timedelta

from datetime import datetime, timedeltafrom decimal import Decimal

from decimal import Decimalfrom app.models import (

from app import create_app    User, Portfolio, Security, Transaction, 

from app.extensions import db    Holding, Platform, PriceHistory, Dividend

from app.models.user import User)

from app.models.platform import Platformfrom tests.fixtures import (

from app.models.security import Security    test_portfolio,

from app.models.portfolio import Portfolio    test_securities,

from app.models.transaction import Transaction    test_platform,

from app.models.holding import Holding    mock_price_service

from app.models.dividend import Dividend)

from app.models.price_history import PriceHistory

from app.models.security_mapping import SecurityMapping@pytest.fixture(autouse=True)

def setup_test_env():

    """Set up test environment variables."""

@pytest.fixture(scope='session')    os.environ["FLASK_ENV"] = "testing"

def app():    yield

    """Create application for the tests."""    os.environ.pop("FLASK_ENV", None)

    # Create a temporary file to serve as the database

    db_fd, db_path = tempfile.mkstemp()@pytest.fixture(scope="function")

    def app():

    app = create_app({    """Create and configure a new app instance for each test."""

        'TESTING': True,    from tests.mocks import MockPriceService, MockDividendService

        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',    from app.services.service_manager import set_services_for_testing

        'SQLALCHEMY_TRACK_MODIFICATIONS': False,    

        'SECRET_KEY': 'test-secret-key',    _app = create_app("testing")

        'JWT_SECRET_KEY': 'test-jwt-secret-key',    

        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),    # Configure mock services

        'REDIS_URL': 'redis://localhost:6379/1',  # Use test database    mock_price_service = MockPriceService()

        'WTF_CSRF_ENABLED': False    mock_dividend_service = MockDividendService()

    })    set_services_for_testing(

            price_service=mock_price_service,

    with app.app_context():        dividend_service=mock_dividend_service

        db.create_all()    )

        yield app    

        db.drop_all()    with _app.app_context():

            # Clear any existing tables

    os.close(db_fd)        db.drop_all()

    os.unlink(db_path)        # Create all tables

        db.create_all()

    

@pytest.fixture(scope='function')    return _app

def client(app):

    """A test client for the app."""@pytest.fixture

    return app.test_client()def client(app):

    """A test client for the app."""

    return app.test_client()

@pytest.fixture(scope='function')

def runner(app):@pytest.fixture

    """A test runner for the app's Click commands."""def price_service():

    return app.test_cli_runner()    """Create a fresh MockPriceService for each test"""

    from tests.mocks import MockPriceService

    return MockPriceService()

@pytest.fixture(scope='function')

def db_session(app):@pytest.fixture

    """Create a database session for the test."""def app_context(app):

    with app.app_context():    """Provide an application context for the test."""

        db.session.begin()    with app.app_context() as ctx:

        yield db.session        yield ctx

        db.session.rollback()

@pytest.fixture(autouse=True)

def celery_app():

@pytest.fixture    """Configure Celery for testing."""

def sample_user(db_session):    from app.tasks.celery_tasks import celery

    """Create a sample user for testing."""    # Configure for testing

    user = User(    celery.conf.update(

        username='testuser',        task_always_eager=True,

        email='test@example.com',        task_eager_propagates=True,

        first_name='Test',        broker_url="memory://",

        last_name='User'        result_backend="cache",

    )        cache_backend="memory",

    user.set_password('testpassword123')        accept_content=["json"],

    db_session.add(user)        enable_utc=True,

    db_session.commit()        timezone="UTC"

    return user    )

    return celery



@pytest.fixture@pytest.fixture

def admin_user(db_session):def db_session(app, app_context):

    """Create an admin user for testing."""    """Provide a database session for testing."""

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")    db.drop_all()  # Clean start

    user = User(    db.create_all()

        username=f'admin_{timestamp}',    

        email=f'admin_{timestamp}@example.com',    yield db.session

        first_name='Admin',    

        last_name='User',    db.session.remove()

        is_admin=True    db.drop_all()

    )

    user.set_password('adminpassword123')@pytest.fixture

    db_session.add(user)def test_user(db_session):

    db_session.commit()    """Create a test user."""

    return user    user = User(

        username="testuser",

        email="test@example.com"

@pytest.fixture    )

def sample_platform(db_session):    user.set_password("password123")

    """Create a sample platform for testing."""    db_session.add(user)

    platform = Platform(    db_session.commit()

        name='Test Broker',    return user

        description='A test trading platform'

    )@pytest.fixture

    db_session.add(platform)def test_security(db_session):

    db_session.commit()    """Create a test security."""

    return platform    security = Security(

        ticker="AAPL",

        name="Apple Inc.",

@pytest.fixture        currency="USD",

def sample_security(db_session):        yahoo_symbol="AAPL"

    """Create a sample security for testing."""    )

    security = Security(    db_session.add(security)

        symbol='AAPL',    db_session.commit()

        name='Apple Inc.',    return security

        sector='Technology',

        currency='USD'@pytest.fixture

    )def test_platform(db_session):

    db_session.add(security)    """Create a test platform."""

    db_session.commit()    platform = Platform(

    return security        name="Test Platform",

        account_type="GIA",

        currency="USD",

@pytest.fixture        trading_fee_fixed=Decimal("9.99"),

def sample_portfolio(db_session, sample_user, sample_platform):        trading_fee_percentage=Decimal("0.00"),

    """Create a sample portfolio for testing."""        fx_fee_percentage=Decimal("0.00"),

    portfolio = Portfolio(        stamp_duty_applicable=False

        name='Test Portfolio',    )

        description='A test portfolio',    db_session.add(platform)

        user_id=sample_user.id,    db_session.commit()

        platform_id=sample_platform.id,    return platform

        currency='USD',

        is_active=True@pytest.fixture

    )def test_portfolio(db_session, test_user, test_platform, test_security):

    db_session.add(portfolio)    """Create a test portfolio with holdings."""

    db_session.commit()    portfolio = Portfolio(

    return portfolio        name="Test Portfolio",

        user_id=test_user.id,

        base_currency="USD"

@pytest.fixture    )

def sample_transaction(db_session, sample_portfolio, sample_security):    db_session.add(portfolio)

    """Create a sample transaction for testing."""    db_session.flush()  # Get ID but don't commit yet

    transaction = Transaction(

        portfolio_id=sample_portfolio.id,    # Create a holding

        security_id=sample_security.id,    holding = Holding(

        transaction_type='BUY',        portfolio_id=portfolio.id,

        quantity=Decimal('100'),        security_id=test_security.id,

        price=Decimal('150.00'),        platform_id=test_platform.id,

        commission=Decimal('9.99'),        quantity=Decimal('10'),

        transaction_date=datetime.now(),        average_cost=Decimal('100.00'),

        currency='USD'        total_cost=Decimal('1000.00'),

    )        current_price=Decimal('110.00'),

    db_session.add(transaction)        current_value=Decimal('1100.00'),

    db_session.commit()        currency="USD"

    return transaction    )

    db_session.add(holding)



@pytest.fixture    # Add price history

def sample_holding(db_session, sample_portfolio, sample_security, sample_platform):    now = datetime.now()

    """Create a sample holding for testing."""    price = PriceHistory(

    holding = Holding(        security_id=test_security.id,

        portfolio_id=sample_portfolio.id,        close_price=Decimal('110.00'),

        security_id=sample_security.id,        price_date=now.date(),

        platform_id=sample_platform.id,        currency="USD",

        quantity=Decimal('100'),        data_source="yahoo"

        average_cost=Decimal('150.00'),    )

        currency='USD',    db_session.add(price)

        last_updated=datetime.now()

    )    db_session.commit()

    db_session.add(holding)    return portfolio

    db_session.commit()

    return holding@pytest.fixture

def test_holding(db_session, test_portfolio, test_security):

    """Create a test holding."""

@pytest.fixture    holding = Holding(

def sample_dividend(db_session, sample_portfolio, sample_security):        portfolio_id=test_portfolio.id,

    """Create a sample dividend for testing."""        security_id=test_security.id,

    dividend = Dividend(        quantity=100,

        portfolio_id=sample_portfolio.id,        cost_basis=Decimal("150.00"),

        security_id=sample_security.id,        currency="USD"

        amount=Decimal('2.50'),    )

        payment_date=datetime.now(),    db_session.add(holding)

        ex_dividend_date=datetime.now() - timedelta(days=5),    db_session.commit()

        currency='USD'    return holding

    )

    db_session.add(dividend)@pytest.fixture

    db_session.commit()def auth_token(db_session, test_user, client):

    return dividend    """Get an authentication token for the test user."""

    response = client.post('/api/auth/login', json={

        'username': "testuser",  # Using the exact username from test_user fixture

@pytest.fixture        'password': 'password123'

def auth_token(client, sample_user):    })

    """Get an authentication token for the sample user."""    assert response.status_code == 200

    response = client.post('/api/auth/login', json={    return response.json['access_token']

        'username': 'testuser',
        'password': 'testpassword123'
    })
    return response.json['access_token']


@pytest.fixture
def admin_auth_token(client, admin_user):
    """Get an authentication token for the admin user."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f'admin_{timestamp}'
    
    response = client.post('/api/auth/login', json={
        'username': username,
        'password': 'adminpassword123'
    })
    return response.json['access_token']


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers with the auth token."""
    return {'Authorization': f'Bearer {auth_token}'}


@pytest.fixture
def admin_auth_headers(admin_auth_token):
    """Get authorization headers with the admin auth token."""
    return {'Authorization': f'Bearer {admin_auth_token}'}


@pytest.fixture
def sample_price_history(db_session, sample_security):
    """Create sample price history for testing."""
    price_history = PriceHistory(
        security_id=sample_security.id,
        date=datetime.now().date(),
        open_price=Decimal('148.50'),
        high_price=Decimal('152.00'),
        low_price=Decimal('147.00'),
        close_price=Decimal('151.20'),
        volume=1000000,
        adjusted_close=Decimal('151.20')
    )
    db_session.add(price_history)
    db_session.commit()
    return price_history


@pytest.fixture
def sample_security_mapping(db_session, sample_security, sample_platform):
    """Create a sample security mapping for testing."""
    mapping = SecurityMapping(
        security_id=sample_security.id,
        platform_id=sample_platform.id,
        platform_symbol='AAPL',
        platform_name='Apple Inc.',
        mapping_type='EXACT'
    )
    db_session.add(mapping)
    db_session.commit()
    return mapping