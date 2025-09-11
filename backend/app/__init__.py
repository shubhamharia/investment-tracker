from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from .extensions import db
from .config import Config

def create_app(config_name='default'):
    app = Flask(__name__)
    
    if config_name == 'testing':
        app.config.from_object('app.config.TestConfig')
    else:
        app.config.from_object('app.config.Config')

    @app.errorhandler(Exception)
    def handle_error(error):
        print(f"Unhandled error: {str(error)}")  # Log the error
        import traceback
        traceback.print_exc()  # Print stack trace
        response = {
            "error": "Internal server error",
            "message": str(error),
            "type": type(error).__name__
        }
        return jsonify(response), 500

    # Initialize extensions
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # Create tables for all models

    # Register blueprints only if they haven't been registered
    if not hasattr(app, '_blueprints_registered'):
        from .api import init_app as init_api
        init_api(app)
        app._blueprints_registered = True

    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy'}

    return app