"""Compatibility shim: re-export PortfolioPerformance from .portfolio

This file prevents SQLAlchemy from seeing two separate Table definitions
when tests import `app.models.portfolio_performance` and `app.models.portfolio`.
The canonical model lives in `app.models.portfolio.PortfolioPerformance`.
"""
from .portfolio import PortfolioPerformance  # noqa: F401

__all__ = ["PortfolioPerformance"]