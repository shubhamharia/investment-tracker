import pytest

def test_transaction_creation():
    response = create_transaction(amount=100, type='credit')
    assert response.status_code == 201
    assert response.json()['amount'] == 100
    assert response.json()['type'] == 'credit'

def test_transaction_retrieval():
    response = get_transaction(transaction_id=1)
    assert response.status_code == 200
    assert response.json()['id'] == 1

def test_transaction_edge_case():
    response = create_transaction(amount=0, type='debit')
    assert response.status_code == 400
    assert 'error' in response.json()