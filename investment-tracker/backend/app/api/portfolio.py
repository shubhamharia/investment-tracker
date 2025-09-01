from flask import jsonify, request
from . import portfolio_bp
from ..models import Holding, Security, Platform
from ..services.portfolio_service import PortfolioService
from ..extensions import db

@portfolio_bp.route('/portfolio', methods=['GET'])
def get_portfolio():
    try:
        holdings = (
            Holding.query
            .join(Security)
            .join(Platform)
            .all()
        )
        
        return jsonify({
            'holdings': [{
                'id': h.id,
                'platform': h.platform.name,
                'security': h.security.name,
                'ticker': h.security.ticker,
                'quantity': float(h.quantity),
                'average_cost': float(h.average_cost),
                'current_price': float(h.current_price) if h.current_price else None,
                'current_value': float(h.current_value) if h.current_value else None,
                'gain_loss': float(h.unrealized_gain_loss) if h.unrealized_gain_loss else None,
                'gain_loss_pct': float(h.unrealized_gain_loss_pct) if h.unrealized_gain_loss_pct else None
            } for h in holdings]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/refresh', methods=['POST'])
def refresh_portfolio():
    try:
        PortfolioService.update_holdings()
        return jsonify({'message': 'Portfolio refreshed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500