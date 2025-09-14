"""
Unit tests for User model.
"""
import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.extensions import db


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation(self, db_session):
        """Test creating a new user."""
        user = User(
            username='newuser',
            email='newuser@example.com',
            first_name='New',
            last_name='User'
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.is_admin is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_password_hashing(self, db_session):
        """Test password hashing and verification."""
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        user.set_password('mypassword')
        
        # Password should be hashed
        assert user.password_hash != 'mypassword'
        assert user.password_hash is not None
        
        # Should verify correct password
        assert user.check_password('mypassword') is True
        
        # Should not verify incorrect password
        assert user.check_password('wrongpassword') is False
    
    def test_user_representation(self, sample_user):
        """Test user string representation."""
        expected = f'<User {sample_user.username}>'
        assert str(sample_user) == expected
        assert repr(sample_user) == expected
    
    def test_user_admin_flag(self, db_session):
        """Test admin user creation."""
        admin_user = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin_user.set_password('adminpass')
        
        db_session.add(admin_user)
        db_session.commit()
        
        assert admin_user.is_admin is True
    
    def test_user_unique_constraints(self, db_session, sample_user):
        """Test unique constraints on username and email."""
        # Try to create user with same username
        duplicate_username = User(
            username='testuser',  # Same as sample_user
            email='different@example.com',
            first_name='Different',
            last_name='User'
        )
        duplicate_username.set_password('password')
        
        db_session.add(duplicate_username)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
        
        db_session.rollback()
        
        # Try to create user with same email
        duplicate_email = User(
            username='differentuser',
            email='test@example.com',  # Same as sample_user
            first_name='Different',
            last_name='User'
        )
        duplicate_email.set_password('password')
        
        db_session.add(duplicate_email)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_user_timestamps(self, db_session):
        """Test that timestamps are set correctly."""
        before_creation = datetime.utcnow()
        
        user = User(
            username='timestampuser',
            email='timestamp@example.com',
            first_name='Time',
            last_name='Stamp'
        )
        user.set_password('password')
        
        db_session.add(user)
        db_session.commit()
        
        after_creation = datetime.utcnow()
        
        assert before_creation <= user.created_at <= after_creation
        assert before_creation <= user.updated_at <= after_creation
        assert user.created_at == user.updated_at  # Should be same on creation
    
    def test_user_serialization(self, sample_user):
        """Test user serialization to dictionary."""
        user_dict = sample_user.to_dict()
        
        expected_keys = {
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_admin', 'created_at', 'updated_at'
        }
        
        assert set(user_dict.keys()) == expected_keys
        assert user_dict['username'] == sample_user.username
        assert user_dict['email'] == sample_user.email
        assert user_dict['is_admin'] == sample_user.is_admin
        
        # Password hash should not be included
        assert 'password_hash' not in user_dict