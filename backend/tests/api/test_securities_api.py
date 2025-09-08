import pytest
from datetime import date
from decimal import Decimal
from app.models import Security, PriceHistory
from flask import url_for

def test_list_securities(client, auth_token):
    """Test listing all securities"""
    # Create test securities
    securities = [
        Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL'),
        Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT')
    ]
    for security in securities:
        security.save()
    
    response = client.get(
        url_for('api.list_securities'),
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['ticker'] == 'AAPL'
    assert response.json[1]['ticker'] == 'MSFT'

def test_create_security(client, auth_token):
    """Test creating a new security"""
    security_data = {
        'ticker': 'GOOGL',
        'name': 'Alphabet Inc.',
        'currency': 'USD',
        'yahoo_symbol': 'GOOGL'
    }
    
    response = client.post(
        url_for('api.create_security'),
        json=security_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 201
    assert response.json['ticker'] == 'GOOGL'
    assert response.json['name'] == 'Alphabet Inc.'
    
    # Verify in database
    security = Security.query.filter_by(ticker='GOOGL').first()
    assert security is not None
    assert security.currency == 'USD'

def test_update_security(client, auth_token):
    """Test updating a security"""
    security = Security(ticker='VOD', name='Vodafone Group', currency='GBP', yahoo_symbol='VOD.L')
    security.save()
    
    update_data = {
        'name': 'Vodafone Group Plc',
        'yahoo_symbol': 'VOD.L'
    }
    
    response = client.put(
        url_for('api.update_security', security_id=security.id),
        json=update_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert response.json['name'] == 'Vodafone Group Plc'
    
    # Verify in database
    security = Security.query.get(security.id)
    assert security.name == 'Vodafone Group Plc'

def test_delete_security(client, auth_token):
    """Test deleting a security"""
    security = Security(ticker='IBM', name='IBM Corp', currency='USD', yahoo_symbol='IBM')
    security.save()
    
    response = client.delete(
        url_for('api.delete_security', security_id=security.id),
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 204
    
    # Verify deletion
    assert Security.query.get(security.id) is None

def test_get_security_price_history(client, auth_token):
    """Test getting price history for a security"""
    security = Security(ticker='TSLA', name='Tesla Inc.', currency='USD', yahoo_symbol='TSLA')
    security.save()
    
    # Add some price history
    prices = [
        PriceHistory(
            security_id=security.id,
            price_date=date(2025, 1, 1),
            open_price=Decimal('100.00'),
            high_price=Decimal('105.00'),
            low_price=Decimal('99.00'),
            close_price=Decimal('102.00'),
            volume=1000000,
            currency='USD'
        )
    ]
    for price in prices:
        price.save()
    
    response = client.get(
        url_for('api.get_security_prices', security_id=security.id),
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert len(response.json) == 1
    assert float(response.json[0]['close_price']) == 102.00

def test_invalid_security_creation(client, auth_token):
    """Test creating a security with invalid data"""
    invalid_data = {
        'ticker': '',  # Empty ticker
        'name': 'Test Company',
        'currency': 'INVALID'  # Invalid currency
    }
    
    response = client.post(
        url_for('api.create_security'),
        json=invalid_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 400
    assert 'error' in response.json
