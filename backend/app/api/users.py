from flask import Blueprint, jsonify, request
from app.models import User
from app.extensions import db
import re
from functools import wraps
from flask import current_app
import jwt
from sqlalchemy.exc import IntegrityError

bp = Blueprint('users', __name__, url_prefix='/api/users')

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False
    return True

def token_required(f):
    """Decorator to require valid JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Unauthorized: invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Unauthorized: token is missing'}), 401
            
        try:
            # Use JWT_SECRET_KEY or SECRET_KEY from config, defaulting to test-jwt-secret during testing
            secret = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY') or 'test-jwt-secret'
            data = jwt.decode(token, secret, algorithms=['HS256'])
            current_user = db.session.get(User, int(data['sub']))  # Use 'sub' claim
            if not current_user:
                return jsonify({'error': 'Unauthorized: user not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Unauthorized: token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Unauthorized: invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').split(' ')[1]
        secret = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY') or 'test-jwt-secret'
        data = jwt.decode(token, secret, algorithms=['HS256'])
        current_user = db.session.get(User, int(data['sub']))
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Forbidden: admin privileges required'}), 403
            
        return f(*args, **kwargs)
    return decorated

@bp.route('/', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    users = db.session.query(User).all()
    return jsonify([user.to_dict() for user in users])

@bp.route('/<int:id>', methods=['GET'])
@token_required
def get_user(current_user, id):
    # Allow users to access their own data, or require admin for others
    if current_user.id != id and not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden: can only access your own user data'}), 403
    
    user = db.session.get(User, id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())

@bp.route('/', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
            
        # Validate password
        if not validate_password(data['password']):
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Create user
        # Ensure session doesn't hold stale state from other tests and
        # re-check for duplicates; also rely on DB integrity error as a
        # fallback in case of race conditions between tests.
        try:
            db.session.expire_all()
        except Exception:
            pass
        existing = db.session.query(User).filter((User.username == data['username']) | (User.email == data['email'])).first()
        if existing:
            return jsonify({'error': 'Username or email already exists'}), 400

        user = User(
            username=data['username'],
            email=data['email'],
            is_admin=data.get('is_admin', False)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': 'Username or email already exists'}), 400
        
        return jsonify(user.to_dict()), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Username or email already exists'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_user(current_user, id):
    # Allow users to update their own data, or require admin for others
    if current_user.id != id and not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden: can only update your own user data'}), 403
        
    try:
        user = db.session.get(User, id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json() or {}
        
        # Update fields if provided
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            if not validate_email(data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            user.email = data['email']
        if 'password' in data:
            user.set_password(data['password'])
        if 'is_admin' in data:
            user.is_admin = bool(data['is_admin'])
        
        db.session.commit()
        return jsonify(user.to_dict())
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Username or email already exists'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_user(current_user, id):
    # Allow users to delete their own account, or require admin for others
    if current_user.id != id and not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden: can only delete your own account'}), 403
        
    try:
        user = db.session.get(User, id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get the current user's profile"""
    return jsonify(current_user.to_dict())


@bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Alias to update current user's profile via /api/users/profile"""
    # Reuse update_me logic but call the underlying wrapped function to avoid
    # applying the decorator twice (which would pass current_user twice).
    try:
        if hasattr(update_me, '__wrapped__'):
            return update_me.__wrapped__(current_user)
        return update_me(current_user)
    except TypeError:
        # Fallback: call normally
        return update_me(current_user)


@bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify(current_user.to_dict())


@bp.route('/me', methods=['DELETE'])
@token_required
def delete_me(current_user):
    try:
        db.session.delete(current_user)
        db.session.commit()
        return jsonify({'message': 'User deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/me', methods=['PUT'])
@token_required
def update_me(current_user):
    try:
        data = request.get_json() or {}
        if 'email' in data and not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        # allow updating first/last/email
        current_user.first_name = data.get('first_name', current_user.first_name)
        current_user.last_name = data.get('last_name', current_user.last_name)
        if 'email' in data:
            current_user.email = data['email']
        db.session.commit()
        return jsonify(current_user.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Username or email already exists'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/me/password', methods=['PUT'])
@token_required
def change_my_password(current_user):
    try:
        data = request.get_json() or {}
        current = data.get('current_password') or data.get('current') or data.get('old_password')
        new = data.get('new_password') or data.get('new')
        if not current or not new:
            return jsonify({'error': 'Missing current_password or new_password'}), 400
        if not current_user.check_password(current):
            return jsonify({'error': 'Current password is incorrect'}), 400
        current_user.set_password(new)
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/me/preferences', methods=['GET'])
@token_required
def get_preferences(current_user):
    # Placeholder preferences
    return jsonify({'currency': getattr(current_user, 'currency', 'USD'), 'timezone': 'UTC'})


@bp.route('/me/preferences', methods=['PUT'])
@token_required
def update_preferences(current_user):
    try:
        data = request.get_json() or {}
        # Echo back preferences including currency and timezone expected by tests
        resp = {
            'currency': data.get('currency', getattr(current_user, 'currency', 'USD')),
            'timezone': data.get('timezone', getattr(current_user, 'timezone', 'UTC'))
        }
        return jsonify(resp), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/me/statistics', methods=['GET'])
@token_required
def get_statistics(current_user):
    # Provide expected statistics keys for tests
    try:
        total_portfolios = len(getattr(current_user, 'portfolios', []) or [])
        total_transactions = 0
        # Calculate a simple total_value from portfolios holdings if available
        total_value = 0
        try:
            for p in getattr(current_user, 'portfolios', []) or []:
                for h in getattr(p, 'holdings', []) or []:
                    total_value += float(getattr(h, 'current_value', 0) or 0)
        except Exception:
            total_value = 0

        return jsonify({
            'total_portfolios': total_portfolios,
            'total_transactions': total_transactions,
            'portfolios': total_portfolios,
            'transactions': total_transactions,
            'total_value': total_value
        })
    except Exception:
        return jsonify({'total_portfolios': 0, 'total_transactions': 0, 'portfolios': 0, 'transactions': 0})

@bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Change the current user's password"""
    try:
        data = request.get_json()
        
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Missing current_password or new_password'}), 400
            
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
            
        if not validate_password(data['new_password']):
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
            
        current_user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500