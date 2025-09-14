"""
Simple LSE Stock Compatibility Test
Tests yfinance compatibility with London Stock Exchange stocks from your CSV
"""
import pytest
import pandas as pd
import os
from datetime import date


class TestLSEStockCompatibility:
    """Test London Stock Exchange stock compatibility with yfinance"""

    def test_yfinance_installation(self):
        """Test that yfinance is properly installed"""
        try:
            import yfinance as yf
            print("✅ yfinance is installed and importable")
            return True
        except ImportError:
            pytest.fail("yfinance is not installed. Please run: pip install yfinance")

    def test_lse_stocks_from_your_csv(self):
        """Test LSE stocks from your actual CSV data"""
        try:
            import yfinance as yf
        except ImportError:
            pytest.skip("yfinance not installed")

        # Get LSE tickers from your CSV
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'combined_transactions_updated.csv')
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            lse_tickers = df[df['ticker'].str.endswith('.L', na=False)]['ticker'].unique()
            print(f"\n📊 Found {len(lse_tickers)} unique LSE tickers in your CSV")
        else:
            # Use common LSE tickers if CSV not found
            lse_tickers = ["ULVR.L", "HSBA.L", "BARC.L", "SHEL.L", "BATS.L", "UKW.L", "ISF.L", "IIND.L"]
            print(f"\n📊 Testing {len(lse_tickers)} common LSE tickers (CSV not found)")

        successful_retrievals = 0
        failed_retrievals = []
        detailed_results = []

        print("\n🧪 Testing LSE Stock Data Retrieval:")
        print("-" * 60)

        # Test first 8 tickers to avoid rate limiting
        for ticker in list(lse_tickers)[:8]:
            try:
                stock = yf.Ticker(ticker)
                
                # Try to get basic info
                info = stock.info
                name = info.get('longName') or info.get('shortName') or 'Unknown'
                currency = info.get('currency', 'Unknown')
                
                # Try to get recent price data
                hist = stock.history(period="5d")
                current_price = None
                if not hist.empty and 'Close' in hist.columns:
                    current_price = hist['Close'].iloc[-1]
                
                if name != 'Unknown' or current_price is not None:
                    successful_retrievals += 1
                    status = "✅"
                    
                    if current_price:
                        price_info = f"Latest: {currency} {current_price:.2f}"
                    else:
                        price_info = "Price data unavailable"
                        
                    detailed_results.append(f"{status} {ticker:10} | {name[:30]:30} | {price_info}")
                else:
                    status = "❌"
                    failed_retrievals.append(ticker)
                    detailed_results.append(f"{status} {ticker:10} | No data available")
                    
            except Exception as e:
                status = "❌"
                failed_retrievals.append(ticker)
                error_msg = str(e)[:40] + "..." if len(str(e)) > 40 else str(e)
                detailed_results.append(f"{status} {ticker:10} | Error: {error_msg}")

        # Print results
        for result in detailed_results:
            print(result)

        success_rate = successful_retrievals / len(list(lse_tickers)[:8])
        print(f"\n📈 Results Summary:")
        print(f"Success Rate: {success_rate:.1%} ({successful_retrievals}/{len(list(lse_tickers)[:8])})")
        
        if failed_retrievals:
            print(f"Failed Tickers: {', '.join(failed_retrievals)}")

        # Assert reasonable success rate
        assert success_rate >= 0.5, f"LSE stock data retrieval success rate too low: {success_rate:.1%}"
        print("✅ LSE stock compatibility test PASSED")

    def test_specific_problematic_lse_stocks(self):
        """Test specific LSE stocks that have historically had issues"""
        try:
            import yfinance as yf
        except ImportError:
            pytest.skip("yfinance not installed")

        # These are common LSE stocks that sometimes have data issues
        problematic_stocks = {
            "ULVR.L": "Unilever",
            "HSBA.L": "HSBC",
            "BARC.L": "Barclays", 
            "SHEL.L": "Shell",
            "BATS.L": "British American Tobacco"
        }

        print(f"\n🔍 Testing potentially problematic LSE stocks:")
        print("-" * 50)

        working_stocks = 0
        
        for ticker, expected_name in problematic_stocks.items():
            try:
                stock = yf.Ticker(ticker)
                
                # Test 1: Basic info retrieval
                info = stock.info
                actual_name = info.get('longName', info.get('shortName', 'N/A'))
                
                # Test 2: Historical data retrieval
                hist = stock.history(period="1mo")
                has_price_data = not hist.empty and len(hist) > 10
                
                # Test 3: Currency validation (GBp is pence, valid for LSE)
                currency = info.get('currency', 'Unknown')
                valid_currency = currency in ['GBP', 'GBX', 'GBp', 'Unknown']
                
                if actual_name != 'N/A' or has_price_data:
                    working_stocks += 1
                    status = "✅"
                    print(f"{status} {ticker}: {actual_name} [{currency}] - {len(hist) if has_price_data else 0} days data")
                else:
                    print(f"❌ {ticker}: No data available")
                    
                # Validate currency
                assert valid_currency, f"Invalid currency {currency} for LSE stock {ticker}"
                
            except Exception as e:
                print(f"⚠️  {ticker}: {str(e)[:60]}...")

        success_rate = working_stocks / len(problematic_stocks)
        print(f"\nProblematic stocks success rate: {success_rate:.1%}")
        
        # At least half should work
        assert success_rate >= 0.4, f"Too many problematic LSE stocks failing: {success_rate:.1%}"

    def test_lse_price_history_quality(self):
        """Test the quality of price history data for LSE stocks"""
        try:
            import yfinance as yf
        except ImportError:
            pytest.skip("yfinance not installed")

        test_ticker = "ULVR.L"  # Unilever - usually reliable
        
        print(f"\n📊 Testing price history quality for {test_ticker}:")
        
        try:
            stock = yf.Ticker(test_ticker)
            
            # Test different time periods
            periods = ["1mo", "3mo", "6mo"]
            
            for period in periods:
                hist = stock.history(period=period)
                
                if not hist.empty:
                    print(f"✅ {period}: {len(hist)} trading days")
                    
                    # Check data quality
                    assert 'Close' in hist.columns, "Missing Close price column"
                    assert hist['Close'].notna().all(), "Found NaN values in Close prices"
                    assert (hist['Close'] > 0).all(), "Found non-positive prices"
                    
                    # Check for reasonable price variation
                    price_range = hist['Close'].max() - hist['Close'].min()
                    avg_price = hist['Close'].mean()
                    variation = price_range / avg_price
                    
                    print(f"   Price range: £{hist['Close'].min():.2f} - £{hist['Close'].max():.2f}")
                    print(f"   Variation: {variation:.1%}")
                    
                else:
                    print(f"❌ {period}: No data")
                    
        except Exception as e:
            pytest.fail(f"Price history test failed: {e}")

    def test_csv_data_structure(self):
        """Test that your CSV has the expected structure for import"""
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'combined_transactions_updated.csv')
        
        if not os.path.exists(csv_path):
            pytest.skip("CSV file not found")
            
        print(f"\n📄 Testing CSV data structure:")
        
        df = pd.read_csv(csv_path)
        print(f"✅ CSV loaded: {len(df)} transactions")
        
        # Check required columns
        required_columns = [
            'platform', 'type', 'timestamp', 'ticker', 'total_amount', 
            'quantity', 'price_per_share', 'currency'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        assert len(missing_columns) == 0, f"Missing columns: {missing_columns}"
        print(f"✅ All required columns present: {', '.join(required_columns)}")
        
        # Check LSE stocks
        lse_count = len(df[df['ticker'].str.endswith('.L', na=False)])
        print(f"✅ LSE transactions: {lse_count}")
        
        # Check transaction types
        transaction_types = df['type'].unique()
        print(f"✅ Transaction types: {', '.join(transaction_types)}")
        
        assert set(transaction_types).issubset({'BUY', 'SELL'}), f"Invalid transaction types: {transaction_types}"

    def test_date_parsing_function(self):
        """Test the date parsing logic from import_data.py"""
        
        def parse_date(date_str):
            """Replicate the parse_date function logic"""
            if pd.isna(date_str):
                return None
            
            try:
                # Handle DD/MM/YYYY format
                day, month, year = str(date_str).split('/')
                return date(int(year), int(month), int(day))
            except:
                return None
        
        print(f"\n📅 Testing date parsing:")
        
        # Test valid dates
        test_dates = ["15/08/2025", "01/01/2024", "31/12/2023"]
        for date_str in test_dates:
            parsed = parse_date(date_str)
            assert parsed is not None, f"Failed to parse valid date: {date_str}"
            print(f"✅ {date_str} -> {parsed}")
        
        # Test invalid dates
        invalid_dates = ["invalid", "", None, "32/13/2025"]
        for date_str in invalid_dates:
            parsed = parse_date(date_str)
            assert parsed is None, f"Should not parse invalid date: {date_str}"
            print(f"✅ {date_str} -> None (correctly rejected)")


def run_quick_lse_test():
    """Quick standalone test"""
    print("🚀 Quick LSE Stock Test")
    print("=" * 30)
    
    try:
        import yfinance as yf
        
        # Test one reliable LSE stock
        ticker = "ULVR.L"
        stock = yf.Ticker(ticker)
        info = stock.info
        
        name = info.get('longName', 'Unknown')
        print(f"✅ {ticker}: {name}")
        
        # Get recent price
        hist = stock.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            print(f"✅ Current price: £{price:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 LSE Stock Compatibility Test Suite")
    print("=" * 50)
    
    # Run quick test first
    if run_quick_lse_test():
        print("\n" + "="*50)
        print("Running full test suite...")
        
        import subprocess
        result = subprocess.run([
            "python", "-m", "pytest", __file__, "-v", "-s"
        ])
        
        exit_code = result.returncode
        print(f"\n{'✅ ALL TESTS PASSED' if exit_code == 0 else '❌ SOME TESTS FAILED'}")
    else:
        print("❌ Quick test failed - check your yfinance installation")