from flask import jsonify
from . import dashboard_bp
from ..services.portfolio_service import PortfolioService
from ..models import Holding, Security, Platform

@dashboard_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    try:
        # Get portfolio summary
        portfolio_summary = PortfolioService.calculate_portfolio_summary()
        
        # Get holdings by platform
        holdings_by_platform = (
            Holding.query
            .join(Platform)
            .join(Security)
            .with_entities(
                Platform.name,
                Platform.account_type,
                func.sum(Holding.current_value).label('total_value')
            )
            .group_by(Platform.name, Platform.account_type)
            .all()
        )
        
        return jsonify({
            'portfolio_summary': portfolio_summary,
            'holdings_by_platform': [
                {
                    'platform': h.name,
                    'account_type': h.account_type,
                    'value': float(h.total_value)
                } for h in holdings_by_platform
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500