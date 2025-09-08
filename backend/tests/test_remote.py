import pytest
import json
from flask import url_for

@pytest.fixture
def create_test_user(client):
    response = client.post('/api/users/', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    return data['id']

def test_create_user(client):
    """Test creating a new user"""
    print("\nTrying to create user")
    response = client.post('/api/users/', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123'
    })
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['username'] == 'newuser'

def test_get_users(client, create_test_user):
    """Test getting list of users"""
    response = client.get('/api/users/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0

def test_create_portfolio(client, create_test_user):
    """Test creating a new portfolio"""
    response = client.post('/api/portfolios/', json={
        'name': 'Test Portfolio',
        'description': 'Test Description',
        'user_id': create_test_user
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Test Portfolio'