import os
import time
from app.extensions import db

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/portfolio')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

    # API
    API_TITLE = 'Investment Tracker API'
    API_VERSION = 'v1'

    @staticmethod
    def create_database(app):
        """Create the database if it doesn't exist."""
        retries = 5
        while retries > 0:
            try:
                with app.app_context():
                    db.create_all()
                    print("Created database tables")
                return
            except Exception as e:
                if retries > 1:
                    retries -= 1
                    print(f"Database connection failed. Retrying... ({retries} attempts left)")
                    time.sleep(5)
                else:
                    raise e

class TestConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:?foreign_keys=ON'