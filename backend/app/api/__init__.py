from flask import Blueprint
from .platforms import bp as platforms_bp
from .securities import bp as securities_bp
from .transactions import bp as transactions_bp
from .users import bp as users_bp
from .portfolios import bp as portfolios_bp
from .holdings import bp as holdings_bp

__all__ = ['platforms', 'securities', 'transactions', 'users', 'portfolios', 'holdings']

def init_app(app):
    app.register_blueprint(platforms_bp)
    app.register_blueprint(securities_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(portfolios_bp)
    app.register_blueprint(holdings_bp)