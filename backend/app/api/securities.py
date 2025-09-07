from flask import Blueprint, jsonify, request
from app.models import Security
from app.extensions import db

bp = Blueprint('securities', __name__, url_prefix='/api/securities')

@bp.route('/', methods=['GET'])
def get_securities():
    securities = Security.query.all()
    return jsonify([security.to_dict() for security in securities])

@bp.route('/<int:id>', methods=['GET'])
def get_security(id):
    security = Security.query.get_or_404(id)
    return jsonify(security.to_dict())

@bp.route('/', methods=['POST'])
def create_security():
    data = request.get_json()
    security = Security(
        symbol=data['symbol'],
        name=data['name'],
        security_type=data['security_type'],
        currency=data.get('currency', 'USD'),
        description=data.get('description')
    )
    db.session.add(security)
    db.session.commit()
    return jsonify(security.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
def update_security(id):
    security = Security.query.get_or_404(id)
    data = request.get_json()
    
    security.symbol = data.get('symbol', security.symbol)
    security.name = data.get('name', security.name)
    security.security_type = data.get('security_type', security.security_type)
    security.currency = data.get('currency', security.currency)
    security.description = data.get('description', security.description)
    
    db.session.commit()
    return jsonify(security.to_dict())

@bp.route('/<int:id>', methods=['DELETE'])
def delete_security(id):
    security = Security.query.get_or_404(id)
    db.session.delete(security)
    db.session.commit()
    return '', 204