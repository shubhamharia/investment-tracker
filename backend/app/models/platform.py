from decimal import Decimal
from . import db, BaseModel
from ..constants import DECIMAL_PLACES, CURRENCY_CODES, ACCOUNT_TYPES

class Platform(BaseModel):
    __tablename__ = 'platforms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('name', name='_platform_name_uc'),)
    account_type = db.Column(db.String(50), default=ACCOUNT_TYPES['GIA'])  # General Investment Account as default
    currency = db.Column(db.String(3), default=CURRENCY_CODES[2])  # GBP is third in CURRENCY_CODES
    description = db.Column(db.String(255))
    trading_fee_fixed = db.Column(db.Numeric(10, 4), default=0)
    trading_fee_percentage = db.Column(db.Numeric(5, 4), default=0)
    fx_fee_percentage = db.Column(db.Numeric(5, 4), default=0)
    stamp_duty_applicable = db.Column(db.Boolean, default=False)
    
    # Relationships
    transactions = db.relationship('Transaction', back_populates='platform', lazy=True)
    holdings = db.relationship('Holding', back_populates='platform', lazy=True)
    dividends = db.relationship('Dividend', back_populates='platform', lazy=True)
    portfolios = db.relationship('app.models.portfolio.Portfolio', back_populates='platform', lazy=True)
    
    def calculate_trading_fees(self, amount):
        """Calculate trading fees for a given transaction amount."""
        try:
            amount = Decimal(str(amount))
            fixed_fee = Decimal(str(self.trading_fee_fixed))
            percentage_fee = (amount * Decimal(str(self.trading_fee_percentage)) / 100)
            
            return (fixed_fee + percentage_fee).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating trading fees: {str(e)}")
    
    def calculate_fx_fees(self, amount):
        """Calculate FX fees for a given amount."""
        try:
            amount = Decimal(str(amount))
            fx_fee = (amount * Decimal(str(self.fx_fee_percentage)) / 100)
            
            return fx_fee.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating FX fees: {str(e)}")
    
    def calculate_stamp_duty(self, amount):
        """Calculate stamp duty if applicable (typically 0.5% for UK stocks)."""
        if not self.stamp_duty_applicable:
            return Decimal('0')
        
        try:
            amount = Decimal(str(amount))
            stamp_duty = (amount * Decimal('0.005'))  # 0.5%
            
            return stamp_duty.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating stamp duty: {str(e)}")
    
    def to_dict(self):
        """Convert platform record to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Platform {self.name}>'