import requests
import pytest

import os
import requests
import pytest
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = os.environ.get('API_URL', 'http://localhost:5000')

# Create a session with retries
session = requests.Session()
retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

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
    print(f"\nTrying to create user at URL: {BASE_URL}/api/users/")
    try:
        response = session.post(f'{BASE_URL}/api/users/', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == 'newuser'
    except Exception as e:
        print(f"Exception during request: {str(e)}")
        raise

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