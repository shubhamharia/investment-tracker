from flask import Blueprint, jsonify, request
from app.models import Security, PriceHistory
from app.extensions import db

bp = Blueprint('securities', __name__, url_prefix='/api/securities')

@bp.route('/', methods=['GET'])
def get_securities():
    securities = Security.query.all()
    return jsonify([security.to_dict() for security in securities])

@bp.route('/<int:security_id>', methods=['GET'])
def get_security(security_id):
    security = Security.query.get_or_404(security_id)
    return jsonify(security.to_dict())

@bp.route('/', methods=['POST'])
def create_security():
    data = request.get_json()
    
    # Validate required fields
    if not data.get('ticker') or not data.get('name'):
        return jsonify({'error': 'Ticker and name are required'}), 400
        
    # Validate currency
    if data.get('currency') and data['currency'] not in ['USD', 'EUR', 'GBP']:
        return jsonify({'error': 'Invalid currency'}), 400
        
    security = Security(
        ticker=data['ticker'],
        name=data['name'],
        currency=data.get('currency', 'USD'),
        yahoo_symbol=data.get('yahoo_symbol')
    )
    
    try:
        db.session.add(security)
        db.session.commit()
        return jsonify(security.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:security_id>', methods=['PUT'])
def update_security(security_id):
    security = Security.query.get_or_404(security_id)
    data = request.get_json()
    
    security.ticker = data.get('ticker', security.ticker)
    security.name = data.get('name', security.name)
    security.currency = data.get('currency', security.currency)
    security.yahoo_symbol = data.get('yahoo_symbol', security.yahoo_symbol)
    db.session.commit()
    return jsonify(security.to_dict())

@bp.route('/<int:security_id>/prices', methods=['GET'])
def get_security_prices(security_id):
    security = Security.query.get_or_404(security_id)
    prices = PriceHistory.query.filter_by(security_id=security_id).order_by(PriceHistory.price_date.desc()).all()
    return jsonify([price.to_dict() for price in prices])

@bp.route('/<int:security_id>', methods=['DELETE'])
def delete_security(security_id):
    security = Security.query.get_or_404(security_id)
    db.session.delete(security)
    db.session.commit()
    return '', 204
    
    db.session.commit()
    return jsonify(security.to_dict())

@bp.route('/<int:security_id>', methods=['DELETE'])
def delete_security(security_id):
    security = Security.query.get_or_404(id)
    db.session.delete(security)
    db.session.commit()
    return '', 204