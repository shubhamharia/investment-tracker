from . import db, BaseModel

class Platform(BaseModel):
    __tablename__ = 'platforms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50))
    currency = db.Column(db.String(3), default='GBP')
    trading_fee_fixed = db.Column(db.Numeric(10, 4), default=0)
    trading_fee_percentage = db.Column(db.Numeric(5, 4), default=0)
    fx_fee_percentage = db.Column(db.Numeric(5, 4), default=0)
    stamp_duty_applicable = db.Column(db.Boolean, default=False)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='platform', lazy=True)
    holdings = db.relationship('Holding', backref='platform', lazy=True)