from decimal import Decimal
from . import db, BaseModel
from datetime import datetime
from ..constants import DECIMAL_PLACES, TRANSACTION_TYPES as VALID_TRANSACTION_TYPES, CURRENCY_CODES

class Transaction(BaseModel):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculate_amounts()
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
    
    def __init__(self, *args, **kwargs):
        if 'fx_rate' not in kwargs:
            kwargs['fx_rate'] = 1
        super().__init__(*args, **kwargs)
        self.calculate_amounts()
    
    def calculate_amounts(self):
        """Calculate transaction amounts including fees."""
        try:
            # Convert values to Decimal
            quantity = Decimal(str(self.quantity))
            price = Decimal(str(self.price_per_share))
            fx_rate = Decimal(str(self.fx_rate))
            
            # Calculate gross amount in transaction currency
            self.gross_amount = (quantity * price).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
            # Get platform fees
            if self.platform:
                self.trading_fees = self.platform.calculate_trading_fees(self.gross_amount)
                self.fx_fees = self.platform.calculate_fx_fees(self.gross_amount) if self.currency != self.platform.currency else Decimal('0')
                self.stamp_duty = self.platform.calculate_stamp_duty(self.gross_amount)
            
            # Calculate net amount
            if self.transaction_type == 'BUY':
                self.net_amount = (self.gross_amount + self.trading_fees + 
                                 self.stamp_duty + self.fx_fees
                                 ).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            else:  # SELL
                self.net_amount = (self.gross_amount - self.trading_fees - 
                                 self.stamp_duty - self.fx_fees
                                 ).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating transaction amounts: {str(e)}")
    
    def validate(self):
        """Validate transaction data."""
        if self.transaction_type not in VALID_TRANSACTION_TYPES:
            raise ValueError(f"Invalid transaction type: {self.transaction_type}")
        
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if self.price_per_share <= 0:
            raise ValueError("Price must be positive")
        
        if not self.currency or self.currency not in CURRENCY_CODES:
            raise ValueError(f"Currency must be one of {CURRENCY_CODES}")
        
        if self.fx_rate <= 0:
            raise ValueError("FX rate must be positive")
    
    def to_dict(self):
        """Convert transaction record to dictionary."""
        return {
            'id': self.id,
            'platform_id': self.platform_id,
            'security_id': self.security_id,
            'transaction_type': self.transaction_type,
            'transaction_date': self.transaction_date.isoformat(),
            'quantity': str(self.quantity),
            'price_per_share': str(self.price_per_share),
            'gross_amount': str(self.gross_amount),
            'trading_fees': str(self.trading_fees),
            'stamp_duty': str(self.stamp_duty),
            'fx_fees': str(self.fx_fees),
            'net_amount': str(self.net_amount),
            'currency': self.currency,
            'fx_rate': str(self.fx_rate),
            'notes': self.notes
        }