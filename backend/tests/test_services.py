from .test_base import TestBase
from app.services import PortfolioService
from datetime import datetime

class TestPortfolioService(TestBase):
    def test_calculate_portfolio_value(self):
        platform = self.create_test_platform()
        security = self.create_test_security()
        
        # Create test transaction
        transaction = Transaction(
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=10,
            price=100.00,
            date=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()

        service = PortfolioService()
        portfolio_value = service.calculate_portfolio_value(platform.id)
        assert portfolio_value == 1000.00  # 10 shares * $100