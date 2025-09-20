from flask import Blueprint, jsonify, request, g, current_app
from functools import wraps
from app.models import User
from app.extensions import db
import jwt
from datetime import datetime, timedelta
import redis
import time

# Reuse validation helpers from users module
from app.api.users import validate_email, validate_password

# Initialize Redis client
import fakeredis
import os

if os.environ.get('FLASK_ENV') == 'testing':
    redis_client = fakeredis.FakeRedis()
else:
    redis_client = redis.Redis.from_url('redis://redis:6379/0')

def rate_limit(key_prefix, limit=10, period=60):
    """Rate limiting decorator using Redis
    
    Args:
        key_prefix (str): Prefix for Redis key (e.g. 'login')
        limit (int): Number of allowed requests
        period (int): Time period in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip rate limiting in test mode (either FLASK_ENV or Flask TESTING config)
            try:
                if os.environ.get('FLASK_ENV') == 'testing' or current_app.config.get('TESTING'):
                    return f(*args, **kwargs)
            except Exception:
                # If current_app isn't available, fallback to env var only
                if os.environ.get('FLASK_ENV') == 'testing':
                    return f(*args, **kwargs)
                
            # Create a key using IP address and prefix
            key = f"{key_prefix}:{request.remote_addr}"
            
            # Get current count
            count = redis_client.get(key)
            if count is None:
                # First request, set initial count and expiry
                redis_client.setex(key, period, 1)
            else:
                count = int(count)
                if count >= limit:
                    # Rate limit exceeded
                    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
                # Increment count
                redis_client.incr(key)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def create_access_token(user, expires_delta=None):
    """Create JWT access token for a user
    
    Args:
        user (User): The user to create token for
        expires_delta (timedelta, optional): Custom expiration time
        
    Returns:
        str: JWT token
    """
    return user.generate_auth_token(
        expiration=int(expires_delta.total_seconds()) if expires_delta else 86400
    )

def verify_token(token):
    """Verify JWT token and return associated user
    
    Args:
        token (str): JWT token to verify
        
    Returns:
        User: User object if token is valid
        
    Raises:
        Exception: If token is invalid
    """
    user = User.verify_auth_token(token)
    if user is None:
        raise Exception("Invalid token")
    return user

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401
            
        try:
            token = auth_header.split(" ")[1]
        except (IndexError, AttributeError):
            return jsonify({"error": "Invalid Authorization header format"}), 401
        
        try:
            current_user = User.verify_auth_token(token)
            if not current_user:
                return jsonify({"error": "Invalid token - user not found"}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        except Exception as e:
            return jsonify({"error": f"Token validation error: {str(e)}"}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

@bp.route('/login', methods=['POST'])
@rate_limit('login', limit=5, period=60)  # 5 attempts per minute
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    user = db.session.query(User).filter_by(username=username).first()
    if user and user.check_password(password):
        # Return a token and user data
        return jsonify({
            "access_token": user.generate_auth_token(),
            "token_type": "bearer",
            "user": user.to_dict()
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@bp.route('/change-password', methods=['POST'])
@token_required
@rate_limit('change_password', limit=3, period=300)  # 3 attempts per 5 minutes
def change_password(current_user):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not all([old_password, new_password]):
        return jsonify({"error": "All fields are required"}), 400
    
    if not current_user.check_password(old_password):
        return jsonify({"error": "Invalid current password"}), 401
    
    current_user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated successfully"}), 200


@bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint used by integration tests."""
    data = request.get_json(silent=True) or {}
    required = ['username', 'email', 'password']
    for k in required:
        if k not in data:
            return jsonify({'error': f'Missing required field: {k}'}), 400

    # Basic validation
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    if not validate_password(data['password']):
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400

    # Check duplicates
    existing = db.session.query(User).filter((User.username == data['username']) | (User.email == data['email'])).first()
    if existing:
        return jsonify({'error': 'Username or email already exists'}), 400

    try:
        user = User(username=data['username'], email=data['email'], first_name=data.get('first_name'), last_name=data.get('last_name'))
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500