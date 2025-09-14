"""
Unit tests for Dividend model.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.models.dividend import Dividend
from app.extensions import db


class TestDividendModel:
    """Test cases for Dividend model."""
    
    def test_dividend_creation(self, db_session, sample_portfolio, sample_security):
        """Test creating a new dividend."""
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
        
        assert dividend.id is not None
        assert dividend.portfolio_id == sample_portfolio.id
        assert dividend.security_id == sample_security.id
        assert dividend.amount == Decimal('2.50')
        assert dividend.currency == 'USD'
        assert dividend.created_at is not None
    
    def test_dividend_representation(self, sample_dividend):
        """Test dividend string representation."""
        expected = f'<Dividend {sample_dividend.security.symbol}: ${sample_dividend.amount}>'
        assert str(sample_dividend) == expected
    
    def test_dividend_relationships(self, sample_dividend):
        """Test dividend relationships."""
        assert sample_dividend.portfolio is not None
        assert sample_dividend.security is not None
        assert sample_dividend.portfolio.id == sample_dividend.portfolio_id
        assert sample_dividend.security.id == sample_dividend.security_id
    
    def test_dividend_serialization(self, sample_dividend):
        """Test dividend serialization to dictionary."""
        dividend_dict = sample_dividend.to_dict()
        
        expected_keys = {
            'id', 'portfolio_id', 'security_id', 'amount',
            'payment_date', 'ex_dividend_date', 'currency',
            'record_date', 'created_at'
        }
        
        assert set(dividend_dict.keys()) == expected_keys
        assert float(dividend_dict['amount']) == float(sample_dividend.amount)
        assert dividend_dict['currency'] == sample_dividend.currency
    
    def test_dividend_different_currencies(self, db_session, sample_portfolio, sample_security):
        """Test dividends with different currencies."""
        currencies = ['USD', 'EUR', 'GBP', 'CAD']
        
        dividends = []
        for i, currency in enumerate(currencies):
            dividend = Dividend(
                portfolio_id=sample_portfolio.id,
                security_id=sample_security.id,
                amount=Decimal('1.25') + Decimal(str(i * 0.25)),
                payment_date=datetime.now(),
                ex_dividend_date=datetime.now() - timedelta(days=5),
                currency=currency
            )
            dividends.append(dividend)
            db_session.add(dividend)
        
        db_session.commit()
        
        for dividend, expected_currency in zip(dividends, currencies):
            assert dividend.currency == expected_currency
    
    def test_dividend_date_validation(self, db_session, sample_portfolio, sample_security):
        """Test dividend date relationships."""
        payment_date = datetime.now()
        ex_date = payment_date - timedelta(days=5)
        record_date = payment_date - timedelta(days=3)
        
        dividend = Dividend(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            amount=Decimal('3.00'),
            payment_date=payment_date,
            ex_dividend_date=ex_date,
            record_date=record_date,
            currency='USD'
        )
        
        db_session.add(dividend)
        db_session.commit()
        
        assert dividend.ex_dividend_date < dividend.payment_date
        if dividend.record_date:
            assert dividend.ex_dividend_date <= dividend.record_date <= dividend.payment_date
    
    def test_dividend_amount_precision(self, db_session, sample_portfolio, sample_security):
        """Test dividend amount precision."""
        precise_amount = Decimal('2.345678')
        
        dividend = Dividend(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            amount=precise_amount,
            payment_date=datetime.now(),
            ex_dividend_date=datetime.now() - timedelta(days=5),
            currency='USD'
        )
        
        db_session.add(dividend)
        db_session.commit()
        
        assert dividend.amount == precise_amount
    
    def test_dividend_quarterly_pattern(self, db_session, sample_portfolio, sample_security):
        """Test quarterly dividend pattern."""
        base_date = datetime(2023, 1, 15)
        quarterly_dividends = []
        
        for quarter in range(4):
            payment_date = base_date + timedelta(days=90 * quarter)
            dividend = Dividend(
                portfolio_id=sample_portfolio.id,
                security_id=sample_security.id,
                amount=Decimal('0.65'),
                payment_date=payment_date,
                ex_dividend_date=payment_date - timedelta(days=30),
                currency='USD'
            )
            quarterly_dividends.append(dividend)
            db_session.add(dividend)
        
        db_session.commit()
        
        assert len(quarterly_dividends) == 4
        total_annual = sum(d.amount for d in quarterly_dividends)
        assert total_annual == Decimal('2.60')
    
    def test_dividend_yield_calculation(self, sample_dividend):
        """Test dividend yield calculation helper."""
        # This would be a method on the model if implemented
        share_price = Decimal('100.00')
        annual_dividend = sample_dividend.amount * 4  # Quarterly assumption
        
        expected_yield = (annual_dividend / share_price) * 100
        # yield = (annual_dividend / share_price) * 100
        
        assert expected_yield > 0
    
    def test_dividend_portfolio_association(self, db_session, sample_security):
        """Test dividend association with different portfolios."""
        from app.models.portfolio import Portfolio
        from app.models.user import User
        from app.models.platform import Platform
        
        # Create additional user and portfolio
        user = User(username='divuser', email='div@example.com', first_name='Div', last_name='User')
        user.set_password('password')
        platform = Platform(name='Div Platform')
        
        db_session.add_all([user, platform])
        db_session.commit()
        
        portfolio = Portfolio(
            name='Dividend Portfolio',
            user_id=user.id,
            platform_id=platform.id,
            currency='USD',
            is_active=True
        )
        db_session.add(portfolio)
        db_session.commit()
        
        dividend = Dividend(
            portfolio_id=portfolio.id,
            security_id=sample_security.id,
            amount=Decimal('1.85'),
            payment_date=datetime.now(),
            ex_dividend_date=datetime.now() - timedelta(days=5),
            currency='USD'
        )
        
        db_session.add(dividend)
        db_session.commit()
        
        assert dividend.portfolio.name == 'Dividend Portfolio'
        assert dividend.portfolio.user.username == 'divuser'