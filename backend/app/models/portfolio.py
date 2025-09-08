from decimal import Decimal
from . import BaseModel
from ..extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy import desc
from datetime import datetime, date, timedelta
from ..services.constants import DECIMAL_PLACES
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
    base_currency = db.Column(db.String(3), default='USD')

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
