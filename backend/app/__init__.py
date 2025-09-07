from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .extensions import db
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from .api import init_app as init_api
    init_api(app)

    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy'}

    return app