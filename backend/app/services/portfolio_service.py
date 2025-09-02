from ..models import Holding, Transaction, Security, Platform
from ..extensions import db
from sqlalchemy import func
import pandas as pd

class PortfolioService:
    @staticmethod
    def calculate_portfolio_summary():
        """Calculate portfolio summary including total value and gains/losses"""
        holdings = Holding.query.all()
        
        total_value = sum(holding.current_value or 0 for holding in holdings)
        total_cost = sum(holding.total_cost or 0 for holding in holdings)
        total_gain_loss = sum(holding.unrealized_gain_loss or 0 for holding in holdings)
        
        if total_cost > 0:
            total_gain_loss_pct = (total_gain_loss / total_cost) * 100
        else:
            total_gain_loss_pct = 0
            
        return {
            'total_value': float(total_value),
            'total_cost': float(total_cost),
            'total_gain_loss': float(total_gain_loss),
            'total_gain_loss_pct': float(total_gain_loss_pct)
        }

    @staticmethod
    def update_holdings():
        """Update all holdings with latest prices and calculations"""
        holdings = Holding.query.all()
        
        for holding in holdings:
            latest_price = (PriceHistory.query
                          .filter_by(security_id=holding.security_id)
                          .order_by(PriceHistory.price_date.desc())
                          .first())
            
            if latest_price:
                holding.current_price = latest_price.close_price
                holding.current_value = holding.quantity * latest_price.close_price
                holding.unrealized_gain_loss = holding.current_value - holding.total_cost
                
                if holding.total_cost > 0:
                    holding.unrealized_gain_loss_pct = (holding.unrealized_gain_loss / holding.total_cost) * 100
                else:
                    holding.unrealized_gain_loss_pct = 0
                    
                holding.last_updated = datetime.utcnow()
        
        db.session.commit()