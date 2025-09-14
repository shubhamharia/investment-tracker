import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.service_manager import ServiceManager
from app.services.price_service import PriceService
from app.services.dividend_service import DividendService
from app.services.portfolio_service import PortfolioService


class TestServiceManager:
    """Test service manager functionality."""

    @pytest.fixture
    def service_manager(self):
        """Create service manager instance."""
        return ServiceManager()

    def test_get_price_service(self, service_manager):
        """Test getting price service instance."""
        price_service = service_manager.get_price_service()
        assert isinstance(price_service, PriceService)
        
        # Test singleton pattern
        price_service2 = service_manager.get_price_service()
        assert price_service is price_service2

    def test_get_dividend_service(self, service_manager):
        """Test getting dividend service instance."""
        dividend_service = service_manager.get_dividend_service()
        assert isinstance(dividend_service, DividendService)
        
        # Test singleton pattern
        dividend_service2 = service_manager.get_dividend_service()
        assert dividend_service is dividend_service2

    def test_get_portfolio_service(self, service_manager):
        """Test getting portfolio service instance."""
        portfolio_service = service_manager.get_portfolio_service()
        assert isinstance(portfolio_service, PortfolioService)
        
        # Test singleton pattern
        portfolio_service2 = service_manager.get_portfolio_service()
        assert portfolio_service is portfolio_service2

    def test_initialize_services(self, service_manager):
        """Test initializing all services."""
        with patch.object(service_manager, '_initialize_price_service') as mock_price:
            with patch.object(service_manager, '_initialize_dividend_service') as mock_dividend:
                with patch.object(service_manager, '_initialize_portfolio_service') as mock_portfolio:
                    service_manager.initialize_services()
                    
                    mock_price.assert_called_once()
                    mock_dividend.assert_called_once()
                    mock_portfolio.assert_called_once()

    def test_refresh_all_prices(self, service_manager, sample_security):
        """Test refreshing prices for all securities."""
        mock_price_service = Mock()
        mock_price_service.update_security_price.return_value = True
        
        with patch.object(service_manager, 'get_price_service', return_value=mock_price_service):
            with patch.object(service_manager, '_get_all_securities', return_value=[sample_security]):
                result = service_manager.refresh_all_prices()
                
                assert result['total_processed'] == 1
                assert result['successful_updates'] == 1
                mock_price_service.update_security_price.assert_called_once_with(sample_security.symbol)

    def test_refresh_all_prices_with_errors(self, service_manager, sample_security):
        """Test refreshing prices with some errors."""
        mock_price_service = Mock()
        mock_price_service.update_security_price.side_effect = Exception("API Error")
        
        with patch.object(service_manager, 'get_price_service', return_value=mock_price_service):
            with patch.object(service_manager, '_get_all_securities', return_value=[sample_security]):
                result = service_manager.refresh_all_prices()
                
                assert result['total_processed'] == 1
                assert result['successful_updates'] == 0
                assert result['errors'] == 1

    def test_calculate_all_portfolio_values(self, service_manager, sample_portfolio):
        """Test calculating values for all portfolios."""
        mock_portfolio_service = Mock()
        mock_portfolio_service.calculate_portfolio_value.return_value = Decimal('20000')
        
        with patch.object(service_manager, 'get_portfolio_service', return_value=mock_portfolio_service):
            with patch.object(service_manager, '_get_all_portfolios', return_value=[sample_portfolio]):
                result = service_manager.calculate_all_portfolio_values()
                
                assert result['total_portfolios'] == 1
                assert sample_portfolio.id in result['portfolio_values']
                assert result['portfolio_values'][sample_portfolio.id] == Decimal('20000')

    def test_update_dividend_projections(self, service_manager, sample_security):
        """Test updating dividend projections for all securities."""
        mock_dividend_service = Mock()
        mock_dividend_service.project_next_dividend.return_value = {
            'projected_amount': Decimal('2.60'),
            'projected_date': datetime.now() + timedelta(days=90)
        }
        
        with patch.object(service_manager, 'get_dividend_service', return_value=mock_dividend_service):
            with patch.object(service_manager, '_get_dividend_paying_securities', return_value=[sample_security]):
                result = service_manager.update_dividend_projections()
                
                assert result['total_processed'] == 1
                assert result['projections_updated'] == 1

    def test_perform_daily_maintenance(self, service_manager):
        """Test performing daily maintenance tasks."""
        with patch.object(service_manager, 'refresh_all_prices', return_value={'successful_updates': 100}):
            with patch.object(service_manager, 'calculate_all_portfolio_values', return_value={'total_portfolios': 50}):
                with patch.object(service_manager, 'update_dividend_projections', return_value={'projections_updated': 25}):
                    with patch.object(service_manager, '_cleanup_old_data') as mock_cleanup:
                        result = service_manager.perform_daily_maintenance()
                        
                        assert 'price_updates' in result
                        assert 'portfolio_calculations' in result
                        assert 'dividend_projections' in result
                        mock_cleanup.assert_called_once()

    def test_get_system_health_status(self, service_manager):
        """Test getting system health status."""
        mock_price_service = Mock()
        mock_price_service.get_health_status.return_value = {'status': 'healthy', 'last_update': datetime.now()}
        
        mock_dividend_service = Mock()
        mock_dividend_service.get_health_status.return_value = {'status': 'healthy', 'last_calculation': datetime.now()}
        
        with patch.object(service_manager, 'get_price_service', return_value=mock_price_service):
            with patch.object(service_manager, 'get_dividend_service', return_value=mock_dividend_service):
                with patch.object(service_manager, '_check_database_health', return_value={'status': 'healthy'}):
                    health_status = service_manager.get_system_health_status()
                    
                    assert 'price_service' in health_status
                    assert 'dividend_service' in health_status
                    assert 'database' in health_status
                    assert health_status['overall_status'] in ['healthy', 'degraded', 'unhealthy']

    def test_bulk_update_security_data(self, service_manager):
        """Test bulk updating security data."""
        securities_data = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corp.', 'sector': 'Technology'},
            {'symbol': 'JNJ', 'name': 'Johnson & Johnson', 'sector': 'Healthcare'}
        ]
        
        with patch.object(service_manager, '_validate_security_data', return_value=True):
            with patch.object(service_manager, '_update_or_create_security') as mock_update:
                mock_update.return_value = True
                
                result = service_manager.bulk_update_security_data(securities_data)
                
                assert result['total_processed'] == 3
                assert result['successful_updates'] == 3
                assert mock_update.call_count == 3

    def test_schedule_background_tasks(self, service_manager):
        """Test scheduling background tasks."""
        with patch('celery.Celery') as mock_celery:
            mock_task = Mock()
            mock_celery.return_value.task.return_value = mock_task
            
            service_manager.schedule_background_tasks()
            
            # Verify tasks were scheduled
            mock_celery.assert_called()

    def test_get_service_metrics(self, service_manager):
        """Test getting service performance metrics."""
        mock_metrics = {
            'price_service': {'api_calls': 1000, 'success_rate': 0.98},
            'dividend_service': {'calculations': 500, 'cache_hits': 450},
            'portfolio_service': {'valuations': 200, 'avg_response_time': 0.15}
        }
        
        with patch.object(service_manager, '_collect_service_metrics', return_value=mock_metrics):
            metrics = service_manager.get_service_metrics()
            
            assert 'price_service' in metrics
            assert 'dividend_service' in metrics
            assert 'portfolio_service' in metrics

    def test_restart_services(self, service_manager):
        """Test restarting all services."""
        with patch.object(service_manager, '_stop_all_services') as mock_stop:
            with patch.object(service_manager, 'initialize_services') as mock_init:
                service_manager.restart_services()
                
                mock_stop.assert_called_once()
                mock_init.assert_called_once()

    def test_configure_service_settings(self, service_manager):
        """Test configuring service settings."""
        settings = {
            'price_service': {
                'api_rate_limit': 100,
                'cache_timeout': 300
            },
            'dividend_service': {
                'projection_window': 365,
                'confidence_threshold': 0.8
            }
        }
        
        with patch.object(service_manager, '_apply_service_settings') as mock_apply:
            service_manager.configure_service_settings(settings)
            
            mock_apply.assert_called_once_with(settings)

    def test_export_service_data(self, service_manager):
        """Test exporting service data."""
        export_config = {
            'include_prices': True,
            'include_dividends': True,
            'date_range': 30
        }
        
        mock_data = {
            'prices': [{'symbol': 'AAPL', 'price': 150.00}],
            'dividends': [{'symbol': 'AAPL', 'amount': 2.50}]
        }
        
        with patch.object(service_manager, '_collect_export_data', return_value=mock_data):
            with patch.object(service_manager, '_format_export_data') as mock_format:
                service_manager.export_service_data(export_config)
                
                mock_format.assert_called_once_with(mock_data, export_config)

    def test_handle_service_failure(self, service_manager):
        """Test handling service failures."""
        error_info = {
            'service': 'price_service',
            'error': 'API rate limit exceeded',
            'timestamp': datetime.now()
        }
        
        with patch.object(service_manager, '_log_service_error') as mock_log:
            with patch.object(service_manager, '_attempt_service_recovery') as mock_recovery:
                with patch.object(service_manager, '_notify_administrators') as mock_notify:
                    service_manager.handle_service_failure(error_info)
                    
                    mock_log.assert_called_once_with(error_info)
                    mock_recovery.assert_called_once()
                    mock_notify.assert_called_once()

    def test_validate_service_dependencies(self, service_manager):
        """Test validating service dependencies."""
        with patch.object(service_manager, '_check_database_connection', return_value=True):
            with patch.object(service_manager, '_check_external_apis', return_value=True):
                with patch.object(service_manager, '_check_cache_service', return_value=True):
                    validation_result = service_manager.validate_service_dependencies()
                    
                    assert validation_result['database'] is True
                    assert validation_result['external_apis'] is True
                    assert validation_result['cache_service'] is True
                    assert validation_result['overall_status'] is True

    def test_get_service_statistics(self, service_manager):
        """Test getting comprehensive service statistics."""
        with patch.object(service_manager, '_calculate_uptime', return_value=99.9):
            with patch.object(service_manager, '_get_error_rates', return_value={'price_service': 0.02}):
                with patch.object(service_manager, '_get_performance_stats', return_value={'avg_response_time': 0.25}):
                    stats = service_manager.get_service_statistics()
                    
                    assert 'uptime' in stats
                    assert 'error_rates' in stats
                    assert 'performance' in stats