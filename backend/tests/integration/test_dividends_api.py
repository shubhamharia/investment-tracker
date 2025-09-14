import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta


class TestDividendsAPI:
    """Test dividends API endpoints."""

    def test_get_all_dividends(self, client, auth_headers, sample_dividend):
        """Test getting all dividends for authenticated user."""
        response = client.get('/api/dividends', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_dividends_unauthorized(self, client):
        """Test getting dividends without authentication."""
        response = client.get('/api/dividends')
        assert response.status_code == 401

    def test_get_dividend_by_id(self, client, auth_headers, sample_dividend):
        """Test getting specific dividend by ID."""
        response = client.get(f'/api/dividends/{sample_dividend.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == sample_dividend.id
        assert data['amount'] == str(sample_dividend.amount)

    def test_get_dividend_not_found(self, client, auth_headers):
        """Test getting non-existent dividend."""
        response = client.get('/api/dividends/99999', headers=auth_headers)
        assert response.status_code == 404

    def test_create_dividend(self, client, auth_headers, sample_portfolio, sample_security):
        """Test creating a new dividend record."""
        dividend_data = {
            'portfolio_id': sample_portfolio.id,
            'security_id': sample_security.id,
            'amount': '5.00',
            'payment_date': '2024-01-15',
            'ex_dividend_date': '2024-01-10',
            'currency': 'USD',
            'dividend_type': 'REGULAR'
        }
        
        response = client.post('/api/dividends', json=dividend_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['amount'] == '5.00'
        assert data['currency'] == 'USD'

    def test_create_dividend_invalid_portfolio(self, client, auth_headers, sample_security):
        """Test creating dividend with invalid portfolio."""
        dividend_data = {
            'portfolio_id': 99999,  # Non-existent portfolio
            'security_id': sample_security.id,
            'amount': '5.00',
            'payment_date': '2024-01-15',
            'currency': 'USD'
        }
        
        response = client.post('/api/dividends', json=dividend_data, headers=auth_headers)
        assert response.status_code == 400

    def test_create_dividend_missing_required_fields(self, client, auth_headers):
        """Test creating dividend with missing required fields."""
        dividend_data = {
            'amount': '5.00'
            # Missing portfolio_id, security_id, payment_date
        }
        
        response = client.post('/api/dividends', json=dividend_data, headers=auth_headers)
        assert response.status_code == 400

    def test_update_dividend(self, client, auth_headers, sample_dividend):
        """Test updating an existing dividend."""
        update_data = {
            'amount': '3.75',
            'dividend_type': 'SPECIAL'
        }
        
        response = client.put(f'/api/dividends/{sample_dividend.id}', json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['amount'] == '3.75'
        assert data['dividend_type'] == 'SPECIAL'

    def test_update_dividend_not_found(self, client, auth_headers):
        """Test updating non-existent dividend."""
        update_data = {
            'amount': '3.75'
        }
        
        response = client.put('/api/dividends/99999', json=update_data, headers=auth_headers)
        assert response.status_code == 404

    def test_delete_dividend(self, client, auth_headers, sample_dividend):
        """Test deleting a dividend."""
        response = client.delete(f'/api/dividends/{sample_dividend.id}', headers=auth_headers)
        assert response.status_code == 200

    def test_delete_dividend_not_found(self, client, auth_headers):
        """Test deleting non-existent dividend."""
        response = client.delete('/api/dividends/99999', headers=auth_headers)
        assert response.status_code == 404

    def test_get_dividends_by_portfolio(self, client, auth_headers, sample_portfolio, sample_dividend):
        """Test getting dividends for specific portfolio."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/dividends', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_dividends_by_security(self, client, auth_headers, sample_security, sample_dividend):
        """Test getting dividends for specific security."""
        response = client.get(f'/api/securities/{sample_security.id}/dividends', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_dividends_by_date_range(self, client, auth_headers, sample_dividend):
        """Test getting dividends within date range."""
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = client.get(f'/api/dividends?start_date={start_date}&end_date={end_date}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_dividend_summary(self, client, auth_headers, sample_dividend):
        """Test getting dividend summary."""
        response = client.get('/api/dividends/summary', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_amount' in data
        assert 'total_count' in data
        assert 'by_currency' in data

    def test_get_dividend_yield_analysis(self, client, auth_headers, sample_dividend):
        """Test getting dividend yield analysis."""
        response = client.get(f'/api/dividends/yield/{sample_dividend.security_id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'annual_yield' in data
        assert 'quarterly_yield' in data

    def test_bulk_import_dividends(self, client, auth_headers, sample_portfolio, sample_security):
        """Test bulk importing dividends."""
        dividends_data = {
            'dividends': [
                {
                    'portfolio_id': sample_portfolio.id,
                    'security_id': sample_security.id,
                    'amount': '2.50',
                    'payment_date': '2024-01-15',
                    'currency': 'USD'
                },
                {
                    'portfolio_id': sample_portfolio.id,
                    'security_id': sample_security.id,
                    'amount': '2.75',
                    'payment_date': '2024-04-15',
                    'currency': 'USD'
                }
            ]
        }
        
        response = client.post('/api/dividends/bulk', json=dividends_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert 'imported_count' in data
        assert data['imported_count'] == 2

    def test_get_dividends_calendar(self, client, auth_headers):
        """Test getting dividend calendar."""
        response = client.get('/api/dividends/calendar', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_export_dividends(self, client, auth_headers, sample_dividend):
        """Test exporting dividends to CSV."""
        response = client.get('/api/dividends/export', headers=auth_headers)
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'

    def test_get_dividend_projections(self, client, auth_headers, sample_dividend):
        """Test getting dividend projections."""
        response = client.get('/api/dividends/projections', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'projected_annual' in data
        assert 'projected_quarterly' in data