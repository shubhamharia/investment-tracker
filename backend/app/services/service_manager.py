"""Service manager for getting service instances"""
import os

# Singleton service instances
_price_service = None
_dividend_service = None

# Import services based on environment
from app.services.price_service import PriceService
from app.services.dividend_service import DividendService

def get_price_service():
    """Get the price service instance"""
    global _price_service
    if not _price_service:
        _price_service = PriceService()
    return _price_service

def get_dividend_service():
    """Get the dividend service instance"""
    global _dividend_service
    if not _dividend_service:
        _dividend_service = DividendService()
    return _dividend_service

def reset_services():
    """Reset all service instances"""
    global _price_service, _dividend_service
    _price_service = None
    _dividend_service = None

def set_services_for_testing(price_service=None, dividend_service=None):
    """Set mock services for testing"""
    global _price_service, _dividend_service
    reset_services()  # Reset services first
    if price_service is not None:
        _price_service = price_service
    if dividend_service is not None:
        _dividend_service = dividend_service