from . import BaseModel
from ..extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class Portfolio(BaseModel):
    """
    Represents an investment portfolio owned by a user.
    A user can have multiple portfolios.
    """
    __tablename__ = 'portfolios'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    updated_at = Column(db.DateTime, onupdate=db.func.current_timestamp())

    # Define relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Portfolio {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
