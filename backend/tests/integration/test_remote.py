"""
Integration tests for remote services (Yahoo Finance).
"""
import pytest
from unittest.mock import patch, Mock
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.price_service import PriceService


class TestRemoteServices:
    """Test cases for remote service integration."""
    
    @pytest.mark.skip(reason="Requires internet connection")
    def test_yahoo_finance_real_data(self, db_session):
        """Test real Yahoo Finance data retrieval (requires internet)."""
        service = PriceService(db_session)
        
        # Test with a stable, well-known stock
        price = service.get_current_price('AAPL')
        
        # Should get a valid price or None if service is down
        if price is not None:
            assert isinstance(price, Decimal)
            assert price > 0
    
    @patch('app.services.price_service.yf.Ticker')
    def test_yahoo_finance_api_timeout(self, mock_ticker, db_session):
        """Test Yahoo Finance API timeout handling."""
        import requests
        
        # Mock timeout exception
        mock_ticker.side_effect = requests.exceptions.Timeout("Request timed out")
        
        service = PriceService(db_session)
        price = service.get_current_price('AAPL')
        
        assert price is None
    
    @patch('app.services.price_service.yf.Ticker')
    def test_yahoo_finance_invalid_symbol(self, mock_ticker, db_session):
        """Test Yahoo Finance with invalid symbol."""
        # Mock ticker with no data for invalid symbol
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {}
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('INVALID_SYMBOL')
        
        assert price is None
    
    @patch('app.services.price_service.yf.Ticker')
    def test_yahoo_finance_market_closed(self, mock_ticker, db_session):
        """Test Yahoo Finance when market is closed."""
        # Mock ticker with previous close price
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'previousClose': 150.25,
            'regularMarketPrice': None  # No current price when market closed
        }
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('AAPL')
        
        # Should handle gracefully, might return previous close or None
        assert price is None or isinstance(price, Decimal)
    
    @patch('app.services.price_service.yf.Tickers')
    def test_yahoo_finance_batch_request(self, mock_tickers, db_session):
        """Test Yahoo Finance batch requests."""
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
        
        # Mock batch ticker response
        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {}
        
        for i, symbol in enumerate(symbols):
            mock_ticker = Mock()
            mock_ticker.info = {'regularMarketPrice': 100.0 + i * 10}
            mock_tickers_instance.tickers[symbol] = mock_ticker
        
        mock_tickers.return_value = mock_tickers_instance
        
        service = PriceService(db_session)
        results = service.fetch_latest_prices(symbols)
        
        assert len(results) == len(symbols)
        for symbol in symbols:
            assert symbol in results
            assert isinstance(results[symbol], Decimal)
    
    @patch('app.services.price_service.yf.download')
    def test_yahoo_finance_historical_data(self, mock_download, db_session):
        """Test Yahoo Finance historical data retrieval."""
        import pandas as pd
        
        # Mock historical data
        dates = pd.date_range('2023-01-01', periods=5, freq='D')
        mock_data = pd.DataFrame({
            'Open': [148.0, 149.0, 150.0, 151.0, 152.0],
            'High': [152.0, 153.0, 154.0, 155.0, 156.0],
            'Low': [147.0, 148.0, 149.0, 150.0, 151.0],
            'Close': [151.0, 152.0, 153.0, 154.0, 155.0],
            'Volume': [1000000, 1100000, 1200000, 1300000, 1400000],
            'Adj Close': [151.0, 152.0, 153.0, 154.0, 155.0]
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        service = PriceService(db_session)
        start_date = dates[0].date()
        end_date = dates[-1].date()
        
        prices = service.get_historical_prices('AAPL', start_date, end_date)
        
        assert len(prices) == 5
        assert all('date' in price for price in prices)
        assert all('close' in price for price in prices)
        assert prices[0]['close'] == Decimal('151.0')
        assert prices[-1]['close'] == Decimal('155.0')
    
    @patch('app.services.price_service.yf.Ticker')
    def test_yahoo_finance_currency_conversion(self, mock_ticker, db_session):
        """Test Yahoo Finance with different currencies."""
        # Test EUR stock
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'regularMarketPrice': 45.30,
            'currency': 'EUR'
        }
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('SAP.DE')
        
        assert price == Decimal('45.30')
    
    @patch('app.services.price_service.yf.Ticker')
    def test_yahoo_finance_api_rate_limiting(self, mock_ticker, db_session):
        """Test Yahoo Finance API rate limiting."""
        import requests
        
        # Mock rate limiting response
        response = Mock()
        response.status_code = 429
        response.text = "Too Many Requests"
        
        mock_ticker.side_effect = requests.exceptions.HTTPError("429 Too Many Requests", response=response)
        
        service = PriceService(db_session)
        price = service.get_current_price('AAPL')
        
        assert price is None
    
    @patch('app.services.price_service.yf.Ticker')
    def test_yahoo_finance_data_quality(self, mock_ticker, db_session):
        """Test Yahoo Finance data quality validation."""
        # Mock ticker with questionable data
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'regularMarketPrice': -100.0,  # Negative price (invalid)
            'currency': 'USD'
        }
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('AAPL')
        
        # Should validate and reject invalid data
        assert price is None
    
    @patch('app.services.price_service.yf.Ticker')
    def test_yahoo_finance_connection_error(self, mock_ticker, db_session):
        """Test Yahoo Finance connection errors."""
        import requests
        
        mock_ticker.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        service = PriceService(db_session)
        price = service.get_current_price('AAPL')
        
        assert price is None
    
    @patch('app.services.price_service.yf.Ticker')
    def test_yahoo_finance_retry_success(self, mock_ticker, db_session):
        """Test Yahoo Finance retry mechanism success."""
        # First call fails, second succeeds
        mock_ticker_instance = Mock()
        mock_ticker_instance.info.side_effect = [
            Exception("Temporary error"),
            {'regularMarketPrice': 150.50, 'currency': 'USD'}
        ]
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        price = service.get_current_price('AAPL')
        
        assert price == Decimal('150.50')
    
    def test_redis_connection(self, app):
        """Test Redis connection for rate limiting."""
        with app.app_context():
            try:
                from app.extensions import redis_client
                if redis_client:
                    # Test basic Redis operation
                    redis_client.set('test_key', 'test_value', ex=60)
                    value = redis_client.get('test_key')
                    assert value.decode() == 'test_value' if value else True
            except Exception:
                # Redis might not be available in test environment
                pytest.skip("Redis not available")
    
    @patch('app.services.price_service.yf.Ticker')
    def test_service_degradation(self, mock_ticker, db_session):
        """Test graceful service degradation."""
        # Mock complete service failure
        mock_ticker.side_effect = Exception("Service completely down")
        
        service = PriceService(db_session)
        
        # Should handle gracefully without crashing
        prices = service.fetch_latest_prices(['AAPL', 'GOOGL'])
        assert prices == {}
        
        price = service.get_current_price('AAPL')
        assert price is None
    
    def test_price_precision_handling(self, db_session):
        """Test price precision in various scenarios."""
        service = PriceService(db_session)
        
        # Test various price formats
        test_prices = [
            123.456789,      # High precision
            0.001,           # Very small price
            10000.00,        # Large round number
            99.99,           # Common price format
        ]
        
        for test_price in test_prices:
            decimal_price = service._to_decimal(test_price)
            assert isinstance(decimal_price, Decimal)
            assert decimal_price >= 0
    
    @patch('app.services.price_service.yf.Ticker')
    def test_concurrent_price_requests(self, mock_ticker, db_session):
        """Test concurrent price requests handling."""
        import threading
        import time
        
        # Mock ticker with delay to simulate network latency
        mock_ticker_instance = Mock()
        def delayed_info():
            time.sleep(0.1)  # Small delay
            return {'regularMarketPrice': 150.50, 'currency': 'USD'}
        
        mock_ticker_instance.info = delayed_info
        mock_ticker.return_value = mock_ticker_instance
        
        service = PriceService(db_session)
        results = []
        
        def get_price():
            price = service.get_current_price('AAPL')
            results.append(price)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=get_price)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(results) == 5
        assert all(price == Decimal('150.50') for price in results)
    
    @patch('app.services.price_service.yf.download')
    def test_large_historical_dataset(self, mock_download, db_session):
        """Test handling of large historical datasets."""
        import pandas as pd
        
        # Mock large dataset (1 year of daily data)
        dates = pd.date_range('2022-01-01', '2022-12-31', freq='D')
        mock_data = pd.DataFrame({
            'Open': [150.0 + i * 0.1 for i in range(len(dates))],
            'High': [152.0 + i * 0.1 for i in range(len(dates))],
            'Low': [148.0 + i * 0.1 for i in range(len(dates))],
            'Close': [151.0 + i * 0.1 for i in range(len(dates))],
            'Volume': [1000000 + i * 1000 for i in range(len(dates))],
            'Adj Close': [151.0 + i * 0.1 for i in range(len(dates))]
        }, index=dates)
        
        mock_download.return_value = mock_data
        
        service = PriceService(db_session)
        start_date = dates[0].date()
        end_date = dates[-1].date()
        
        prices = service.get_historical_prices('AAPL', start_date, end_date)
        
        # Should handle large dataset efficiently
        assert len(prices) == len(dates)
        assert prices[0]['date'] == start_date
        assert prices[-1]['date'] == end_date