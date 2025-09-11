from flask import Blueprint

def init_app(app):
    # Only register blueprints if they haven't been registered
    if hasattr(app, '_blueprints_registered'):
        return
        
    from .platforms import bp as platforms_bp
    from .securities import bp as securities_bp
    from .transactions import bp as transactions_bp
    from .users import bp as users_bp
    from .portfolios import bp as portfolios_bp
    from .holdings import bp as holdings_bp

    blueprints = [
        (platforms_bp, 'platforms'),
        (securities_bp, 'securities'),
        (transactions_bp, 'transactions'),
        (users_bp, 'users'),
        (portfolios_bp, 'portfolios'),
        (holdings_bp, 'holdings')
    ]

    for blueprint, name in blueprints:
        if name not in app.blueprints:
            app.register_blueprint(blueprint)
            
    app._blueprints_registered = True