import pytest

def test_dashboard_endpoint(client):
    response = client.get('/api/dashboard')
    assert response.status_code == 200
    assert 'data' in response.json

def test_dashboard_error_handling(client):
    response = client.get('/api/dashboard?error=true')
    assert response.status_code == 400
    assert 'error' in response.json