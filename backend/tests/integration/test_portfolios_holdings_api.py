import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta


class TestPortfoliosHoldingsAPI:
    """Test portfolio holdings API endpoints."""

    def test_get_portfolio_holdings(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test getting all holdings for a portfolio."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_portfolio_holdings_unauthorized(self, client, sample_portfolio):
        """Test getting portfolio holdings without authentication."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings')
        assert response.status_code == 401

    def test_get_portfolio_holdings_not_found(self, client, auth_headers):
        """Test getting holdings for non-existent portfolio."""
        response = client.get('/api/portfolios/99999/holdings', headers=auth_headers)
        assert response.status_code == 404

    def test_get_specific_holding(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test getting specific holding by ID."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/{sample_holding.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == sample_holding.id
        assert data['quantity'] == str(sample_holding.quantity)

    def test_get_holding_not_found(self, client, auth_headers, sample_portfolio):
        """Test getting non-existent holding."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/99999', headers=auth_headers)
        assert response.status_code == 404

    def test_create_holding(self, client, auth_headers, sample_portfolio, sample_security, sample_platform):
        """Test creating a new holding."""
        holding_data = {
            'security_id': sample_security.id,
            'platform_id': sample_platform.id,
            'quantity': '50.0',
            'average_cost': '160.00',
            'currency': 'USD'
        }
        
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/holdings', json=holding_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['quantity'] == '50.0'
        assert data['average_cost'] == '160.00'

    def test_create_holding_invalid_portfolio(self, client, auth_headers, sample_security, sample_platform):
        """Test creating holding for invalid portfolio."""
        holding_data = {
            'security_id': sample_security.id,
            'platform_id': sample_platform.id,
            'quantity': '50.0',
            'average_cost': '160.00'
        }
        
        response = client.post('/api/portfolios/99999/holdings', json=holding_data, headers=auth_headers)
        assert response.status_code == 404

    def test_create_holding_missing_fields(self, client, auth_headers, sample_portfolio):
        """Test creating holding with missing required fields."""
        holding_data = {
            'quantity': '50.0'
            # Missing security_id, platform_id, average_cost
        }
        
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/holdings', json=holding_data, headers=auth_headers)
        assert response.status_code == 400

    def test_update_holding(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test updating an existing holding."""
        update_data = {
            'quantity': '75.0',
            'average_cost': '155.00'
        }
        
        response = client.put(f'/api/portfolios/{sample_portfolio.id}/holdings/{sample_holding.id}', 
                            json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['quantity'] == '75.0'
        assert data['average_cost'] == '155.00'

    def test_update_holding_not_found(self, client, auth_headers, sample_portfolio):
        """Test updating non-existent holding."""
        update_data = {
            'quantity': '75.0'
        }
        
        response = client.put(f'/api/portfolios/{sample_portfolio.id}/holdings/99999', 
                            json=update_data, headers=auth_headers)
        assert response.status_code == 404

    def test_delete_holding(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test deleting a holding."""
        response = client.delete(f'/api/portfolios/{sample_portfolio.id}/holdings/{sample_holding.id}', 
                               headers=auth_headers)
        assert response.status_code == 200

    def test_delete_holding_not_found(self, client, auth_headers, sample_portfolio):
        """Test deleting non-existent holding."""
        response = client.delete(f'/api/portfolios/{sample_portfolio.id}/holdings/99999', 
                               headers=auth_headers)
        assert response.status_code == 404

    def test_get_holdings_summary(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test getting holdings summary for portfolio."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/summary', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_value' in data
        assert 'total_cost' in data
        assert 'total_gain_loss' in data
        assert 'holding_count' in data

    def test_get_holdings_by_security(self, client, auth_headers, sample_portfolio, sample_security, sample_holding):
        """Test getting holdings for specific security."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/security/{sample_security.id}', 
                            headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_holdings_by_platform(self, client, auth_headers, sample_portfolio, sample_platform, sample_holding):
        """Test getting holdings for specific platform."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/platform/{sample_platform.id}', 
                            headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_holdings_allocation(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test getting holdings allocation breakdown."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/allocation', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'by_security' in data
        assert 'by_sector' in data
        assert 'by_platform' in data

    def test_bulk_update_holdings(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test bulk updating multiple holdings."""
        update_data = {
            'holdings': [
                {
                    'id': sample_holding.id,
                    'quantity': '80.0',
                    'average_cost': '152.00'
                }
            ]
        }
        
        response = client.put(f'/api/portfolios/{sample_portfolio.id}/holdings/bulk', 
                            json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'updated_count' in data

    def test_bulk_import_holdings(self, client, auth_headers, sample_portfolio, sample_security, sample_platform):
        """Test bulk importing holdings."""
        holdings_data = {
            'holdings': [
                {
                    'security_id': sample_security.id,
                    'platform_id': sample_platform.id,
                    'quantity': '25.0',
                    'average_cost': '148.00',
                    'currency': 'USD'
                },
                {
                    'security_id': sample_security.id,
                    'platform_id': sample_platform.id,
                    'quantity': '30.0',
                    'average_cost': '152.00',
                    'currency': 'USD'
                }
            ]
        }
        
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/holdings/bulk', 
                             json=holdings_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert 'imported_count' in data

    def test_rebalance_holdings(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test rebalancing portfolio holdings."""
        rebalance_data = {
            'target_allocation': {
                str(sample_holding.security_id): 0.6  # 60% allocation
            },
            'rebalance_method': 'PROPORTIONAL'
        }
        
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/holdings/rebalance', 
                             json=rebalance_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'suggested_trades' in data

    def test_get_holdings_performance(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test getting holdings performance metrics."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/performance', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        if data:  # If holdings exist
            holding = data[0]
            assert 'unrealized_gain_loss' in holding
            assert 'percentage_gain_loss' in holding

    def test_export_holdings(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test exporting holdings to CSV."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/export', headers=auth_headers)
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'

    def test_get_holdings_history(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test getting holdings history."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/history', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_holding_transactions(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test getting transactions for a specific holding."""
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings/{sample_holding.id}/transactions', 
                            headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_update_holding_notes(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test updating holding notes."""
        notes_data = {
            'notes': 'This is a long-term investment position'
        }
        
        response = client.put(f'/api/portfolios/{sample_portfolio.id}/holdings/{sample_holding.id}/notes', 
                            json=notes_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['notes'] == 'This is a long-term investment position'

    def test_set_holding_alerts(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test setting alerts for a holding."""
        alert_data = {
            'alerts': [
                {
                    'type': 'PRICE_ABOVE',
                    'threshold': '170.00',
                    'enabled': True
                },
                {
                    'type': 'GAIN_PERCENTAGE',
                    'threshold': '10.0',
                    'enabled': True
                }
            ]
        }
        
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/holdings/{sample_holding.id}/alerts', 
                             json=alert_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'alerts_count' in data

    def test_get_holdings_with_filters(self, client, auth_headers, sample_portfolio, sample_holding):
        """Test getting holdings with various filters."""
        # Test with minimum value filter
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings?min_value=1000', headers=auth_headers)
        assert response.status_code == 200
        
        # Test with sector filter
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings?sector=Technology', headers=auth_headers)
        assert response.status_code == 200
        
        # Test with currency filter
        response = client.get(f'/api/portfolios/{sample_portfolio.id}/holdings?currency=USD', headers=auth_headers)
        assert response.status_code == 200

    def test_consolidate_holdings(self, client, auth_headers, sample_portfolio):
        """Test consolidating holdings for same security across platforms."""
        consolidation_data = {
            'strategy': 'AVERAGE_COST',
            'target_platform_id': 1
        }
        
        response = client.post(f'/api/portfolios/{sample_portfolio.id}/holdings/consolidate', 
                             json=consolidation_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'consolidation_plan' in data