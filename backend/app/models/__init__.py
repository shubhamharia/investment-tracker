from ..extensions import db
from datetime import datetime

class BaseModel(db.Model):
    __abstract__ = True
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
from .platform import Platform
from .holding import Holding
from .price_history import PriceHistory
from .transaction import Transaction
from .dividend import Dividend
from .portfolio import Portfolio

__all__ = [
    'User',
    'Security',
    'Platform',
    'PriceHistory',
    'Holding',
    'Dividend',
    'Portfolio' # <-- Added to the list of all available models
]
