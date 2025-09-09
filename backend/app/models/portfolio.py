from decimal import Decimal
from . import BaseModel
from ..extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy import desc
from datetime import datetime, date, timedelta
from ..constants import DECIMAL_PLACES, CURRENCY_CODES
from .dividend import Dividend
from .holding import Holding

class PortfolioPerformance(BaseModel):
    """Track daily portfolio performance metrics."""
    __tablename__ = 'portfolio_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_value = db.Column(db.Numeric(15, 4), nullable=False)
    cash_value = db.Column(db.Numeric(15, 4), nullable=False)
    invested_value = db.Column(db.Numeric(15, 4), nullable=False)
    total_gain_loss = db.Column(db.Numeric(15, 4), nullable=False)
    daily_gain_loss = db.Column(db.Numeric(15, 4), nullable=False)
    dividend_income = db.Column(db.Numeric(15, 4), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="performance_history")

    def validate(self):
        """Validate portfolio performance data."""
        if not self.portfolio_id:
            raise ValueError("Portfolio is required")
        if not self.date:
            raise ValueError("Date is required")
        if not self.total_value:
            raise ValueError("Total value is required")
        if not self.currency or self.currency not in CURRENCY_CODES:
            raise ValueError(f"Currency must be one of {CURRENCY_CODES}")
        if self.cash_value is None:
            raise ValueError("Cash value is required")
        if self.invested_value is None:
            raise ValueError("Invested value is required")
        if self.total_gain_loss is None:
            raise ValueError("Total gain/loss is required")
        if self.daily_gain_loss is None:
            raise ValueError("Daily gain/loss is required")
        if self.dividend_income is None:
            raise ValueError("Dividend income is required")

    def calculate_performance_metrics(self, previous_performance=None):
        """Calculate performance metrics including daily changes."""
        try:
            if hasattr(self.portfolio, 'initial_value'):
                initial_value = Decimal(str(self.portfolio.initial_value))
                self.total_gain_loss = (Decimal(str(self.total_value)) - initial_value
                                      ).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            
            if previous_performance:
                prev_value = Decimal(str(previous_performance.total_value))
                current_value = Decimal(str(self.total_value))
                self.daily_gain_loss = (current_value - prev_value
                                      ).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            else:
                self.daily_gain_loss = Decimal('0')
            
            return True
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error calculating performance metrics: {str(e)}")

    def to_dict(self):
        """Convert performance record to dictionary."""
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'date': self.date.isoformat(),
            'total_value': str(self.total_value),
            'cash_value': str(self.cash_value),
            'invested_value': str(self.invested_value),
            'total_gain_loss': str(self.total_gain_loss),
            'daily_gain_loss': str(self.daily_gain_loss),
            'dividend_income': str(self.dividend_income),
            'currency': self.currency
        }

