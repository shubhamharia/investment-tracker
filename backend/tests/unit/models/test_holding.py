"""
Unit tests for Holding model.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from app.models.holding import Holding
from app.extensions import db


class TestHoldingModel:
    """Test cases for Holding model."""
    
    def test_holding_creation(self, db_session, sample_portfolio, sample_security, sample_platform):
        """Test creating a new holding."""
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            platform_id=sample_platform.id,
            quantity=Decimal('100'),
            average_cost=Decimal('50.00'),
            currency='USD',
            last_updated=datetime.now()
        )
        
        db_session.add(holding)
        db_session.commit()
        
        assert holding.id is not None
        assert holding.portfolio_id == sample_portfolio.id
        assert holding.security_id == sample_security.id
        assert holding.platform_id == sample_platform.id
        assert holding.quantity == Decimal('100')
        assert holding.average_cost == Decimal('50.00')
        assert holding.currency == 'USD'
        assert holding.last_updated is not None
        assert holding.created_at is not None
    
    def test_holding_total_cost(self, db_session, sample_portfolio, sample_security, sample_platform):
        """Test holding total cost calculation."""
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            platform_id=sample_platform.id,
            quantity=Decimal('100'),
            average_cost=Decimal('50.00'),
            currency='USD',
            last_updated=datetime.now()
        )
        
        expected_total = Decimal('100') * Decimal('50.00')
        assert holding.total_cost == expected_total
    
    def test_holding_representation(self, sample_holding):
        """Test holding string representation."""
        expected = f'<Holding {sample_holding.security.symbol}: {sample_holding.quantity} @ {sample_holding.average_cost}>'
        assert str(sample_holding) == expected
    
    def test_holding_relationships(self, sample_holding):
        """Test holding relationships."""
        assert sample_holding.portfolio is not None
        assert sample_holding.security is not None
        assert sample_holding.platform is not None
        assert sample_holding.portfolio.id == sample_holding.portfolio_id
        assert sample_holding.security.id == sample_holding.security_id
        assert sample_holding.platform.id == sample_holding.platform_id
    
    def test_holding_serialization(self, sample_holding):
        """Test holding serialization to dictionary."""
        holding_dict = sample_holding.to_dict()
        
        expected_keys = {
            'id', 'portfolio_id', 'security_id', 'platform_id',
            'quantity', 'average_cost', 'currency', 'last_updated',
            'created_at', 'total_cost'
        }
        
        assert set(holding_dict.keys()) == expected_keys
        assert float(holding_dict['quantity']) == float(sample_holding.quantity)
        assert float(holding_dict['average_cost']) == float(sample_holding.average_cost)
        assert holding_dict['currency'] == sample_holding.currency
    
    def test_holding_unique_constraint(self, db_session, sample_portfolio, sample_security, sample_platform):
        """Test holding unique constraint (portfolio + security + platform)."""
        holding1 = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            platform_id=sample_platform.id,
            quantity=Decimal('100'),
            average_cost=Decimal('50.00'),
            currency='USD',
            last_updated=datetime.now()
        )
        
        holding2 = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            platform_id=sample_platform.id,  # Same combination
            quantity=Decimal('50'),
            average_cost=Decimal('60.00'),
            currency='USD',
            last_updated=datetime.now()
        )
        
        db_session.add(holding1)
        db_session.commit()
        
        db_session.add(holding2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_holding_zero_quantity(self, db_session, sample_portfolio, sample_security, sample_platform):
        """Test holding with zero quantity."""
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            platform_id=sample_platform.id,
            quantity=Decimal('0'),
            average_cost=Decimal('50.00'),
            currency='USD',
            last_updated=datetime.now()
        )
        
        db_session.add(holding)
        db_session.commit()
        
        assert holding.quantity == Decimal('0')
        assert holding.total_cost == Decimal('0')
    
    def test_holding_negative_quantity(self, db_session, sample_portfolio, sample_security, sample_platform):
        """Test holding with negative quantity (short position)."""
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            platform_id=sample_platform.id,
            quantity=Decimal('-50'),  # Short position
            average_cost=Decimal('100.00'),
            currency='USD',
            last_updated=datetime.now()
        )
        
        db_session.add(holding)
        db_session.commit()
        
        assert holding.quantity == Decimal('-50')
        assert holding.total_cost == Decimal('-5000.00')  # Negative total cost for short
    
    def test_holding_decimal_precision(self, db_session, sample_portfolio, sample_security, sample_platform):
        """Test holding with high decimal precision."""
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=sample_security.id,
            platform_id=sample_platform.id,
            quantity=Decimal('123.456789'),
            average_cost=Decimal('987.654321'),
            currency='USD',
            last_updated=datetime.now()
        )
        
        db_session.add(holding)
        db_session.commit()
        
        assert holding.quantity == Decimal('123.456789')
        assert holding.average_cost == Decimal('987.654321')
        
        # Total cost should maintain precision
        expected_total = Decimal('123.456789') * Decimal('987.654321')
        assert holding.total_cost == expected_total
    
    def test_holding_different_currencies(self, db_session, sample_portfolio, sample_platform):
        """Test holdings with different currencies."""
        from app.models.security import Security
        
        # Create securities with different currencies
        usd_security = Security(
            symbol='AAPL',
            name='Apple Inc.',
            currency='USD'
        )
        
        eur_security = Security(
            symbol='SAP',
            name='SAP SE',
            currency='EUR'
        )
        
        db_session.add_all([usd_security, eur_security])
        db_session.commit()
        
        # Create holdings in different currencies
        usd_holding = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=usd_security.id,
            platform_id=sample_platform.id,
            quantity=Decimal('100'),
            average_cost=Decimal('150.00'),
            currency='USD',
            last_updated=datetime.now()
        )
        
        eur_holding = Holding(
            portfolio_id=sample_portfolio.id,
            security_id=eur_security.id,
            platform_id=sample_platform.id,
            quantity=Decimal('50'),
            average_cost=Decimal('120.00'),
            currency='EUR',
            last_updated=datetime.now()
        )
        
        db_session.add_all([usd_holding, eur_holding])
        db_session.commit()
        
        assert usd_holding.currency == 'USD'
        assert eur_holding.currency == 'EUR'
        assert usd_holding.total_cost == Decimal('15000.00')
        assert eur_holding.total_cost == Decimal('6000.00')
    
    def test_holding_update_timestamp(self, sample_holding, db_session):
        """Test holding timestamp updates."""
        original_updated = sample_holding.last_updated
        
        # Update the holding
        sample_holding.quantity = Decimal('200')
        sample_holding.last_updated = datetime.now()
        
        db_session.commit()
        
        assert sample_holding.last_updated > original_updated
    
    def test_holding_current_value_calculation(self, sample_holding):
        """Test current value calculation (would need current price)."""
        # This would require current price data
        # For now, just test the total_cost property
        expected_cost = sample_holding.quantity * sample_holding.average_cost
        assert sample_holding.total_cost == expected_cost
        
        # TODO: Add current_value property that uses current market price
        # current_value = quantity * current_price
        # unrealized_gain_loss = current_value - total_cost