import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta


class TestAnalyticsAPI:
    """Test analytics API endpoints."""

    def test_get_portfolio_analytics(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio analytics."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_value' in data
        assert 'total_cost' in data
        assert 'total_gain_loss' in data
        assert 'percentage_gain_loss' in data

    def test_get_portfolio_analytics_unauthorized(self, client, sample_portfolio):
        """Test getting portfolio analytics without authentication."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}')
        assert response.status_code == 401

    def test_get_portfolio_analytics_not_found(self, client, auth_headers):
        """Test getting analytics for non-existent portfolio."""
        response = client.get('/api/analytics/portfolio/99999', headers=auth_headers)
        assert response.status_code == 404

    def test_get_portfolio_performance_history(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio performance history."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/performance', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_portfolio_allocation(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio allocation analysis."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/allocation', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'by_security' in data
        assert 'by_sector' in data
        assert 'by_currency' in data

    def test_get_portfolio_risk_metrics(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio risk metrics."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/risk', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'volatility' in data
        assert 'beta' in data
        assert 'sharpe_ratio' in data

    def test_get_security_analytics(self, client, auth_headers, sample_security):
        """Test getting security analytics."""
        response = client.get(f'/api/analytics/security/{sample_security.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'current_price' in data
        assert 'price_change' in data
        assert 'volume' in data

    def test_get_security_price_history(self, client, auth_headers, sample_security):
        """Test getting security price history."""
        response = client.get(f'/api/analytics/security/{sample_security.id}/price-history', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_security_technical_indicators(self, client, auth_headers, sample_security):
        """Test getting security technical indicators."""
        response = client.get(f'/api/analytics/security/{sample_security.id}/indicators', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'sma_20' in data
        assert 'sma_50' in data
        assert 'rsi' in data

    def test_get_overall_analytics(self, client, auth_headers):
        """Test getting overall user analytics."""
        response = client.get('/api/analytics/overview', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_portfolio_value' in data
        assert 'total_invested' in data
        assert 'total_gain_loss' in data
        assert 'portfolio_count' in data

    def test_get_performance_comparison(self, client, auth_headers, sample_portfolio):
        """Test getting performance comparison with benchmarks."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/benchmark', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'portfolio_return' in data
        assert 'benchmark_return' in data
        assert 'outperformance' in data

    def test_get_dividend_analytics(self, client, auth_headers, sample_portfolio):
        """Test getting dividend analytics."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/dividends', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_dividends' in data
        assert 'yield' in data
        assert 'growth_rate' in data

    def test_get_transaction_analytics(self, client, auth_headers, sample_portfolio):
        """Test getting transaction analytics."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/transactions', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'transaction_count' in data
        assert 'buy_count' in data
        assert 'sell_count' in data
        assert 'total_fees' in data

    def test_get_sector_analysis(self, client, auth_headers):
        """Test getting sector analysis."""
        response = client.get('/api/analytics/sectors', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_correlation_matrix(self, client, auth_headers, sample_portfolio):
        """Test getting correlation matrix for portfolio holdings."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/correlation', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'correlation_matrix' in data

    def test_get_monte_carlo_simulation(self, client, auth_headers, sample_portfolio):
        """Test getting Monte Carlo simulation results."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/simulation', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'scenarios' in data
        assert 'confidence_intervals' in data

    def test_get_analytics_with_date_range(self, client, auth_headers, sample_portfolio):
        """Test getting analytics with specific date range."""
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        response = client.get(
            f'/api/analytics/portfolio/{sample_portfolio.id}?start_date={start_date}&end_date={end_date}',
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_tax_analytics(self, client, auth_headers, sample_portfolio):
        """Test getting tax analytics."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/tax', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'realized_gains' in data
        assert 'unrealized_gains' in data
        assert 'tax_loss_harvesting' in data

    def test_get_rebalancing_suggestions(self, client, auth_headers, sample_portfolio):
        """Test getting rebalancing suggestions."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/rebalance', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'current_allocation' in data
        assert 'target_allocation' in data
        assert 'suggestions' in data

    def test_export_analytics_report(self, client, auth_headers, sample_portfolio):
        """Test exporting analytics report."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/export', headers=auth_headers)
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '') or \
               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers.get('Content-Type', '')

    def test_get_peer_comparison(self, client, auth_headers, sample_portfolio):
        """Test getting peer comparison analytics."""
        response = client.get(f'/api/analytics/portfolio/{sample_portfolio.id}/peers', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'peer_performance' in data
        assert 'percentile_rank' in data