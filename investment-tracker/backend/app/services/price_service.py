import yfinance as yf
from datetime import datetime, timedelta
from ..models import Security, PriceHistory
from ..extensions import db
import pandas as pd
import logging

class PriceService:
    @staticmethod
    def fetch_latest_prices(security):
        """Fetch latest price data for a security from Yahoo Finance"""
        try:
            ticker = yf.Ticker(security.yahoo_symbol)
            hist = ticker.history(period="2d")
            
            if hist.empty:
                logging.warning(f"No price data found for {security.yahoo_symbol}")
                return None
                
            latest_price = hist.iloc[-1]
            
            price_history = PriceHistory(
                security_id=security.id,
                price_date=hist.index[-1].date(),
                open_price=latest_price['Open'],
                high_price=latest_price['High'],
                low_price=latest_price['Low'],
                close_price=latest_price['Close'],
                volume=latest_price['Volume'],
                currency=security.currency,
                data_source='yahoo'
            )
            
            return price_history
            
        except Exception as e:
            logging.error(f"Error fetching price for {security.yahoo_symbol}: {str(e)}")
            return None

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