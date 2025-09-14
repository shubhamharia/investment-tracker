"""
Unit tests for Portfolio model.
"""
import pytest
from datetime import datetime
from app.models.portfolio import Portfolio
from app.extensions import db


class TestPortfolioModel:
    """Test cases for Portfolio model."""
    
    def test_portfolio_creation(self, db_session, sample_user, sample_platform):
        """Test creating a new portfolio."""
        portfolio = Portfolio(
            name='Test Portfolio',
            description='A test investment portfolio',
            user_id=sample_user.id,
            platform_id=sample_platform.id,
            currency='USD',
            is_active=True
        )
        
        db_session.add(portfolio)
        db_session.commit()
        
        assert portfolio.id is not None
        assert portfolio.name == 'Test Portfolio'
        assert portfolio.description == 'A test investment portfolio'
        assert portfolio.user_id == sample_user.id
        assert portfolio.platform_id == sample_platform.id
        assert portfolio.currency == 'USD'
        assert portfolio.is_active is True
        assert portfolio.created_at is not None
        assert portfolio.updated_at is not None
    
    def test_portfolio_representation(self, sample_portfolio):
        """Test portfolio string representation."""
        expected = f'<Portfolio {sample_portfolio.name}>'
        assert str(sample_portfolio) == expected
        assert repr(sample_portfolio) == expected
    
    def test_portfolio_relationships(self, sample_portfolio):
        """Test portfolio relationships."""
        assert sample_portfolio.user is not None
        assert sample_portfolio.platform is not None
        assert sample_portfolio.user.id == sample_portfolio.user_id
        assert sample_portfolio.platform.id == sample_portfolio.platform_id
        
        # Should have empty collections initially
        assert len(sample_portfolio.transactions) == 0
        assert len(sample_portfolio.holdings) == 0
        assert len(sample_portfolio.dividends) == 0
    
    def test_portfolio_serialization(self, sample_portfolio):
        """Test portfolio serialization to dictionary."""
        portfolio_dict = sample_portfolio.to_dict()
        
        expected_keys = {
            'id', 'name', 'description', 'user_id', 'platform_id',
            'currency', 'is_active', 'created_at', 'updated_at'
        }
        
        assert set(portfolio_dict.keys()) == expected_keys
        assert portfolio_dict['name'] == sample_portfolio.name
        assert portfolio_dict['currency'] == sample_portfolio.currency
        assert portfolio_dict['is_active'] == sample_portfolio.is_active
    
    def test_portfolio_with_transactions(self, db_session, sample_portfolio, sample_security):
        """Test portfolio with related transactions."""
        from app.models.transaction import Transaction
        from decimal import Decimal
        
        transaction = Transaction(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price=Decimal('50.00'),
            commission=Decimal('9.99'),
            transaction_date=datetime.now(),
            currency='USD'
        )
        
        db_session.add(transaction)
        db_session.commit()
        
        # Refresh to load relationships
        db_session.refresh(sample_portfolio)
        
        assert len(sample_portfolio.transactions) == 1
        assert sample_portfolio.transactions[0].id == transaction.id
    
    def test_portfolio_active_status(self, db_session, sample_user, sample_platform):
        """Test portfolio active status."""
        active_portfolio = Portfolio(
            name='Active Portfolio',
            user_id=sample_user.id,
            platform_id=sample_platform.id,
            currency='USD',
            is_active=True
        )
        
        inactive_portfolio = Portfolio(
            name='Inactive Portfolio',
            user_id=sample_user.id,
            platform_id=sample_platform.id,
            currency='USD',
            is_active=False
        )
        
        db_session.add_all([active_portfolio, inactive_portfolio])
        db_session.commit()
        
        assert active_portfolio.is_active is True
        assert inactive_portfolio.is_active is False
    
    def test_portfolio_currency_support(self, db_session, sample_user, sample_platform):
        """Test portfolio with different currencies."""
        currencies = ['USD', 'EUR', 'GBP', 'CAD', 'JPY']
        
        portfolios = []
        for currency in currencies:
            portfolio = Portfolio(
                name=f'{currency} Portfolio',
                user_id=sample_user.id,
                platform_id=sample_platform.id,
                currency=currency,
                is_active=True
            )
            portfolios.append(portfolio)
            db_session.add(portfolio)
        
        db_session.commit()
        
        for portfolio, expected_currency in zip(portfolios, currencies):
            assert portfolio.currency == expected_currency
    
    def test_portfolio_user_association(self, db_session, sample_platform):
        """Test portfolio association with different users."""
        from app.models.user import User
        
        user1 = User(
            username='user1',
            email='user1@example.com',
            first_name='User',
            last_name='One'
        )
        user1.set_password('password')
        
        user2 = User(
            username='user2',
            email='user2@example.com',
            first_name='User',
            last_name='Two'
        )
        user2.set_password('password')
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        portfolio1 = Portfolio(
            name='User 1 Portfolio',
            user_id=user1.id,
            platform_id=sample_platform.id,
            currency='USD',
            is_active=True
        )
        
        portfolio2 = Portfolio(
            name='User 2 Portfolio',
            user_id=user2.id,
            platform_id=sample_platform.id,
            currency='USD',
            is_active=True
        )
        
        db_session.add_all([portfolio1, portfolio2])
        db_session.commit()
        
        assert portfolio1.user_id == user1.id
        assert portfolio2.user_id == user2.id
        assert portfolio1.user.username == 'user1'
        assert portfolio2.user.username == 'user2'
    
    def test_portfolio_total_value(self, sample_portfolio):
        """Test portfolio total value calculation (basic test)."""
        # This would be calculated based on holdings
        # For now, just test that the portfolio exists
        assert sample_portfolio.id is not None
        
        # TODO: Add actual total value calculation when holdings are added
        # This would involve summing up all holdings' current values
    
    def test_portfolio_description_optional(self, db_session, sample_user, sample_platform):
        """Test portfolio creation without description."""
        portfolio = Portfolio(
            name='No Description Portfolio',
            user_id=sample_user.id,
            platform_id=sample_platform.id,
            currency='USD',
            is_active=True
        )
        
        db_session.add(portfolio)
        db_session.commit()
        
        assert portfolio.id is not None
        assert portfolio.name == 'No Description Portfolio'
        assert portfolio.description is None