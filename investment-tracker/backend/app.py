# app.py - Main Flask Application
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import text
import redis
import os
import logging

# Initialize Flask app
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Secret key for Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://portfolio_user:portfolio_pass@localhost/portfolio_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Redis configuration for Celery
app.config['CELERY_BROKER_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)


# Redis connection
redis_client = redis.Redis.from_url(app.config['CELERY_BROKER_URL'])

# Celery configuration
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# Database Models
class Platform(db.Model):
    __tablename__ = 'platforms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50))  # ISA, GIA, LISA, etc.
    currency = db.Column(db.String(3), default='GBP')
    trading_fee_fixed = db.Column(db.Numeric(10, 4), default=0)
    trading_fee_percentage = db.Column(db.Numeric(5, 4), default=0)
    fx_fee_percentage = db.Column(db.Numeric(5, 4), default=0)
    stamp_duty_applicable = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='platform', lazy=True)
    holdings = db.relationship('Holding', backref='platform', lazy=True)

class Security(db.Model):
    __tablename__ = 'securities'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    isin = db.Column(db.String(12))
    name = db.Column(db.String(200))
    sector = db.Column(db.String(100))
    exchange = db.Column(db.String(50))
    currency = db.Column(db.String(3))
    instrument_type = db.Column(db.String(20))  # STOCK, ETF, FUND
    country = db.Column(db.String(2))
    yahoo_symbol = db.Column(db.String(20))  # For API calls
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='security', lazy=True)
    price_history = db.relationship('PriceHistory', backref='security', lazy=True)
    holdings = db.relationship('Holding', backref='security', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('ticker', 'exchange'),)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # BUY, SELL, DIVIDEND
    transaction_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Numeric(15, 8), nullable=False)
    price_per_share = db.Column(db.Numeric(15, 8), nullable=False)
    gross_amount = db.Column(db.Numeric(15, 4), nullable=False)
    trading_fees = db.Column(db.Numeric(10, 4), default=0)
    stamp_duty = db.Column(db.Numeric(10, 4), default=0)
    fx_fees = db.Column(db.Numeric(10, 4), default=0)
    net_amount = db.Column(db.Numeric(15, 4), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    fx_rate = db.Column(db.Numeric(15, 8), default=1)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    price_date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Numeric(15, 8))
    high_price = db.Column(db.Numeric(15, 8))
    low_price = db.Column(db.Numeric(15, 8))
    close_price = db.Column(db.Numeric(15, 8), nullable=False)
    volume = db.Column(db.BigInteger)
    currency = db.Column(db.String(3), nullable=False)
    data_source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('security_id', 'price_date'),)

class Holding(db.Model):
    __tablename__ = 'holdings'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    quantity = db.Column(db.Numeric(15, 8), nullable=False)
    average_cost = db.Column(db.Numeric(15, 8), nullable=False)
    total_cost = db.Column(db.Numeric(15, 4), nullable=False)
    current_price = db.Column(db.Numeric(15, 8))
    current_value = db.Column(db.Numeric(15, 4))
    unrealized_gain_loss = db.Column(db.Numeric(15, 4))
    unrealized_gain_loss_pct = db.Column(db.Numeric(8, 4), default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('platform_id', 'security_id'),)

