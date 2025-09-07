from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .extensions import db
from .config import Config

def create_app(config_name='default'):
    app = Flask(__name__)
    
    if config_name == 'testing':
        app.config.from_object('app.config.TestConfig')
    else:
        app.config.from_object('app.config.Config')

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from .api import init_app as init_api
    init_api(app)

    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy'}

    return app