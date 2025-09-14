from decimal import Decimal
from . import db, BaseModel
from datetime import datetime
from ..constants import DECIMAL_PLACES, TRANSACTION_TYPES as VALID_TRANSACTION_TYPES, CURRENCY_CODES

class Transaction(BaseModel):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    
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
    
    # Define relationships
    portfolio = db.relationship("Portfolio", back_populates="transactions")
    platform = db.relationship("Platform", back_populates="transactions")
    security = db.relationship("Security", back_populates="transactions")
    
    def __init__(self, *args, **kwargs):
        # Set defaults for numeric fields
        defaults = {
            'fx_rate': 1,
            'trading_fees': 0,
            'stamp_duty': 0,
            'fx_fees': 0
        }
        
        # Apply defaults if not provided
        for field, default in defaults.items():
            if field not in kwargs:
                kwargs[field] = default
                    
        super().__init__(*args, **kwargs)
        self.calculate_amounts()
        self.validate()  # Validate before updating holding
        self.update_holding()
    
    def calculate_amounts(self):
        """Calculate transaction amounts including fees."""
        try:
            # Convert values to Decimal and ensure defaults
            quantity = Decimal(str(self.quantity))
            price = Decimal(str(self.price_per_share))
            fx_rate = Decimal(str(self.fx_rate or 1))
            self.trading_fees = Decimal('0') if self.trading_fees is None else Decimal(str(self.trading_fees))
            self.stamp_duty = Decimal('0') if self.stamp_duty is None else Decimal(str(self.stamp_duty))
            self.fx_fees = Decimal('0') if self.fx_fees is None else Decimal(str(self.fx_fees))
            
            # Calculate gross amount in transaction currency
            self.gross_amount = (quantity * price).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
            # Get platform fees
            if self.platform and not (self.trading_fees or self.fx_fees or self.stamp_duty):
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

        # Validate sell transactions
        if self.transaction_type == 'SELL':
            from . import Holding
            holding = Holding.query.filter_by(
                portfolio_id=self.portfolio_id,
                security_id=self.security_id,
                platform_id=self.platform_id
            ).first()
            if not holding or holding.quantity < self.quantity:
                raise ValueError("Cannot sell more shares than held")

        # For sell transactions, verify enough shares are held
        if self.transaction_type == 'SELL':
            from . import Holding
            holding = Holding.query.filter_by(
                portfolio_id=self.portfolio_id,
                security_id=self.security_id,
                platform_id=self.platform_id
            ).first()
            if not holding:
                raise ValueError("No shares held for this security")
            if holding.quantity < self.quantity:
                raise ValueError(f"Insufficient shares for sale: have {holding.quantity}, want to sell {self.quantity}")
    
    def update_holding(self):
        """Create or update holding based on transaction."""
        from . import Holding
        holding = Holding.query.filter_by(
            portfolio_id=self.portfolio_id,
            security_id=self.security_id,
            platform_id=self.platform_id
        ).first()

        if self.transaction_type == 'BUY':
            if not holding:
                # Create new holding for buy transaction
                total_cost = (self.quantity * self.price_per_share + 
                            self.trading_fees + self.stamp_duty + self.fx_fees)
                holding = Holding(
                    portfolio_id=self.portfolio_id,
                    security_id=self.security_id,
                    platform_id=self.platform_id,
                    quantity=self.quantity,
                    currency=self.currency,
                    average_cost=(total_cost / self.quantity).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}')),
                    total_cost=total_cost.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
                )
                db.session.add(holding)
            else:
                # Update existing holding for buy
                # For buys, add costs including fees to the existing holding
                transaction_cost = self.quantity * self.price_per_share
                total_fees = self.trading_fees + self.stamp_duty + self.fx_fees
                new_quantity = holding.quantity + self.quantity
                
                # Calculate new weighted average cost and total
                total_cost = holding.total_cost + transaction_cost + total_fees
                holding.average_cost = (total_cost / new_quantity).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
                holding.quantity = new_quantity
                holding.total_cost = total_cost

        elif self.transaction_type == 'SELL':
            if not holding or holding.quantity < self.quantity:
                raise ValueError("Cannot sell more shares than held")
                
            # Calculate sell impact including fees
            old_cost = holding.total_cost
            sell_amount = self.quantity * self.price_per_share
            sell_fees = self.trading_fees + self.stamp_duty + self.fx_fees
            sell_total = sell_amount - sell_fees
            
            # Reduce quantity and adjust total cost
            holding.quantity = holding.quantity - self.quantity
            
            # Calculate the cost basis of the sold shares and subtract from total cost
            sold_cost_basis = (old_cost * (self.quantity / (self.quantity + holding.quantity))).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            holding.total_cost = (old_cost - sold_cost_basis).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
            if holding.quantity == 0:
                db.session.delete(holding)
                return
        
        # Update current price if available
        if hasattr(self.security, 'current_price') and self.security.current_price:
            holding.current_price = self.security.current_price
            
        if holding:
            holding.calculate_values()

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