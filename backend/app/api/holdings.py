from flask import Blueprint, jsonify, request
from decimal import Decimal
from app.models import Holding
from app.extensions import db

bp = Blueprint('holdings', __name__, url_prefix='/api/holdings')

@bp.route('/portfolio/<int:portfolio_id>', methods=['GET'])
def get_holdings(portfolio_id):
    holdings = Holding.query.filter_by(portfolio_id=portfolio_id).all()
    return jsonify([holding.to_dict() for holding in holdings])

@bp.route('/portfolio/<int:portfolio_id>/holding/<int:holding_id>', methods=['GET'])
def get_holding(portfolio_id, holding_id):
    holding = Holding.query.filter_by(portfolio_id=portfolio_id, id=holding_id).first_or_404()
    return jsonify(holding.to_dict())

@bp.route('/portfolio/<int:portfolio_id>/holding', methods=['POST'])
def create_holding(portfolio_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # Add portfolio_id to data
        data['portfolio_id'] = portfolio_id

        # Validate required fields
        required_fields = ['security_id', 'platform_id', 'quantity', 'average_cost']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        from decimal import Decimal
        
        holding = Holding(
            portfolio_id=portfolio_id,
            security_id=data['security_id'],
            platform_id=data['platform_id'],
            quantity=Decimal(str(data['quantity'])),
            average_cost=Decimal(str(data['average_cost'])),
            currency=data.get('currency', 'USD')
        )
        db.session.add(holding)
        db.session.commit()
        return jsonify(holding.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/portfolio/<int:portfolio_id>/holding/<int:holding_id>', methods=['PUT'])
def update_holding(portfolio_id, holding_id):
    holding = Holding.query.filter_by(portfolio_id=portfolio_id, id=holding_id).first_or_404()
    data = request.get_json()
    
    if 'quantity' in data:
        holding.quantity = Decimal(str(data['quantity']))
    if 'average_cost' in data:
        holding.average_cost = Decimal(str(data['average_cost']))
        
    db.session.commit()
    return jsonify(holding.to_dict())
    
@bp.route('/portfolio/<int:portfolio_id>/holding/<int:holding_id>', methods=['DELETE'])
def delete_holding(portfolio_id, holding_id):
    holding = Holding.query.filter_by(portfolio_id=portfolio_id, id=holding_id).first_or_404()
    db.session.delete(holding)
    db.session.commit()
    return '', 204
    
@bp.route('/portfolio/<int:portfolio_id>/holding/<int:holding_id>/value', methods=['GET'])
def get_holding_value(portfolio_id, holding_id):
    holding = Holding.query.filter_by(portfolio_id=portfolio_id, id=holding_id).first_or_404()
    holding.calculate_values()
    return jsonify({
        'current_value': str(holding.current_value),
        'unrealized_gain_loss': str(holding.unrealized_gain_loss),
    'unrealized_gain_loss_pct': str(holding.unrealized_gain_loss_pct)
})