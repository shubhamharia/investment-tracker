from flask import Blueprint, jsonify, request
from app.models import Platform
from app.extensions import db

bp = Blueprint('platforms', __name__, url_prefix='/api/platforms')

@bp.route('/', methods=['GET'])
def get_platforms():
    platforms = Platform.query.all()
    return jsonify([platform.to_dict() for platform in platforms])

@bp.route('/<int:id>', methods=['GET'])
def get_platform(id):
    platform = Platform.query.get_or_404(id)
    return jsonify(platform.to_dict())

@bp.route('/', methods=['POST'])
def create_platform():
    data = request.get_json()
    platform = Platform(
        name=data['name'],
        description=data.get('description')
    )
    db.session.add(platform)
    db.session.commit()
    return jsonify(platform.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
def update_platform(id):
    platform = Platform.query.get_or_404(id)
    data = request.get_json()
    platform.name = data.get('name', platform.name)
    platform.description = data.get('description', platform.description)
    db.session.commit()
    return jsonify(platform.to_dict())

@bp.route('/<int:id>', methods=['DELETE'])
def delete_platform(id):
    platform = Platform.query.get_or_404(id)
    db.session.delete(platform)
    db.session.commit()
    return '', 204