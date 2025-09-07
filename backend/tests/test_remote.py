import requests
import pytest

BASE_URL = 'http://your-raspberry-pi-ip'  # Replace with your Pi's IP address

def test_create_user():
    response = requests.post(f'{BASE_URL}/api/users/', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.json()
    assert data['username'] == 'testuser'
    return data['id']

def test_get_users():
    response = requests.get(f'{BASE_URL}/api/users/')
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

def test_create_portfolio(user_id):
    response = requests.post(f'{BASE_URL}/api/portfolios/', json={
        'name': 'Test Portfolio',
        'description': 'Test Description',
        'user_id': user_id
    })
    assert response.status_code == 201
    data = response.json()
    assert data['name'] == 'Test Portfolio'