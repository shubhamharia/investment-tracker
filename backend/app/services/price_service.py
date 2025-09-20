import os
import time
import yfinance as yf
from datetime import datetime, timedelta
from decimal import Decimal
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
from ..models import Security, PriceHistory, Holding
from ..extensions import db
import pandas as pd
import logging
import requests
from flask import current_app

class PriceService:
    def __init__(self, db_session=None):
        """Compatibility PriceService used by tests.

        Accepts an optional SQLAlchemy session (db_session) used by unit tests.
        """
        self.db_session = db_session
        self.debug = os.environ.get("DEBUG_YAHOO") == "1"
        self.timeout = int(os.environ.get("YAHOO_API_TIMEOUT", "10"))
        self._max_retries = int(os.environ.get("YAHOO_MAX_RETRIES", "3"))
        self._initial_backoff = float(os.environ.get("YAHOO_INITIAL_BACKOFF", "2.0"))
        self._backoff_delay = self._initial_backoff

        if self.debug:
            logging.info(f"PriceService initialized with timeout={self.timeout}s, max_retries={self._max_retries}")

    def _debug_log(self, msg, *args):
        """Log debug information if debug mode is enabled"""
        print(f"[Yahoo Finance] {msg}")  # Always print
        if self.debug:
            logging.info(f"[Yahoo Finance] {msg}", *args)

    def _to_decimal(self, v):
        if v is None:
            return None
        return Decimal(str(v))

    def _validate_symbol(self, symbol: str) -> bool:
        if not symbol or not isinstance(symbol, str):
            return False
        # Allow dots (e.g. BRK.B); enforce a reasonable maximum length
        return len(symbol) <= 10

    def _increase_backoff(self):
        """Increase the backoff delay exponentially"""
        self._backoff_delay *= 2  # Exponential backoff
        max_backoff = float(os.environ.get("YAHOO_MAX_BACKOFF", "60.0"))
        self._backoff_delay = min(self._backoff_delay, max_backoff)
        if self.debug:
            self._debug_log(f"Increased backoff delay to {self._backoff_delay}s")

    def _test_network_connectivity(self):
        """Test basic network connectivity"""
        try:
            # Test basic internet connectivity
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            self._debug_log(f"Network test: HTTP {response.status_code}")
            return True
        except Exception as e:
            self._debug_log(f"Network connectivity issue: {e}")
            return False

    def _test_yahoo_finance_connectivity(self):
        """Test Yahoo Finance specific connectivity"""
        try:
            # Test Yahoo Finance API endpoint
            test_url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL"
            response = requests.get(test_url, timeout=10)
            self._debug_log(f"Yahoo Finance test: HTTP {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self._debug_log(f"Yahoo Finance connectivity issue: {e}")
            return False

    def get_current_price(self, security):
        """
        Get current price for a single security with retry mechanism.

        Args:
            security: The security to fetch price for

        Returns:
            The current price

        Raises:
            RequestException: On network errors after all retries exhausted
            ValueError: On invalid data format
            HTTPError: On API errors (including rate limits)
            Timeout: On request timeout
        """
        # Tests expect this method to accept a symbol string (e.g. 'AAPL') or a Security object
        symbol = None
        if isinstance(security, Security):
            symbol = getattr(security, 'symbol', None) or getattr(security, 'yahoo_symbol', None)
        else:
            symbol = security

        if not self._validate_symbol(symbol):
            return None

        attempts = 0
        last_error = None

        while attempts < self._max_retries:
            try:
                ticker = yf.Ticker(symbol)

                # Some tests mock ticker.info as callable (side_effect list) and sometimes as dict.
                info_attr = getattr(ticker, 'info', None)
                try:
                    info = info_attr() if callable(info_attr) else info_attr
                except Exception as e:
                    # If the mock raised an exception, propagate to retry loop
                    raise

                if not info or 'regularMarketPrice' not in info:
                    return None

                price = info.get('regularMarketPrice')
                if price is None:
                    return None
                # Validate numeric price and reject invalid values (e.g., negative prices)
                try:
                    dec_price = self._to_decimal(price)
                except Exception:
                    return None

                if dec_price is None:
                    return None

                # Reject non-positive prices
                try:
                    if dec_price <= 0:
                        return None
                except Exception:
                    return None

                self._backoff_delay = self._initial_backoff
                return dec_price

            except Exception as e:
                last_error = e
                attempts += 1
                time.sleep(self._backoff_delay)

        # exhausted retries
        current_app.logger.error(f"Price fetch failed for {symbol}: {last_error}")
        return None

    def fetch_latest_prices(self, securities, max_time=30):
        """Fetch latest prices for multiple securities.

        Args:
            securities: A single Security object or a list of Security objects
            max_time: Maximum time in seconds to spend on the entire batch

        Returns:
            A single PriceHistory object for a single security input,
            or a list of PriceHistory objects if a list was provided
        """
        # Tests expect a simple dict mapping symbol->Decimal price when given a list of symbols
        single_security = not isinstance(securities, list)
        input_symbols = [securities] if single_security else securities

        results = {}

        # Prefer using yf.Tickers when available (tests patch this)
        try:
            tickers_obj = yf.Tickers(' '.join(input_symbols))
            tickers_map = getattr(tickers_obj, 'tickers', {}) or {}
            for sym, tk in tickers_map.items():
                info_attr = getattr(tk, 'info', None)
                try:
                    info = info_attr() if callable(info_attr) else info_attr
                except Exception:
                    info = None

                if info and info.get('regularMarketPrice') is not None:
                    try:
                        p = self._to_decimal(info.get('regularMarketPrice'))
                        if p is not None and p > 0:
                            results[sym] = p
                    except Exception:
                        pass

            # Fallback: if tickers didn't contain some symbols, query them individually
            for sym in input_symbols:
                if sym not in results:
                    price = self.get_current_price(sym)
                    if price is not None:
                        results[sym] = price

        except Exception:
            # On any failure, fallback to per-symbol lookups
            for sym in input_symbols:
                price = self.get_current_price(sym)
                if price is not None:
                    results[sym] = price

        return results if not single_security else results.get(input_symbols[0])

    def get_historical_prices(self, symbol, start_date, end_date):
        """Return historical prices between two dates as a list of dicts.

        Tests patch `yf.download` so this method should call it and translate
        the returned DataFrame into the format expected by tests.
        """
        try:
            df = yf.download(symbol, start=start_date, end=end_date)
        except Exception as e:
            current_app.logger.error(f"Error downloading historical prices for {symbol}: {e}")
            return []

        if df is None or df.empty:
            return []

        results = []
        for idx, row in df.iterrows():
            try:
                results.append({
                    'date': idx.date(),
                    'open': self._to_decimal(row.get('Open')),
                    'high': self._to_decimal(row.get('High')),
                    'low': self._to_decimal(row.get('Low')),
                    'close': self._to_decimal(row.get('Close')),
                    'volume': int(row.get('Volume')) if row.get('Volume') is not None else None,
                    'adj_close': self._to_decimal(row.get('Adj Close')) if 'Adj Close' in row.index else None
                })
            except Exception:
                continue

        return results

    def update_price_history(self, security_id, start_date, end_date):
        """Fetch historical prices and persist PriceHistory records for a security."""
        # Allow tests to patch get_historical_prices
        historical = self.get_historical_prices(self._symbol_for_security_id(security_id), start_date, end_date)
        if not historical:
            return None

        # Determine session to use
        session = self.db_session or db.session

        try:
            # Load security to get currency
            security = session.get(Security, security_id) if hasattr(session, 'get') else Security.query.get(security_id)
            for item in historical:
                # Check existing
                existing = (PriceHistory.query
                            .filter_by(security_id=security_id, date=item['date'])
                            .first())
                if existing:
                    existing.open_price = item.get('open')
                    existing.high_price = item.get('high')
                    existing.low_price = item.get('low')
                    existing.close_price = item.get('close')
                    existing.volume = item.get('volume')
                    existing.adjusted_close = item.get('adj_close')
                    existing.currency = getattr(security, 'currency', None)
                else:
                    ph = PriceHistory(
                        security_id=security_id,
                        date=item.get('date'),
                        open_price=item.get('open'),
                        high_price=item.get('high'),
                        low_price=item.get('low'),
                        close_price=item.get('close'),
                        volume=item.get('volume'),
                        adjusted_close=item.get('adj_close'),
                        currency=getattr(security, 'currency', None),
                        data_source='yahoo'
                    )
                    session.add(ph)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error saving historical prices for security {security_id}: {e}")
            return None

    def _symbol_for_security_id(self, security_id):
        # Helper to resolve a symbol from a security id
        try:
            sec = Security.query.get(security_id)
            if sec:
                return getattr(sec, 'symbol', None) or getattr(sec, 'yahoo_symbol', None)
        except Exception:
            pass
        return None

    def _update_holdings_with_price(self, security_id, price):
        """Update all holdings of a security with the latest price data."""
        if price is None:
            return
            
        holdings = Holding.query.filter_by(security_id=security_id).all()
        for holding in holdings:
            holding.current_price = price
            holding.current_value = holding.quantity * price
            holding.unrealized_gain_loss = holding.current_value - holding.total_cost
            holding.unrealized_gain_loss_pct = (
                (holding.unrealized_gain_loss / holding.total_cost * 100)
                if holding.total_cost else Decimal('0')
            )
            holding.last_updated = datetime.utcnow()
        db.session.flush()

    @staticmethod
    def update_all_prices():
        """Update prices for all securities in the database"""
        securities = Security.query.all()
        updated_count = 0
        service = PriceService(db.session)
        
        for security in securities:
            if not security.yahoo_symbol:
                continue
                
            price_history = service.fetch_latest_prices(security)
            if price_history:
                try:
                    db.session.add(price_history)
                    db.session.commit()
                    updated_count += 1
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Error saving price for {security.yahoo_symbol}: {str(e)}")
                    
        return updated_count