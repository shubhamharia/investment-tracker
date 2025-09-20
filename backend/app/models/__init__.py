from ..extensions import db
from datetime import datetime

class BaseModel(db.Model):
    __abstract__ = True
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        # Ensure created_at and updated_at are identical on Python-side instantiation
        # set created_at/updated_at to the same UTC value if not provided
        now = kwargs.get('created_at') or kwargs.get('updated_at') or datetime.utcnow()
        kwargs.setdefault('created_at', now)
        kwargs.setdefault('updated_at', now)
        super().__init__(*args, **kwargs)

    def validate(self):
        """Base validation method to be overridden by child classes."""
        pass

    def save(self):
        """Save the model after validation."""
        self.validate()
        db.session.add(self)
        db.session.commit()

    def update(self, **kwargs):
        """Update model attributes after validation."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.validate()
        db.session.commit()

# Import all models after BaseModel definition
from .user import User 
from .security import Security
from .security_mapping import SecurityMapping
from .platform import Platform
from .holding import Holding
from .price_history import PriceHistory
from .transaction import Transaction
from .dividend import Dividend
from .portfolio import Portfolio, PortfolioPerformance

__all__ = [
    'User',
    'Security',
    'SecurityMapping',
    'Platform',
    'PriceHistory',
    'Holding',
    'Dividend',
    'Portfolio',
    'PortfolioPerformance',
    'Transaction'
]
