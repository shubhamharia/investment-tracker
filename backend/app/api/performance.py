from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from decimal import Decimal
from ..models import Portfolio, Security, PriceHistory
from ..extensions import db
from .auth import token_required

bp = Blueprint('performance', __name__)

@bp.route('/api/portfolios/<int:portfolio_id>/reports/performance', methods=['GET'])
@token_required
def generate_performance_report(current_user, portfolio_id):
    """Generate detailed performance report for portfolio"""
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

    # Get holdings summary
    holdings = portfolio.holdings
    holdings_data = []
    for holding in holdings:
        latest_price = PriceHistory.query.filter_by(
            security_id=holding.security_id
        ).order_by(
            PriceHistory.price_date.desc()
        ).first()

        if latest_price:
            price = latest_price.close_price
        else:
            price = holding.current_price or holding.average_cost

        holdings_data.append({
            'security': holding.security.ticker,
            'quantity': str(holding.quantity),
            'avg_cost': str(holding.average_cost),
            'current_price': str(price),
            'market_value': str(holding.quantity * price),
            'gain_loss': str(Decimal(str(holding.quantity * price)) - holding.total_cost),
            'gain_loss_pct': str(((Decimal(str(holding.quantity * price)) - holding.total_cost) / holding.total_cost * 100 if holding.total_cost else 0))
        })

    # Get basic performance metrics
    total_value = sum(Decimal(h['market_value']) for h in holdings_data)
    total_cost = sum(h.total_cost for h in holdings)
    total_gain = total_value - total_cost

    # Calculate portfolio breakdown
    by_security = {}
    for holding in holdings_data:
        by_security[holding['security']] = float(holding['market_value'])
    
    total = sum(by_security.values())
    for security, value in by_security.items():
        by_security[security] = (value / total * 100) if total > 0 else 0

    total_gain_loss_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0
    return jsonify({
        'portfolio_summary': {
            'total_value': str(total_value),
            'total_cost': str(total_cost),
            'total_gain': str(total_gain),
            'return_pct': str((total_gain / total_cost * 100) if total_cost > 0 else 0)
        },
        'holdings_breakdown': holdings_data,
        'allocation': {
            'by_security': by_security
        },
        'charts_data': {
            'labels': list(by_security.keys()),
            'values': list(by_security.values())
        },
        'total_gain_loss_pct': str(total_gain_loss_pct),
        'holdings': [holding.to_dict() for holding in holdings]
    })
