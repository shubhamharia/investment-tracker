def test_portfolio_api():
    response = client.get('/api/portfolio')
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_portfolio_create():
    data = {"name": "Test Portfolio", "description": "A test portfolio"}
    response = client.post('/api/portfolio', json=data)
    assert response.status_code == 201
    assert response.json()['name'] == data['name']

def test_portfolio_update():
    data = {"name": "Updated Portfolio"}
    response = client.put('/api/portfolio/1', json=data)
    assert response.status_code == 200
    assert response.json()['name'] == data['name']

def test_portfolio_delete():
    response = client.delete('/api/portfolio/1')
    assert response.status_code == 204

def test_portfolio_not_found():
    response = client.get('/api/portfolio/999')
    assert response.status_code == 404