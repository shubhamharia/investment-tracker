from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from config import Config

db = SQLAlchemy()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)