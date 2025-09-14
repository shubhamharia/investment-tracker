"""Service manager for coordinating and managing all application services."""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

# Singleton service instances
_price_service = None
_dividend_service = None
_portfolio_service = None

# Import services based on environment
from app.services.price_service import PriceService
from app.services.dividend_service import DividendService
from app.services.portfolio_service import PortfolioService


class ServiceManager:
    """Centralized service manager for coordinating all application services."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._services = {}
        self._health_status = {}
        self._metrics = {}
    
    def get_price_service(self) -> PriceService:
        """Get the price service instance."""
        global _price_service
        if not _price_service:
            _price_service = PriceService()
        return _price_service
    
    def get_dividend_service(self) -> DividendService:
        """Get the dividend service instance."""
        global _dividend_service
        if not _dividend_service:
            _dividend_service = DividendService()
        return _dividend_service
    
    def get_portfolio_service(self) -> PortfolioService:
        """Get the portfolio service instance."""
        global _portfolio_service
        if not _portfolio_service:
            _portfolio_service = PortfolioService()
        return _portfolio_service
    
    def initialize_services(self):
        """Initialize all services."""
        try:
            self._initialize_price_service()
            self._initialize_dividend_service()
            self._initialize_portfolio_service()
            self.logger.info("All services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _initialize_price_service(self):
        """Initialize price service."""
        price_service = self.get_price_service()
        # Additional initialization logic here
        
    def _initialize_dividend_service(self):
        """Initialize dividend service."""
        dividend_service = self.get_dividend_service()
        # Additional initialization logic here
        
    def _initialize_portfolio_service(self):
        """Initialize portfolio service."""
        portfolio_service = self.get_portfolio_service()
        # Additional initialization logic here
    
    def refresh_all_prices(self) -> Dict[str, Any]:
        """Refresh prices for all securities."""
        price_service = self.get_price_service()
        securities = self._get_all_securities()
        
        results = {
            'total_processed': 0,
            'successful_updates': 0,
            'errors': 0,
            'failed_symbols': []
        }
        
        for security in securities:
            try:
                results['total_processed'] += 1
                success = price_service.update_security_price(security.symbol)
                if success:
                    results['successful_updates'] += 1
                else:
                    results['errors'] += 1
                    results['failed_symbols'].append(security.symbol)
            except Exception as e:
                results['errors'] += 1
                results['failed_symbols'].append(security.symbol)
                self.logger.error(f"Failed to update price for {security.symbol}: {e}")
        
        return results
    
    def calculate_all_portfolio_values(self) -> Dict[str, Any]:
        """Calculate values for all portfolios."""
        portfolio_service = self.get_portfolio_service()
        portfolios = self._get_all_portfolios()
        
        results = {
            'total_portfolios': 0,
            'portfolio_values': {},
            'errors': []
        }
        
        for portfolio in portfolios:
            try:
                results['total_portfolios'] += 1
                value = portfolio_service.calculate_portfolio_value(portfolio.id)
                results['portfolio_values'][portfolio.id] = value
            except Exception as e:
                results['errors'].append(f"Portfolio {portfolio.id}: {str(e)}")
                self.logger.error(f"Failed to calculate value for portfolio {portfolio.id}: {e}")
        
        return results
    
    def update_dividend_projections(self) -> Dict[str, Any]:
        """Update dividend projections for all securities."""
        dividend_service = self.get_dividend_service()
        securities = self._get_dividend_paying_securities()
        
        results = {
            'total_processed': 0,
            'projections_updated': 0,
            'errors': 0
        }
        
        for security in securities:
            try:
                results['total_processed'] += 1
                projection = dividend_service.project_next_dividend(security.id)
                if projection:
                    results['projections_updated'] += 1
            except Exception as e:
                results['errors'] += 1
                self.logger.error(f"Failed to update dividend projection for {security.symbol}: {e}")
        
        return results
    
    def perform_daily_maintenance(self) -> Dict[str, Any]:
        """Perform daily maintenance tasks."""
        maintenance_results = {
            'timestamp': datetime.utcnow(),
            'price_updates': {},
            'portfolio_calculations': {},
            'dividend_projections': {},
            'cleanup_results': {}
        }
        
        try:
            # Refresh all prices
            maintenance_results['price_updates'] = self.refresh_all_prices()
            
            # Calculate portfolio values
            maintenance_results['portfolio_calculations'] = self.calculate_all_portfolio_values()
            
            # Update dividend projections
            maintenance_results['dividend_projections'] = self.update_dividend_projections()
            
            # Cleanup old data
            maintenance_results['cleanup_results'] = self._cleanup_old_data()
            
        except Exception as e:
            self.logger.error(f"Daily maintenance failed: {e}")
            maintenance_results['error'] = str(e)
        
        return maintenance_results
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        health_status = {
            'timestamp': datetime.utcnow(),
            'overall_status': 'healthy'
        }
        
        try:
            # Check price service health
            price_service = self.get_price_service()
            health_status['price_service'] = price_service.get_health_status()
            
            # Check dividend service health
            dividend_service = self.get_dividend_service()
            health_status['dividend_service'] = dividend_service.get_health_status()
            
            # Check database health
            health_status['database'] = self._check_database_health()
            
            # Determine overall status
            if any(status.get('status') == 'unhealthy' for status in health_status.values() if isinstance(status, dict)):
                health_status['overall_status'] = 'unhealthy'
            elif any(status.get('status') == 'degraded' for status in health_status.values() if isinstance(status, dict)):
                health_status['overall_status'] = 'degraded'
                
        except Exception as e:
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    def _get_all_securities(self) -> List:
        """Get all securities from database."""
        # Mock implementation - replace with actual database query
        return []
    
    def _get_all_portfolios(self) -> List:
        """Get all portfolios from database."""
        # Mock implementation - replace with actual database query
        return []
    
    def _get_dividend_paying_securities(self) -> List:
        """Get securities that pay dividends."""
        # Mock implementation - replace with actual database query
        return []
    
    def _cleanup_old_data(self) -> Dict[str, Any]:
        """Cleanup old data."""
        # Mock implementation
        return {'cleaned_records': 0}
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        # Mock implementation
        return {'status': 'healthy', 'connections': 5}
    
    def reset_services(self):
        """Reset all service instances."""
        global _price_service, _dividend_service, _portfolio_service
        _price_service = None
        _dividend_service = None
        _portfolio_service = None


# Legacy functions for backward compatibility
def get_price_service():
    """Get the price service instance."""
    global _price_service
    if not _price_service:
        _price_service = PriceService()
    return _price_service


def get_dividend_service():
    """Get the dividend service instance."""
    global _dividend_service
    if not _dividend_service:
        _dividend_service = DividendService()
    return _dividend_service


def reset_services():
    """Reset all service instances."""
    global _price_service, _dividend_service, _portfolio_service
    _price_service = None
    _dividend_service = None
    _portfolio_service = None

def set_services_for_testing(price_service=None, dividend_service=None):
    """Set mock services for testing"""
    global _price_service, _dividend_service
    reset_services()  # Reset services first
    if price_service is not None:
        _price_service = price_service
    if dividend_service is not None:
        _dividend_service = dividend_service