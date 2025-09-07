import os
import sqlalchemy

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/investment_tracker'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'

    @staticmethod
    def create_database(app):
        """Create the database if it doesn't exist."""
        engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        inspector = sqlalchemy.inspect(engine)
        if not inspector.has_table("platform"):  # Check for any table
            with app.app_context():
                from .extensions import db
                db.create_all()
                print("Created database tables")

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://portfolio_user:portfolio_pass@localhost/portfolio_test_db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}