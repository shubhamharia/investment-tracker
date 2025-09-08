from . import db, BaseModel
from datetime import datetime
from sqlalchemy.orm import relationship

class Holding(BaseModel):
    __tablename__ = 'holdings'
    
    # Define the relationship with Portfolio
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    quantity = db.Column(db.Numeric(15, 8), nullable=False)
    average_cost = db.Column(db.Numeric(15, 8), nullable=False)
    total_cost = db.Column(db.Numeric(15, 4), nullable=False)
    current_price = db.Column(db.Numeric(15, 8))
    current_value = db.Column(db.Numeric(15, 4))
    unrealized_gain_loss = db.Column(db.Numeric(15, 4))
    unrealized_gain_loss_pct = db.Column(db.Numeric(8, 4), default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('platform_id', 'security_id'),)

    def calculate_values(self):
        """Calculate current value and unrealized gain/loss"""
        from decimal import Decimal, ROUND_HALF_UP
        if self.current_price is not None and self.quantity is not None:
            self.current_value = self.current_price * self.quantity
            if self.total_cost:
                self.unrealized_gain_loss = self.current_value - self.total_cost
                if self.total_cost > 0:
                    self.unrealized_gain_loss_pct = (self.unrealized_gain_loss / self.total_cost * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculate_values()

    def to_dict(self):
        self.calculate_values()
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'security_id': self.security_id,
            'platform_id': self.platform_id,
            'quantity': float(self.quantity) if self.quantity else None,
            'average_cost': float(self.average_cost) if self.average_cost else None,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'current_price': float(self.current_price) if self.current_price else None,
            'current_value': float(self.current_value) if self.current_value else None,
            'unrealized_gain_loss': float(self.unrealized_gain_loss) if self.unrealized_gain_loss else None,
            'unrealized_gain_loss_pct': float(self.unrealized_gain_loss_pct) if self.unrealized_gain_loss_pct else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }