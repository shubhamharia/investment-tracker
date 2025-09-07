# backend/app/config.py
import os
import sqlalchemy

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
        engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        inspector = sqlalchemy.inspect(engine)
        if not inspector.has_table("users"):  # Check for any table
            with app.app_context():
                db = app.extensions['sqlalchemy'].db
                db.create_all()
                print("Created database tables")

class TestConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'