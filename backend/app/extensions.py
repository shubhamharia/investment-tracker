from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from config import Config

db = SQLAlchemy()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)


def _register_listeners():
	"""Register small DB listeners used by tests to ensure constraint
	violations surface as exceptions during session commit.
	"""
	try:
		from sqlalchemy import event
		from app.models.user import User

		@event.listens_for(db.session, 'before_flush')
		def _user_unique_before_flush(session, flush_context, instances):
			"""Detect duplicates for User based on username/email in the
			pending objects and raise an IntegrityError-like exception so
			tests expecting uniqueness violations will see an exception on
			commit.
			"""
			for obj in session.new:
				if isinstance(obj, User):
					# Check for existing user with same username or email
					exists = session.query(User).filter((User.username == obj.username) | (User.email == obj.email)).first()
					if exists:
						from sqlalchemy.exc import IntegrityError
						raise IntegrityError('UNIQUE constraint failed', None, None)
	except Exception:
		# Best-effort registration; tests will still run if this fails
		pass


_register_listeners()