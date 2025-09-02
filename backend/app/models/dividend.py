from . import db, BaseModel

class Dividend(BaseModel):
    __tablename__ = 'dividends'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    ex_date = db.Column(db.Date, nullable=False)
    pay_date = db.Column(db.Date)
    dividend_per_share = db.Column(db.Numeric(15, 8), nullable=False)
    quantity_held = db.Column(db.Numeric(15, 8), nullable=False)
    gross_dividend = db.Column(db.Numeric(15, 4), nullable=False)
    withholding_tax = db.Column(db.Numeric(15, 4), default=0)
    net_dividend = db.Column(db.Numeric(15, 4), nullable=False)
    currency = db.Column(db.String(3), nullable=False)