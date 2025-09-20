import traceback
from datetime import datetime
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.platform import Platform
from app.models.security import Security
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.transaction import Transaction

conf = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": 'sqlite:///:memory:',
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "SECRET_KEY": "test-secret-key",
    "JWT_SECRET_KEY": "test-jwt-secret-key",
    "WTF_CSRF_ENABLED": False
}
app = create_app(conf)
with app.app_context():
    try:
        db.create_all()
        user = User(username='testuser', email='t@example.com', first_name='T', last_name='U')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

        platform = Platform(name='Test Broker')
        security = Security(symbol='AAPL', name='Apple Inc.', sector='Technology', currency='USD')
        db.session.add_all([platform, security])
        db.session.commit()

        portfolio = Portfolio(name='Test Portfolio', description='desc', user_id=user.id, platform_id=platform.id, currency='USD', is_active=True)
        db.session.add(portfolio)
        db.session.commit()

        # add transaction (which will create the holding via Transaction.update_holding())
        tx = Transaction(portfolio_id=portfolio.id, security_id=security.id, transaction_type='BUY', quantity=Decimal('100'), price=Decimal('150.00'), commission=Decimal('0.00'), transaction_date=datetime.utcnow(), currency='USD')
        db.session.add(tx)
        db.session.commit()

        # Retrieve the holding created by the transaction update_holding flow
        h = Holding.query.filter_by(portfolio_id=portfolio.id, security_id=security.id, platform_id=platform.id).first()
        if not h:
            print('No holding found after transaction creation')

        client = app.test_client()
        # login
        resp = client.post('/api/auth/login', json={'username':'testuser','password':'pass'})
        print('login', resp.status_code, resp.get_json())
        token = resp.get_json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}

        endpoints = [
            f'/api/portfolios/{portfolio.id}/holdings/performance',
            f'/api/portfolios/{portfolio.id}/holdings/export',
            f'/api/portfolios/{portfolio.id}/holdings/{h.id}/transactions'
        ]

        for ep in endpoints:
            try:
                print('\nREQUEST', ep)
                r = client.get(ep, headers=headers)
                print('STATUS', r.status_code)
                print('HEADERS', dict(r.headers))
                try:
                    print('JSON', r.get_json())
                except Exception:
                    print('TEXT', r.get_data(as_text=True))
            except Exception:
                print('ERROR during request')
                traceback.print_exc()

    except Exception:
        traceback.print_exc()
    finally:
        db.session.remove()
        db.drop_all()
