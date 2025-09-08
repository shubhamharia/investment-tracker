from flask import Blueprint, jsonify, request
from app.models import Portfolio
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
        value = sum(holding.current_value for holding in portfolio.holdings)
        return jsonify({
            'portfolio_id': portfolio.id,
            'value': value
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500