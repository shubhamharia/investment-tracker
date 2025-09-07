import pytest
from app import create_app
from app.extensions import db
from app.models import User, Portfolio, Security, Platform

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