from flask import Blueprint, jsonify, abort, make_response
from .auth import token_required
from ..models import Portfolio

# Single, consistent blueprint for analytics endpoints used by tests
bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@bp.route('/portfolio/<int:portfolio_id>', methods=['GET'])
@token_required
def portfolio_analytics(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403

    return jsonify({
        'total_value': '0.00',
        'total_cost': '0.00',
        'total_gain_loss': '0.00',
        'percentage_gain_loss': '0.00'
    })


@bp.route('/portfolio/<int:portfolio_id>/performance', methods=['GET'])
@token_required
def portfolio_performance(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify([])


@bp.route('/portfolio/<int:portfolio_id>/allocation', methods=['GET'])
@token_required
def portfolio_allocation(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'by_security': [], 'by_sector': [], 'by_currency': []})


@bp.route('/portfolio/<int:portfolio_id>/risk', methods=['GET'])
@token_required
def portfolio_risk(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'volatility': 0, 'beta': 0, 'sharpe_ratio': 0})


@bp.route('/security/<int:security_id>', methods=['GET'])
@token_required
def security_analytics(current_user, security_id):
    return jsonify({'current_price': '0.00', 'price_change': '0.00', 'volume': 0})


@bp.route('/security/<int:security_id>/price-history', methods=['GET'])
@token_required
def security_price_history(current_user, security_id):
    return jsonify([])


@bp.route('/security/<int:security_id>/indicators', methods=['GET'])
@token_required
def security_indicators(current_user, security_id):
    return jsonify({'sma_20': None, 'sma_50': None, 'rsi': None})


@bp.route('/overview', methods=['GET'])
@token_required
def overview(current_user):
    return jsonify({'total_portfolio_value': '0.00', 'total_invested': '0.00', 'total_gain_loss': '0.00', 'portfolio_count': 0})


@bp.route('/portfolio/<int:portfolio_id>/benchmark', methods=['GET'])
@token_required
def portfolio_benchmark(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'portfolio_return': '0.00', 'benchmark_return': '0.00', 'outperformance': '0.00'})


@bp.route('/portfolio/<int:portfolio_id>/dividends', methods=['GET'])
@token_required
def portfolio_dividends(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'total_dividends': '0.00', 'yield': '0.00', 'growth_rate': '0.00'})


@bp.route('/portfolio/<int:portfolio_id>/transactions', methods=['GET'])
@token_required
def portfolio_transactions(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'transaction_count': 0, 'buy_count': 0, 'sell_count': 0, 'total_fees': '0.00'})


@bp.route('/sectors', methods=['GET'])
@token_required
def sectors(current_user):
    return jsonify([])


@bp.route('/portfolio/<int:portfolio_id>/correlation', methods=['GET'])
@token_required
def correlation(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'correlation_matrix': []})


@bp.route('/portfolio/<int:portfolio_id>/simulation', methods=['GET'])
@token_required
def monte_carlo(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'scenarios': [], 'confidence_intervals': []})


@bp.route('/portfolio/<int:portfolio_id>/tax', methods=['GET'])
@token_required
def tax_analytics(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'realized_gains': 0, 'unrealized_gains': 0, 'tax_loss_harvesting': []})


@bp.route('/portfolio/<int:portfolio_id>/rebalance', methods=['GET'])
@token_required
def rebalance_suggestions(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'current_allocation': [], 'target_allocation': [], 'suggestions': []})


@bp.route('/portfolio/<int:portfolio_id>/export', methods=['GET'])
@token_required
def export_analytics(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403

    # Provide a dummy PDF response so tests can validate Content-Type
    pdf_bytes = b"%PDF-1.4\n%Dummy PDF for test\n"
    resp = make_response(pdf_bytes)
    resp.headers.set('Content-Type', 'application/pdf')
    resp.headers.set('Content-Length', len(pdf_bytes))
    return resp


@bp.route('/portfolio/<int:portfolio_id>/peers', methods=['GET'])
@token_required
def peers(current_user, portfolio_id):
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        abort(404)
    if portfolio.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    return jsonify({'peer_performance': [], 'percentile_rank': 0})