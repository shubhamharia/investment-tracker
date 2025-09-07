import pytest
from app import create_app, db
from app.models import Platform, Security, Transaction

class TestBase:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def create_test_platform(self):
        platform = Platform(
            name='Test Platform',
            description='Test Description'
        )
        db.session.add(platform)
        db.session.commit()
        return platform

    def create_test_security(self):
        security = Security(
            symbol='TEST',
            name='Test Security',
            security_type='STOCK'
        )
        db.session.add(security)
        db.session.commit()
        return security