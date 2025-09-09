import pytest
from app.models import User

def test_create_user(db_session):
    """Test user creation"""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.username == 'testuser'
    assert user.check_password('password123')

def test_password_hashing(db_session):
    """Test password hashing works correctly"""
    user = User(username='test', email='test@test.com')
    user.set_password('cat')
    assert not user.check_password('dog')
    assert user.check_password('cat')

def test_unique_username(db_session):
    """Test username uniqueness constraint"""
    user1 = User(username='testuser', email='test1@test.com')
    user1.set_password('test')
    db_session.add(user1)
    db_session.commit()

    user2 = User(username='testuser', email='test2@test.com')
    user2.set_password('test')
    db_session.add(user2)
    with pytest.raises(Exception):  # Should raise integrity error
        db_session.commit()
