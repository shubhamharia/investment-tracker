import pytest
import json

def test_create_user(client, db_session):
    response = client.post('/api/users/', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['username'] == 'newuser'
    assert 'id' in data

def test_get_users(client, test_user):
    response = client.get('/api/users/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0
    assert data[0]['username'] == 'testuser'

def test_create_portfolio(client, test_user):
    response = client.post('/api/portfolios/', json={
        'name': 'Test Portfolio',
        'description': 'Test Description',
        'user_id': test_user.id
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Test Portfolio'
    assert data['user_id'] == test_user.id