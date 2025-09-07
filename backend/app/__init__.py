from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from .extensions import db, celery

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    celery.conf.update(app.config)

    # Register blueprints (API routes)
    from .api import platforms, securities, transactions, users, portfolios, holdings
    app.register_blueprint(platforms.bp)
    app.register_blueprint(securities.bp)
    app.register_blueprint(transactions.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(portfolios.bp)
    app.register_blueprint(holdings.bp)

    return app