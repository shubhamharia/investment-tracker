import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.security import Security
from app.models.platform import Platform
from app.models.holding import Holding

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_user(db_session):
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('password123')
    db_session.session.add(user)
    db_session.session.commit()
    return user

@pytest.fixture
def test_portfolio(db_session, test_user):
    portfolio = Portfolio(
        name='Test Portfolio',
        description='Test Description',
        user=test_user
    )
    db_session.session.add(portfolio)
    db_session.session.commit()
    return portfolio

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
        account_type='Trading'
    )
    db_session.session.add(platform)
    db_session.session.commit()
    return platform

@pytest.fixture
def test_holding(db_session, test_portfolio, test_security, test_platform):
    holding = Holding(
        portfolio=test_portfolio,
        security=test_security,
        platform=test_platform,
        quantity=10.0,
        average_cost=150.00,
        total_cost=1500.00
    )
    db_session.session.add(holding)
    db_session.session.commit()
    return holding