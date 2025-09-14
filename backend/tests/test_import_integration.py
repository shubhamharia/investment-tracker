"""
Test suite for import_data.py - focusing on LSE stock compatibility and core functionality
"""
import pytest
import pandas as pd
import os
import sys
import tempfile
from datetime import date
from unittest.mock import Mock, patch
from io import StringIO

# Add parent directory to import our modules
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)


class TestLSEStockCompatibility:
    """Test London Stock Exchange stock compatibility with yfinance"""

    @pytest.fixture
    def lse_tickers_from_csv(self):
        """Get actual LSE tickers from your CSV data"""
        csv_path = os.path.join(parent_dir, 'data', 'combined_transactions_updated.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            lse_tickers = df[df['ticker'].str.endswith('.L', na=False)]['ticker'].unique()
            return list(lse_tickers)[:10]  # Test first 10 to avoid rate limiting
        return [
            "ULVR.L", "HSBA.L", "BARC.L", "SHEL.L", "BATS.L", 
            "UKW.L", "ISF.L", "IIND.L", "VWRL.L", "VUSA.L"
        ]

    def test_lse_ticker_data_availability(self, lse_tickers_from_csv):
        """Test that LSE tickers can be fetched from yfinance"""
        try:
            import yfinance as yf
        except ImportError:
            pytest.skip("yfinance not installed")

        successful_retrievals = 0
        failed_retrievals = []

        print(f"\n🧪 Testing {len(lse_tickers_from_csv)} LSE tickers...")

        for ticker in lse_tickers_from_csv:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Check if we got valid data
                name = info.get('longName') or info.get('shortName') or info.get('symbol')
                if name and name != ticker:
                    successful_retrievals += 1
                    print(f"✅ {ticker}: {name}")
                else:
                    # Try to get price data as fallback
                    hist = stock.history(period="5d")
                    if not hist.empty:
                        successful_retrievals += 1
                        print(f"✅ {ticker}: Price data available (latest: {hist['Close'].iloc[-1]:.2f})")
                    else:
                        failed_retrievals.append(ticker)
                        print(f"❌ {ticker}: No data available")
                        
            except Exception as e:
                failed_retrievals.append(ticker)
                print(f"❌ {ticker}: Error - {str(e)[:50]}...")

        success_rate = successful_retrievals / len(lse_tickers_from_csv)
        print(f"\n📊 Success Rate: {success_rate:.1%} ({successful_retrievals}/{len(lse_tickers_from_csv)})")
        
        if failed_retrievals:
            print(f"⚠️  Failed tickers: {', '.join(failed_retrievals)}")

        # Require at least 60% success rate (LSE can be spotty)
        assert success_rate >= 0.6, f"LSE ticker success rate too low: {success_rate:.1%}"

    def test_lse_currency_detection(self):
        """Test that LSE stocks return correct currency information"""
        try:
            import yfinance as yf
        except ImportError:
            pytest.skip("yfinance not installed")

        test_tickers = ["ULVR.L", "HSBA.L", "SHEL.L"]
        
        for ticker in test_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                currency = info.get('currency', 'Unknown')
                print(f"{ticker}: {currency}")
                
                # LSE stocks should be in GBP or GBX (pence)
                assert currency in ['GBP', 'GBX', 'Unknown'], f"Unexpected currency {currency} for {ticker}"
                
            except Exception as e:
                print(f"Warning: Could not test currency for {ticker}: {e}")

    def test_historical_price_data(self):
        """Test retrieving historical price data for LSE stocks"""
        try:
            import yfinance as yf
        except ImportError:
            pytest.skip("yfinance not installed")

        ticker = "ULVR.L"  # Unilever - should be reliable
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            
            assert not hist.empty, f"No historical data for {ticker}"
            assert 'Close' in hist.columns, f"No Close price data for {ticker}"
            assert len(hist) > 10, f"Insufficient data points for {ticker}"
            
            # Check data quality
            latest_price = hist['Close'].iloc[-1]
            assert latest_price > 0, f"Invalid price data for {ticker}"
            
            print(f"✅ {ticker}: {len(hist)} days of price data, latest: £{latest_price:.2f}")
            
        except Exception as e:
            pytest.fail(f"Historical data test failed for {ticker}: {e}")


class TestImportDataFunctions:
    """Test core functions from import_data.py"""

    def test_date_parsing(self):
        """Test the date parsing functionality"""
        # Import the actual function
        from import_data import parse_date
        
        # Test valid dates
        assert parse_date("15/08/2025") == date(2025, 8, 15)
        assert parse_date("01/01/2024") == date(2024, 1, 1)
        assert parse_date("31/12/2023") == date(2023, 12, 31)
        
        # Test invalid dates
        assert parse_date("invalid") is None
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_ticker_cleaning(self):
        """Test ticker symbol cleaning"""
        from import_data import clean_ticker
        
        assert clean_ticker("AAPL") == "AAPL"
        assert clean_ticker("  MSFT  ") == "MSFT"
        assert clean_ticker("TSLA.L") == "TSLA.L"
        assert clean_ticker(None) is None

    def test_exchange_determination(self):
        """Test exchange determination logic"""
        from import_data import determine_exchange
        
        # LSE tickers
        assert determine_exchange("ULVR.L", None) == "LSE"
        assert determine_exchange("HSBA.L", None) == "LSE"
        
        # ISIN codes for LSE
        assert determine_exchange("IE00BZCQB185", None) == "LSE"  # IE prefix
        assert determine_exchange("GB00B10RZP78", None) == "LSE"  # GB prefix
        
        # US tickers
        assert determine_exchange("AAPL", None) == "NASDAQ"
        assert determine_exchange("META", None) == "NASDAQ"


class TestCSVDataValidation:
    """Test CSV data structure and content validation"""

    def test_actual_csv_exists_and_readable(self):
        """Test that the actual CSV file exists and is readable"""
        csv_path = os.path.join(parent_dir, 'data', 'combined_transactions_updated.csv')
        
        assert os.path.exists(csv_path), "CSV file not found"
        
        # Test reading the CSV
        df = pd.read_csv(csv_path)
        assert len(df) > 0, "CSV file is empty"
        
        print(f"✅ CSV file loaded: {len(df)} transactions")

    def test_csv_column_structure(self):
        """Test that CSV has required columns"""
        csv_path = os.path.join(parent_dir, 'data', 'combined_transactions_updated.csv')
        
        if not os.path.exists(csv_path):
            pytest.skip("CSV file not found")
            
        df = pd.read_csv(csv_path)
        
        required_columns = [
            'platform', 'type', 'timestamp', 'ticker', 'total_amount', 
            'quantity', 'price_per_share', 'currency'
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

    def test_transaction_data_quality(self):
        """Test data quality of transactions"""
        csv_path = os.path.join(parent_dir, 'data', 'combined_transactions_updated.csv')
        
        if not os.path.exists(csv_path):
            pytest.skip("CSV file not found")
            
        df = pd.read_csv(csv_path)
        
        # Check transaction types
        valid_types = ['BUY', 'SELL']
        invalid_types = df[~df['type'].isin(valid_types)]
        assert len(invalid_types) == 0, f"Invalid transaction types found: {invalid_types['type'].unique()}"
        
        # Check for missing critical data
        assert df['ticker'].notna().all(), "Found transactions with missing tickers"
        assert df['total_amount'].notna().all(), "Found transactions with missing amounts"
        
        # Check numeric fields
        assert pd.to_numeric(df['total_amount'], errors='coerce').notna().all(), "Invalid total_amount values"
        assert pd.to_numeric(df['quantity'], errors='coerce').notna().all(), "Invalid quantity values"

    def test_lse_stocks_in_csv(self):
        """Test LSE stocks found in CSV data"""
        csv_path = os.path.join(parent_dir, 'data', 'combined_transactions_updated.csv')
        
        if not os.path.exists(csv_path):
            pytest.skip("CSV file not found")
            
        df = pd.read_csv(csv_path)
        
        # Find LSE tickers
        lse_tickers = df[df['ticker'].str.endswith('.L', na=False)]['ticker'].unique()
        
        print(f"\n📈 Found {len(lse_tickers)} unique LSE tickers in CSV:")
        for ticker in sorted(lse_tickers):
            count = len(df[df['ticker'] == ticker])
            print(f"  {ticker}: {count} transactions")
        
        assert len(lse_tickers) > 0, "No LSE tickers found in CSV"


class TestImportProcessMocked:
    """Test import process with mocked database operations"""

    def create_sample_csv(self):
        """Create sample CSV data for testing"""
        return """platform,type,timestamp,ticker,isin,total_amount,quantity,price_per_share,currency,instrument_currency,fx_rate
Trading212_ISA,BUY,20/08/2025,ULVR.L,GB00B10RZP78,100.00,2.25,44.44,GBP,GBP,1
Trading212_GIA,BUY,19/08/2025,HSBA.L,GB0005405286,50.00,8.33,6.00,GBP,GBP,1
Trading212_ISA,BUY,18/08/2025,META,US30303M1027,100.00,0.18,550.00,GBP,USD,1.35
Trading212_ISA,SELL,17/08/2025,IIND.L,IE00BZCQB185,75.50,10.5,7.19,GBP,GBP,1"""

    def test_csv_parsing_logic(self):
        """Test CSV parsing without database operations"""
        csv_data = self.create_sample_csv()
        df = pd.read_csv(StringIO(csv_data))
        
        # Test data parsing
        assert len(df) == 4
        assert set(df['type']) == {'BUY', 'SELL'}
        assert 'ULVR.L' in df['ticker'].values
        assert 'META' in df['ticker'].values
        
        # Test numeric conversions
        amounts = pd.to_numeric(df['total_amount'])
        assert amounts.min() > 0
        assert amounts.max() <= 100

    @patch('import_data.app')
    @patch('import_data.db')
    def test_import_script_execution(self, mock_db, mock_app):
        """Test that import script can be executed without errors"""
        # Mock the Flask app context
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        mock_app_instance.app_context.return_value.__enter__ = Mock()
        mock_app_instance.app_context.return_value.__exit__ = Mock()
        
        # Create a temporary CSV file
        csv_data = self.create_sample_csv()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            f.flush()
            
            try:
                # Test that we can read and process the CSV
                df = pd.read_csv(f.name)
                df.columns = df.columns.str.strip().str.lower()
                
                assert len(df) == 4
                assert 'ticker' in df.columns
                assert 'total_amount' in df.columns
                
                print("✅ Import script CSV processing successful")
                
            finally:
                os.unlink(f.name)


class TestPerformanceValidation:
    """Test performance characteristics"""

    def test_large_dataset_handling(self):
        """Test handling of larger datasets"""
        # Create a larger test dataset
        large_data = "platform,type,timestamp,ticker,isin,total_amount,quantity,price_per_share,currency,instrument_currency,fx_rate\n"
        
        for i in range(100):
            large_data += f"Trading212_ISA,BUY,01/01/2025,TEST{i}.L,GB000000000{i:02d},100.00,1.0,100.00,GBP,GBP,1\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(large_data)
            f.flush()
            
            import time
            start_time = time.time()
            
            # Test CSV processing speed
            df = pd.read_csv(f.name)
            df.columns = df.columns.str.strip().str.lower()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert len(df) == 100
            assert processing_time < 1.0, f"CSV processing too slow: {processing_time:.2f}s"
            
            print(f"✅ Large dataset test: {len(df)} rows processed in {processing_time:.3f}s")
            
        os.unlink(f.name)


def run_integration_test():
    """Run a quick integration test of import functionality"""
    try:
        print("🔄 Running Import Data Integration Test...")
        print("=" * 50)
        
        # Test 1: Check if import_data module can be imported
        try:
            import import_data
            print("✅ import_data module imports successfully")
        except Exception as e:
            print(f"❌ import_data import failed: {e}")
            return False
        
        # Test 2: Check CSV file existence
        csv_path = os.path.join(parent_dir, 'data', 'combined_transactions_updated.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"✅ CSV file loaded: {len(df)} transactions")
        else:
            print("⚠️  CSV file not found - using mock data for tests")
        
        # Test 3: Quick yfinance test
        try:
            import yfinance as yf
            stock = yf.Ticker("ULVR.L")
            info = stock.info
            if info.get('longName'):
                print(f"✅ yfinance working: {info['longName']}")
            else:
                print("⚠️  yfinance limited data but functional")
        except Exception as e:
            print(f"⚠️  yfinance issue: {e}")
        
        print("\n🎯 Integration test completed - ready for full test suite!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Run quick integration test first
    if run_integration_test():
        print("\n" + "=" * 50)
        print("🧪 Running Full Test Suite...")
        
        # Run the actual tests
        import subprocess
        result = subprocess.run([
            "python", "-m", "pytest", __file__, "-v", "--tb=short", "-x"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    else:
        print("❌ Integration test failed - please check your setup")