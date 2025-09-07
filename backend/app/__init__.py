import os
from flask import Flask
from config import Config  # Changed from `..config` to `config`
from .extensions import db
from .api import platforms, securities, transactions, users, portfolios, holdings
from celery import Celery

def create_app(config_class=Config):
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Initialize and configure Celery
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)

    # Register blueprints (API routes)
    app.register_blueprint(platforms.bp)
    app.register_blueprint(securities.bp)
    app.register_blueprint(transactions.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(portfolios.bp)
    app.register_blueprint(holdings.bp)

    return app, celery

# The final, crucial step: create the app instance for Gunicorn
app, celery = create_app()
