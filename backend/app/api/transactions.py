from flask import jsonify, request
from . import transactions_bp
from ..models import Transaction, Security, Platform
from ..services.constants import TRANSACTION_TYPES
from ..extensions import db
from datetime import datetime

@transactions_bp.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        transactions = (
            Transaction.query
            .join(Security)
            .join(Platform)
            .order_by(Transaction.transaction_date.desc())
            .all()
        )
        
        return jsonify({
            'transactions': [{
                'id': t.id,
                'date': t.transaction_date.isoformat(),
                'platform': t.platform.name,
                'security': t.security.name,
                'ticker': t.security.ticker,
                'type': t.transaction_type,
                'quantity': float(t.quantity),
                'price': float(t.price_per_share),
                'gross_amount': float(t.gross_amount),
                'net_amount': float(t.net_amount)
            } for t in transactions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/transactions', methods=['POST'])
def add_transaction():
    try:
        data = request.get_json()
        
        transaction = Transaction(
            platform_id=data['platform_id'],
            security_id=data['security_id'],
            transaction_type=data['transaction_type'],
            transaction_date=datetime.strptime(data['transaction_date'], '%Y-%m-%d').date(),
            quantity=data['quantity'],
            price_per_share=data['price_per_share'],
            gross_amount=data['gross_amount'],
            net_amount=data['net_amount'],
            currency=data['currency']
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({'message': 'Transaction added successfully', 'id': transaction.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500