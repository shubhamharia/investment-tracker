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
    symbol = db.Column(db.String(20), nullable=False)
    isin = db.Column(db.String(12))
    name = db.Column(db.String(200))
    sector = db.Column(db.String(100))
    exchange = db.Column(db.String(50))
    currency = db.Column(db.String(3), nullable=False)
    instrument_type = db.Column(db.String(20))
    country = db.Column(db.String(2))
    yahoo_symbol = db.Column(db.String(20))

    def validate(self):
        """Validate security data."""
        if not self.currency or self.currency not in CURRENCY_CODES:
            raise ValueError(f"Currency must be one of {CURRENCY_CODES}")
        if not self.symbol:
            raise ValueError("Symbol is required")
        if not self.name:
            raise ValueError("Name is required")
        if self.instrument_type and self.instrument_type not in INSTRUMENT_TYPES.values():
            raise ValueError(f"Instrument type must be one of {list(INSTRUMENT_TYPES.values())}")
    
    # Relationships
    transactions = db.relationship('Transaction', back_populates='security', lazy=True)
    price_history = db.relationship('PriceHistory', back_populates='security', lazy=True)
    holdings = db.relationship('Holding', back_populates='security', lazy=True)
    dividends = db.relationship('Dividend', back_populates='security', lazy=True)
    platform_mappings = db.relationship('app.models.security_mapping.SecurityMapping',
                                   back_populates='security', lazy='select',
                                   cascade='all, delete-orphan')
    __table_args__ = (
        db.UniqueConstraint('symbol', name='_security_symbol_uc'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<Security {self.symbol}: {self.name}>'
    
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
            'symbol': self.symbol,
            'name': self.name,
            'sector': self.sector,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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