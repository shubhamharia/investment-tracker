from . import BaseModel
from ..extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from flask import current_app

class User(BaseModel):
    """
    User model for authentication and profile management
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128))
    is_active = Column(Boolean, default=True)
    first_name = Column(String(64))
    last_name = Column(String(64))

    def set_password(self, password):
        """Set the user's password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user to dictionary representation"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expires_in=86400):
        """Generate authentication JWT token
        
        Args:
            expires_in (int): Token expiration time in seconds, defaults to 24 hours
            
        Returns:
            str: JWT token
        """
        now = datetime.utcnow()
        payload = {
            'id': self.id,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )

    @staticmethod
    def verify_auth_token(token):
        """Verify and decode JWT token
        
        Args:
            token (str): JWT token to verify
            
        Returns:
            User: User object if token is valid, None otherwise
        """
        try:
            data = jwt.decode(
                token,
                current_app.config.get('SECRET_KEY'),
                algorithms=['HS256']
            )
            return User.query.get(data['id'])
        except:
            return None

    def to_dict(self):
        try:
            return {
                'id': self.id,
                'username': self.username,
                'email': self.email,
                'is_active': self.is_active,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
        except Exception as e:
            print(f"Error in to_dict(): {str(e)}")
            raise