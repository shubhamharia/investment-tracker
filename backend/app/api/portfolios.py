from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import desc
from app.models import Portfolio, PortfolioPerformance
from app.extensions import db

bp = Blueprint('portfolios', __name__, url_prefix='/api/portfolios')

@bp.route('/', methods=['GET'])
def get_portfolios():
    portfolios = Portfolio.query.all()
    return jsonify([portfolio.to_dict() for portfolio in portfolios])

@bp.route('/<int:id>', methods=['GET'])
def get_portfolio(id):
    portfolio = Portfolio.query.get_or_404(id)
    return jsonify(portfolio.to_dict())

@bp.route('/', methods=['POST'])
def create_portfolio():
    data = request.get_json()
    new_portfolio = Portfolio(**data)
    db.session.add(new_portfolio)
    db.session.commit()
    return jsonify(new_portfolio.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
def update_portfolio(id):
    portfolio = Portfolio.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(portfolio, key, value)
    db.session.commit()
    return jsonify(portfolio.to_dict())

@bp.route('/<int:id>', methods=['DELETE'])
def delete_portfolio(id):
    portfolio = Portfolio.query.get_or_404(id)
    db.session.delete(portfolio)
    db.session.commit()
    return '', 204

@bp.route('/<int:id>/value', methods=['GET'])
def get_portfolio_value(id):
    try:
        portfolio = Portfolio.query.get_or_404(id)
        total_value = sum(holding.current_value or 0 for holding in portfolio.holdings)
        total_cost = sum(holding.total_cost or 0 for holding in portfolio.holdings)
        unrealized_gain_loss = total_value - total_cost
        
        return jsonify({
            'portfolio_id': portfolio.id,
            'total_value': total_value,
            'total_cost': total_cost,
            'unrealized_gain_loss': unrealized_gain_loss,
            'unrealized_gain_loss_pct': (unrealized_gain_loss / total_cost * 100) if total_cost else 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:id>/holdings', methods=['POST'])
def add_holding(id):
    try:
        portfolio = Portfolio.query.get_or_404(id)
        data = request.get_json()
        
        # Add portfolio_id to the data
        data['portfolio_id'] = portfolio.id
        
        # Convert numeric fields to Decimal for precise calculations
        from decimal import Decimal
        if 'quantity' in data:
            data['quantity'] = Decimal(str(data['quantity']))
        if 'average_cost' in data:
            data['average_cost'] = Decimal(str(data['average_cost']))
        
        # Calculate total_cost
        if 'quantity' in data and 'average_cost' in data:
            data['total_cost'] = data['quantity'] * data['average_cost']
        
        from app.models import Holding
        new_holding = Holding(**data)
        db.session.add(new_holding)
        db.session.commit()
        return jsonify(new_holding.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500