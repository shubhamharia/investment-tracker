from flask import Flask
from .extensions import db, migrate, cors, celery
from config import config
import logging

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    
    # Configure Celery
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    # Register blueprints
    from .api import dashboard_bp, portfolio_bp, transactions_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(portfolio_bp, url_prefix='/api')
    app.register_blueprint(transactions_bp, url_prefix='/api')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not Found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal Server Error'}, 500
    
    return app