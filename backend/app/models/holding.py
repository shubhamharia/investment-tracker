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