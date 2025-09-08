from flask import Blueprint, jsonify, request
from app.models import User
from app.extensions import db

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@bp.route('/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())

@bp.route('/', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
            
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Check if user already exists
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 409

        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({"error": "Email already exists"}), 409

        new_user = User(
            username=data['username'],
            email=data['email']
        )
        new_user.set_password(data['password'])
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify(new_user.to_dict()), 201
        except Exception as db_error:
            db.session.rollback()
            import traceback
            error_details = {
                "error": str(db_error),
                "traceback": traceback.format_exc()
            }
            print("Database error:", error_details)
            return jsonify({"error": "Failed to create user", "details": str(db_error)}), 500
            return jsonify({"error": "Database error", "details": str(db_error)}), 500
            
        return jsonify(new_user.to_dict()), 201
        
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        import traceback
        traceback.print_exc()  # Print full traceback
        return jsonify({
            "error": "Internal server error",
            "type": type(e).__name__,
            "details": str(e)
        }), 500

@bp.route('/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(user, key, value)
    db.session.commit()
    return jsonify(user.to_dict())

@bp.route('/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return '', 204