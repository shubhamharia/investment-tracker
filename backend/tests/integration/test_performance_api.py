import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta


class TestPerformanceAPI:
    """Test performance API endpoints."""

    def test_get_portfolio_performance(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio performance metrics."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_return' in data
        assert 'annualized_return' in data
        assert 'volatility' in data
        assert 'sharpe_ratio' in data

    def test_get_portfolio_performance_unauthorized(self, client, sample_portfolio):
        """Test getting portfolio performance without authentication."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}')
        assert response.status_code == 401

    def test_get_portfolio_performance_not_found(self, client, auth_headers):
        """Test getting performance for non-existent portfolio."""
        response = client.get('/api/performance/portfolio/99999', headers=auth_headers)
        assert response.status_code == 404

    def test_get_portfolio_performance_history(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio performance history."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/history', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_portfolio_performance_with_period(self, client, auth_headers, sample_portfolio):
        """Test getting portfolio performance with specific period."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}?period=1Y', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'period' in data
        assert data['period'] == '1Y'

    def test_get_benchmark_comparison(self, client, auth_headers, sample_portfolio):
        """Test getting benchmark comparison."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/benchmark', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'portfolio_return' in data
        assert 'benchmark_return' in data
        assert 'alpha' in data
        assert 'beta' in data

    def test_get_security_performance(self, client, auth_headers, sample_security):
        """Test getting security performance metrics."""
        response = client.get(f'/api/performance/security/{sample_security.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'price_return' in data
        assert 'total_return' in data
        assert 'volatility' in data

    def test_get_security_performance_history(self, client, auth_headers, sample_security):
        """Test getting security performance history."""
        response = client.get(f'/api/performance/security/{sample_security.id}/history', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_risk_metrics(self, client, auth_headers, sample_portfolio):
        """Test getting risk metrics."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/risk', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'var_95' in data
        assert 'var_99' in data
        assert 'max_drawdown' in data
        assert 'beta' in data

    def test_get_attribution_analysis(self, client, auth_headers, sample_portfolio):
        """Test getting performance attribution analysis."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/attribution', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'security_contribution' in data
        assert 'sector_contribution' in data

    def test_get_drawdown_analysis(self, client, auth_headers, sample_portfolio):
        """Test getting drawdown analysis."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/drawdown', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'current_drawdown' in data
        assert 'max_drawdown' in data
        assert 'drawdown_periods' in data

    def test_get_rolling_returns(self, client, auth_headers, sample_portfolio):
        """Test getting rolling returns analysis."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/rolling-returns', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'rolling_1m' in data
        assert 'rolling_3m' in data
        assert 'rolling_1y' in data

    def test_get_correlation_analysis(self, client, auth_headers, sample_portfolio):
        """Test getting correlation analysis."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/correlation', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'correlation_matrix' in data

    def test_get_performance_summary(self, client, auth_headers):
        """Test getting overall performance summary."""
        response = client.get('/api/performance/summary', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_return' in data
        assert 'best_performer' in data
        assert 'worst_performer' in data

    def test_get_sector_performance(self, client, auth_headers):
        """Test getting sector performance analysis."""
        response = client.get('/api/performance/sectors', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_platform_performance(self, client, auth_headers, sample_platform):
        """Test getting platform performance comparison."""
        response = client.get('/api/performance/platforms', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_holding_performance(self, client, auth_headers, sample_holding):
        """Test getting individual holding performance."""
        response = client.get(f'/api/performance/holding/{sample_holding.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'unrealized_gain_loss' in data
        assert 'percentage_gain_loss' in data

    def test_calculate_custom_benchmark(self, client, auth_headers, sample_portfolio):
        """Test calculating custom benchmark performance."""
        benchmark_data = {
            'components': [
                {'symbol': 'SPY', 'weight': 0.6},
                {'symbol': 'BND', 'weight': 0.4}
            ]
        }
        
        response = client.post(
            f'/api/performance/portfolio/{sample_portfolio.id}/custom-benchmark',
            json=benchmark_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'benchmark_return' in data
        assert 'comparison' in data

    def test_get_monte_carlo_simulation(self, client, auth_headers, sample_portfolio):
        """Test getting Monte Carlo simulation results."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/monte-carlo', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'scenarios' in data
        assert 'confidence_intervals' in data
        assert 'expected_return' in data

    def test_get_stress_test_results(self, client, auth_headers, sample_portfolio):
        """Test getting stress test results."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/stress-test', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'scenarios' in data
        assert 'impact' in data

    def test_run_custom_stress_test(self, client, auth_headers, sample_portfolio):
        """Test running custom stress test."""
        stress_test_data = {
            'scenarios': [
                {'name': 'Market Crash', 'equity_change': -0.3, 'bond_change': -0.1},
                {'name': 'Interest Rate Rise', 'equity_change': -0.1, 'bond_change': -0.2}
            ]
        }
        
        response = client.post(
            f'/api/performance/portfolio/{sample_portfolio.id}/stress-test',
            json=stress_test_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'results' in data

    def test_get_performance_rankings(self, client, auth_headers):
        """Test getting performance rankings among user's portfolios."""
        response = client.get('/api/performance/rankings', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_export_performance_report(self, client, auth_headers, sample_portfolio):
        """Test exporting performance report."""
        response = client.get(f'/api/performance/portfolio/{sample_portfolio.id}/export', headers=auth_headers)
        assert response.status_code == 200
        assert 'application/pdf' in response.headers.get('Content-Type', '') or \
               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers.get('Content-Type', '')

    def test_get_performance_alerts(self, client, auth_headers):
        """Test getting performance alerts."""
        response = client.get('/api/performance/alerts', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_create_performance_alert(self, client, auth_headers, sample_portfolio):
        """Test creating performance alert."""
        alert_data = {
            'portfolio_id': sample_portfolio.id,
            'alert_type': 'DRAWDOWN',
            'threshold': 0.1,  # 10% drawdown
            'message': 'Portfolio drawdown exceeds 10%'
        }
        
        response = client.post('/api/performance/alerts', json=alert_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['portfolio_id'] == sample_portfolio.id
        assert data['alert_type'] == 'DRAWDOWN'