from flask import Blueprint, jsonify, request
from app.models import Holding
from app.extensions import db

bp = Blueprint('holdings', __name__, url_prefix='/api/holdings')

@bp.route('/', methods=['GET'])
def get_holdings():
    holdings = Holding.query.all()
    return jsonify([holding.to_dict() for holding in holdings])

@bp.route('/<int:id>', methods=['GET'])
def get_holding(id):
    holding = Holding.query.get_or_404(id)
    return jsonify(holding.to_dict())

@bp.route('/', methods=['POST'])
def create_holding():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # Validate required fields
        required_fields = ['security_id', 'platform_id', 'quantity', 'average_cost']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Convert numeric fields
        data['quantity'] = float(data['quantity'])
        data['average_cost'] = float(data['average_cost'])
        data['total_cost'] = data['quantity'] * data['average_cost']

        new_holding = Holding(**data)
        db.session.add(new_holding)
        db.session.commit()
        return jsonify(new_holding.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>', methods=['PUT'])
def update_holding(id):
    try:
        holding = Holding.query.get_or_404(id)
        data = request.get_json()
        
        if 'quantity' in data:
            data['quantity'] = float(data['quantity'])
        if 'average_cost' in data:
            data['average_cost'] = float(data['average_cost'])
        if 'total_cost' in data:
            data['total_cost'] = float(data['total_cost'])
            
        for key, value in data.items():
            setattr(holding, key, value)
            
        db.session.commit()
        return jsonify(holding.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
def delete_holding(id):
    holding = Holding.query.get_or_404(id)
    db.session.delete(holding)
    db.session.commit()
    return '', 204