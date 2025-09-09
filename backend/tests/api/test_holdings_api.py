import pytest
from datetime import date
from decimal import Decimal
from app.models import Holding, Security, Platform, Portfolio, Transaction
from flask import url_for

def test_list_holdings(client, auth_token, test_portfolio):
    """Test listing holdings for a portfolio"""
    # Create test data
    security = Security(ticker='AAPL', name='Apple Inc.', currency='USD', yahoo_symbol='AAPL')
    platform = Platform(name='Test Platform', currency='USD')
    from app.extensions import db
    db.session.add_all([security, platform])
    db.session.commit()
    
    # Create holdings through transactions
    transactions = [
        Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('100'),
            price_per_share=Decimal('100.00'),
            trading_fees=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 1)
        ),
        Transaction(
            portfolio_id=test_portfolio.id,
            security_id=security.id,
            platform_id=platform.id,
            transaction_type='BUY',
            quantity=Decimal('50'),
            price_per_share=Decimal('100.00'),
            trading_fees=Decimal('9.99'),
            currency='USD',
            transaction_date=date(2025, 1, 2)
        )
    ]
    for transaction in transactions:
        db.session.add(transaction)
        db.session.commit()
    
    response = client.get(
        url_for('api.list_holdings', portfolio_id=test_portfolio.id),
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert len(response.json) == 2
    assert Decimal(response.json[0]['quantity']) == Decimal('100')

def test_create_holding(client, auth_token, test_portfolio):
    """Test creating a new holding"""
    security = Security(ticker='MSFT', name='Microsoft Corp', currency='USD', yahoo_symbol='MSFT')
    platform = Platform(name='Test Platform', currency='USD')
    security.save()
    platform.save()
    
    holding_data = {
        'security_id': security.id,
        'platform_id': platform.id,
        'quantity': '75',
        'currency': 'USD'
    }
    
    response = client.post(
        url_for('api.create_holding', portfolio_id=test_portfolio.id),
        json=holding_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 201
    assert Decimal(response.json['quantity']) == Decimal('75')
    
    # Verify in database
    holding = Holding.query.get(response.json['id'])
    assert holding is not None
    assert holding.portfolio_id == test_portfolio.id

def test_update_holding(client, auth_token, test_portfolio):
    """Test updating a holding"""
    security = Security(ticker='GOOGL', name='Alphabet Inc.', currency='USD', yahoo_symbol='GOOGL')
    platform = Platform(name='Test Platform', currency='USD')
    security.save()
    platform.save()
    
    holding = Holding(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        quantity=Decimal('100'),
        currency='USD'
    )
    holding.save()
    
    update_data = {
        'quantity': '150'
    }
    
    response = client.put(
        url_for('api.update_holding', portfolio_id=test_portfolio.id, holding_id=holding.id),
        json=update_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert Decimal(response.json['quantity']) == Decimal('150')
    
    # Verify in database
    holding = Holding.query.get(holding.id)
    assert holding.quantity == Decimal('150')

def test_delete_holding(client, auth_token, test_portfolio):
    """Test deleting a holding"""
    security = Security(ticker='VOD', name='Vodafone Group', currency='GBP', yahoo_symbol='VOD.L')
    platform = Platform(name='Test Platform', currency='GBP')
    security.save()
    platform.save()
    
    holding = Holding(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        quantity=Decimal('1000'),
        currency='GBP'
    )
    holding.save()
    
    response = client.delete(
        url_for('api.delete_holding', portfolio_id=test_portfolio.id, holding_id=holding.id),
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 204
    
    # Verify deletion
    assert Holding.query.get(holding.id) is None

def test_get_holding_value(client, auth_token, test_portfolio):
    """Test getting current value of a holding"""
    security = Security(ticker='TSLA', name='Tesla Inc.', currency='USD', yahoo_symbol='TSLA')
    platform = Platform(name='Test Platform', currency='USD')
    security.save()
    platform.save()
    
    holding = Holding(
        portfolio_id=test_portfolio.id,
        security_id=security.id,
        platform_id=platform.id,
        quantity=Decimal('10'),
        currency='USD'
    )
    holding.save()
    
    response = client.get(
        url_for('api.get_holding_value', portfolio_id=test_portfolio.id, holding_id=holding.id),
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert 'current_value' in response.json
    assert 'unrealized_gain_loss' in response.json

def test_invalid_holding_creation(client, auth_token, test_portfolio):
    """Test creating a holding with invalid data"""
    invalid_data = {
        'security_id': 9999,  # Non-existent security
        'platform_id': 9999,  # Non-existent platform
        'quantity': '-100',  # Negative quantity
        'currency': 'INVALID'  # Invalid currency
    }
    
    response = client.post(
        url_for('api.create_holding', portfolio_id=test_portfolio.id),
        json=invalid_data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 400
    assert 'error' in response.json
