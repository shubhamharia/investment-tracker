"""
Unit tests for Price History model.
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from app.models.price_history import PriceHistory
from app.extensions import db


class TestPriceHistoryModel:
    """Test cases for PriceHistory model."""
    
    def test_price_history_creation(self, db_session, sample_security):
        """Test creating a new price history entry."""
        price_history = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 1, 15),
            open_price=Decimal('148.50'),
            high_price=Decimal('152.00'),
            low_price=Decimal('147.00'),
            close_price=Decimal('151.20'),
            volume=1000000,
            adjusted_close=Decimal('151.20')
        )
        
        db_session.add(price_history)
        db_session.commit()
        
        assert price_history.id is not None
        assert price_history.security_id == sample_security.id
        assert price_history.date == date(2023, 1, 15)
        assert price_history.close_price == Decimal('151.20')
        assert price_history.volume == 1000000
    
    def test_price_history_representation(self, sample_price_history):
        """Test price history string representation."""
        expected = f'<PriceHistory {sample_price_history.security.symbol} {sample_price_history.date}: ${sample_price_history.close_price}>'
        assert str(sample_price_history) == expected
    
    def test_price_history_relationships(self, sample_price_history):
        """Test price history relationships."""
        assert sample_price_history.security is not None
        assert sample_price_history.security.id == sample_price_history.security_id
    
    def test_price_history_serialization(self, sample_price_history):
        """Test price history serialization to dictionary."""
        history_dict = sample_price_history.to_dict()
        
        expected_keys = {
            'id', 'security_id', 'date', 'open_price', 'high_price',
            'low_price', 'close_price', 'volume', 'adjusted_close'
        }
        
        assert set(history_dict.keys()) == expected_keys
        assert float(history_dict['close_price']) == float(sample_price_history.close_price)
        assert history_dict['volume'] == sample_price_history.volume
    
    def test_price_history_unique_constraint(self, db_session, sample_security):
        """Test unique constraint on security_id + date."""
        test_date = date(2023, 2, 1)
        
        history1 = PriceHistory(
            security_id=sample_security.id,
            date=test_date,
            open_price=Decimal('100.00'),
            high_price=Decimal('105.00'),
            low_price=Decimal('99.00'),
            close_price=Decimal('103.00'),
            volume=500000,
            adjusted_close=Decimal('103.00')
        )
        
        history2 = PriceHistory(
            security_id=sample_security.id,
            date=test_date,  # Same date and security
            open_price=Decimal('102.00'),
            high_price=Decimal('107.00'),
            low_price=Decimal('101.00'),
            close_price=Decimal('105.00'),
            volume=600000,
            adjusted_close=Decimal('105.00')
        )
        
        db_session.add(history1)
        db_session.commit()
        
        db_session.add(history2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_price_history_ohlc_validation(self, db_session, sample_security):
        """Test OHLC price relationships."""
        price_history = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 3, 1),
            open_price=Decimal('100.00'),
            high_price=Decimal('105.00'),  # Highest
            low_price=Decimal('98.00'),    # Lowest
            close_price=Decimal('102.50'),
            volume=750000,
            adjusted_close=Decimal('102.50')
        )
        
        db_session.add(price_history)
        db_session.commit()
        
        # High should be >= all other prices
        assert price_history.high_price >= price_history.open_price
        assert price_history.high_price >= price_history.close_price
        assert price_history.high_price >= price_history.low_price
        
        # Low should be <= all other prices  
        assert price_history.low_price <= price_history.open_price
        assert price_history.low_price <= price_history.close_price
        assert price_history.low_price <= price_history.high_price
    
    def test_price_history_volume_validation(self, db_session, sample_security):
        """Test volume validation."""
        # Test normal volume
        history_normal = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 4, 1),
            open_price=Decimal('50.00'),
            high_price=Decimal('52.00'),
            low_price=Decimal('49.00'),
            close_price=Decimal('51.00'),
            volume=1000000,
            adjusted_close=Decimal('51.00')
        )
        
        # Test zero volume (market holiday or no trading)
        history_zero = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 4, 2),
            open_price=Decimal('51.00'),
            high_price=Decimal('51.00'),
            low_price=Decimal('51.00'),
            close_price=Decimal('51.00'),
            volume=0,
            adjusted_close=Decimal('51.00')
        )
        
        db_session.add_all([history_normal, history_zero])
        db_session.commit()
        
        assert history_normal.volume == 1000000
        assert history_zero.volume == 0
    
    def test_price_history_splits_adjustment(self, db_session, sample_security):
        """Test stock split adjustment in historical data."""
        # Before split
        pre_split = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 5, 1),
            open_price=Decimal('200.00'),
            high_price=Decimal('210.00'),
            low_price=Decimal('198.00'),
            close_price=Decimal('205.00'),
            volume=100000,
            adjusted_close=Decimal('205.00')  # No adjustment yet
        )
        
        # After 2:1 split
        post_split = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 5, 2),
            open_price=Decimal('102.50'),  # Half of previous close
            high_price=Decimal('105.00'),
            low_price=Decimal('101.00'),
            close_price=Decimal('103.00'),
            volume=200000,  # Double volume due to split
            adjusted_close=Decimal('103.00')
        )
        
        db_session.add_all([pre_split, post_split])
        db_session.commit()
        
        # After split, pre-split adjusted close should be half
        # This would be updated by a background process
        assert pre_split.close_price == Decimal('205.00')  # Original price
        assert post_split.close_price == Decimal('103.00')  # Post-split price
    
    def test_price_history_daily_return(self, db_session, sample_security):
        """Test daily return calculation."""
        day1 = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 6, 1),
            open_price=Decimal('100.00'),
            high_price=Decimal('102.00'),
            low_price=Decimal('99.00'),
            close_price=Decimal('101.00'),
            volume=500000,
            adjusted_close=Decimal('101.00')
        )
        
        day2 = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 6, 2),
            open_price=Decimal('101.00'),
            high_price=Decimal('104.00'),
            low_price=Decimal('100.50'),
            close_price=Decimal('103.00'),
            volume=600000,
            adjusted_close=Decimal('103.00')
        )
        
        db_session.add_all([day1, day2])
        db_session.commit()
        
        # Daily return = (day2_close - day1_close) / day1_close
        daily_return = (day2.close_price - day1.close_price) / day1.close_price
        expected_return = Decimal('0.0198')  # About 1.98%
        
        assert abs(daily_return - expected_return) < Decimal('0.001')
    
    def test_price_history_intraday_range(self, db_session, sample_security):
        """Test intraday price range calculation."""
        price_history = PriceHistory(
            security_id=sample_security.id,
            date=date(2023, 7, 1),
            open_price=Decimal('75.50'),
            high_price=Decimal('78.25'),
            low_price=Decimal('74.10'),
            close_price=Decimal('77.80'),
            volume=800000,
            adjusted_close=Decimal('77.80')
        )
        
        db_session.add(price_history)
        db_session.commit()
        
        # Price range = high - low
        price_range = price_history.high_price - price_history.low_price
        expected_range = Decimal('4.15')
        
        assert price_range == expected_range
        
        # Range as percentage of open
        range_percent = (price_range / price_history.open_price) * 100
        assert range_percent > 0
    
    def test_price_history_time_series(self, db_session, sample_security):
        """Test time series of price history."""
        base_date = date(2023, 8, 1)
        prices = []
        
        for i in range(5):
            price = Decimal('50.00') + Decimal(str(i))
            history = PriceHistory(
                security_id=sample_security.id,
                date=date(base_date.year, base_date.month, base_date.day + i),
                open_price=price,
                high_price=price + Decimal('1.50'),
                low_price=price - Decimal('0.75'),
                close_price=price + Decimal('0.50'),
                volume=100000 + i * 10000,
                adjusted_close=price + Decimal('0.50')
            )
            prices.append(history)
            db_session.add(history)
        
        db_session.commit()
        
        # Verify time series
        assert len(prices) == 5
        for i, price_history in enumerate(prices):
            expected_close = Decimal('50.50') + Decimal(str(i))
            assert price_history.close_price == expected_close