class Portfolio(BaseModel):
    """
    Represents an investment portfolio owned by a user.
    A user can have multiple portfolios.
    """
    __tablename__ = 'portfolios'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    initial_value = db.Column(db.Numeric(15, 4), default=0)
    base_currency = db.Column(db.String(3), default=CURRENCY_CODES[0])  # USD is first in CURRENCY_CODES

    def calculate_total_value(self):
        """Calculate the total current value of all holdings."""
        total = Decimal('0')
        for holding in self.holdings:
            holding.calculate_values()
            if holding.current_value:
                total += holding.current_value
        return total.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))

    def update_performance(self):
        """Update portfolio performance metrics."""
        from . import PortfolioPerformance
        
        current_value = self.calculate_total_value()
        performance = PortfolioPerformance(
            portfolio_id=self.id,
            value_date=datetime.utcnow().date(),
            total_value=current_value
        )
        
        # Calculate gain/loss
        if self.initial_value:
            performance.gain_loss = current_value - self.initial_value
            if self.initial_value > 0:
                performance.gain_loss_pct = (performance.gain_loss / self.initial_value * 100).quantize(Decimal('0.01'))
            else:
                performance.gain_loss_pct = Decimal('0')
        
        db.session.add(performance)
        return performance

    def calculate_total_value(self):
        """Calculate the total current value of all holdings."""
        total = Decimal('0')
        for holding in self.holdings:
            holding.calculate_values()
            if holding.current_value:
                total += holding.current_value
        return total.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))

    def update_performance(self):
        """Update portfolio performance metrics."""
        from . import PortfolioPerformance, Holding
        
        # Calculate total invested value from holdings
        holdings = Holding.query.filter_by(portfolio_id=self.id).all()
        invested_value = sum(holding.total_cost for holding in holdings if holding.total_cost)
        
        # Calculate current total value
        current_value = self.calculate_total_value()
        
        # Create new performance record
        performance = PortfolioPerformance(
            portfolio_id=self.id,
            date=datetime.utcnow().date(),
            total_value=current_value,
            cash_value=Decimal('0'),
            invested_value=invested_value,
            total_gain_loss=current_value - invested_value,
            daily_gain_loss=Decimal('0'),
            dividend_income=Decimal('0'),
            currency=self.base_currency
        )
        
        # Calculate gain/loss if we have an initial value
        if self.initial_value:
            performance.gain_loss = current_value - self.initial_value
            if self.initial_value > 0:
                performance.gain_loss_pct = (performance.gain_loss / self.initial_value * 100)\
                    .quantize(Decimal('0.01'))
        
        db.session.add(performance)
        db.session.commit()
        return performance

    def validate(self):
        """Validate portfolio data."""
        if not self.name:
            raise ValueError("Portfolio name is required")
        if not self.user_id:
            raise ValueError("User is required")
        if not self.base_currency or self.base_currency not in CURRENCY_CODES:
            raise ValueError(f"Base currency must be one of {CURRENCY_CODES}")
        if self.initial_value is None or self.initial_value < 0:
            raise ValueError("Initial value cannot be negative")

    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    performance_history = relationship("PortfolioPerformance", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Portfolio {self.name}>'

    def get_performance_at_date(self, target_date):
        """Get portfolio performance for a specific date."""
        return (PortfolioPerformance.query
                .filter_by(portfolio_id=self.id)
                .filter(PortfolioPerformance.date <= target_date)
                .order_by(desc(PortfolioPerformance.date))
                .first())

    def record_daily_performance(self, current_date=None):
        """Record portfolio performance for the day."""
        if current_date is None:
            current_date = date.today()

        # Get previous performance for comparison
        previous_performance = (PortfolioPerformance.query
                              .filter_by(portfolio_id=self.id)
                              .filter(PortfolioPerformance.date < current_date)
                              .order_by(desc(PortfolioPerformance.date))
                              .first())

        # Calculate current values
        total_value = sum(h.calculate_value() for h in self.holdings)
        invested_value = sum(h.calculate_cost_basis() for h in self.holdings)
        cash_value = Decimal('0')  # To be implemented with cash management
        dividend_income = sum(d.net_dividend for d in self.get_dividends_for_period(current_date))

        # Create new performance record
        performance = PortfolioPerformance(
            portfolio_id=self.id,
            date=current_date,
            total_value=total_value,
            cash_value=cash_value,
            invested_value=invested_value,
            total_gain_loss=Decimal('0'),  # Will be calculated
            daily_gain_loss=Decimal('0'),  # Will be calculated
            dividend_income=dividend_income,
            currency=self.base_currency
        )

        # Calculate metrics
        performance.calculate_performance_metrics(previous_performance)
        
        db.session.add(performance)
        db.session.commit()
        
        return performance

    def get_dividends_for_period(self, end_date, days=365):
        """Get dividends for a specific period."""
        start_date = end_date - timedelta(days=days)
        return (Dividend.query
                .join(Holding)
                .filter(Holding.portfolio_id == self.id)
                .filter(Dividend.ex_date.between(start_date, end_date))
                .all())

    def to_dict(self, include_performance=False):
        """Convert portfolio to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'base_currency': self.base_currency,
            'initial_value': str(self.initial_value)
        }
        
        if include_performance:
            latest_performance = (PortfolioPerformance.query
                                .filter_by(portfolio_id=self.id)
                                .order_by(desc(PortfolioPerformance.date))
                                .first())
            if latest_performance:
                data['latest_performance'] = latest_performance.to_dict()
        
        return data
