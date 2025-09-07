import pytest
from decimal import Decimal
import json

def test_create_portfolio_api(client, test_user):
    """Test portfolio creation via API"""
    response = client.post('/api/portfolios/', json={
        'name': 'API Test Portfolio',
        'description': 'Created via API',
        'user_id': test_user.id
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'API Test Portfolio'

def test_add_holding_api(client, test_user, test_portfolio, test_security, test_platform):
    """Test adding a holding via API"""
    response = client.post(f'/api/portfolios/{test_portfolio.id}/holdings', json={
        'security_id': test_security.id,
        'platform_id': test_platform.id,
        'quantity': '10.0',
        'average_cost': '150.00'
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert Decimal(data['quantity']) == Decimal('10.0')

def test_get_portfolio_value_api(client, test_user, test_portfolio):
    """Test getting portfolio value via API"""
    response = client.get(f'/api/portfolios/{test_portfolio.id}/value')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_value' in data
    assert 'total_cost' in data
    assert 'unrealized_gain_loss' in data

def test_update_holding_api(client, test_holding):
    """Test updating a holding via API"""
    response = client.put(f'/api/holdings/{test_holding.id}', json={
        'quantity': '15.0',
        'average_cost': '155.00'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert Decimal(data['quantity']) == Decimal('15.0')
