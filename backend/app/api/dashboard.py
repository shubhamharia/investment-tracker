from flask import jsonify
from sqlalchemy import func
from decimal import Decimal
from . import dashboard_bp
from ..services.portfolio_service import PortfolioService
from ..models import Holding, Security, Platform
from ..services.constants import DECIMAL_PLACES

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
                    'value': str(Decimal(str(h.total_value)).quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}')))
                } for h in holdings_by_platform
            ]
        })
    except ValueError as e:
        return jsonify({'error': 'Invalid data format', 'details': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500