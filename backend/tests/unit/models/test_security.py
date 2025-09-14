"""
Unit tests for Security model.
"""
import pytest
from app.models.security import Security
from app.extensions import db


class TestSecurityModel:
    """Test cases for Security model."""
    
    def test_security_creation(self, db_session):
        """Test creating a new security."""
        security = Security(
            symbol='GOOGL',
            name='Alphabet Inc.',
            sector='Technology',
            currency='USD'
        )
        
        db_session.add(security)
        db_session.commit()
        
        assert security.id is not None
        assert security.symbol == 'GOOGL'
        assert security.name == 'Alphabet Inc.'
        assert security.sector == 'Technology'
        assert security.currency == 'USD'
        assert security.created_at is not None
        assert security.updated_at is not None
    
    def test_security_representation(self, sample_security):
        """Test security string representation."""
        expected = f'<Security {sample_security.symbol}: {sample_security.name}>'
        assert str(sample_security) == expected
        assert repr(sample_security) == expected
    
    def test_security_unique_symbol(self, db_session, sample_security):
        """Test that security symbols must be unique."""
        duplicate_security = Security(
            symbol='AAPL',  # Same as sample_security
            name='Different Apple Inc.',
            sector='Technology',
            currency='USD'
        )
        
        db_session.add(duplicate_security)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_security_serialization(self, sample_security):
        """Test security serialization to dictionary."""
        security_dict = sample_security.to_dict()
        
        expected_keys = {
            'id', 'symbol', 'name', 'sector', 'currency',
            'created_at', 'updated_at'
        }
        
        assert set(security_dict.keys()) == expected_keys
        assert security_dict['symbol'] == sample_security.symbol
        assert security_dict['name'] == sample_security.name
        assert security_dict['sector'] == sample_security.sector
        assert security_dict['currency'] == sample_security.currency
    
    def test_security_relationships(self, sample_security):
        """Test security relationships."""
        # Should have empty relationships initially
        assert len(sample_security.transactions) == 0
        assert len(sample_security.holdings) == 0
        assert len(sample_security.dividends) == 0
        assert len(sample_security.price_history) == 0
    
    def test_security_with_transactions(self, db_session, sample_security, sample_portfolio):
        """Test security with related transactions."""
        from app.models.transaction import Transaction
        from datetime import datetime
        from decimal import Decimal
        
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
        
        # Refresh to load relationships
        db_session.refresh(sample_security)
        
        assert len(sample_security.transactions) == 1
        assert sample_security.transactions[0].id == transaction.id
    
    def test_security_currency_codes(self, db_session):
        """Test different currency codes."""
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD']
        
        for i, currency in enumerate(currencies):
            security = Security(
                symbol=f'TEST{i}',
                name=f'Test Security {i}',
                sector='Test',
                currency=currency
            )
            db_session.add(security)
        
        db_session.commit()
        
        # Verify all were created with correct currencies
        securities = db_session.query(Security).filter(
            Security.symbol.like('TEST%')
        ).all()
        
        assert len(securities) == len(currencies)
        security_currencies = [s.currency for s in securities]
        assert set(security_currencies) == set(currencies)
    
    def test_security_sector_classification(self, db_session):
        """Test different sector classifications."""
        sectors = [
            'Technology', 'Healthcare', 'Financial Services',
            'Consumer Cyclical', 'Communication Services', 'Industrials',
            'Consumer Defensive', 'Energy', 'Utilities', 'Real Estate',
            'Basic Materials'
        ]
        
        for i, sector in enumerate(sectors):
            security = Security(
                symbol=f'SECT{i}',
                name=f'Sector Test {i}',
                sector=sector,
                currency='USD'
            )
            db_session.add(security)
        
        db_session.commit()
        
        # Verify all sectors were saved correctly
        securities = db_session.query(Security).filter(
            Security.symbol.like('SECT%')
        ).all()
        
        assert len(securities) == len(sectors)
        security_sectors = [s.sector for s in securities]
        assert set(security_sectors) == set(sectors)
    
    def test_security_optional_fields(self, db_session):
        """Test security with minimal required fields."""
        security = Security(
            symbol='MIN',
            name='Minimal Security',
            currency='USD'
        )
        
        db_session.add(security)
        db_session.commit()
        
        assert security.id is not None
        assert security.symbol == 'MIN'
        assert security.name == 'Minimal Security'
        assert security.currency == 'USD'
        assert security.sector is None  # Optional field