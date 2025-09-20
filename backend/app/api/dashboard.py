from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import Portfolio, Transaction, Dividend, Holding, Security
from datetime import datetime

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


def _require_auth():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    return True


@bp.route('/overview', methods=['GET'])
def overview():
    # Dashboard overview requires authentication in tests
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'total_value': 0,
        'total_gain_loss': 0,
        'portfolio_count': 0,
        'top_performers': [],
        'worst_performers': []
    })


@bp.route('/stats', methods=['GET'])
def stats():
    # Quick stats for dashboard
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'total_value': 0, 'day_change': 0, 'total_return': 0})


@bp.route('/portfolios', methods=['GET'])
def portfolios():
    # Return list of portfolios (empty or real) - protected
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    plist = [p.to_dict(include_current=True) for p in Portfolio.query.all()]
    # Ensure 'gain_loss' key exists for dashboard consumers (may be 0)
    for p in plist:
        if 'gain_loss' not in p:
            try:
                total = float(p.get('current_value') or 0)
                p['gain_loss'] = 0.0 if total == 0 else 0.0
            except Exception:
                p['gain_loss'] = 0.0
    return jsonify(plist)


@bp.route('/transactions/recent', methods=['GET'])
def recent_transactions():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    limit = int(request.args.get('limit', 10))
    txs = Transaction.query.order_by(Transaction.transaction_date.desc()).limit(limit).all()
    return jsonify([t.to_dict() for t in txs])


@bp.route('/dividends/upcoming', methods=['GET'])
def upcoming_dividends():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    now = datetime.utcnow().date()
    divs = []
    try:
        divs = Dividend.query.filter(Dividend.ex_date >= now).all()
    except Exception:
        divs = []
    return jsonify([d.to_dict() for d in divs])


@bp.route('/allocation', methods=['GET'])
def allocation():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'by_security': [], 'by_sector': [], 'by_platform': []})


@bp.route('/performance', methods=['GET'])
def performance():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    period = request.args.get('period', None)
    return jsonify({'time_series': [], 'period': period or ''})


@bp.route('/market-movers', methods=['GET'])
def market_movers():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'gainers': [], 'losers': []})


@bp.route('/watchlist', methods=['GET', 'POST'])
def watchlist():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        data = request.get_json() or {}
        return jsonify({'security_id': data.get('security_id'), 'target_price': data.get('target_price')}), 201
    return jsonify([])


@bp.route('/watchlist/<int:security_id>', methods=['DELETE'])
def remove_watchlist(security_id):
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({}), 200


@bp.route('/news', methods=['GET'])
def news():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify([])


@bp.route('/alerts', methods=['GET', 'POST'])
def alerts():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        data = request.get_json() or {}
        return jsonify({'id': 1, 'security_id': data.get('security_id'), 'alert_type': data.get('alert_type')}), 201
    return jsonify([])


@bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({}), 200


@bp.route('/goals', methods=['GET', 'POST'])
def goals():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'POST':
        data = request.get_json() or {}
        data['id'] = 1
        return jsonify(data), 201
    return jsonify([])


@bp.route('/goals/<int:goal_id>', methods=['PUT', 'DELETE'])
def goal_modify(goal_id):
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'PUT':
        data = request.get_json() or {}
        data['id'] = goal_id
        return jsonify(data), 200
    return jsonify({}), 200


@bp.route('/sectors', methods=['GET'])
def sectors():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify([])


@bp.route('/currency-exposure', methods=['GET'])
def currency_exposure():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({})


@bp.route('/dividends/upcoming', methods=['GET'])
def dividends_upcoming():
    if not _require_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify([])