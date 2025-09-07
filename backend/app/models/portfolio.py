from . import BaseModel
from ..extensions import db
from sqlalchemy.orm import relationship
from datetime import datetime

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

    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Portfolio {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat()
        }
