from flask import Blueprint, jsonify, request, current_app
from ..models import Dividend, Security, Holding
from ..extensions import db
from datetime import datetime
from decimal import Decimal
from .auth import token_required

bp = Blueprint('dividends', __name__)

@bp.route('/api/dividends', methods=['POST'])
@token_required
def create_dividend(current_user):
    """Record a new dividend"""
    data = request.get_json()
    
    # Get the holding to get the quantity
    holding = Holding.query.filter_by(security_id=data['security_id']).first()
    if not holding:
        return jsonify({'error': 'No holding found for this security'}), 404

    dividend = Dividend(
        security_id=data['security_id'],
        portfolio_id=holding.portfolio_id,
        platform_id=holding.platform_id,
        ex_date=datetime.strptime(data['ex_date'], '%Y-%m-%d').date(),
        pay_date=datetime.strptime(data['payment_date'], '%Y-%m-%d').date(),
        dividend_per_share=Decimal(data['amount_per_share']),
        quantity_held=holding.quantity,
        currency=data['currency']
    )
    db.session.add(dividend)
    db.session.commit()
    
    return jsonify({
        'id': dividend.id,
        'security_id': dividend.security_id,
        'ex_date': dividend.ex_date.isoformat(),
        'pay_date': dividend.pay_date.isoformat(),
        'dividend_per_share': str(dividend.dividend_per_share),
        'currency': dividend.currency
    }), 201

@bp.route('/api/securities/<int:security_id>/dividends', methods=['GET'])
@token_required
def get_security_dividends(current_user, security_id):
    """Get dividend history for a security"""
    dividends = Dividend.query.filter_by(security_id=security_id).all()
    return jsonify([{
        'id': div.id,
        'ex_date': div.ex_date.isoformat(),
        'payment_date': div.payment_date.isoformat(),
        'amount_per_share': str(div.amount_per_share),
        'currency': div.currency
    } for div in dividends]), 200