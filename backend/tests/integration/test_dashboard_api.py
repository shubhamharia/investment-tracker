import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta


class TestDashboardAPI:
    """Test dashboard API endpoints."""

    def test_get_dashboard_overview(self, client, auth_headers):
        """Test getting dashboard overview."""
        response = client.get('/api/dashboard/overview', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_value' in data
        assert 'total_gain_loss' in data
        assert 'portfolio_count' in data
        assert 'top_performers' in data
        assert 'worst_performers' in data

    def test_get_dashboard_unauthorized(self, client):
        """Test getting dashboard without authentication."""
        response = client.get('/api/dashboard/overview')
        assert response.status_code == 401

    def test_get_portfolio_summary(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio summary for dashboard."""
        response = client.get('/api/dashboard/portfolios', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        if data:  # If portfolios exist
            portfolio = data[0]
            assert 'id' in portfolio
            assert 'name' in portfolio
            assert 'current_value' in portfolio
            assert 'gain_loss' in portfolio

    def test_get_recent_transactions(self, client, auth_headers, sample_transaction):
        """Test getting recent transactions for dashboard."""
        response = client.get('/api/dashboard/transactions/recent', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_recent_transactions_with_limit(self, client, auth_headers, sample_transaction):
        """Test getting recent transactions with limit."""
        response = client.get('/api/dashboard/transactions/recent?limit=5', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_upcoming_dividends(self, client, auth_headers, sample_dividend):
        """Test getting upcoming dividends for dashboard."""
        response = client.get('/api/dashboard/dividends/upcoming', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_portfolio_allocation_chart(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio allocation chart data."""
        response = client.get('/api/dashboard/allocation', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'by_security' in data
        assert 'by_sector' in data
        assert 'by_platform' in data

    def test_get_performance_chart_data(self, client, auth_headers):
        """Test getting performance chart data."""
        response = client.get('/api/dashboard/performance', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'time_series' in data
        assert 'period' in data

    def test_get_performance_chart_with_period(self, client, auth_headers):
        """Test getting performance chart data with specific period."""
        response = client.get('/api/dashboard/performance?period=1M', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'time_series' in data
        assert data['period'] == '1M'

    def test_get_market_movers(self, client, auth_headers, sample_security):
        """Test getting market movers for dashboard."""
        response = client.get('/api/dashboard/market-movers', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'gainers' in data
        assert 'losers' in data

    def test_get_watchlist(self, client, auth_headers):
        """Test getting watchlist for dashboard."""
        response = client.get('/api/dashboard/watchlist', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_add_to_watchlist(self, client, auth_headers, sample_security):
        """Test adding security to watchlist."""
        watchlist_data = {
            'security_id': sample_security.id,
            'target_price': '160.00'
        }
        
        response = client.post('/api/dashboard/watchlist', json=watchlist_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['security_id'] == sample_security.id

    def test_remove_from_watchlist(self, client, auth_headers, sample_security):
        """Test removing security from watchlist."""
        # First add to watchlist
        watchlist_data = {'security_id': sample_security.id}
        client.post('/api/dashboard/watchlist', json=watchlist_data, headers=auth_headers)
        
        # Then remove
        response = client.delete(f'/api/dashboard/watchlist/{sample_security.id}', headers=auth_headers)
        assert response.status_code == 200

    def test_get_news_feed(self, client, auth_headers):
        """Test getting news feed for dashboard."""
        response = client.get('/api/dashboard/news', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_alerts(self, client, auth_headers):
        """Test getting alerts for dashboard."""
        response = client.get('/api/dashboard/alerts', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_create_alert(self, client, auth_headers, sample_security):
        """Test creating price alert."""
        alert_data = {
            'security_id': sample_security.id,
            'alert_type': 'PRICE_ABOVE',
            'threshold': '160.00',
            'message': 'AAPL above $160'
        }
        
        response = client.post('/api/dashboard/alerts', json=alert_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['security_id'] == sample_security.id
        assert data['alert_type'] == 'PRICE_ABOVE'

    def test_delete_alert(self, client, auth_headers, sample_security):
        """Test deleting alert."""
        # First create alert
        alert_data = {
            'security_id': sample_security.id,
            'alert_type': 'PRICE_BELOW',
            'threshold': '140.00'
        }
        create_response = client.post('/api/dashboard/alerts', json=alert_data, headers=auth_headers)
        alert_id = create_response.get_json()['id']
        
        # Then delete
        response = client.delete(f'/api/dashboard/alerts/{alert_id}', headers=auth_headers)
        assert response.status_code == 200

    def test_get_quick_stats(self, client, auth_headers):
        """Test getting quick stats for dashboard."""
        response = client.get('/api/dashboard/stats', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_value' in data
        assert 'day_change' in data
        assert 'total_return' in data

    def test_get_sector_performance(self, client, auth_headers):
        """Test getting sector performance for dashboard."""
        response = client.get('/api/dashboard/sectors', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_currency_exposure(self, client, auth_headers):
        """Test getting currency exposure for dashboard."""
        response = client.get('/api/dashboard/currency-exposure', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, dict)

    def test_get_goals_progress(self, client, auth_headers):
        """Test getting investment goals progress."""
        response = client.get('/api/dashboard/goals', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_create_investment_goal(self, client, auth_headers):
        """Test creating investment goal."""
        goal_data = {
            'name': 'Retirement Fund',
            'target_amount': '1000000.00',
            'target_date': '2040-12-31',
            'description': 'Build retirement fund'
        }
        
        response = client.post('/api/dashboard/goals', json=goal_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['name'] == 'Retirement Fund'
        assert data['target_amount'] == '1000000.00'

    def test_update_investment_goal(self, client, auth_headers):
        """Test updating investment goal."""
        # First create goal
        goal_data = {
            'name': 'Emergency Fund',
            'target_amount': '50000.00',
            'target_date': '2025-12-31'
        }
        create_response = client.post('/api/dashboard/goals', json=goal_data, headers=auth_headers)
        goal_id = create_response.get_json()['id']
        
        # Then update
        update_data = {
            'target_amount': '75000.00'
        }
        response = client.put(f'/api/dashboard/goals/{goal_id}', json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['target_amount'] == '75000.00'

    def test_delete_investment_goal(self, client, auth_headers):
        """Test deleting investment goal."""
        # First create goal
        goal_data = {
            'name': 'House Down Payment',
            'target_amount': '100000.00',
            'target_date': '2026-06-30'
        }
        create_response = client.post('/api/dashboard/goals', json=goal_data, headers=auth_headers)
        goal_id = create_response.get_json()['id']
        
        # Then delete
        response = client.delete(f'/api/dashboard/goals/{goal_id}', headers=auth_headers)
        assert response.status_code == 200