from decimal import Decimal
from . import db, BaseModel
from ..constants import DECIMAL_PLACES, CURRENCY_CODES

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
    
    # Relationships
    platform = db.relationship('Platform', backref='dividends', lazy=True)
    security = db.relationship('Security', backref='dividends', lazy=True)
    
    def validate(self):
        """Validate dividend data."""
        if not self.platform_id:
            raise ValueError("Platform is required")
        if not self.security_id:
            raise ValueError("Security is required")
        if not self.ex_date:
            raise ValueError("Ex-date is required")
        if not self.dividend_per_share or self.dividend_per_share <= 0:
            raise ValueError("Dividend per share must be positive")
        if not self.quantity_held or self.quantity_held <= 0:
            raise ValueError("Quantity held must be positive")
        if self.withholding_tax < 0:
            raise ValueError("Withholding tax cannot be negative")
        if not self.currency or self.currency not in CURRENCY_CODES:
            raise ValueError(f"Currency must be one of {CURRENCY_CODES}")

    def calculate_amounts(self):
        """Calculate gross and net dividend amounts."""
        try:
            # Calculate gross amount
            self.gross_dividend = (Decimal(str(self.dividend_per_share)) * 
                                 Decimal(str(self.quantity_held))).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
            # Calculate net amount
            self.net_dividend = (self.gross_dividend - 
                               Decimal(str(self.withholding_tax))).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            raise ValueError(f"Error calculating dividend amounts: {str(e)}")
    
    def to_dict(self):
        """Convert dividend record to dictionary."""
        return {
            'id': self.id,
            'platform_id': self.platform_id,
            'security_id': self.security_id,
            'ex_date': self.ex_date.isoformat() if self.ex_date else None,
            'pay_date': self.pay_date.isoformat() if self.pay_date else None,
            'dividend_per_share': str(self.dividend_per_share),
            'quantity_held': str(self.quantity_held),
            'gross_dividend': str(self.gross_dividend),
            'withholding_tax': str(self.withholding_tax),
            'net_dividend': str(self.net_dividend),
            'currency': self.currency
        }