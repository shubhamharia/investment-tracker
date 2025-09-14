from ..models import Holding, Transaction, Security, Platform, Portfolio
from ..extensions import db
from sqlalchemy import func
import pandas as pd
from decimal import Decimal
from datetime import datetime

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
    def calculate_holdings(portfolio_id=None):
        """Calculate holdings from transactions for a specific portfolio or all portfolios"""
        try:
            # Clear existing holdings if recalculating for specific portfolio
            if portfolio_id:
                Holding.query.filter_by(portfolio_id=portfolio_id).delete()
            else:
                # For import process, only calculate for portfolios that exist
                portfolios = Portfolio.query.all()
                if not portfolios:
                    print("No portfolios found. Holdings calculation skipped.")
                    return
                
                for portfolio in portfolios:
                    PortfolioService.calculate_holdings(portfolio.id)
                return
            
            # Get all transactions for this portfolio
            transactions = Transaction.query.filter_by(portfolio_id=portfolio_id).all()
            
            # Group transactions by platform and security
            holdings_data = {}
            
            for transaction in transactions:
                key = (transaction.platform_id, transaction.security_id)
                
                if key not in holdings_data:
                    holdings_data[key] = {
                        'platform_id': transaction.platform_id,
                        'security_id': transaction.security_id,
                        'total_quantity': Decimal('0'),
                        'total_cost': Decimal('0'),
                        'currency': transaction.currency
                    }
                
                # Add/subtract quantity based on transaction type
                if transaction.transaction_type == 'BUY':
                    holdings_data[key]['total_quantity'] += transaction.quantity
                    holdings_data[key]['total_cost'] += transaction.gross_amount
                elif transaction.transaction_type == 'SELL':
                    holdings_data[key]['total_quantity'] -= transaction.quantity
                    # For sells, reduce total cost proportionally
                    if holdings_data[key]['total_quantity'] > 0:
                        cost_per_share = holdings_data[key]['total_cost'] / holdings_data[key]['total_quantity']
                        holdings_data[key]['total_cost'] -= (transaction.quantity * cost_per_share)
            
            # Create holding records for non-zero positions
            for key, data in holdings_data.items():
                if data['total_quantity'] > 0:  # Only create holdings for positive quantities
                    average_cost = data['total_cost'] / data['total_quantity']
                    
                    holding = Holding(
                        portfolio_id=portfolio_id,
                        platform_id=data['platform_id'],
                        security_id=data['security_id'],
                        quantity=data['total_quantity'],
                        average_cost=average_cost,
                        total_cost=data['total_cost'],
                        currency=data['currency'],
                        last_updated=datetime.utcnow()
                    )
                    
                    db.session.add(holding)
            
            db.session.commit()
            print(f"Holdings calculated for portfolio {portfolio_id}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error calculating holdings: {str(e)}")
            raise

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