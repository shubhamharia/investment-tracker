from ..extensions import db
from datetime import datetime

class BaseModel(db.Model):
    __abstract__ = True
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

from .user import User 
from .platform import Platform
from .security import Security
from .transaction import Transaction
from .price_history import PriceHistory
from .holding import Holding
from .dividend import Dividend
from .portfolio import Portfolio 

__all__ = [
    'Platform',
    'Security',
    'Transaction',
    'PriceHistory',
    'Holding',
    'Dividend',
    'Portfolio' # <-- Added to the list of all available models
]
