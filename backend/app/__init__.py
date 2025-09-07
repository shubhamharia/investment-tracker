from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from ..config import Config
from .extensions import db, celery
from .api import api_bp # It's a good practice to use the imported blueprint object directly

def create_app(config_class=Config):
    """Factory function for creating the Flask app instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    celery.conf.update(app.config)

    # Register blueprints (API routes)
    # The import needs to be inside the function to avoid circular import issues
    from .api import platforms, securities, transactions, users, portfolios, holdings
    app.register_blueprint(platforms.bp)
    app.register_blueprint(securities.bp)
    app.register_blueprint(transactions.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(portfolios.bp)
    app.register_blueprint(holdings.bp)

    # Optional: You may have more initialization logic here

    return app

# The final, crucial step: create the app instance for Gunicorn
app = create_app()
