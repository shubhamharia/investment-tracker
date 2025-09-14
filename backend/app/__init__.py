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
        
    # Disable URL trailing slash redirect
    app.url_map.strict_slashes = False

    # Initialize extensions
    db.init_app(app)
    
    # Import and initialize blueprints
    from .api import init_app as init_api
    init_api(app)

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "error": "Not Found",
            "message": str(error)
        }), 404

    @app.errorhandler(Exception)
    def handle_error(error):
        print(f"Unhandled error: {str(error)}")  # Log the error
        import traceback
        traceback.print_exc()  # Print stack trace

        # Handle SQLAlchemy integrity errors
        if isinstance(error, db.exc.IntegrityError):
            return jsonify({
                "error": "Validation Error",
                "message": str(error)
            }), 400

        response = {
            "error": "Internal server error",
            "message": str(error),
            "type": type(error).__name__
        }
        return jsonify(response), 500

    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy'}

    return app