from . import db, BaseModel
from datetime import datetime

class Transaction(BaseModel):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # BUY, SELL, DIVIDEND
    transaction_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Numeric(15, 8), nullable=False)
    price_per_share = db.Column(db.Numeric(15, 8), nullable=False)
    gross_amount = db.Column(db.Numeric(15, 4), nullable=False)
    trading_fees = db.Column(db.Numeric(10, 4), default=0)
    stamp_duty = db.Column(db.Numeric(10, 4), default=0)
    fx_fees = db.Column(db.Numeric(10, 4), default=0)
    net_amount = db.Column(db.Numeric(15, 4), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    fx_rate = db.Column(db.Numeric(15, 8), default=1)
    notes = db.Column(db.Text)