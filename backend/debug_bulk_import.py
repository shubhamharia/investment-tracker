import tempfile
import os
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.platform import Platform
from app.models.security import Security
from app.models.portfolio import Portfolio

# Create app
db_fd, db_path = tempfile.mkstemp()
app = create_app({
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "SECRET_KEY": "test-secret-key",
    "JWT_SECRET_KEY": "test-jwt-secret-key",
    "WTF_CSRF_ENABLED": False
})

with app.app_context():
    db.create_all()
    # create user
    user = User(username='testuser', email='test@example.com', first_name='T', last_name='U')
    user.set_password('testpassword123')
    db.session.add(user)
    db.session.commit()

    # create platform, security, portfolio
    platform = Platform(name='Test Broker')
    security = Security(symbol='AAPL', name='Apple Inc.', sector='Technology', currency='USD')
    db.session.add_all([platform, security])
    db.session.commit()

    portfolio = Portfolio(name='Test Portfolio', description='desc', user_id=user.id, platform_id=platform.id, currency='USD', is_active=True)
    db.session.add(portfolio)
    db.session.commit()

    client = app.test_client()
    # login
    resp = client.post('/api/auth/login', json={'username':'testuser','password':'testpassword123'})
    print('login status', resp.status_code, resp.get_json())
    token = resp.get_json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    holdings_data = {
        'holdings': [
            {'security_id': security.id, 'platform_id': platform.id, 'quantity': '25.0', 'average_cost': '148.00', 'currency': 'USD'},
            {'security_id': security.id, 'platform_id': platform.id, 'quantity': '30.0', 'average_cost': '152.00', 'currency': 'USD'}
        ]
    }

    resp = client.post(f'/api/portfolios/{portfolio.id}/holdings/bulk', json=holdings_data, headers=headers)
    print('bulk import status', resp.status_code)
    try:
        print('json:', resp.get_json())
    except Exception:
        print('data:', resp.get_data(as_text=True))

    # cleanup
    db.drop_all()
    os.close(db_fd)
    os.unlink(db_path)
