from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__)
portfolio_bp = Blueprint('portfolio', __name__)
transactions_bp = Blueprint('transactions', __name__)

from . import dashboard, portfolio, transactions