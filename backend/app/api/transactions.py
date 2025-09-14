from flask import Blueprint, jsonify, request
from decimal import Decimal, InvalidOperation
from app.models import Transaction, Holding, Portfolio
from app.extensions import db
from app.constants import DECIMAL_PLACES, TRANSACTION_TYPES as VALID_TRANSACTION_TYPES, CURRENCY_CODES
from app.api.auth import token_required
from datetime import datetime

bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@bp.route('/', methods=['GET'])
@token_required
def get_transactions(current_user):
    try:
        # Only return transactions for portfolios owned by the current user
        portfolios = db.session.query(Portfolio).filter_by(user_id=current_user.id).all()
        portfolio_ids = [p.id for p in portfolios]
        transactions = db.session.query(Transaction).filter(Transaction.portfolio_id.in_(portfolio_ids)).all()
        return jsonify([transaction.to_dict() for transaction in transactions])
    except Exception as e:
        return jsonify({'error': 'Failed to fetch transactions', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['GET'])
@token_required
def get_transaction(current_user, id):
    try:
        transaction = db.session.get(Transaction, id)
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Check if the user owns the portfolio this transaction belongs to
        portfolio = db.session.get(Portfolio, transaction.portfolio_id)
        if portfolio.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized: transaction belongs to another user'}), 403
            
        return jsonify(transaction.to_dict())
    except Exception as e:
        return jsonify({'error': 'Failed to get transaction', 'details': str(e)}), 500

@bp.route('/', methods=['POST'])
@token_required
def create_transaction(current_user):
    try:
        data = request.get_json()
        print(f"Received transaction data: {data}")
        
        # Validate required fields
        required_fields = ['portfolio_id', 'security_id', 'transaction_type', 'quantity', 'price_per_share']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate quantity
        try:
            quantity = Decimal(str(data['quantity']))
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be positive'}), 400
        except (InvalidOperation, ValueError):
            return jsonify({'error': 'Invalid quantity value'}), 400
            
        # Check if the user owns the portfolio
        portfolio = db.session.get(Portfolio, data['portfolio_id'])
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        if portfolio.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized: portfolio belongs to another user'}), 403
            
        # Validate transaction type
        if data['transaction_type'] not in VALID_TRANSACTION_TYPES:
            return jsonify({'error': f'Invalid transaction type. Must be one of: {", ".join(VALID_TRANSACTION_TYPES)}'}), 400
            
        # Validate currency
        if 'currency' in data and data['currency'] not in CURRENCY_CODES:
            return jsonify({'error': f'Invalid currency code. Must be one of: {", ".join(CURRENCY_CODES)}'}), 400
            
        # For SELL transactions, check if there are enough shares
        if data['transaction_type'] == 'SELL':
            holding = db.session.query(Holding)\
                .filter_by(portfolio_id=data['portfolio_id'], security_id=data['security_id'])\
                .first()
            if not holding or holding.quantity < quantity:
                return jsonify({'error': 'Insufficient shares for sale'}), 400
            
        if portfolio.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized: portfolio does not belong to current user'}), 403
        
        # Validate transaction type
        transaction_type = data['transaction_type'].upper()
        print(f"Validating transaction type: {transaction_type}, valid types: {VALID_TRANSACTION_TYPES}")
        if transaction_type not in VALID_TRANSACTION_TYPES:
            return jsonify({
                'error': f'Invalid transaction type: {transaction_type}. Valid types: {list(VALID_TRANSACTION_TYPES.keys())}'
            }), 400
        
        # Convert price and fees to Decimal
        try:
            price_per_share = Decimal(str(data['price_per_share'])).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            if price_per_share <= 0:
                return jsonify({'error': 'Price per share must be positive'}), 400
                
            trading_fees = Decimal(str(data.get('trading_fees', '0.0'))).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            if trading_fees < 0:
                return jsonify({'error': 'Trading fees cannot be negative'}), 400
                
            quantity = Decimal(str(data['quantity'])).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be positive'}), 400
                
            print(f"Converted numeric values - price: {price_per_share}, fees: {trading_fees}, quantity: {quantity}")
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid numeric value format: {str(e)}'}), 400
            
        # Parse transaction date
        try:
            if isinstance(data['transaction_date'], str):
                transaction_date = datetime.fromisoformat(data['transaction_date'].replace('Z', '+00:00'))
            else:
                transaction_date = data['transaction_date']
                
            # Validate transaction date is not in the future (allow some timezone tolerance)
            from datetime import timedelta
            max_allowed_date = datetime.utcnow().date() + timedelta(days=1)
            if transaction_date.date() > max_allowed_date:
                return jsonify({'error': 'Transaction date cannot be in the future'}), 400
                
            print(f"Parsed transaction date: {transaction_date}")
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid transaction_date format: {str(e)}'}), 400
            
        # Validate currency
        if 'currency' not in data:
            return jsonify({'error': 'Currency is required'}), 400
        if data['currency'] not in CURRENCY_CODES:
            return jsonify({'error': f'Invalid currency code. Must be one of: {", ".join(CURRENCY_CODES)}'}), 400
        # Currency must match portfolio's base currency
        if data['currency'] != portfolio.base_currency:
            return jsonify({'error': f'Transaction currency {data["currency"]} must match portfolio base currency {portfolio.base_currency}'}), 400
            
        # For SELL transactions, verify sufficient shares
        if data['transaction_type'].upper() == 'SELL':
            holding = db.session.query(Holding).filter_by(
                portfolio_id=data['portfolio_id'],
                security_id=data['security_id'],
                platform_id=data['platform_id']
            ).first()
            
            if not holding or holding.quantity < quantity:
                return jsonify({'error': 'Insufficient shares for sale'}), 400

        # Calculate gross and net amounts
        gross_amount = quantity * price_per_share
        net_amount = gross_amount + trading_fees
        print(f"Calculated amounts - gross: {gross_amount}, net: {net_amount}")

        transaction_data = {
            'portfolio_id': data['portfolio_id'],
            'security_id': data['security_id'],
            'platform_id': data['platform_id'],
            'transaction_type': transaction_type,
            'quantity': quantity,
            'price_per_share': price_per_share,
            'transaction_date': transaction_date,
            'trading_fees': trading_fees,
            'currency': data['currency'],
            'gross_amount': gross_amount,
            'net_amount': net_amount
        }
        print("Creating transaction with data:", transaction_data)
        
        transaction = Transaction(**transaction_data)
        
        db.session.add(transaction)
        db.session.commit()
        
        # Update related holdings
        holding = db.session.query(Holding).filter_by(
            portfolio_id=transaction.portfolio_id,
            security_id=transaction.security_id,
            platform_id=transaction.platform_id
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
@token_required
def update_transaction(current_user, id):
    try:
        transaction = db.session.get(Transaction, id)
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
            
        # Check if the user owns the portfolio this transaction belongs to
        portfolio = db.session.get(Portfolio, transaction.portfolio_id)
        if portfolio.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized: transaction belongs to another user'}), 403
            
        data = request.get_json()
        
        # Validate transaction type if provided
        if 'transaction_type' in data and data['transaction_type'].lower() not in [t.lower() for t in VALID_TRANSACTION_TYPES]:
            return jsonify({'error': 'Invalid transaction type'}), 400
        
        # Handle numeric fields with proper decimal conversion
        if 'price_per_share' in data:
            try:
                data['price_per_share'] = Decimal(str(data['price_per_share'])).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid price_per_share format'}), 400
        
        if 'trading_fees' in data:
            try:
                data['trading_fees'] = Decimal(str(data['trading_fees'])).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid trading_fees format'}), 400
        
        if 'quantity' in data:
            try:
                data['quantity'] = Decimal(str(data['quantity'])).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}'))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid quantity format'}), 400
        
        # Handle transaction date
        if 'transaction_date' in data:
            try:
                if isinstance(data['transaction_date'], str):
                    data['transaction_date'] = datetime.fromisoformat(data['transaction_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid transaction_date format'}), 400
        
        # Update fields
        for key, value in data.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)
        
        # Recalculate amounts
        if 'quantity' in data or 'price_per_share' in data or 'trading_fees' in data:
            transaction.gross_amount = transaction.quantity * transaction.price_per_share
            transaction.net_amount = transaction.gross_amount + transaction.trading_fees
        
        db.session.commit()
        
        # Update related holdings
        holding = db.session.query(Holding).filter_by(
            portfolio_id=transaction.portfolio_id,
            security_id=transaction.security_id,
            platform_id=transaction.platform_id
        ).first()
        
        if holding:
            holding.calculate_values()
            db.session.commit()
            
        return jsonify(transaction.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update transaction', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_transaction(current_user, id):
    try:
        transaction = db.session.get(Transaction, id)
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
            
        # Check if the user owns the portfolio this transaction belongs to
        portfolio = db.session.get(Portfolio, transaction.portfolio_id)
        if portfolio.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized: transaction belongs to another user'}), 403
            
        # Keep references for later
        portfolio_id = transaction.portfolio_id
        security_id = transaction.security_id
        platform_id = transaction.platform_id
        
        db.session.delete(transaction)
        db.session.commit()
        
        # Update related holdings
        holding = db.session.query(Holding).filter_by(
            portfolio_id=portfolio_id,
            security_id=security_id,
            platform_id=platform_id
        ).first()
        
        if holding:
            holding.calculate_values()
            db.session.commit()
        
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete transaction', 'details': str(e)}), 500