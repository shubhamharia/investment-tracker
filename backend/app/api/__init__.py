from flask import Blueprint

def init_app(app):
    """Initialize the application with all required blueprints."""
    # Import blueprint factory functions
    from .securities import create_blueprint as create_securities_bp
    from .platforms import bp as platforms_bp
    from .transactions import bp as transactions_bp
    from .users import bp as users_bp
    from .portfolios import bp as portfolios_bp
    from .holdings import bp as holdings_bp
    from .auth import bp as auth_bp
    from .dividends import bp as dividends_bp
    from .mappings import bp as mappings_bp
    from .analytics import bp as analytics_bp
    from .performance import bp as performance_bp
    from .dashboard import bp as dashboard_bp

    # Create fresh blueprint instances for each app
    securities_bp = create_securities_bp()
    # Ensure portfolio-related submodules which attach routes to the portfolios blueprint are imported
    from . import portfolios_holdings

    # Register blueprints in a specific order to avoid conflicts
    app.register_blueprint(securities_bp)  # Register securities first as it's causing issues
    app.register_blueprint(platforms_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(portfolios_bp)
    app.register_blueprint(holdings_bp)
    app.register_blueprint(dividends_bp)
    # Register any additional app-level routes provided by modules
    try:
        from . import dividends as _div_mod
        if hasattr(_div_mod, 'register_additional_routes'):
            _div_mod.register_additional_routes(app)
    except Exception:
        pass
    app.register_blueprint(mappings_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(dashboard_bp)