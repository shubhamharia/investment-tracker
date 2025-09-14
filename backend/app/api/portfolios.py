from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import desc
from app.models import Portfolio, Holding, Transaction, PortfolioPerformance
from app.extensions import db
from functools import wraps
from app.api.auth import token_required
from decimal import Decimal, InvalidOperation

bp = Blueprint('portfolios', __name__, url_prefix='/api/portfolios')

def validate_portfolio_data(data):
    """Validate portfolio creation/update data"""
    if not data:
        return False, "No data provided"
    if 'name' not in data:
        return False, "Portfolio name is required"
    if 'base_currency' in data:
        from app.constants import CURRENCY_CODES
        if data['base_currency'] not in CURRENCY_CODES:
            return False, f"Invalid currency code. Must be one of: {', '.join(CURRENCY_CODES)}"
    return True, None

@bp.route('/', methods=['GET'])
@token_required
def get_portfolios(current_user):
    portfolios = db.session.query(Portfolio).filter_by(user_id=current_user.id).all()
    return jsonify([portfolio.to_dict() for portfolio in portfolios])

@bp.route('/<int:id>', methods=['GET'])
@token_required
def get_portfolio(current_user, id):
    portfolio = db.session.get(Portfolio, id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404
    if portfolio.user_id != current_user.id:
        return jsonify({"error": "Unauthorized access"}), 403
    return jsonify(portfolio.to_dict())

@bp.route('/', methods=['POST'])
@token_required
def create_portfolio(current_user):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    is_valid, error = validate_portfolio_data(data)
    if not is_valid:
        return jsonify({"error": error}), 400
        
    try:
        portfolio = Portfolio(
            name=data['name'],
            user_id=current_user.id,
            description=data.get('description'),
            base_currency=data.get('base_currency', 'USD')
        )
        db.session.add(portfolio)
        db.session.commit()
        return jsonify(portfolio.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 503
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_portfolio(current_user, id):
    portfolio = db.session.get(Portfolio, id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404
    if portfolio.user_id != current_user.id:
        return jsonify({"error": "Unauthorized access"}), 403
    
    data = request.get_json()
    is_valid, error = validate_portfolio_data(data)
    if not is_valid:
        return jsonify({"error": error}), 400
    
    try:
        for key, value in data.items():
            if hasattr(portfolio, key):
                setattr(portfolio, key, value)
        db.session.commit()
        return jsonify(portfolio.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_portfolio(current_user, id):
    portfolio = db.session.get(Portfolio, id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404
    if portfolio.user_id != current_user.id:
        return jsonify({"error": "Unauthorized access"}), 403
    
    try:
        db.session.delete(portfolio)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>/holdings', methods=['GET'])
@token_required
def get_portfolio_holdings(current_user, id):
    """Get all holdings for a portfolio"""
    try:
        portfolio = db.session.get(Portfolio, id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        if portfolio.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
            
        holdings = portfolio.holdings  # Use relationship
        return jsonify([holding.to_dict() for holding in holdings])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>/transactions', methods=['GET'])
@token_required
def get_portfolio_transactions(current_user, id):
    """Get all transactions for a portfolio"""
    try:
        portfolio = db.session.get(Portfolio, id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        if portfolio.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
            
        transactions = portfolio.transactions  # Use relationship
        return jsonify([tx.to_dict() for tx in transactions])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>/performance', methods=['GET'])
@token_required
def get_portfolio_performance(current_user, id):
    """Get performance data for a portfolio"""
    try:
        portfolio = db.session.get(Portfolio, id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        if portfolio.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
            
        # Get the most recent performance snapshot
        performance = PortfolioPerformance.query\
            .filter_by(portfolio_id=portfolio.id)\
            .order_by(PortfolioPerformance.date.desc())\
            .first()
                      
        # Calculate current totals from holdings
        total_value = Decimal('0')
        cost_basis = Decimal('0')
        for holding in portfolio.holdings:
            cost_basis += Decimal(str(holding.total_cost or '0'))
            current_value = holding.current_value or Decimal(str(holding.total_cost))
            total_value += current_value
            
        returns = total_value - cost_basis
        return_percentage = (returns / cost_basis * 100) if cost_basis else Decimal('0')
            
        return jsonify({
            'total_value': str(total_value),
            'cost_basis': str(cost_basis),
            'returns': str(returns),
            'return_percentage': str(return_percentage)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>/value', methods=['GET'])
@token_required
def get_portfolio_value(current_user, id):
    """Get value data for a portfolio"""
    try:
        portfolio = db.session.get(Portfolio, id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        if portfolio.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
                      
        # Calculate current totals from holdings
        total_value = Decimal('0')
        total_cost = Decimal('0')
        for holding in portfolio.holdings:
            total_cost += Decimal(str(holding.total_cost or '0'))
            current_value = holding.current_value or Decimal(str(holding.total_cost))
            total_value += current_value
            
        unrealized_gain_loss = total_value - total_cost
        unrealized_gain_loss_pct = (unrealized_gain_loss / total_cost * 100) if total_cost else Decimal('0')
            
        return jsonify({
            'total_value': str(total_value),
            'total_cost': str(total_cost),
            'unrealized_gain_loss': str(unrealized_gain_loss),
            'unrealized_gain_loss_pct': str(unrealized_gain_loss_pct)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500