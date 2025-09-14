"""
Unit tests for Transaction model.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from app.models.transaction import Transaction
from app.extensions import db


class TestTransactionModel:
    """Test cases for Transaction model."""
    
    def test_transaction_creation(self, db_session, sample_portfolio, sample_security):
        """Test creating a new transaction."""
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
        
        assert transaction.id is not None
        assert transaction.portfolio_id == sample_portfolio.id
        assert transaction.security_id == sample_security.id
        assert transaction.transaction_type == 'BUY'
        assert transaction.quantity == Decimal('100')
        assert transaction.price == Decimal('50.00')
        assert transaction.commission == Decimal('9.99')
        assert transaction.currency == 'USD'
        assert transaction.created_at is not None
    
    def test_transaction_total_value(self, db_session, sample_portfolio, sample_security):
        """Test transaction total value calculation."""
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
        
        # Total value = quantity * price + commission
        expected_total = Decimal('100') * Decimal('50.00') + Decimal('9.99')
        assert transaction.total_value == expected_total
    
    def test_transaction_types(self, db_session, sample_portfolio, sample_security):
        """Test different transaction types."""
        buy_transaction = Transaction(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price=Decimal('50.00'),
            commission=Decimal('9.99'),
            transaction_date=datetime.now(),
            currency='USD'
        )
        
        sell_transaction = Transaction(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            transaction_type='SELL',
            quantity=Decimal('50'),
            price=Decimal('55.00'),
            commission=Decimal('9.99'),
            transaction_date=datetime.now(),
            currency='USD'
        )
        
        db_session.add_all([buy_transaction, sell_transaction])
        db_session.commit()
        
        assert buy_transaction.transaction_type == 'BUY'
        assert sell_transaction.transaction_type == 'SELL'
    
    def test_transaction_validation(self, db_session, sample_portfolio, sample_security):
        """Test transaction validation."""
        # Test negative quantity should not be allowed in business logic
        transaction = Transaction(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            transaction_type='BUY',
            quantity=Decimal('-100'),  # Negative quantity
            price=Decimal('50.00'),
            commission=Decimal('9.99'),
            transaction_date=datetime.now(),
            currency='USD'
        )
        
        # Should be able to create (validation happens at API level)
        db_session.add(transaction)
        db_session.commit()
        assert transaction.id is not None
    
    def test_transaction_relationships(self, sample_transaction):
        """Test transaction relationships."""
        assert sample_transaction.portfolio is not None
        assert sample_transaction.security is not None
        assert sample_transaction.portfolio.id == sample_transaction.portfolio_id
        assert sample_transaction.security.id == sample_transaction.security_id
    
    def test_transaction_representation(self, sample_transaction):
        """Test transaction string representation."""
        expected = f'<Transaction {sample_transaction.id}: {sample_transaction.transaction_type} {sample_transaction.quantity} {sample_transaction.security.symbol}>'
        assert str(sample_transaction) == expected
    
    def test_transaction_serialization(self, sample_transaction):
        """Test transaction serialization to dictionary."""
        transaction_dict = sample_transaction.to_dict()
        
        expected_keys = {
            'id', 'portfolio_id', 'security_id', 'transaction_type',
            'quantity', 'price', 'commission', 'transaction_date',
            'currency', 'notes', 'created_at', 'total_value'
        }
        
        assert set(transaction_dict.keys()) == expected_keys
        assert transaction_dict['transaction_type'] == sample_transaction.transaction_type
        assert float(transaction_dict['quantity']) == float(sample_transaction.quantity)
        assert float(transaction_dict['price']) == float(sample_transaction.price)
    
    def test_transaction_update_holding(self, db_session, sample_portfolio, sample_security, sample_platform):
        """Test that transaction updates holding correctly."""
        # Create initial transaction
        transaction1 = Transaction(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price=Decimal('50.00'),
            commission=Decimal('9.99'),
            transaction_date=datetime.now(),
            currency='USD'
        )
        
        db_session.add(transaction1)
        db_session.commit()
        
        # Check holding was created/updated
        from app.models.holding import Holding
        holding = db_session.query(Holding).filter_by(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            platform_id=sample_platform.id
        ).first()
        
        assert holding is not None
        assert holding.quantity == Decimal('100')
        
        # Add another transaction
        transaction2 = Transaction(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            transaction_type='BUY',
            quantity=Decimal('50'),
            price=Decimal('60.00'),
            commission=Decimal('9.99'),
            transaction_date=datetime.now(),
            currency='USD'
        )
        
        db_session.add(transaction2)
        db_session.commit()
        
        # Refresh holding
        db_session.refresh(holding)
        
        # Should have updated quantity and average cost
        assert holding.quantity == Decimal('150')  # 100 + 50
        # Average cost = (100*50 + 50*60) / 150 = 8000 / 150 = 53.33
        expected_avg_cost = (Decimal('100') * Decimal('50.00') + Decimal('50') * Decimal('60.00')) / Decimal('150')
        assert abs(holding.average_cost - expected_avg_cost) < Decimal('0.01')
    
    def test_transaction_currency_validation(self, db_session, sample_portfolio, sample_security):
        """Test transaction with different currencies."""
        eur_transaction = Transaction(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price=Decimal('45.00'),
            commission=Decimal('8.50'),
            transaction_date=datetime.now(),
            currency='EUR'
        )
        
        db_session.add(eur_transaction)
        db_session.commit()
        
        assert eur_transaction.currency == 'EUR'
        assert eur_transaction.id is not None