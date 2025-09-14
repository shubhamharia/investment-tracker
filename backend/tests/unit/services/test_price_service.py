"""
Unit tests for Price Service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, date
import yfinance as yf
from app.services.price_service import PriceService
from app.models.security import Security
from app.models.price_history import PriceHistory


class TestPriceService:
    """Test cases for PriceService."""
    
    def test_price_service_initialization(self, db_session):
        """Test PriceService initialization."""
        service = PriceService(db_session)
        assert service.db_session == db_session
    
    @patch('app.services.price_service.yf.Ticker')
    def test_get_current_price_success(self, mock_ticker, db_session, sample_security):
        """Test successful current price retrieval."""
        # Mock yfinance ticker
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'regularMarketPrice': 150.50,
            'currency': 'USD'
        }
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('AAPL')
        
        assert price == Decimal('150.50')
        mock_ticker.assert_called_once_with('AAPL')
    
    @patch('app.services.price_service.yf.Ticker')
    def test_get_current_price_failure(self, mock_ticker, db_session):
        """Test current price retrieval failure."""
        # Mock yfinance ticker to raise exception
        mock_ticker.side_effect = Exception("Network error")
        
        service = PriceService(db_session)
        price = service.get_current_price('INVALID')
        
        assert price is None
    
    @patch('app.services.price_service.yf.Ticker')
    def test_get_current_price_no_data(self, mock_ticker, db_session):
        """Test current price retrieval with no data."""
        # Mock yfinance ticker with empty info
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {}
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('NODATA')
        
        assert price is None
    
    @patch('app.services.price_service.yf.download')
    def test_get_historical_prices_success(self, mock_download, db_session, sample_security):
        """Test successful historical prices retrieval."""
        # Mock yfinance download
        import pandas as pd
        mock_data = pd.DataFrame({
            'Open': [148.0, 149.0],
            'High': [152.0, 153.0],
            'Low': [147.0, 148.0],
            'Close': [151.0, 152.0],
            'Volume': [1000000, 1100000],
            'Adj Close': [151.0, 152.0]
        }, index=pd.DatetimeIndex(['2023-01-01', '2023-01-02']))
        mock_download.return_value = mock_data
        
        service = PriceService(db_session)
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 2)
        
        prices = service.get_historical_prices('AAPL', start_date, end_date)
        
        assert len(prices) == 2
        assert prices[0]['date'] == date(2023, 1, 1)
        assert prices[0]['close'] == Decimal('151.0')
        assert prices[1]['date'] == date(2023, 1, 2)
        assert prices[1]['close'] == Decimal('152.0')
    
    @patch('app.services.price_service.yf.download')
    def test_get_historical_prices_failure(self, mock_download, db_session):
        """Test historical prices retrieval failure."""
        mock_download.side_effect = Exception("Network error")
        
        service = PriceService(db_session)
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 2)
        
        prices = service.get_historical_prices('INVALID', start_date, end_date)
        
        assert prices == []
    
    @patch('app.services.price_service.yf.Tickers')
    def test_fetch_latest_prices_success(self, mock_tickers, db_session):
        """Test successful batch price fetching."""
        # Create test securities
        securities = [
            Security(symbol='AAPL', name='Apple Inc.', currency='USD'),
            Security(symbol='GOOGL', name='Alphabet Inc.', currency='USD')
        ]
        for security in securities:
            db_session.add(security)
        db_session.commit()
        
        # Mock yfinance tickers
        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {
            'AAPL': Mock(info={'regularMarketPrice': 150.50}),
            'GOOGL': Mock(info={'regularMarketPrice': 2800.75})
        }
        mock_tickers.return_value = mock_tickers_instance
        
        service = PriceService(db_session)
        results = service.fetch_latest_prices(['AAPL', 'GOOGL'])
        
        assert 'AAPL' in results
        assert 'GOOGL' in results
        assert results['AAPL'] == Decimal('150.50')
        assert results['GOOGL'] == Decimal('2800.75')
    
    @patch('app.services.price_service.yf.Tickers')
    def test_fetch_latest_prices_partial_failure(self, mock_tickers, db_session):
        """Test batch price fetching with partial failures."""
        # Mock yfinance tickers with mixed results
        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {
            'AAPL': Mock(info={'regularMarketPrice': 150.50}),
            'INVALID': Mock(info={})  # No price data
        }
        mock_tickers.return_value = mock_tickers_instance
        
        service = PriceService(db_session)
        results = service.fetch_latest_prices(['AAPL', 'INVALID'])
        
        assert 'AAPL' in results
        assert 'INVALID' not in results
        assert results['AAPL'] == Decimal('150.50')
    
    @patch('app.services.price_service.PriceService.get_historical_prices')
    def test_update_price_history(self, mock_get_historical, db_session, sample_security):
        """Test updating price history for a security."""
        # Mock historical prices
        mock_get_historical.return_value = [
            {
                'date': date(2023, 1, 1),
                'open': Decimal('148.0'),
                'high': Decimal('152.0'),
                'low': Decimal('147.0'),
                'close': Decimal('151.0'),
                'volume': 1000000,
                'adj_close': Decimal('151.0')
            }
        ]
        
        service = PriceService(db_session)
        service.update_price_history(sample_security.id, date(2023, 1, 1), date(2023, 1, 1))
        
        # Check that price history was created
        price_history = db_session.query(PriceHistory).filter_by(
            security_id=sample_security.id,
            date=date(2023, 1, 1)
        ).first()
        
        assert price_history is not None
        assert price_history.close_price == Decimal('151.0')
        assert price_history.volume == 1000000
    
    def test_validate_symbol(self, db_session):
        """Test symbol validation."""
        service = PriceService(db_session)
        
        # Valid symbols
        assert service._validate_symbol('AAPL') is True
        assert service._validate_symbol('GOOGL') is True
        assert service._validate_symbol('BRK.B') is True
        
        # Invalid symbols
        assert service._validate_symbol('') is False
        assert service._validate_symbol(None) is False
        assert service._validate_symbol('TOOLONGSYMBOL') is False
    
    @patch('app.services.price_service.yf.Ticker')
    def test_retry_mechanism(self, mock_ticker, db_session):
        """Test retry mechanism for failed requests."""
        # Mock ticker to fail first two times, succeed third time
        mock_ticker_instance = Mock()
        mock_ticker_instance.info.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            {'regularMarketPrice': 150.50}
        ]
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('AAPL')
        
        assert price == Decimal('150.50')
        assert mock_ticker_instance.info.call_count == 3
    
    @patch('app.services.price_service.yf.Ticker')
    def test_currency_handling(self, mock_ticker, db_session):
        """Test currency handling in price data."""
        # Mock ticker with different currencies
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'regularMarketPrice': 45.30,
            'currency': 'EUR'
        }
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('SAP')
        
        assert price == Decimal('45.30')
    
    def test_decimal_precision(self, db_session):
        """Test decimal precision handling."""
        service = PriceService(db_session)
        
        # Test conversion from float to Decimal
        test_price = 123.456789
        decimal_price = service._to_decimal(test_price)
        
        assert isinstance(decimal_price, Decimal)
        assert decimal_price == Decimal('123.456789')
    
    @patch('app.services.price_service.yf.Ticker')
    def test_error_logging(self, mock_ticker, db_session):
        """Test error logging for failed requests."""
        mock_ticker.side_effect = Exception("Network timeout")
        
        service = PriceService(db_session)
        
        with patch('app.services.price_service.current_app.logger') as mock_logger:
            price = service.get_current_price('AAPL')
            
            assert price is None
            mock_logger.error.assert_called()
    
    def test_cache_invalidation(self, db_session):
        """Test price cache invalidation."""
        service = PriceService(db_session)
        
        # This would test caching mechanism if implemented
        # For now, just verify the service works without caching
        assert service is not None
    
    @patch('app.services.price_service.yf.download')
    def test_bulk_historical_update(self, mock_download, db_session):
        """Test bulk historical price updates."""
        import pandas as pd
        
        # Create multiple securities
        securities = []
        for i, symbol in enumerate(['AAPL', 'GOOGL', 'MSFT']):
            security = Security(
                symbol=symbol,
                name=f'Test Company {i}',
                currency='USD'
            )
            securities.append(security)
            db_session.add(security)
        db_session.commit()
        
        # Mock download for each symbol
        mock_data = pd.DataFrame({
            'Open': [148.0],
            'High': [152.0],
            'Low': [147.0],
            'Close': [151.0],
            'Volume': [1000000],
            'Adj Close': [151.0]
        }, index=pd.DatetimeIndex(['2023-01-01']))
        mock_download.return_value = mock_data
        
        service = PriceService(db_session)
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 1)
        
        # Update all securities
        for security in securities:
            service.update_price_history(security.id, start_date, end_date)
        
        # Verify price history was created for all
        price_histories = db_session.query(PriceHistory).all()
        assert len(price_histories) == 3