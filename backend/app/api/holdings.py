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
        
        from decimal import Decimal
        
        # Convert numeric fields to Decimal
        if 'quantity' in data:
            data['quantity'] = Decimal(str(data['quantity']))
        if 'average_cost' in data:
            data['average_cost'] = Decimal(str(data['average_cost']))
            
        # Update total_cost if both quantity and average_cost are present
        if 'quantity' in data and 'average_cost' in data:
            data['total_cost'] = data['quantity'] * data['average_cost']
        elif 'quantity' in data:
            data['total_cost'] = data['quantity'] * holding.average_cost
        elif 'average_cost' in data:
            data['total_cost'] = holding.quantity * data['average_cost']
            
        # Update holding fields
        for key, value in data.items():
            setattr(holding, key, value)
            
        holding.calculate_values()
        db.session.commit()
        
        return jsonify(holding.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
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