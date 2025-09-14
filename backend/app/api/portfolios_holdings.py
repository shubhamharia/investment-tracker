from app.api.portfolios import bp
from flask import jsonify, request
from app.models import Portfolio, Holding, Transaction, PortfolioPerformance
from app.extensions import db
from app.api.auth import token_required
from datetime import datetime, date

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
            
        holdings = Holding.query.filter_by(portfolio_id=id).all()
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
            
        transactions = Transaction.query.filter_by(portfolio_id=id).order_by(Transaction.transaction_date.desc()).all()
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
        performance = (PortfolioPerformance.query
                      .filter_by(portfolio_id=id)
                      .order_by(PortfolioPerformance.date.desc())
                      .first())
                      
        if not performance:
            # If no performance data exists, calculate current totals
            holdings = Holding.query.filter_by(portfolio_id=id).all()
            total_value = sum(holding.current_value or 0 for holding in holdings)
            cost_basis = sum(holding.total_cost or 0 for holding in holdings)
            
            return jsonify({
                'total_value': str(total_value),
                'cost_basis': str(cost_basis),
                'returns': str(total_value - cost_basis),
                'return_percentage': str((total_value - cost_basis) / cost_basis * 100) if cost_basis else '0'
            })
            
        return jsonify(performance.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500