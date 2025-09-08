from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import desc
from . import db, BaseModel
from ..services.constants import DECIMAL_PLACES

class PriceHistory(BaseModel):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    price_date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Numeric(15, 8))
    high_price = db.Column(db.Numeric(15, 8))
    low_price = db.Column(db.Numeric(15, 8))
    close_price = db.Column(db.Numeric(15, 8), nullable=False)
    volume = db.Column(db.BigInteger)
    currency = db.Column(db.String(3), nullable=False)
    data_source = db.Column(db.String(50))
    
    __table_args__ = (db.UniqueConstraint('security_id', 'price_date'),)
    
    @classmethod
    def get_latest_price(cls, security_id):
        """Get the latest price for a security."""
        return (cls.query
                .filter_by(security_id=security_id)
                .order_by(desc(cls.price_date))
                .first())
    
    @classmethod
    def get_price_at_date(cls, security_id, target_date):
        """Get the price at a specific date, falling back to the most recent previous price."""
        return (cls.query
                .filter_by(security_id=security_id)
                .filter(cls.price_date <= target_date)
                .order_by(desc(cls.price_date))
                .first())
    
    def calculate_daily_change(self):
        """Calculate daily price change and percentage."""
        try:
            if not self.open_price:
                return None, None
            
            change = (Decimal(str(self.close_price)) - 
                     Decimal(str(self.open_price))).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
            if Decimal(str(self.open_price)) == 0:
                change_pct = Decimal('0')
            else:
                change_pct = ((change / Decimal(str(self.open_price))) * 100
                             ).quantize(Decimal('0.01'))
            
            return change, change_pct
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating daily change: {str(e)}")
    
    def calculate_volatility(self, days=30):
        """Calculate price volatility over a given period."""
        try:
            end_date = self.price_date
            start_date = end_date - timedelta(days=days)
            
            prices = (PriceHistory.query
                     .filter_by(security_id=self.security_id)
                     .filter(PriceHistory.price_date.between(start_date, end_date))
                     .order_by(PriceHistory.price_date)
                     .all())
            
            if len(prices) < 2:
                return Decimal('0')
            
            # Calculate daily returns
            returns = []
            for i in range(1, len(prices)):
                prev_price = Decimal(str(prices[i-1].close_price))
                curr_price = Decimal(str(prices[i].close_price))
                if prev_price > 0:
                    daily_return = ((curr_price - prev_price) / prev_price) * 100
                    returns.append(daily_return)
            
            if not returns:
                return Decimal('0')
            
            # Calculate standard deviation of returns
            mean = sum(returns) / len(returns)
            variance = sum((x - mean) ** 2 for x in returns) / len(returns)
            volatility = Decimal(str(variance ** Decimal('0.5'))).quantize(Decimal('0.01'))
            
            return volatility
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating volatility: {str(e)}")
    
    def to_dict(self):
        """Convert price history record to dictionary."""
        daily_change, daily_change_pct = self.calculate_daily_change()
        
        return {
            'id': self.id,
            'security_id': self.security_id,
            'price_date': self.price_date.isoformat(),
            'open_price': str(self.open_price) if self.open_price else None,
            'high_price': str(self.high_price) if self.high_price else None,
            'low_price': str(self.low_price) if self.low_price else None,
            'close_price': str(self.close_price),
            'volume': self.volume,
            'currency': self.currency,
            'data_source': self.data_source,
            'daily_change': str(daily_change) if daily_change is not None else None,
            'daily_change_pct': str(daily_change_pct) if daily_change_pct is not None else None
        }