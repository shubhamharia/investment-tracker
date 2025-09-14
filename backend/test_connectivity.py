#!/usr/bin/env python3
"""
Connectivity test script for Yahoo Finance and network diagnostics.
"""

import requests
import yfinance as yf
import time
from datetime import datetime

def test_basic_connectivity():
    """Test basic internet connectivity"""
    print("=== Testing Basic Connectivity ===")
    try:
        response = requests.get("https://httpbin.org/status/200", timeout=10)
        print(f"✅ Basic HTTP connectivity: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        return False

def test_yahoo_finance_api():
    """Test Yahoo Finance API connectivity"""
    print("\n=== Testing Yahoo Finance API ===")
    try:
        # Test the API endpoint directly
        test_url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL"
        response = requests.get(test_url, timeout=10)
        print(f"✅ Yahoo Finance API: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Yahoo Finance API failed: {e}")
        return False

def test_yfinance_library():
    """Test yfinance library with multiple symbols"""
    print("\n=== Testing yfinance Library ===")
    test_symbols = ["AAPL", "MSFT", "NVDA", "ULVR.L", "HSBA.L"]
    
    for symbol in test_symbols:
        try:
            print(f"Testing {symbol}...")
            ticker = yf.Ticker(symbol)
            
            # Configure session with proper headers
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            ticker._session = session
            
            hist = ticker.history(period="1d", timeout=15)
            
            if not hist.empty:
                latest = hist.iloc[-1]
                print(f"✅ {symbol}: ${latest['Close']:.2f}")
            else:
                print(f"⚠️  {symbol}: No data returned")
                
        except Exception as e:
            print(f"❌ {symbol}: {e}")
        
        time.sleep(1)  # Rate limiting

def test_network_settings():
    """Test network configuration and DNS"""
    print("\n=== Network Configuration ===")
    
    # Test DNS resolution
    try:
        import socket
        ip = socket.gethostbyname("finance.yahoo.com")
        print(f"✅ DNS resolution for finance.yahoo.com: {ip}")
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
    
    # Test connectivity to various endpoints
    endpoints = [
        "https://finance.yahoo.com",
        "https://query1.finance.yahoo.com",
        "https://query2.finance.yahoo.com"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.head(endpoint, timeout=10)
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def main():
    """Run all connectivity tests"""
    print("Yahoo Finance Connectivity Test")
    print("=" * 40)
    print(f"Timestamp: {datetime.now()}")
    
    # Run all tests
    basic_ok = test_basic_connectivity()
    api_ok = test_yahoo_finance_api()
    test_yfinance_library()
    test_network_settings()
    
    print("\n=== Summary ===")
    if basic_ok and api_ok:
        print("✅ Connectivity tests passed")
        exit(0)
    else:
        print("❌ Some connectivity tests failed")
        exit(1)

if __name__ == "__main__":
    main()