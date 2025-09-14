import os
import time
import yfinance as yf
from datetime import datetime, timedelta
from decimal import Decimal
from requests.exceptions import RequestException, HTTPError, Timeout
from ..models import Security, PriceHistory, Holding
from ..extensions import db
import pandas as pd
import logging

class PriceService:
    def __init__(self):
        self.debug = os.environ.get("DEBUG_YAHOO") == "1"
        self.timeout = int(os.environ.get("YAHOO_API_TIMEOUT", "5"))
        self._max_retries = int(os.environ.get("YAHOO_MAX_RETRIES", "3"))
        self._initial_backoff = float(os.environ.get("YAHOO_INITIAL_BACKOFF", "1.0"))
        self._backoff_delay = self._initial_backoff

        if self.debug:
            logging.info(f"PriceService initialized with timeout={self.timeout}s, max_retries={self._max_retries}")

    def _debug_log(self, msg, *args):
        """Log debug information if debug mode is enabled"""
        print(f"[Yahoo Finance] {msg}")  # Always print
        if self.debug:
            logging.info(f"[Yahoo Finance] {msg}", *args)

    def _increase_backoff(self):
        """Increase the backoff delay exponentially"""
        self._backoff_delay *= 2  # Exponential backoff
        max_backoff = float(os.environ.get("YAHOO_MAX_BACKOFF", "32.0"))
        self._backoff_delay = min(self._backoff_delay, max_backoff)
        if self.debug:
            self._debug_log(f"Increased backoff delay to {self._backoff_delay}s")

        

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
        attempts = 0
        last_error = None

        while attempts < self._max_retries:
            try:
                start_time = datetime.now()
                self._debug_log(f"Fetching price for {security.yahoo_symbol} (attempt {attempts + 1}/{self._max_retries})")

                ticker = yf.Ticker(security.yahoo_symbol)
                self._debug_log("Getting ticker history")
                hist = ticker.history(period="1d")

                response_time = (datetime.now() - start_time).total_seconds()
                self._debug_log(f"Yahoo Finance API request completed in {response_time:.2f} seconds")

                if hist.empty:
                    raise ValueError(f"No price data found for {security.yahoo_symbol}")

                # Get all price data from the latest row
                latest_data = hist.iloc[-1]

                # Validate and convert to Decimal for consistent decimal arithmetic
                price_data = {}
                for field in ['Open', 'High', 'Low', 'Close']:
                    raw_value = latest_data[field]
                    
                    if not isinstance(raw_value, (int, float)) or raw_value <= 0:
                        raise ValueError(f"Invalid {field} price: {raw_value}")
                    
                    # Convert to Decimal using string representation
                    decimal_value = Decimal(str(raw_value))
                    price_data[field] = decimal_value
                
                price_data['Volume'] = int(latest_data['Volume'])

                # Success - reset backoff delay
                self._backoff_delay = self._initial_backoff
                self._debug_log(f"Latest price data: {price_data}")
                return price_data

            except HTTPError as e:
                last_error = e
                if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                    self._debug_log("Rate limit hit, backing off...")
                    self._increase_backoff()
                    time.sleep(self._backoff_delay)
                    attempts += 1
                else:
                    raise  # Re-raise other HTTP errors

            except (RequestException, Timeout) as e:
                last_error = e
                self._debug_log(f"Network error: {type(e).__name__} - {str(e)}")
                self._increase_backoff()
                time.sleep(self._backoff_delay)
                attempts += 1

            except ValueError as e:
                self._debug_log(f"Data validation error: {str(e)}")
                self._debug_log(f"Error fetching Yahoo Finance data for {security.yahoo_symbol}")
                raise  # Don't retry on validation errors

            except Exception as e:
                self._debug_log(f"Unexpected error: {type(e).__name__} - {str(e)}")
                raise  # Don't retry on unexpected errors

        # If we get here, we've exhausted all retries
        logging.error(f"Max retries exceeded for {security.yahoo_symbol}")
        raise last_error or RequestException("Max retries exceeded")

    def fetch_latest_prices(self, securities, max_time=30):
        """Fetch latest prices for multiple securities.

        Args:
            securities: A single Security object or a list of Security objects
            max_time: Maximum time in seconds to spend on the entire batch

        Returns:
            A single PriceHistory object for a single security input,
            or a list of PriceHistory objects if a list was provided
        """
        single_security = not isinstance(securities, list)
        if single_security:
            securities = [securities]

        results = []
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=max_time)

        self._debug_log("Starting batch price fetch")

        try:
            for security in securities:
                if datetime.now() >= end_time:
                    self._debug_log("Maximum batch time reached, stopping batch fetch")
                    break

                self._debug_log(f"Processing {security.yahoo_symbol}")
                try:
                    # Calculate remaining time for this security
                    remaining_time = (end_time - datetime.now()).total_seconds()
                    if remaining_time <= 0:
                        break

                    # Set timeout for individual price fetch
                    self.timeout = min(int(remaining_time), self.timeout)
                    
                    price_data = self.get_current_price(security)
                    if price_data is not None:
                        timestamp = datetime.now()
                        self._debug_log(f"Transformed Yahoo Finance data: {price_data}")
                        try:
                            price_history = PriceHistory(
                                security_id=security.id,
                                price_date=timestamp.date(),
                                volume=price_data['Volume'],
                                currency=security.currency,
                                data_source='yahoo',
                                open_price=price_data['Open'],
                                high_price=price_data['High'],
                                low_price=price_data['Low'],
                                close_price=price_data['Close']
                            )
                            
                            results.append(price_history)
                            self._debug_log(f"Added price history for {security.yahoo_symbol}")
                        except Exception as e:
                            error_msg = f"Error creating price history for {security.yahoo_symbol}: {type(e).__name__} - {str(e)}"
                            logging.error(error_msg)
                            if single_security:
                                return None
                            continue
                except Exception as e:
                    error_msg = f"Error fetching price for {security.yahoo_symbol}: {type(e).__name__} - {str(e)}"
                    self._debug_log(error_msg)
                    logging.error(error_msg)
                    if single_security:
                        return None
                    continue

            total_time = (datetime.now() - start_time).total_seconds()
            self._debug_log(f"Batch fetch completed in {total_time:.2f}s")
            self._debug_log(f"Successful fetches: {len(results)}/{len(securities)}")

            if not results:
                return None if single_security else []

            try:
                # Check for existing records and handle duplicates
                final_results = []
                for result in results:
                    # Check if a record already exists for this security and date
                    existing = PriceHistory.query.filter_by(
                        security_id=result.security_id,
                        price_date=result.price_date
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.open_price = result.open_price
                        existing.high_price = result.high_price
                        existing.low_price = result.low_price
                        existing.close_price = result.close_price
                        existing.volume = result.volume
                        existing.currency = result.currency
                        existing.data_source = result.data_source
                        final_results.append(existing)
                    else:
                        db.session.add(result)
                        final_results.append(result)
                
                db.session.flush()

                # Update holdings with new prices
                for result in final_results:
                    self._update_holdings_with_price(result.security_id, result.close_price)

                return final_results[0] if single_security else final_results
            except Exception as e:
                db.session.rollback()
                error_msg = f"Error saving price data: {type(e).__name__} - {str(e)}"
                self._debug_log(error_msg)
                return None if single_security else []

            return results[0] if single_security else results

        except Exception as e:
            self._debug_log(f"Batch fetch failed: {str(e)}")
            raise

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
        service = PriceService()
        
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