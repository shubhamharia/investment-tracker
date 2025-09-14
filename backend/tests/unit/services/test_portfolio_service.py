import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.portfolio_service import PortfolioService
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.transaction import Transaction


class TestPortfolioService:
    """Test portfolio service functionality."""

    @pytest.fixture
    def service(self):
        """Create portfolio service instance."""
        return PortfolioService()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return Mock()

    def test_calculate_portfolio_value(self, service, sample_portfolio):
        """Test calculating total portfolio value."""
        # Mock holdings with current prices
        mock_holdings = [
            Mock(quantity=Decimal('100'), security_id=1),
            Mock(quantity=Decimal('50'), security_id=2)
        ]
        
        mock_prices = {1: Decimal('150.00'), 2: Decimal('80.00')}
        
        with patch.object(service, '_get_portfolio_holdings', return_value=mock_holdings):
            with patch.object(service, '_get_current_prices', return_value=mock_prices):
                total_value = service.calculate_portfolio_value(sample_portfolio.id)
                
                # Expected: (100 * 150) + (50 * 80) = 19000
                assert total_value == Decimal('19000.00')

    def test_calculate_portfolio_value_no_holdings(self, service, sample_portfolio):
        """Test calculating portfolio value with no holdings."""
        with patch.object(service, '_get_portfolio_holdings', return_value=[]):
            total_value = service.calculate_portfolio_value(sample_portfolio.id)
            assert total_value == Decimal('0.00')

    def test_calculate_portfolio_performance(self, service, sample_portfolio):
        """Test calculating portfolio performance metrics."""
        # Mock historical values
        historical_values = [
            {'date': datetime.now() - timedelta(days=365), 'value': Decimal('18000')},
            {'date': datetime.now() - timedelta(days=180), 'value': Decimal('18500')},
            {'date': datetime.now(), 'value': Decimal('19000')}
        ]
        
        with patch.object(service, '_get_historical_values', return_value=historical_values):
            performance = service.calculate_portfolio_performance(sample_portfolio.id)
            
            assert 'total_return' in performance
            assert 'annualized_return' in performance
            assert 'volatility' in performance

    def test_calculate_asset_allocation(self, service, sample_portfolio):
        """Test calculating asset allocation."""
        # Mock holdings with sector information
        mock_holdings = [
            Mock(
                quantity=Decimal('100'),
                current_price=Decimal('150'),
                security=Mock(sector='Technology')
            ),
            Mock(
                quantity=Decimal('50'),
                current_price=Decimal('80'),
                security=Mock(sector='Healthcare')
            )
        ]
        
        with patch.object(service, '_get_portfolio_holdings_with_securities', return_value=mock_holdings):
            allocation = service.calculate_asset_allocation(sample_portfolio.id)
            
            assert 'by_sector' in allocation
            assert 'by_security' in allocation
            assert allocation['by_sector']['Technology'] == pytest.approx(78.95, rel=0.01)
            assert allocation['by_sector']['Healthcare'] == pytest.approx(21.05, rel=0.01)

    def test_rebalance_portfolio(self, service, sample_portfolio):
        """Test portfolio rebalancing suggestions."""
        # Mock current allocation
        current_allocation = {
            'Technology': 0.8,
            'Healthcare': 0.2
        }
        
        # Target allocation
        target_allocation = {
            'Technology': 0.6,
            'Healthcare': 0.4
        }
        
        portfolio_value = Decimal('20000')
        
        with patch.object(service, 'calculate_asset_allocation', return_value={'by_sector': current_allocation}):
            with patch.object(service, 'calculate_portfolio_value', return_value=portfolio_value):
                suggestions = service.rebalance_portfolio(sample_portfolio.id, target_allocation)
                
                assert 'trades' in suggestions
                assert 'rebalance_amount' in suggestions

    def test_calculate_risk_metrics(self, service, sample_portfolio):
        """Test calculating portfolio risk metrics."""
        # Mock historical returns
        returns = [0.02, -0.01, 0.03, -0.02, 0.01, 0.04, -0.01]
        
        with patch.object(service, '_calculate_daily_returns', return_value=returns):
            risk_metrics = service.calculate_risk_metrics(sample_portfolio.id)
            
            assert 'volatility' in risk_metrics
            assert 'var_95' in risk_metrics
            assert 'var_99' in risk_metrics
            assert 'max_drawdown' in risk_metrics

    def test_compare_with_benchmark(self, service, sample_portfolio):
        """Test comparing portfolio performance with benchmark."""
        # Mock portfolio and benchmark returns
        portfolio_returns = [0.02, -0.01, 0.03, -0.02, 0.01]
        benchmark_returns = [0.015, -0.005, 0.025, -0.015, 0.008]
        
        with patch.object(service, '_get_portfolio_returns', return_value=portfolio_returns):
            with patch.object(service, '_get_benchmark_returns', return_value=benchmark_returns):
                comparison = service.compare_with_benchmark(sample_portfolio.id, 'SPY')
                
                assert 'alpha' in comparison
                assert 'beta' in comparison
                assert 'correlation' in comparison
                assert 'tracking_error' in comparison

    def test_get_top_performers(self, service, sample_portfolio):
        """Test getting top performing holdings."""
        # Mock holdings with performance data
        mock_holdings = [
            Mock(
                security=Mock(symbol='AAPL'),
                unrealized_gain_loss=Decimal('1000'),
                percentage_gain_loss=15.5
            ),
            Mock(
                security=Mock(symbol='MSFT'),
                unrealized_gain_loss=Decimal('500'),
                percentage_gain_loss=8.2
            ),
            Mock(
                security=Mock(symbol='GOOGL'),
                unrealized_gain_loss=Decimal('-200'),
                percentage_gain_loss=-3.1
            )
        ]
        
        with patch.object(service, '_get_holdings_with_performance', return_value=mock_holdings):
            top_performers = service.get_top_performers(sample_portfolio.id, limit=2)
            
            assert len(top_performers) == 2
            assert top_performers[0]['symbol'] == 'AAPL'
            assert top_performers[1]['symbol'] == 'MSFT'

    def test_get_worst_performers(self, service, sample_portfolio):
        """Test getting worst performing holdings."""
        mock_holdings = [
            Mock(
                security=Mock(symbol='AAPL'),
                unrealized_gain_loss=Decimal('1000'),
                percentage_gain_loss=15.5
            ),
            Mock(
                security=Mock(symbol='GOOGL'),
                unrealized_gain_loss=Decimal('-200'),
                percentage_gain_loss=-3.1
            )
        ]
        
        with patch.object(service, '_get_holdings_with_performance', return_value=mock_holdings):
            worst_performers = service.get_worst_performers(sample_portfolio.id, limit=1)
            
            assert len(worst_performers) == 1
            assert worst_performers[0]['symbol'] == 'GOOGL'

    def test_calculate_correlation_matrix(self, service, sample_portfolio):
        """Test calculating correlation matrix for portfolio holdings."""
        # Mock price data for holdings
        price_data = {
            'AAPL': [150, 152, 148, 155, 153],
            'MSFT': [280, 285, 275, 290, 288],
            'GOOGL': [2800, 2850, 2750, 2900, 2880]
        }
        
        with patch.object(service, '_get_holdings_price_data', return_value=price_data):
            correlation_matrix = service.calculate_correlation_matrix(sample_portfolio.id)
            
            assert isinstance(correlation_matrix, dict)
            assert 'AAPL' in correlation_matrix
            assert 'MSFT' in correlation_matrix['AAPL']

    def test_optimize_portfolio(self, service, sample_portfolio):
        """Test portfolio optimization using modern portfolio theory."""
        # Mock expected returns and covariance matrix
        expected_returns = {'AAPL': 0.12, 'MSFT': 0.10, 'GOOGL': 0.15}
        covariance_matrix = {
            'AAPL': {'AAPL': 0.04, 'MSFT': 0.02, 'GOOGL': 0.03},
            'MSFT': {'AAPL': 0.02, 'MSFT': 0.03, 'GOOGL': 0.02},
            'GOOGL': {'AAPL': 0.03, 'MSFT': 0.02, 'GOOGL': 0.05}
        }
        
        with patch.object(service, '_calculate_expected_returns', return_value=expected_returns):
            with patch.object(service, '_calculate_covariance_matrix', return_value=covariance_matrix):
                optimization = service.optimize_portfolio(sample_portfolio.id, target_return=0.12)
                
                assert 'optimal_weights' in optimization
                assert 'expected_return' in optimization
                assert 'expected_risk' in optimization

    def test_generate_performance_report(self, service, sample_portfolio):
        """Test generating comprehensive performance report."""
        with patch.multiple(service,
                          calculate_portfolio_value=Mock(return_value=Decimal('20000')),
                          calculate_portfolio_performance=Mock(return_value={'total_return': 0.15}),
                          calculate_risk_metrics=Mock(return_value={'volatility': 0.12}),
                          get_top_performers=Mock(return_value=[]),
                          get_worst_performers=Mock(return_value=[])):
            
            report = service.generate_performance_report(sample_portfolio.id)
            
            assert 'current_value' in report
            assert 'performance' in report
            assert 'risk' in report
            assert 'top_performers' in report
            assert 'worst_performers' in report

    def test_calculate_sharpe_ratio(self, service, sample_portfolio):
        """Test calculating Sharpe ratio."""
        portfolio_return = 0.12
        risk_free_rate = 0.03
        volatility = 0.15
        
        with patch.object(service, '_get_portfolio_return', return_value=portfolio_return):
            with patch.object(service, '_get_risk_free_rate', return_value=risk_free_rate):
                with patch.object(service, '_get_portfolio_volatility', return_value=volatility):
                    sharpe_ratio = service.calculate_sharpe_ratio(sample_portfolio.id)
                    
                    # Expected: (0.12 - 0.03) / 0.15 = 0.6
                    assert sharpe_ratio == pytest.approx(0.6, rel=0.01)

    def test_analyze_drawdowns(self, service, sample_portfolio):
        """Test analyzing portfolio drawdowns."""
        # Mock portfolio value history
        value_history = [
            {'date': datetime(2024, 1, 1), 'value': Decimal('20000')},
            {'date': datetime(2024, 2, 1), 'value': Decimal('18000')},  # 10% drawdown
            {'date': datetime(2024, 3, 1), 'value': Decimal('17000')},  # 15% drawdown (max)
            {'date': datetime(2024, 4, 1), 'value': Decimal('19000')},  # Recovery
            {'date': datetime(2024, 5, 1), 'value': Decimal('21000')}   # New high
        ]
        
        with patch.object(service, '_get_portfolio_value_history', return_value=value_history):
            drawdown_analysis = service.analyze_drawdowns(sample_portfolio.id)
            
            assert 'max_drawdown' in drawdown_analysis
            assert 'current_drawdown' in drawdown_analysis
            assert 'drawdown_periods' in drawdown_analysis

    def test_stress_test_portfolio(self, service, sample_portfolio):
        """Test stress testing portfolio under various scenarios."""
        scenarios = [
            {'name': 'Market Crash', 'equity_change': -0.3, 'bond_change': -0.1},
            {'name': 'Interest Rate Rise', 'equity_change': -0.1, 'bond_change': -0.2}
        ]
        
        # Mock current allocation
        allocation = {
            'by_asset_class': {'Equity': 0.7, 'Fixed Income': 0.3}
        }
        
        current_value = Decimal('20000')
        
        with patch.object(service, 'calculate_asset_allocation', return_value=allocation):
            with patch.object(service, 'calculate_portfolio_value', return_value=current_value):
                stress_test = service.stress_test_portfolio(sample_portfolio.id, scenarios)
                
                assert 'scenario_results' in stress_test
                assert len(stress_test['scenario_results']) == 2

    def test_calculate_tax_efficiency(self, service, sample_portfolio):
        """Test calculating portfolio tax efficiency."""
        # Mock holdings with tax information
        holdings_data = [
            {'symbol': 'AAPL', 'gain_loss': Decimal('1000'), 'holding_period': 400},  # Long-term
            {'symbol': 'MSFT', 'gain_loss': Decimal('500'), 'holding_period': 200},   # Short-term
            {'symbol': 'GOOGL', 'gain_loss': Decimal('-300'), 'holding_period': 100}  # Loss
        ]
        
        with patch.object(service, '_get_holdings_tax_data', return_value=holdings_data):
            tax_efficiency = service.calculate_tax_efficiency(sample_portfolio.id)
            
            assert 'tax_efficiency_ratio' in tax_efficiency
            assert 'tax_loss_harvesting_opportunities' in tax_efficiency
            assert 'estimated_tax_liability' in tax_efficiency