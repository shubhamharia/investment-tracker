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
    is_admin = Column(Boolean, default=False)

    # Relationships
    portfolios = relationship(
        "Portfolio",
        back_populates="user",
        passive_deletes=True,  # This prevents SQLAlchemy from nullifying foreign keys
        cascade="all, delete-orphan"  # This ensures portfolios are deleted when user is deleted
    )

    def set_password(self, password):
        """Set the user's password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration=86400):
        """Generate a JWT token for authentication
        
        Args:
            expiration (int): Token expiration time in seconds, defaults to 24 hours
            
        Returns:
            str: JWT token
            
        The token contains standard claims:
        - sub: Subject (user ID)
        - iat: Issued At
        - exp: Expiration
        """
        try:
            now = datetime.utcnow()
            payload = {
                'sub': str(self.id),  # JWT sub claim should be a string
                'exp': int((now + timedelta(seconds=expiration)).timestamp()),  # Convert to UTC timestamp
                'iat': int(now.timestamp())
            }
            # Always use JWT_SECRET_KEY or fall back to SECRET_KEY
            secret = current_app.config.get('JWT_SECRET_KEY') or current_app.config['SECRET_KEY']
            return jwt.encode(
                payload,
                secret,
                algorithm='HS256'
            )
        except jwt.InvalidTokenError as e:
            print(f"Error generating token - invalid token: {e}")
            return None
        except Exception as e:
            print(f"Error generating token: {e}")
            return None

    @staticmethod
    def verify_auth_token(token):
        """Verify and decode JWT token
        
        Args:
            token (str): JWT token to verify
            
        Returns:
            User: User object if token is valid, None otherwise
            
        Raises:
            jwt.ExpiredSignatureError: When token has expired
            jwt.InvalidTokenError: When token is invalid
        """
        try:
            # Always use JWT_SECRET_KEY or fall back to SECRET_KEY
            secret = current_app.config.get('JWT_SECRET_KEY') or current_app.config['SECRET_KEY']
            data = jwt.decode(
                token,
                secret,
                algorithms=['HS256']
            )
            user = db.session.get(User, int(data['sub']))
            if not user:
                raise jwt.InvalidTokenError("User not found")
            return user
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            # Let these exceptions propagate up for specific handling
            raise
        except Exception as e:
            print(f"Unexpected error verifying token: {e}")
            raise jwt.InvalidTokenError(str(e))

    def to_dict(self):
        """Convert user to dictionary representation"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_admin': self.is_admin
        }

    def __repr__(self):
        return f'<User {self.id}>'