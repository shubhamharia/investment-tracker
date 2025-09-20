from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import relationship
from . import db, BaseModel
from ..constants import DECIMAL_PLACES

class PriceHistory(BaseModel):
    __tablename__ = 'price_history'

    id = db.Column(db.Integer, primary_key=True)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    # Price fields
    open_price = db.Column(db.Numeric(15, DECIMAL_PLACES), nullable=True)
    high_price = db.Column(db.Numeric(15, DECIMAL_PLACES), nullable=True)
    low_price = db.Column(db.Numeric(15, DECIMAL_PLACES), nullable=True)
    close_price = db.Column(db.Numeric(15, DECIMAL_PLACES), nullable=False)
    volume = db.Column(db.BigInteger)
    # Make currency optional for tests; we will default to the security currency or 'USD' when missing
    currency = db.Column(db.String(3), nullable=True)
    adjusted_close = db.Column(db.Numeric(15, DECIMAL_PLACES))
    data_source = db.Column(db.String(50))

    # Relationships
    security = relationship('Security', back_populates='price_history')

    __table_args__ = (db.UniqueConstraint('security_id', 'date'),)

    def __init__(self, *args, **kwargs):
        # If currency isn't provided, try to derive from the related Security (if security_id present)
        if 'currency' not in kwargs or kwargs.get('currency') is None:
            sec_id = kwargs.get('security_id')
            if sec_id:
                try:
                    # Local import to avoid circular import problems
                    from .security import Security
                    sec = db.session.get(Security, sec_id) if db.session and sec_id else None
                    if sec and getattr(sec, 'currency', None):
                        kwargs['currency'] = sec.currency
                    else:
                        kwargs['currency'] = 'USD'
                except Exception:
                    kwargs['currency'] = 'USD'
            else:
                kwargs['currency'] = 'USD'

        super().__init__(*args, **kwargs)

    def __repr__(self):
        # Match the test expectation: '<PriceHistory {symbol} {date}: ${close}>'
        sym = self.security.symbol if getattr(self, 'security', None) else self.security_id
        return f'<PriceHistory {sym} {self.date}: ${self.close_price}>'

    @db.validates('open_price', 'high_price', 'low_price', 'close_price')
    def _validate_prices(self, key, value):
        if value is None:
            if key == 'close_price':
                raise ValueError("Close price cannot be None")
            return None
        return Decimal(str(value))

    @db.validates('adjusted_close')
    def _validate_adjusted(self, key, value):
        if value is None:
            return None
        return Decimal(str(value))

    @property
    def formatted_close(self):
        return str(self.close_price) if self.close_price is not None else None

    @classmethod
    def get_latest_price(cls, security_id):
        """Get the latest price for a security."""
        return (cls.query
                .filter_by(security_id=security_id)
                .order_by(desc(cls.date))
                .first())

    @classmethod
    def get_price_at_date(cls, security_id, target_date):
        """Get the price at a specific date, falling back to the most recent previous price."""
        return (cls.query
                .filter_by(security_id=security_id)
                .filter(cls.date <= target_date)
                .order_by(desc(cls.date))
                .first())

    def calculate_daily_change(self):
        """Calculate daily price change and percentage."""
        try:
            if not self.open_price:
                return None, None

            change = (Decimal(str(self.close_price)) -
                      Decimal(str(self.open_price))).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))

            if Decimal(str(self.open_price)) == 0:
                change_pct = Decimal('0')
            else:
                change_pct = ((change / Decimal(str(self.open_price))) * 100).quantize(Decimal('0.01'))

            return change, change_pct
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating daily change: {str(e)}")

    def calculate_volatility(self, days=30):
        """Calculate price volatility over a given period."""
        try:
            end_date = self.date
            start_date = end_date - timedelta(days=days)

            prices = (PriceHistory.query
                      .filter_by(security_id=self.security_id)
                      .filter(PriceHistory.date.between(start_date, end_date))
                      .order_by(PriceHistory.date)
                      .all())

            if len(prices) < 2:
                return Decimal('0')

            # Calculate daily returns
            returns = []
            for i in range(1, len(prices)):
                prev_price = Decimal(str(prices[i - 1].close_price))
                curr_price = Decimal(str(prices[i].close_price))
                if prev_price > 0:
                    daily_return = ((curr_price - prev_price) / prev_price) * 100
                    returns.append(daily_return)

            if not returns:
                return Decimal('0')

            # Calculate standard deviation of returns
            mean = sum(returns) / len(returns)
            variance = sum((x - mean) ** 2 for x in returns) / len(returns)
            volatility = Decimal(str(variance ** Decimal('0.5'))).quantize(Decimal('0.01'))

            return volatility
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating volatility: {str(e)}")

    def to_dict(self):
        """Convert price history record to dictionary."""
        daily_change, daily_change_pct = self.calculate_daily_change()

        # Tests expect a compact set of keys for price history serialization
        return {
            'id': self.id,
            'security_id': self.security_id,
            'date': self.date.isoformat() if self.date else None,
            'open_price': str(self.open_price) if self.open_price else None,
            'high_price': str(self.high_price) if self.high_price else None,
            'low_price': str(self.low_price) if self.low_price else None,
            'close_price': str(self.close_price) if self.close_price is not None else None,
            'volume': self.volume,
            'adjusted_close': str(self.adjusted_close) if self.adjusted_close is not None else None
        }