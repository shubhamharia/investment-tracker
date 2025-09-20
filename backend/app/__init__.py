from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from .extensions import db
from .config import Config

def create_app(config=None):
    """Create Flask app.

    Accept either a config name string (e.g. 'testing') or a config
    dictionary with config keys. Tests call `create_app({...})`, so
    support that usage by updating app.config when a dict is passed.
    """
    app = Flask(__name__)

    # Support passing a dict of config overrides (used by tests)
    if isinstance(config, dict):
        # Load defaults first then overlay provided config
        app.config.from_object('app.config.Config')
        app.config.update(config)
    else:
        if config == 'testing':
            app.config.from_object('app.config.TestConfig')
        else:
            app.config.from_object('app.config.Config')
        
    # Disable URL trailing slash redirect
    app.url_map.strict_slashes = False

    # Initialize extensions
    db.init_app(app)
    # If running under tests, explicitly create all tables at startup so the
    # test request context doesn't have to attempt schema creation in a
    # before_request hook. This makes the test lifecycle more deterministic
    # and keeps schema setup separate from request handling.
    if app.config.get('TESTING'):
        with app.app_context():
            try:
                # (Silent) create tables using configured DB URI for tests
                db.create_all()
            except Exception:
                # If creation fails, let the normal request handling surface
                # the underlying error rather than hiding it here.
                pass
    
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

    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_error(error):
        # Preserve HTTPExceptions so Flask test assertions get proper status codes
        if isinstance(error, HTTPException):
            return jsonify({
                'error': error.name,
                'message': error.description
            }), error.code

        print(f"Unhandled error: {str(error)}")  # Log the error
        import traceback
        traceback.print_exc()  # Print stack trace

        # Handle SQLAlchemy integrity errors
        try:
            from sqlalchemy.exc import IntegrityError
            if isinstance(error, IntegrityError):
                return jsonify({
                    "error": "Validation Error",
                    "message": str(error)
                }), 400
        except Exception:
            pass

        response = {
            "error": "Internal server error",
            "message": str(error),
            "type": type(error).__name__
        }
        return jsonify(response), 500

    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy'}

    # Backwards-compatible health endpoint expected by tests
    @app.route('/health')
    def legacy_health():
        return {'status': 'healthy'}

    # (Removed request-time schema creation; tests should rely on fixture-managed
    # schema setup or the explicit startup-time create_all above.)

    return app