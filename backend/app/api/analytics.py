from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from decimal import Decimal
from ..models import Portfolio, Holding, PriceHistory, Dividend
from ..extensions import db
from .auth import token_required

bp = Blueprint('analytics', __name__)

def calculate_portfolio_metrics(portfolio, start_date=None, end_date=None):
    """Calculate detailed portfolio performance metrics"""
    # Get all holdings
    holdings = Holding.query.filter_by(portfolio_id=portfolio.id).all()

    # Calculate basic metrics
    total_cost = sum(h.total_cost or Decimal('0') for h in holdings)
    total_value = sum(h.current_value or Decimal('0') for h in holdings)
    unrealized_gains = total_value - total_cost

    # Get price histories
    price_histories = []
    for holding in holdings:
        query = PriceHistory.query.filter_by(security_id=holding.security_id)
        if start_date:
            query = query.filter(PriceHistory.price_date >= start_date)
        if end_date:
            query = query.filter(PriceHistory.price_date <= end_date)
        price_histories.extend(query.order_by(PriceHistory.price_date).all())

    # Calculate total return
    dividends = Dividend.query.filter(
        Dividend.security_id.in_([h.security_id for h in holdings])
    )
    if start_date:
        dividends = dividends.filter(Dividend.ex_date >= start_date)
    if end_date:
        dividends = dividends.filter(Dividend.ex_date <= end_date)
    dividend_income = sum(
        d.amount_per_share * h.quantity
        for d in dividends.all()
        for h in holdings
        if h.security_id == d.security_id
    )

    # Calculate performance metrics
    try:
        if total_cost > 0:
            return_pct = ((total_value - total_cost) / total_cost) * 100
            total_return = unrealized_gains + dividend_income
            dividend_yield = (dividend_income / total_cost) * 100
        else:
            return_pct = Decimal('0')
            total_return = Decimal('0')
            dividend_yield = Decimal('0')
    except (TypeError, ZeroDivisionError):
        return_pct = Decimal('0')
        total_return = Decimal('0')
        dividend_yield = Decimal('0')

    return {
        'total_return': str(total_return),
        'return_percentage': str(return_pct),
        'market_value': str(total_value),
        'cost_basis': str(total_cost),
        'realized_gains': '0.00',  # To be implemented
        'unrealized_gains': str(unrealized_gains),
        'dividend_income': str(dividend_income),
        'dividend_yield': str(dividend_yield),
        'performance_metrics': {
            'alpha': '0.00',  # To be implemented
            'beta': '1.00',   # To be implemented
            'sharpe_ratio': '0.00',  # To be implemented
            'volatility': '0.00'  # To be implemented
        }
    }

@bp.route('/api/portfolios/<int:portfolio_id>/analytics', methods=['GET'])
@token_required
def get_portfolio_analytics(current_user, portfolio_id):
    """Get detailed portfolio analytics"""
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403

    # Parse period parameter
    period = request.args.get('period', 'YTD')
    if period == 'YTD':
        start_date = datetime(datetime.now().year, 1, 1).date()
        end_date = datetime.now().date()
    elif period == '1Y':
        start_date = (datetime.now().date() - timedelta(days=365))
        end_date = datetime.now().date()
    else:
        start_date = None
        end_date = None

    analytics = calculate_portfolio_metrics(portfolio, start_date, end_date)
    return jsonify(analytics)

@bp.route('/api/portfolios/<int:portfolio_id>/reports/tax', methods=['GET'])
@token_required
def generate_tax_report(current_user, portfolio_id):
    """Generate tax report for portfolio"""
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403

    # Get report year
    year = request.args.get('year', datetime.now().year)
    try:
        year = int(year)
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
    except ValueError:
        return jsonify({'error': 'Invalid year'}), 400

    # Get all relevant transactions
    holdings = Holding.query.filter_by(portfolio_id=portfolio_id).all()

    # Calculate tax metrics
    dividend_income = sum(
        d.amount_per_share * h.quantity
        for h in holdings
        for d in Dividend.query.filter(
            Dividend.security_id == h.security_id,
            Dividend.ex_date >= start_date,
            Dividend.ex_date <= end_date
        ).all()
    )

    return jsonify({
        'realized_gains': {
            'short_term': '0.00',  # To be implemented
            'long_term': '0.00'    # To be implemented
        },
        'dividend_income': str(dividend_income),
        'tax_summary': {
            'total_taxable_amount': str(dividend_income),
            'estimated_tax': str(dividend_income * Decimal('0.15'))  # Assuming 15% tax rate
        }
    })