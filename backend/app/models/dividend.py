from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from . import db, BaseModel
from ..constants import DECIMAL_PLACES, CURRENCY_CODES

class Dividend(BaseModel):
    __tablename__ = 'dividends'

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    # Platform can be omitted in some tests so allow nullable
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=True)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    ex_dividend_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date)
    record_date = db.Column(db.Date)
    amount = db.Column(db.Numeric(15, 8), nullable=False)
    currency = db.Column(db.String(3), nullable=False)

    # Relationships
    portfolio = db.relationship('Portfolio', back_populates='dividends', lazy=True)
    platform = db.relationship('Platform', back_populates='dividends', lazy=True)
    security = db.relationship('Security', back_populates='dividends', lazy=True)

    def validate(self):
        """Validate dividend data."""
        if not self.portfolio_id:
            raise ValueError("Portfolio is required")
        if not self.security_id:
            raise ValueError("Security is required")
        if not self.ex_dividend_date:
            raise ValueError("Ex-dividend date is required")
        if not self.amount or Decimal(str(self.amount)) < 0:
            raise ValueError("Amount must be positive")
        if not self.currency or self.currency not in CURRENCY_CODES:
            raise ValueError(f"Currency must be one of {CURRENCY_CODES}")

    def to_dict(self):
        """Convert dividend record to dictionary."""
        # Return the raw stored Decimal string for amount (tests compare to str(Decimal))
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'security_id': self.security_id,
            'amount': str(self.amount),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'ex_dividend_date': self.ex_dividend_date.isoformat() if self.ex_dividend_date else None,
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Dividend {self.security.symbol if self.security else self.security_id}: ${self.amount}>'