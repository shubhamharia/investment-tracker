from flask import Blueprint
from .platforms import bp as platforms_bp
from .securities import bp as securities_bp
from .transactions import bp as transactions_bp
from .users import bp as users_bp
from .portfolios import bp as portfolios_bp
from .holdings import bp as holdings_bp

__all__ = ['platforms', 'securities', 'transactions', 'users', 'portfolios', 'holdings']