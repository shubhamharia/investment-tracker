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
    data = request.get_json()
    new_user = User(**data)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

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