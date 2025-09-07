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
        retries = 5
        while retries > 0:
            try:
                engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
                inspector = sqlalchemy.inspect(engine)
                
                # Create tables if they don't exist
                with app.app_context():
                    from app.extensions import db
                    db.create_all()
                    print("Database tables ready")
                return
            except Exception as e:
                if retries > 1:
                    retries -= 1
                    print(f"Database initialization failed. Retrying... ({retries} attempts left)")
                    print(f"Error: {str(e)}")
                    import time
                    time.sleep(5)
                else:
                    print("Failed to initialize database after all retries")
                    raise

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}