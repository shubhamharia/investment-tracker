import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta


class TestUsersAPI:
    """Test users API endpoints."""

    def test_create_user_success(self, client):
        """Test successful user creation."""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = client.post('/api/users', json=user_data)
        assert response.status_code == 201
        
        data = response.get_json()
        assert 'id' in data
        assert data['username'] == 'newuser'
        assert data['email'] == 'newuser@example.com'
        assert 'password' not in data  # Password should not be returned

    def test_create_user_duplicate_username(self, client, sample_user):
        """Test user creation with duplicate username."""
        user_data = {
            'username': 'testuser',  # Same as sample_user
            'email': 'different@example.com',
            'password': 'password123',
            'first_name': 'Different',
            'last_name': 'User'
        }
        
        response = client.post('/api/users', json=user_data)
        assert response.status_code == 400

    def test_create_user_duplicate_email(self, client, sample_user):
        """Test user creation with duplicate email."""
        user_data = {
            'username': 'differentuser',
            'email': 'testuser@example.com',  # Same as sample_user
            'password': 'password123',
            'first_name': 'Different',
            'last_name': 'User'
        }
        
        response = client.post('/api/users', json=user_data)
        assert response.status_code == 400

    def test_create_user_missing_required_fields(self, client):
        """Test user creation with missing required fields."""
        user_data = {
            'username': 'newuser',
            # Missing email and password
        }
        
        response = client.post('/api/users', json=user_data)
        assert response.status_code == 400

    def test_get_current_user(self, client, sample_user, auth_headers):
        """Test getting current user information."""
        response = client.get('/api/users/me', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['username'] == sample_user.username
        assert data['email'] == sample_user.email
        assert 'password' not in data

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication."""
        response = client.get('/api/users/me')
        assert response.status_code == 401

    def test_update_current_user(self, client, sample_user, auth_headers):
        """Test updating current user information."""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = client.put('/api/users/me', json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['first_name'] == 'Updated'
        assert data['last_name'] == 'Name'

    def test_update_current_user_email(self, client, sample_user, auth_headers):
        """Test updating current user email."""
        update_data = {
            'email': 'updated@example.com'
        }
        
        response = client.put('/api/users/me', json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['email'] == 'updated@example.com'

    def test_update_current_user_duplicate_email(self, client, sample_user, auth_headers, db_session):
        """Test updating current user with duplicate email."""
        # Create another user
        from app.models.user import User
        other_user = User(
            username='otheruser',
            email='other@example.com',
            first_name='Other',
            last_name='User'
        )
        other_user.set_password('password123')
        db_session.add(other_user)
        db_session.commit()
        
        update_data = {
            'email': 'other@example.com'  # Duplicate email
        }
        
        response = client.put('/api/users/me', json=update_data, headers=auth_headers)
        assert response.status_code == 400

    def test_change_password(self, client, sample_user, auth_headers):
        """Test changing user password."""
        password_data = {
            'current_password': 'testpassword123',
            'new_password': 'newpassword123'
        }
        
        response = client.put('/api/users/me/password', json=password_data, headers=auth_headers)
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client, sample_user, auth_headers):
        """Test changing password with wrong current password."""
        password_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }
        
        response = client.put('/api/users/me/password', json=password_data, headers=auth_headers)
        assert response.status_code == 400

    def test_change_password_missing_fields(self, client, sample_user, auth_headers):
        """Test changing password with missing fields."""
        password_data = {
            'current_password': 'testpassword123'
            # Missing new_password
        }
        
        response = client.put('/api/users/me/password', json=password_data, headers=auth_headers)
        assert response.status_code == 400

    def test_delete_current_user(self, client, sample_user, auth_headers):
        """Test deleting current user."""
        response = client.delete('/api/users/me', headers=auth_headers)
        assert response.status_code == 200

    def test_get_user_preferences(self, client, sample_user, auth_headers):
        """Test getting user preferences."""
        response = client.get('/api/users/me/preferences', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'currency' in data
        assert 'timezone' in data

    def test_update_user_preferences(self, client, sample_user, auth_headers):
        """Test updating user preferences."""
        preferences_data = {
            'currency': 'EUR',
            'timezone': 'Europe/London'
        }
        
        response = client.put('/api/users/me/preferences', json=preferences_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['currency'] == 'EUR'
        assert data['timezone'] == 'Europe/London'

    def test_get_user_statistics(self, client, sample_user, auth_headers):
        """Test getting user statistics."""
        response = client.get('/api/users/me/statistics', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_portfolios' in data
        assert 'total_transactions' in data
        assert 'total_value' in data

    def test_admin_get_all_users(self, client, admin_auth_headers):
        """Test admin getting all users."""
        response = client.get('/api/users', headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_admin_get_user_by_id(self, client, sample_user, admin_auth_headers):
        """Test admin getting user by ID."""
        response = client.get(f'/api/users/{sample_user.id}', headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == sample_user.id

    def test_non_admin_cannot_get_all_users(self, client, auth_headers):
        """Test non-admin cannot get all users."""
        response = client.get('/api/users', headers=auth_headers)
        assert response.status_code == 403

    def test_non_admin_cannot_get_other_user(self, client, sample_user, auth_headers, db_session):
        """Test non-admin cannot get other user's information."""
        # Create another user
        from app.models.user import User
        other_user = User(
            username='otheruser',
            email='other@example.com',
            first_name='Other',
            last_name='User'
        )
        other_user.set_password('password123')
        db_session.add(other_user)
        db_session.commit()
        
        response = client.get(f'/api/users/{other_user.id}', headers=auth_headers)
        assert response.status_code == 403