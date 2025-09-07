from flask import Blueprint, jsonify, request
from app.models import Transaction
from app.extensions import db

bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@bp.route('/', methods=['GET'])
def get_transactions():
    transactions = Transaction.query.all()
    return jsonify([transaction.to_dict() for transaction in transactions])

@bp.route('/<int:id>', methods=['GET'])
def get_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    return jsonify(transaction.to_dict())

@bp.route('/', methods=['POST'])
def create_transaction():
    data = request.get_json()
    transaction = Transaction(
        portfolio_id=data['portfolio_id'],
        security_id=data['security_id'],
        transaction_type=data['transaction_type'],
        quantity=data['quantity'],
        price=data['price'],
        transaction_date=data['transaction_date'],
        fees=data.get('fees', 0.0)
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify(transaction.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
def update_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    data = request.get_json()
    
    for field in ['portfolio_id', 'security_id', 'transaction_type', 
                 'quantity', 'price', 'transaction_date', 'fees']:
        if field in data:
            setattr(transaction, field, data[field])
    
    db.session.commit()
    return jsonify(transaction.to_dict())

@bp.route('/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return '', 204