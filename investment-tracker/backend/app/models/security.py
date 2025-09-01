from . import db, BaseModel

class Security(BaseModel):
    __tablename__ = 'securities'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    isin = db.Column(db.String(12))
    name = db.Column(db.String(200))
    sector = db.Column(db.String(100))
    exchange = db.Column(db.String(50))
    currency = db.Column(db.String(3))
    instrument_type = db.Column(db.String(20))
    country = db.Column(db.String(2))
    yahoo_symbol = db.Column(db.String(20))
    
    # Relationships
    transactions = db.relationship('Transaction', backref='security', lazy=True)
    price_history = db.relationship('PriceHistory', backref='security', lazy=True)
    holdings = db.relationship('Holding', backref='security', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('ticker', 'exchange'),)