import pytest
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.platform import Platform
from app.models.security import Security
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.holding import Holding
from app.models.dividend import Dividend
from app.models.price_history import PriceHistory
from app.models.security_mapping import SecurityMapping

@pytest.fixture(scope="session")
def app():
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret-key",
        "JWT_SECRET_KEY": "test-jwt-secret-key",
        "WTF_CSRF_ENABLED": False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def db_session(app):
    """Provide a clean database for each test by recreating all tables.
    This is simpler and reliable for the test-suite running against
    SQLite in CI and avoids depending on Flask-SQLAlchemy internals.
    """
    with app.app_context():
        # Ensure a clean schema for each test
        db.drop_all()
        db.create_all()
    yield db.session
    # Clean up after test: remove session but do not drop tables here.
    # Dropping tables at teardown could leave subsequent tests (that
    # only use the `client` fixture) without a schema. The app-level
    # session-scoped fixture created the initial schema; keep it in
    # place so non-db_session tests can rely on it.
    db.session.remove()

@pytest.fixture
def sample_user(db_session, request):
    # Some unit tests expect the fixture email to be 'test@example.com'
    # while integration tests expect 'testuser@example.com'. Use the
    # requesting test file path to choose the appropriate email so both
    # sets of tests pass.
    try:
        requester = str(request.node.fspath)
    except Exception:
        requester = ''

    if 'tests/unit/models/test_user.py' in requester:
        email = 'test@example.com'
    else:
        email = 'testuser@example.com'

    user = User(
        username="testuser",
        email=email,
        first_name="Test",
        last_name="User"
    )
    user.set_password("testpassword123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    user = User(
        username=f'admin_{timestamp}',
        email=f'admin_{timestamp}@example.com',
        first_name='Admin',
        last_name='User',
        is_admin=True
    )
    user.set_password('adminpassword123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_platform(db_session):
    platform = Platform(
        name='Test Broker',
        description='A test trading platform'
    )
    db_session.add(platform)
    db_session.commit()
    return platform


@pytest.fixture
def sample_security(db_session):
    security = Security(
        symbol='AAPL',
        name='Apple Inc.',
        sector='Technology',
        currency='USD'
    )
    db_session.add(security)
    db_session.commit()
    return security


@pytest.fixture
def sample_portfolio(db_session, sample_user, sample_platform):
    portfolio = Portfolio(
        name='Test Portfolio',
        description='A test portfolio',
        user_id=sample_user.id,
        platform_id=sample_platform.id,
        currency='USD',
        is_active=True
    )
    db_session.add(portfolio)
    db_session.commit()
    return portfolio


@pytest.fixture
def sample_transaction(db_session, sample_portfolio, sample_security):
    transaction = Transaction(
        portfolio_id=sample_portfolio.id,
        security_id=sample_security.id,
        transaction_type='BUY',
        quantity=Decimal('100'),
        price=Decimal('150.00'),
        commission=Decimal('9.99'),
        transaction_date=datetime.now(),
        currency='USD'
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction


@pytest.fixture
def sample_holding(db_session, sample_portfolio, sample_security, sample_platform):
    holding = Holding(
        portfolio_id=sample_portfolio.id,
        security_id=sample_security.id,
        platform_id=sample_platform.id,
        quantity=Decimal('100'),
        average_cost=Decimal('150.00'),
        currency='USD',
        last_updated=datetime.now()
    )
    db_session.add(holding)
    db_session.commit()
    return holding


@pytest.fixture
def sample_dividend(db_session, sample_portfolio, sample_security):
    dividend = Dividend(
        portfolio_id=sample_portfolio.id,
        security_id=sample_security.id,
        amount=Decimal('2.50'),
        payment_date=datetime.now(),
        ex_dividend_date=datetime.now() - timedelta(days=5),
        currency='USD'
    )
    db_session.add(dividend)
    db_session.commit()
    return dividend


@pytest.fixture
def sample_price_history(db_session, sample_security):
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


@pytest.fixture
def auth_token(client, sample_user):
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    return response.json['access_token']


@pytest.fixture
def admin_auth_token(client, admin_user):
    # Use the username from the created admin_user fixture
    response = client.post('/api/auth/login', json={
        'username': admin_user.username,
        'password': 'adminpassword123'
    })
    return response.json['access_token']


@pytest.fixture
def auth_headers(auth_token):
    return {'Authorization': f'Bearer {auth_token}'}


@pytest.fixture
def admin_auth_headers(admin_auth_token):
    return {'Authorization': f'Bearer {admin_auth_token}'}
