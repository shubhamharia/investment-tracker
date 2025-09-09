import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from ..models import Security, Dividend, Holding
from ..extensions import db
import logging

class DividendService:
    @staticmethod
    def fetch_dividend_data(security):
        """Fetch dividend information from Yahoo Finance"""
        try:
            ticker = yf.Ticker(security.yahoo_symbol)
            # Get dividend data for the last year
            dividends_df = getattr(ticker.actions, 'Dividends', None)
            if dividends_df is None:
                dividends_df = getattr(ticker, 'dividends', pd.Series())
            dividends = pd.DataFrame({'Dividends': dividends_df})
            if dividends.empty:
                logging.info(f"No dividend data found for {security.yahoo_symbol}")
                return []
            
            dividend_list = []
            # Process dates in reverse chronological order
            for date, row in dividends.iloc[::-1].iterrows():
                dividend_amount = row['Dividends']
                # Get unique platforms from holdings that existed on dividend date
                holdings = Holding.query.filter_by(security_id=security.id)\
                    .filter(Holding.created_at <= date)\
                    .with_entities(Holding.platform_id, Holding.quantity)\
                    .distinct().all()
                
                for platform_id, quantity in holdings:
                    # Check if dividend already recorded
                    existing_dividend = Dividend.query.filter_by(
                        security_id=security.id,
                        platform_id=platform_id,
                        ex_date=date.date()
                    ).first()
                    
                    if not existing_dividend:
                        dividend = Dividend(
                            security_id=security.id,
                            platform_id=platform_id,
                            ex_date=date.date(),
                            pay_date=date.date() + timedelta(days=15),  # Estimated pay date
                            dividend_per_share=Decimal(str(dividend_amount)),
                            quantity_held=quantity,
                            currency=security.currency
                        )
                        dividend.calculate_amounts()
                        dividend_list.append(dividend)
            
            return dividend_list
            
        except Exception as e:
            logging.error(f"Error fetching dividends for {security.yahoo_symbol}: {str(e)}")
            return []

    @staticmethod
    def update_all_dividends():
        """Update dividends for all securities in the database"""
        securities = Security.query.filter(Security.yahoo_symbol.isnot(None)).all()
        new_dividend_count = 0
        
        for security in securities:
            dividends = DividendService.fetch_dividend_data(security)
            for dividend in dividends:
                try:
                    db.session.add(dividend)
                    db.session.commit()
                    new_dividend_count += 1
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Error saving dividend: {str(e)}")
        
        return new_dividend_count
