import requests
import pytest

import os
BASE_URL = os.environ.get('API_URL', 'http://localhost:5000')  # Can be overridden with environment variable

@pytest.fixture
def create_test_user():
    response = requests.post(f'{BASE_URL}/api/users/', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.json()
    return data['id']

def test_create_user():
    response = requests.post(f'{BASE_URL}/api/users/', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.json()
    assert data['username'] == 'newuser'

def test_get_users(create_test_user):
    response = requests.get(f'{BASE_URL}/api/users/')
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

def test_create_portfolio(create_test_user):
    response = requests.post(f'{BASE_URL}/api/portfolios/', json={
        'name': 'Test Portfolio',
        'description': 'Test Description',
        'user_id': create_test_user
    })
    assert response.status_code == 201
    data = response.json()
    assert data['name'] == 'Test Portfolio'