class Dividend(db.Model):
    __tablename__ = 'dividends'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    ex_date = db.Column(db.Date, nullable=False)
    pay_date = db.Column(db.Date)
    dividend_per_share = db.Column(db.Numeric(15, 8), nullable=False)
    quantity_held = db.Column(db.Numeric(15, 8), nullable=False)
    gross_dividend = db.Column(db.Numeric(15, 4), nullable=False)
    withholding_tax = db.Column(db.Numeric(15, 4), default=0)
    net_dividend = db.Column(db.Numeric(15, 4), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Price Service
class PriceService:
    @staticmethod
    def get_yahoo_symbol(ticker, exchange=None):
        """Convert ticker to Yahoo Finance symbol"""
        if exchange and exchange.upper() == 'LSE':
            if not ticker.endswith('.L'):
                return f"{ticker}.L"
        return ticker
    
    @staticmethod
    def fetch_current_price(ticker, exchange=None):
        """Fetch current price from Yahoo Finance"""
        try:
            yahoo_symbol = PriceService.get_yahoo_symbol(ticker, exchange)
            stock = yf.Ticker(yahoo_symbol)
            info = stock.info
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            currency = info.get('currency', 'GBP')
            
            return {
                'price': float(current_price) if current_price else None,
                'currency': currency,
                'symbol': yahoo_symbol
            }
        except Exception as e:
            app.logger.error(f"Error fetching price for {ticker}: {str(e)}")
            return None
    
    @staticmethod
    def fetch_historical_prices(ticker, start_date, end_date, exchange=None):
        """Fetch historical prices from Yahoo Finance"""
        try:
            yahoo_symbol = PriceService.get_yahoo_symbol(ticker, exchange)
            stock = yf.Ticker(yahoo_symbol)
            
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return None
            
            # Get currency from info
            info = stock.info
            currency = info.get('currency', 'GBP')
            
            return {
                'data': hist,
                'currency': currency,
                'symbol': yahoo_symbol
            }
        except Exception as e:
            app.logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
            return None

# Portfolio Service
class PortfolioService:
    @staticmethod
    def calculate_holdings():
        """Recalculate all holdings from transactions"""
        # Clear existing holdings
        Holding.query.delete()
        
        # Get all transactions grouped by platform and security
        transactions = db.session.query(
            Transaction.platform_id,
            Transaction.security_id,
            db.func.sum(
                db.case(
                    (Transaction.transaction_type == 'BUY', Transaction.quantity),
                    else_=-Transaction.quantity
                )
            ).label('total_quantity'),
            db.func.sum(
                db.case(
                    (Transaction.transaction_type == 'BUY', Transaction.net_amount),
                    else_=-Transaction.net_amount
                )
            ).label('total_cost')
        ).group_by(
            Transaction.platform_id, 
            Transaction.security_id
        ).having(
            db.func.sum(
                db.case(
                    (Transaction.transaction_type == 'BUY', Transaction.quantity),
                    else_=-Transaction.quantity
                )
            ) > 0
        ).all()
        
        # Create holdings
        for trans in transactions:
            avg_cost = trans.total_cost / trans.total_quantity if trans.total_quantity > 0 else 0
            
            holding = Holding(
                platform_id=trans.platform_id,
                security_id=trans.security_id,
                quantity=trans.total_quantity,
                average_cost=avg_cost,
                total_cost=trans.total_cost,
                last_updated=datetime.utcnow()
            )
            db.session.add(holding)
        
        db.session.commit()
    
    @staticmethod
    def update_holding_prices():
        """Update current prices for all holdings"""
        holdings = Holding.query.all()
        
        for holding in holdings:
            security = holding.security
            price_data = PriceService.fetch_current_price(
                security.ticker, 
                security.exchange
            )
            
            if price_data and price_data['price']:
                holding.current_price = Decimal(str(price_data['price']))
                holding.current_value = holding.quantity * holding.current_price
                holding.unrealized_gain_loss = holding.current_value - holding.total_cost
                
                if holding.total_cost > 0:
                    holding.unrealized_gain_loss_pct = (
                        holding.unrealized_gain_loss / holding.total_cost * 100
                    )
                
                holding.last_updated = datetime.utcnow()
        
        db.session.commit()

# Celery Tasks
@celery.task
def update_prices():
    """Celery task to update all prices"""
    with app.app_context():
        PortfolioService.update_holding_prices()
        return "Prices updated successfully"

@celery.task
def import_historical_data(security_id, start_date):
    """Import historical price data for a security"""
    with app.app_context():
        security = Security.query.get(security_id)
        if not security:
            return f"Security {security_id} not found"
        
        hist_data = PriceService.fetch_historical_prices(
            security.ticker,
            start_date,
            datetime.now().date(),
            security.exchange
        )
        
        if not hist_data:
            return f"No historical data found for {security.ticker}"
        
        # Import price history
        for date_idx, row in hist_data['data'].iterrows():
            price_date = date_idx.date()
            
            existing = PriceHistory.query.filter_by(
                security_id=security_id,
                price_date=price_date
            ).first()
            
            if not existing:
                price_history = PriceHistory(
                    security_id=security_id,
                    price_date=price_date,
                    open_price=Decimal(str(row['Open'])),
                    high_price=Decimal(str(row['High'])),
                    low_price=Decimal(str(row['Low'])),
                    close_price=Decimal(str(row['Close'])),
                    volume=int(row['Volume']) if row['Volume'] > 0 else None,
                    currency=hist_data['currency'],
                    data_source='yahoo'
                )
                db.session.add(price_history)
        
        db.session.commit()
        return f"Historical data imported for {security.ticker}"

# API Routes
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get portfolio dashboard data"""
    try:
        # Get holdings with current prices
        holdings_query = db.session.query(
            Holding,
            Platform.name.label('platform_name'),
            Platform.account_type,
            Security.ticker,
            Security.name.label('security_name'),
            Security.currency.label('security_currency')
        ).join(Platform).join(Security).all()
        
        holdings = []
        total_value = 0
        total_cost = 0
        
        for holding, platform_name, account_type, ticker, security_name, security_currency in holdings_query:
            holding_data = {
                'id': holding.id,
                'platform': f"{platform_name}_{account_type}" if account_type else platform_name,
                'ticker': ticker,
                'security_name': security_name,
                'quantity': float(holding.quantity),
                'average_cost': float(holding.average_cost),
                'total_cost': float(holding.total_cost),
                'current_price': float(holding.current_price) if holding.current_price else None,
                'current_value': float(holding.current_value) if holding.current_value else None,
                'unrealized_gain_loss': float(holding.unrealized_gain_loss) if holding.unrealized_gain_loss else None,
                'unrealized_gain_loss_pct': float(holding.unrealized_gain_loss_pct) if holding.unrealized_gain_loss_pct else None,
                'currency': security_currency,
                'last_updated': holding.last_updated.isoformat() if holding.last_updated else None
            }
            holdings.append(holding_data)
            
            if holding.current_value:
                total_value += float(holding.current_value)
            if holding.total_cost:
                total_cost += float(holding.total_cost)
        
        # Calculate summary statistics
        total_gain_loss = total_value - total_cost
        total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        # Get platform breakdown
        platform_summary = db.session.query(
            Platform.name,
            Platform.account_type,
            db.func.sum(Holding.current_value).label('total_value'),
            db.func.sum(Holding.total_cost).label('total_cost'),
            db.func.count(Holding.id).label('num_holdings')
        ).join(Holding).group_by(Platform.id, Platform.name, Platform.account_type).all()
        
        platforms = []
        for platform in platform_summary:
            platform_data = {
                'name': f"{platform.name}_{platform.account_type}" if platform.account_type else platform.name,
                'total_value': float(platform.total_value) if platform.total_value else 0,
                'total_cost': float(platform.total_cost) if platform.total_cost else 0,
                'num_holdings': platform.num_holdings,
                'gain_loss': float(platform.total_value - platform.total_cost) if platform.total_value and platform.total_cost else 0
            }
            platforms.append(platform_data)
        
        return jsonify({
            'summary': {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_gain_loss': total_gain_loss,
                'total_gain_loss_pct': total_gain_loss_pct,
                'num_holdings': len(holdings),
                'last_updated': datetime.utcnow().isoformat()
            },
            'holdings': holdings,
            'platforms': platforms
        })
    
    except Exception as e:
        app.logger.error(f"Error getting dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get transaction history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        transactions_query = db.session.query(
            Transaction,
            Platform.name.label('platform_name'),
            Platform.account_type,
            Security.ticker,
            Security.name.label('security_name')
        ).join(Platform).join(Security).order_by(
            Transaction.transaction_date.desc(),
            Transaction.created_at.desc()
        )
        
        transactions = transactions_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        result = []
        for transaction, platform_name, account_type, ticker, security_name in transactions.items:
            transaction_data = {
                'id': transaction.id,
                'platform': f"{platform_name}_{account_type}" if account_type else platform_name,
                'ticker': ticker,
                'security_name': security_name,
                'transaction_type': transaction.transaction_type,
                'transaction_date': transaction.transaction_date.isoformat(),
                'quantity': float(transaction.quantity),
                'price_per_share': float(transaction.price_per_share),
                'gross_amount': float(transaction.gross_amount),
                'trading_fees': float(transaction.trading_fees),
                'net_amount': float(transaction.net_amount),
                'currency': transaction.currency,
                'fx_rate': float(transaction.fx_rate),
                'notes': transaction.notes
            }
            result.append(transaction_data)
        
        return jsonify({
            'transactions': result,
            'pagination': {
                'page': transactions.page,
                'pages': transactions.pages,
                'per_page': transactions.per_page,
                'total': transactions.total,
                'has_next': transactions.has_next,
                'has_prev': transactions.has_prev
            }
        })
    
    except Exception as e:
        app.logger.error(f"Error getting transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh-prices', methods=['POST'])
def refresh_prices():
    """Trigger price refresh"""
    try:
        # Queue the price update task
        task = update_prices.delay()
        return jsonify({
            'message': 'Price update queued',
            'task_id': task.id
        })
    except Exception as e:
        app.logger.error(f"Error refreshing prices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-data', methods=['POST'])
def import_csv_data():
    """Import data from CSV"""
    try:
        # This would be implemented to handle your CSV import
        # For now, return a placeholder
        return jsonify({'message': 'CSV import endpoint - to be implemented'})
    except Exception as e:
        app.logger.error(f"Error importing data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio')
def get_portfolio():
    try:
        # Get all holdings
        holdings = db.session.query(
            Security.ticker,
            Security.name,
            Platform.name.label('platform'),
            db.func.sum(Transaction.quantity).label('total_quantity'),
            db.func.avg(Transaction.price_per_share).label('avg_price')
        ).join(
            Transaction, Transaction.security_id == Security.id
        ).join(
            Platform, Transaction.platform_id == Platform.id
        ).group_by(
            Security.ticker,
            Security.name,
            Platform.name
        ).having(
            db.func.sum(Transaction.quantity) > 0
        ).all()

        return jsonify({
            'holdings': [
                {
                    'ticker': h.ticker,
                    'name': h.name,
                    'platform': h.platform,
                    'quantity': float(h.total_quantity),
                    'avg_price': float(h.avg_price)
                }
                for h in holdings
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check
@app.route('/health')
def health_check():
    app.logger.info("Health check requested")
    response = {
        'status': 'unknown',
        'database': 'unknown',
        'redis': 'unknown',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        # Test database connection using SQLAlchemy 2.0+ syntax
        with db.engine.connect() as conn:
            result = conn.execute(text('SELECT 1')).scalar()
            response['database'] = 'connected' if result == 1 else 'error'
            app.logger.info(f"Database connection test result: {result}")
    except Exception as e:
        app.logger.error(f"Database health check failed: {e}")
        response['database'] = f'error: {str(e)}'
    
    try:
        # Test Redis connection
        redis_ok = redis_client.ping()
        response['redis'] = 'connected' if redis_ok else 'error'
        app.logger.info(f"Redis connection test result: {redis_ok}")
    except Exception as e:
        app.logger.error(f"Redis health check failed: {e}")
        response['redis'] = f'error: {str(e)}'
    
    # Set overall status
    response['status'] = 'healthy' if (
        response['database'] == 'connected' and 
        response['redis'] == 'connected'
    ) else 'unhealthy'
    
    app.logger.info(f"Health check response: {response}")
    return jsonify(response)

def create_db():
    """Create all database tables."""
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
