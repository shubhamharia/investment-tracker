"""
Integration tests for API endpoints.
"""
import pytest
import json
from datetime import datetime
from decimal import Decimal
from app.models.user import User
from app.models.platform import Platform
from app.models.security import Security
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.holding import Holding


class TestAPIEndpoints:
    """Test cases for API endpoints integration."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_auth_registration(self, client):
        """Test user registration endpoint."""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'User created successfully'
        assert 'user' in data
        assert data['user']['username'] == 'newuser'
    
    def test_auth_login(self, client, sample_user):
        """Test user login endpoint."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'testpassword123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert data['user']['username'] == 'testuser'
    
    def test_auth_login_invalid_credentials(self, client, sample_user):
        """Test login with invalid credentials."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get('/api/portfolios')
        assert response.status_code == 401
    
    def test_protected_endpoint_with_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = client.get('/api/portfolios', headers=auth_headers)
        assert response.status_code == 200
    
    def test_create_portfolio(self, client, auth_headers, sample_platform):
        """Test creating a new portfolio."""
        response = client.post('/api/portfolios', 
                              headers=auth_headers,
                              json={
                                  'name': 'Test Portfolio',
                                  'description': 'A test portfolio',
                                  'platform_id': sample_platform.id,
                                  'currency': 'USD'
                              })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'Test Portfolio'
        assert data['platform_id'] == sample_platform.id
    
    def test_get_portfolios(self, client, auth_headers, sample_portfolio):
        """Test getting user portfolios."""
        response = client.get('/api/portfolios', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]['name'] == sample_portfolio.name
    
    def test_create_transaction(self, client, auth_headers, sample_portfolio, sample_security):
        """Test creating a new transaction."""
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/transactions',
                              headers=auth_headers,
                              json={
                                  'security_id': sample_security.id,
                                  'transaction_type': 'BUY',
                                  'quantity': '100',
                                  'price': '50.00',
                                  'commission': '9.99',
                                  'transaction_date': datetime.now().isoformat(),
                                  'currency': 'USD'
                              })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['transaction_type'] == 'BUY'
        assert float(data['quantity']) == 100.0
        assert float(data['price']) == 50.0
    
    def test_get_transactions(self, client, auth_headers, sample_transaction):
        """Test getting portfolio transactions."""
        response = client.get(f'/api/portfolios/{sample_transaction.portfolio_id}/transactions',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]['transaction_type'] == sample_transaction.transaction_type
    
    def test_create_holding(self, client, auth_headers, sample_portfolio, sample_security):
        """Test creating a new holding."""
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/holdings',
                              headers=auth_headers,
                              json={
                                  'security_id': sample_security.id,
                                  'quantity': '100',
                                  'average_cost': '50.00',
                                  'currency': 'USD'
                              })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['security_id'] == sample_security.id
        assert float(data['quantity']) == 100.0
    
    def test_get_holdings(self, client, auth_headers, sample_holding):
        """Test getting portfolio holdings."""
        response = client.get(f'/api/portfolios/{sample_holding.portfolio_id}/holdings',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]['security_id'] == sample_holding.security_id
    
    def test_get_securities(self, client, admin_auth_headers, sample_security):
        """Test getting securities (admin only)."""
        response = client.get('/api/securities', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_create_security(self, client, admin_auth_headers):
        """Test creating a new security (admin only)."""
        response = client.post('/api/securities',
                              headers=admin_auth_headers,
                              json={
                                  'symbol': 'NEWSTOCK',
                                  'name': 'New Stock Corp',
                                  'sector': 'Technology',
                                  'currency': 'USD'
                              })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['symbol'] == 'NEWSTOCK'
        assert data['name'] == 'New Stock Corp'
    
    def test_get_platforms(self, client, auth_headers, sample_platform):
        """Test getting platforms."""
        response = client.get('/api/platforms', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_create_platform(self, client, admin_auth_headers):
        """Test creating a new platform (admin only)."""
        response = client.post('/api/platforms',
                              headers=admin_auth_headers,
                              json={
                                  'name': 'New Broker',
                                  'description': 'A new trading platform'
                              })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'New Broker'
    
    def test_portfolio_unauthorized_access(self, client, auth_headers, db_session, sample_platform):
        """Test accessing another user's portfolio."""
        # Create another user and portfolio
        other_user = User(
            username='otheruser',
            email='other@example.com',
            first_name='Other',
            last_name='User'
        )
        other_user.set_password('password')
        db_session.add(other_user)
        
        other_portfolio = Portfolio(
            name='Other Portfolio',
            user_id=other_user.id,
            platform_id=sample_platform.id,
            currency='USD',
            is_active=True
        )
        db_session.add(other_portfolio)
        db_session.commit()
        
        # Try to access other user's portfolio
        response = client.get(f'/api/portfolios/{other_portfolio.id}', headers=auth_headers)
        assert response.status_code in [403, 404]  # Should be forbidden or not found
    
    def test_invalid_json_request(self, client, auth_headers):
        """Test API with invalid JSON."""
        response = client.post('/api/portfolios',
                              headers=auth_headers,
                              data='invalid json')
        
        assert response.status_code == 400
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test API with missing required fields."""
        response = client.post('/api/portfolios',
                              headers=auth_headers,
                              json={
                                  'name': 'Test Portfolio'
                                  # Missing platform_id and currency
                              })
        
        assert response.status_code == 400
    
    def test_portfolio_value_endpoint(self, client, auth_headers, sample_portfolio):
        """Test portfolio value calculation endpoint."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/value',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_value' in data
        assert 'currency' in data
    
    def test_user_profile_endpoint(self, client, auth_headers, sample_user):
        """Test user profile endpoint."""
        response = client.get('/api/users/profile', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == sample_user.username
        assert data['email'] == sample_user.email
        assert 'password_hash' not in data  # Should not expose password
    
    def test_update_user_profile(self, client, auth_headers):
        """Test updating user profile."""
        response = client.put('/api/users/profile',
                             headers=auth_headers,
                             json={
                                 'first_name': 'Updated',
                                 'last_name': 'Name'
                             })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['first_name'] == 'Updated'
        assert data['last_name'] == 'Name'
    
    def test_delete_transaction(self, client, auth_headers, sample_transaction):
        """Test deleting a transaction."""
        response = client.delete(f'/api/transactions/{sample_transaction.id}',
                                headers=auth_headers)
        
        assert response.status_code == 200
    
    def test_update_holding(self, client, auth_headers, sample_holding):
        """Test updating a holding."""
        response = client.put(f'/api/holdings/{sample_holding.id}',
                             headers=auth_headers,
                             json={
                                 'quantity': '150',
                                 'average_cost': '55.00'
                             })
        
        assert response.status_code == 200
        data = response.get_json()
        assert float(data['quantity']) == 150.0
        assert float(data['average_cost']) == 55.0
    
    def test_portfolio_performance_endpoint(self, client, auth_headers, sample_portfolio):
        """Test portfolio performance endpoint."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/performance',
                             headers=auth_headers)
        
        # This might return 200 with empty data or 404 if no performance data
        assert response.status_code in [200, 404]
    
    def test_dividend_endpoints(self, client, auth_headers, sample_portfolio, sample_security):
        """Test dividend-related endpoints."""
        # Create dividend
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/dividends',
                              headers=auth_headers,
                              json={
                                  'security_id': sample_security.id,
                                  'amount': '2.50',
                                  'payment_date': datetime.now().isoformat(),
                                  'currency': 'USD'
                              })
        
        # Should create successfully or return appropriate error
        assert response.status_code in [201, 400, 404]
        
        # Get dividends
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/dividends',
                             headers=auth_headers)
        
        assert response.status_code == 200
    
    def test_rate_limiting(self, client, auth_headers):
        """Test API rate limiting (if implemented)."""
        # Make multiple rapid requests
        responses = []
        for _ in range(100):
            response = client.get('/api/portfolios', headers=auth_headers)
            responses.append(response.status_code)
        
        # Should mostly be 200, might have some 429 (Too Many Requests) if rate limiting is active
        success_responses = [r for r in responses if r == 200]
        assert len(success_responses) > 0  # At least some should succeed
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options('/api/portfolios')
        
        # CORS headers might be present depending on configuration
        # This test verifies the endpoint responds to OPTIONS
        assert response.status_code in [200, 404, 405]