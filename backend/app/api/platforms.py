from flask import Blueprint, jsonify, request
from app.models import Platform
from app.extensions import db

bp = Blueprint('platforms', __name__, url_prefix='/api/platforms')

@bp.route('/', methods=['GET'])
def get_platforms():
    try:
        platforms = Platform.query.all()
        return jsonify([platform.to_dict() for platform in platforms])
    except Exception as e:
        return jsonify({'error': 'Failed to fetch platforms', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['GET'])
def get_platform(id):
    try:
        platform = Platform.query.get_or_404(id)
        return jsonify(platform.to_dict())
    except Exception as e:
        return jsonify({'error': 'Platform not found', 'details': str(e)}), 404

@bp.route('/', methods=['POST'])
def create_platform():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Platform name is required'}), 400
            
        # Check for duplicate platform names
        existing_platform = Platform.query.filter_by(name=data['name']).first()
        if existing_platform:
            return jsonify({'error': 'Platform with this name already exists'}), 409
        
        platform = Platform(
            name=data['name'],
            description=data.get('description'),
            account_type=data.get('account_type', 'general')  # Add default account type
        )
        
        db.session.add(platform)
        db.session.commit()
        return jsonify(platform.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create platform', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['PUT'])
def update_platform(id):
    try:
        platform = Platform.query.get_or_404(id)
        data = request.get_json()
        
        # Check for name conflicts if name is being updated
        if 'name' in data and data['name'] != platform.name:
            existing_platform = Platform.query.filter_by(name=data['name']).first()
            if existing_platform:
                return jsonify({'error': 'Platform with this name already exists'}), 409
        
        platform.name = data.get('name', platform.name)
        platform.description = data.get('description', platform.description)
        platform.account_type = data.get('account_type', platform.account_type)
        
        db.session.commit()
        return jsonify(platform.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update platform', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
def delete_platform(id):
    try:
        platform = Platform.query.get_or_404(id)
        
        # Check if platform has any associated holdings
        if platform.holdings.count() > 0:
            return jsonify({
                'error': 'Cannot delete platform with existing holdings',
                'details': 'Please remove all holdings from this platform first'
            }), 400
        
        db.session.delete(platform)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete platform', 'details': str(e)}), 500