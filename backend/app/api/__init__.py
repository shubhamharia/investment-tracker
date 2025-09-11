from flask import Blueprint

def init_app(app):
    """Initialize the application with all required blueprints."""
    from .platforms import bp as platforms_bp
    from .securities import bp as securities_bp
    from .transactions import bp as transactions_bp
    from .users import bp as users_bp
    from .portfolios import bp as portfolios_bp
    from .holdings import bp as holdings_bp

    # Define all blueprints that need to be registered
    blueprints = {
        'platforms': platforms_bp,
        'securities': securities_bp,
        'transactions': transactions_bp,
        'users': users_bp,
        'portfolios': portfolios_bp,
        'holdings': holdings_bp
    }

    # Remove any existing blueprint registrations to avoid conflicts
    for name in blueprints:
        if name in app.blueprints:
            app.blueprints.pop(name)
            app.view_functions = {
                key: value for key, value in app.view_functions.items()
                if not key.startswith(f"{name}.")
            }

    # Register all blueprints fresh
    for name, blueprint in blueprints.items():
        app.register_blueprint(blueprint)