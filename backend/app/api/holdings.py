from flask import Blueprint, jsonify, request
from decimal import Decimal, InvalidOperation
from app.models import Holding, Portfolio
from app.extensions import db
from app.api.auth import token_required
from flask import g

bp = Blueprint('holdings', __name__, url_prefix='/api/holdings')

def get_portfolio_and_holding(current_user, portfolio_id, holding_id=None):
    """Helper function to get portfolio and holding with authorization checks"""
    portfolio = db.session.get(Portfolio, portfolio_id)
    if not portfolio:
        return None, None, ('Portfolio not found', 404)
        
    if portfolio.user_id != current_user.id:
        return None, None, ('Unauthorized: portfolio does not belong to current user', 403)
    
    if holding_id is not None:
        holding = db.session.query(Holding).filter_by(portfolio_id=portfolio_id, id=holding_id).first()
        if not holding:
            return portfolio, None, ('Holding not found', 404)
        return portfolio, holding, None
    
    return portfolio, None, None

@bp.route('/portfolio/<int:portfolio_id>', methods=['GET'])
@token_required
def get_holdings(current_user, portfolio_id):
    # Check if the user owns the portfolio
    portfolio = db.session.get(Portfolio, portfolio_id)
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
        
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized: portfolio does not belong to current user'}), 403
    
    holdings = db.session.query(Holding).filter_by(portfolio_id=portfolio_id).all()
    return jsonify([holding.to_dict() for holding in holdings])

@bp.route('/portfolio/<int:portfolio_id>/holding/<int:holding_id>', methods=['GET'])
@token_required
def get_holding(current_user, portfolio_id, holding_id):
    # Check if the user owns the portfolio
    portfolio = db.session.get(Portfolio, portfolio_id)
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404
        
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized: portfolio does not belong to current user'}), 403
    
    holding = db.session.query(Holding).filter_by(portfolio_id=portfolio_id, id=holding_id).first()
    if not holding:
        return jsonify({"error": "Holding not found"}), 404
    return jsonify(holding.to_dict())

@bp.route('/portfolio/<int:portfolio_id>/holding', methods=['POST'])
@token_required
def create_holding(current_user, portfolio_id):
    try:
        portfolio, _, error = get_portfolio_and_holding(current_user, portfolio_id)
        if error:
            return jsonify({'error': error[0]}), error[1]
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # Add portfolio_id to data
        data['portfolio_id'] = portfolio_id

        # Validate required fields
        required_fields = ['security_id', 'platform_id', 'quantity', 'average_cost', 'currency']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        quantity = Decimal(str(data['quantity']))
        average_cost = Decimal(str(data['average_cost']))
        total_cost = data.get('total_cost')
        if total_cost is None:
            total_cost = quantity * average_cost
        else:
            total_cost = Decimal(str(total_cost))
        
        holding = Holding(
            portfolio_id=portfolio_id,
            security_id=data['security_id'],
            platform_id=data['platform_id'],
            quantity=quantity,
            average_cost=average_cost,
            total_cost=total_cost,
            currency=data['currency']
        )
        
        db.session.add(holding)
        db.session.commit()
        
        return jsonify(holding.to_dict()), 201
        
    except (ValueError, InvalidOperation) as e:
        return jsonify({"error": f"Invalid numeric value: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
        
@bp.route('/portfolio/<int:portfolio_id>/holding/<int:holding_id>', methods=['PUT'])
@token_required
def update_holding(current_user, portfolio_id, holding_id):
    try:
        _, holding, error = get_portfolio_and_holding(current_user, portfolio_id, holding_id)
        if error:
            return jsonify({'error': error[0]}), error[1]
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        if 'quantity' in data:
            holding.quantity = Decimal(str(data['quantity']))
        if 'average_cost' in data:
            holding.average_cost = Decimal(str(data['average_cost']))
        if 'total_cost' in data:
            holding.total_cost = Decimal(str(data['total_cost']))
        if 'currency' in data:
            holding.currency = data['currency']
        
        db.session.commit()
        return jsonify(holding.to_dict())
        
    except ValueError as e:
        return jsonify({"error": f"Invalid numeric value: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@bp.route('/portfolio/<int:portfolio_id>/holding/<int:holding_id>', methods=['DELETE'])
@token_required
def delete_holding(current_user, portfolio_id, holding_id):
    try:
        _, holding, error = get_portfolio_and_holding(current_user, portfolio_id, holding_id)
        if error:
            return jsonify({'error': error[0]}), error[1]
            
        db.session.delete(holding)
        db.session.commit()
        return "", 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@bp.route('/portfolio/<int:portfolio_id>/holding/<int:holding_id>/value', methods=['GET'])
@token_required
def get_holding_value(current_user, portfolio_id, holding_id):
    try:
        _, holding, error = get_portfolio_and_holding(current_user, portfolio_id, holding_id)
        if error:
            return jsonify({'error': error[0]}), error[1]
            
        current_price = float(holding.current_price) if holding.current_price else None
        current_value = float(holding.current_value) if holding.current_value else None
        unrealized_gain_loss = None
        if current_value is not None and holding.total_cost is not None:
            unrealized_gain_loss = current_value - float(holding.total_cost)
        
        return jsonify({
            "current_price": current_price,
            "current_value": current_value,
            "unrealized_gain_loss": unrealized_gain_loss,
            "currency": holding.currency
        })
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500