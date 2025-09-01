from . import db, BaseModel

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