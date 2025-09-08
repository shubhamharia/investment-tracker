from decimal import Decimal
from datetime import datetime
from sqlalchemy import desc
from . import db, BaseModel
from .price_history import PriceHistory
from .dividend import Dividend
from ..constants import DECIMAL_PLACES, CURRENCY_CODES, INSTRUMENT_TYPES

class Security(BaseModel):
    __tablename__ = 'securities'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    isin = db.Column(db.String(12))
    name = db.Column(db.String(200))
    sector = db.Column(db.String(100))
    exchange = db.Column(db.String(50))
    currency = db.Column(db.String(3), nullable=False)
    instrument_type = db.Column(db.String(20))
    country = db.Column(db.String(2))
    
    def validate(self):
        """Validate security data."""
        if not self.currency or self.currency not in CURRENCY_CODES:
            raise ValueError(f"Currency must be one of {CURRENCY_CODES}")
        if not self.ticker:
            raise ValueError("Ticker is required")
        if not self.name:
            raise ValueError("Name is required")
        if self.instrument_type and self.instrument_type not in INSTRUMENT_TYPES.values():
            raise ValueError(f"Instrument type must be one of {list(INSTRUMENT_TYPES.values())}")
    yahoo_symbol = db.Column(db.String(20))
    
    # Relationships
    transactions = db.relationship('Transaction', backref='security', lazy=True)
    price_history = db.relationship('PriceHistory', backref='security', lazy=True)
    holdings = db.relationship('Holding', backref='security', lazy=True)
    dividends = db.relationship('Dividend', backref='security', lazy=True)
    platform_mappings = db.relationship('SecurityMapping', backref='security', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('ticker', 'exchange'),)
    
    def get_current_price(self):
        """Get the most recent price for the security."""
        latest_price = (self.price_history
                       .order_by(desc(PriceHistory.price_date))
                       .first())
        return latest_price.close_price if latest_price else None
    
    def calculate_market_cap(self):
        """Calculate market capitalization if shares outstanding is available."""
        try:
            current_price = self.get_current_price()
            if not current_price or not hasattr(self, 'shares_outstanding'):
                return None
            
            market_cap = (Decimal(str(current_price)) * 
                         Decimal(str(self.shares_outstanding))
                         ).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
            return market_cap
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating market cap: {str(e)}")
    
    def calculate_yield(self, period_days=365):
        """Calculate dividend yield based on recent dividends."""
        try:
            current_price = self.get_current_price()
            if not current_price:
                return Decimal('0')
            
            # Get dividends for the last period
            cutoff_date = datetime.now().date()
            recent_dividends = (Dividend.query
                              .filter_by(security_id=self.id)
                              .filter(Dividend.ex_date >= cutoff_date)
                              .all())
            
            if not recent_dividends:
                return Decimal('0')
            
            # Sum up dividends
            total_dividends = sum(Decimal(str(d.dividend_per_share)) for d in recent_dividends)
            
            # Calculate yield
            if Decimal(str(current_price)) > 0:
                dividend_yield = ((total_dividends / Decimal(str(current_price))) * 100
                                ).quantize(Decimal('0.01'))
                return dividend_yield
            return Decimal('0')
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating yield: {str(e)}")
    
    def get_price_change(self, days=365):
        """Calculate price change over a period."""
        try:
            current_price = self.get_current_price()
            if not current_price:
                return None, None
            
            # Get historical price
            cutoff_date = datetime.now().date()
            historical_price = (PriceHistory.query
                              .filter_by(security_id=self.id)
                              .filter(PriceHistory.price_date <= cutoff_date)
                              .order_by(desc(PriceHistory.price_date))
                              .first())
            
            if not historical_price:
                return None, None
            
            price_change = (Decimal(str(current_price)) - 
                          Decimal(str(historical_price.close_price))
                          ).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
            if Decimal(str(historical_price.close_price)) > 0:
                change_pct = ((price_change / Decimal(str(historical_price.close_price))) * 100
                             ).quantize(Decimal('0.01'))
            else:
                change_pct = Decimal('0')
            
            return price_change, change_pct
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating price change: {str(e)}")
    
    def to_dict(self, include_metrics=False):
        """Convert security record to dictionary."""
        data = {
            'id': self.id,
            'ticker': self.ticker,
            'isin': self.isin,
            'name': self.name,
            'sector': self.sector,
            'exchange': self.exchange,
            'currency': self.currency,
            'instrument_type': self.instrument_type,
            'country': self.country,
            'yahoo_symbol': self.yahoo_symbol
        }
        
        if include_metrics:
            current_price = self.get_current_price()
            price_change, change_pct = self.get_price_change()
            
            data.update({
                'current_price': str(current_price) if current_price else None,
                'price_change': str(price_change) if price_change is not None else None,
                'price_change_pct': str(change_pct) if change_pct is not None else None,
                'dividend_yield': str(self.calculate_yield()),
                'market_cap': str(self.calculate_market_cap()) if self.calculate_market_cap() else None
            })
        
        return data


class SecurityMapping(BaseModel):
    """Map platform-specific security identifiers to master securities."""
    __tablename__ = 'security_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    platform_symbol = db.Column(db.String(50), nullable=False)
    platform_name = db.Column(db.String(200))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    platform = db.relationship('Platform', backref='security_mappings', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('platform_id', 'platform_symbol'),)
    
    @classmethod
    def get_or_create_mapping(cls, platform_id, platform_symbol, platform_name=None):
        """Get existing mapping or create placeholder for user verification."""
        mapping = cls.query.filter_by(
            platform_id=platform_id,
            platform_symbol=platform_symbol
        ).first()
        
        if not mapping:
            mapping = cls(
                platform_id=platform_id,
                platform_symbol=platform_symbol,
                platform_name=platform_name,
                is_verified=False
            )
            db.session.add(mapping)
            db.session.commit()
        
        return mapping
    
    def verify_mapping(self, security_id):
        """Verify the mapping with a security."""
        self.security_id = security_id
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert mapping to dictionary."""
        return {
            'id': self.id,
            'platform_id': self.platform_id,
            'security_id': self.security_id if self.security_id else None,
            'platform_symbol': self.platform_symbol,
            'platform_name': self.platform_name,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'notes': self.notes
        }