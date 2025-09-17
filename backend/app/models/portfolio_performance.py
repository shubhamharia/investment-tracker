"""Compatibility shim: re-export PortfolioPerformance from .portfolio

This file prevents SQLAlchemy from seeing two separate Table definitions
when tests import `app.models.portfolio_performance` and `app.models.portfolio`.
The canonical model lives in `app.models.portfolio.PortfolioPerformance`.
"""
from .portfolio import PortfolioPerformance  # noqa: F401

__all__ = ['PortfolioPerformance']
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.extensions import db


class PortfolioPerformance(db.Model):
    """Portfolio performance tracking model."""
    
    __tablename__ = 'portfolio_performance'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_value = Column(Numeric(15, 2), nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)
    cash_value = Column(Numeric(15, 2), nullable=False, default=0)
    unrealized_gain_loss = Column(Numeric(15, 2), nullable=False, default=0)
    realized_gain_loss = Column(Numeric(15, 2), nullable=False, default=0)
    dividend_income = Column(Numeric(15, 2), nullable=False, default=0)
    total_return = Column(Numeric(10, 4), nullable=False, default=0)  # As percentage
    benchmark_return = Column(Numeric(10, 4), nullable=True)  # As percentage
    alpha = Column(Numeric(10, 4), nullable=True)
    beta = Column(Numeric(10, 4), nullable=True)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    volatility = Column(Numeric(10, 4), nullable=True)
    max_drawdown = Column(Numeric(10, 4), nullable=True)
    currency = Column(String(3), nullable=False, default='USD')
    is_snapshot = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship('Portfolio', back_populates='performance_history')
    
    def __repr__(self):
        return f'<PortfolioPerformance {self.portfolio_id}: {self.total_value} on {self.date}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'date': self.date.isoformat() if self.date else None,
            'total_value': str(self.total_value),
            'total_cost': str(self.total_cost),
            'cash_value': str(self.cash_value),
            'unrealized_gain_loss': str(self.unrealized_gain_loss),
            'realized_gain_loss': str(self.realized_gain_loss),
            'dividend_income': str(self.dividend_income),
            'total_return': str(self.total_return),
            'benchmark_return': str(self.benchmark_return) if self.benchmark_return else None,
            'alpha': str(self.alpha) if self.alpha else None,
            'beta': str(self.beta) if self.beta else None,
            'sharpe_ratio': str(self.sharpe_ratio) if self.sharpe_ratio else None,
            'volatility': str(self.volatility) if self.volatility else None,
            'max_drawdown': str(self.max_drawdown) if self.max_drawdown else None,
            'currency': self.currency,
            'is_snapshot': self.is_snapshot,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_percentage_gain_loss(self):
        """Calculate percentage gain/loss."""
        if self.total_cost > 0:
            return ((self.total_value - self.total_cost) / self.total_cost) * 100
        return Decimal('0')
    
    def calculate_roi(self):
        """Calculate return on investment."""
        if self.total_cost > 0:
            total_gain = self.unrealized_gain_loss + self.realized_gain_loss + self.dividend_income
            return (total_gain / self.total_cost) * 100
        return Decimal('0')
    
    @classmethod
    def create_snapshot(cls, portfolio_id, performance_data):
        """Create a performance snapshot."""
        snapshot = cls(
            portfolio_id=portfolio_id,
            is_snapshot=True,
            **performance_data
        )
        db.session.add(snapshot)
        return snapshot