from flask import Blueprint, jsonify, request
from decimal import Decimal
from app.models import Transaction, Holding
from app.extensions import db
from app.constants import DECIMAL_PLACES, TRANSACTION_TYPES as VALID_TRANSACTION_TYPES

bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@bp.route('/', methods=['GET'])
def get_transactions():
    try:
        transactions = Transaction.query.all()
        return jsonify([transaction.to_dict() for transaction in transactions])
    except Exception as e:
        return jsonify({'error': 'Failed to fetch transactions', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['GET'])
def get_transaction(id):
    try:
        transaction = Transaction.query.get_or_404(id)
        return jsonify(transaction.to_dict())
    except Exception as e:
        return jsonify({'error': 'Transaction not found', 'details': str(e)}), 404

@bp.route('/', methods=['POST'])
def create_transaction():
    try:
        data = request.get_json()
        
        # Validate transaction type
        if data['transaction_type'] not in VALID_TRANSACTION_TYPES:
            return jsonify({'error': 'Invalid transaction type'}), 400
        
        # Convert price and fees to Decimal
        try:
            price = Decimal(str(data['price'])).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            fees = Decimal(str(data.get('fees', '0.0'))).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid price or fees format'}), 400
        
        transaction = Transaction(
            portfolio_id=data['portfolio_id'],
            security_id=data['security_id'],
            transaction_type=data['transaction_type'],
            quantity=Decimal(str(data['quantity'])),
            price=price,
            transaction_date=data['transaction_date'],
            fees=fees
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Update related holdings
        holding = Holding.query.filter_by(
            portfolio_id=transaction.portfolio_id,
            security_id=transaction.security_id
        ).first()
        
        if holding:
            holding.calculate_values()
            db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create transaction', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['PUT'])
def update_transaction(id):
    try:
        transaction = Transaction.query.get_or_404(id)
        data = request.get_json()
        
        # Validate transaction type if provided
        if 'transaction_type' in data and data['transaction_type'] not in VALID_TRANSACTION_TYPES:
            return jsonify({'error': 'Invalid transaction type'}), 400
        
        # Handle numeric fields with proper decimal conversion
        if 'price' in data:
            try:
                data['price'] = Decimal(str(data['price'])).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid price format'}), 400
        
        if 'fees' in data:
            try:
                data['fees'] = Decimal(str(data['fees'])).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid fees format'}), 400
        
        if 'quantity' in data:
            try:
                data['quantity'] = Decimal(str(data['quantity']))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid quantity format'}), 400
        
        # Update fields
        for field in ['portfolio_id', 'security_id', 'transaction_type', 
                     'quantity', 'price', 'transaction_date', 'fees']:
            if field in data:
                setattr(transaction, field, data[field])
        
        db.session.commit()
        
        # Update related holdings
        holding = Holding.query.filter_by(
            portfolio_id=transaction.portfolio_id,
            security_id=transaction.security_id
        ).first()
        
        if holding:
            holding.calculate_values()
            db.session.commit()
        
        return jsonify(transaction.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update transaction', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    try:
        transaction = Transaction.query.get_or_404(id)
        portfolio_id = transaction.portfolio_id
        security_id = transaction.security_id
        
        db.session.delete(transaction)
        db.session.commit()
        
        # Update related holdings after deletion
        holding = Holding.query.filter_by(
            portfolio_id=portfolio_id,
            security_id=security_id
        ).first()
        
        if holding:
            holding.calculate_values()
            db.session.commit()
        
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete transaction', 'details': str(e)}), 500