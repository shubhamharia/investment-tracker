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
        user = User(
            username=data['username'],
            email=data['email'],
            is_admin=data.get('is_admin', False)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user.to_dict()), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Username or email already exists'}), 409
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
        
        data = request.get_json()
        
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
        return jsonify({'error': 'Username or email already exists'}), 409
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
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get the current user's profile"""
    return jsonify(current_user.to_dict())

@bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Change the current user's password"""
    try:
        data = request.get_json()
        
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Missing current_password or new_password'}), 400
            
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
            
        if not validate_password(data['new_password']):
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
            
        current_user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500