import yfinance as yf
from datetime import datetime, timedelta
from ..models import Security, PriceHistory
from ..extensions import db
import pandas as pd
import logging

class PriceService:
    @staticmethod
    def fetch_latest_prices(securities):
        """Fetch latest price data for securities from Yahoo Finance
        
        Args:
            securities: A single security or list of securities
        Returns:
            A PriceHistory object or None on error if a single security was provided,
            or a list of PriceHistory objects if a list was provided
        """
        single_security = not isinstance(securities, list)
        if single_security:
            securities = [securities]
            
        results = []
        for security in securities:
            try:
                ticker = yf.Ticker(security.yahoo_symbol)
                hist = ticker.history(period="2d")
                
                if hist.empty:
                    logging.warning(f"No price data found for {security.yahoo_symbol}")
                    continue
                    
                latest_price = hist.iloc[-1]
                
                price_history = PriceHistory(
                    security_id=security.id,
                    price_date=hist.index[-1].date(),
                    open_price=float(latest_price['Open']),
                    high_price=float(latest_price['High']),
                    low_price=float(latest_price['Low']),
                    close_price=float(latest_price['Close']),
                    volume=int(latest_price['Volume']),
                    currency=security.currency,
                    data_source='yahoo'
                )
                
                # Add to session and flush to get the ID
                db.session.add(price_history)
                db.session.flush()
                results.append(price_history)
                
            except Exception as e:
                logging.error(f"Error fetching price for {security.yahoo_symbol}: {str(e)}")
                db.session.rollback()
                if single_security:
                    return None
                continue
                
        # Return single object for single security input
        if single_security:
            return results[0] if results else None
            
        return results
                
        return results

    @staticmethod
    def update_all_prices():
        """Update prices for all securities in the database"""
        securities = Security.query.all()
        updated_count = 0
        
        for security in securities:
            if not security.yahoo_symbol:
                continue
                
            price_history = PriceService.fetch_latest_prices(security)
            if price_history:
                try:
                    db.session.add(price_history)
                    db.session.commit()
                    updated_count += 1
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Error saving price for {security.yahoo_symbol}: {str(e)}")
                    
        return updated_count