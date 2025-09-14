import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.dividend_service import DividendService
from app.models.dividend import Dividend
from app.models.security import Security
from app.models.portfolio import Portfolio


class TestDividendService:
    """Test dividend service functionality."""

    @pytest.fixture
    def service(self):
        """Create dividend service instance."""
        return DividendService()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return Mock()

    def test_calculate_annual_yield(self, service, sample_security, sample_portfolio):
        """Test calculating annual dividend yield."""
        # Mock recent dividends
        dividends = [
            Mock(amount=Decimal('2.50'), payment_date=datetime.now() - timedelta(days=90)),
            Mock(amount=Decimal('2.50'), payment_date=datetime.now() - timedelta(days=180)),
            Mock(amount=Decimal('2.50'), payment_date=datetime.now() - timedelta(days=270)),
            Mock(amount=Decimal('2.50'), payment_date=datetime.now() - timedelta(days=360))
        ]
        
        with patch.object(service, '_get_recent_dividends', return_value=dividends):
            with patch.object(service, '_get_current_price', return_value=Decimal('150.00')):
                yield_pct = service.calculate_annual_yield(sample_security.id)
                
                # Expected: (2.50 * 4) / 150.00 = 6.67%
                assert yield_pct == pytest.approx(6.67, rel=0.01)

    def test_calculate_annual_yield_no_dividends(self, service, sample_security):
        """Test calculating annual yield with no dividends."""
        with patch.object(service, '_get_recent_dividends', return_value=[]):
            yield_pct = service.calculate_annual_yield(sample_security.id)
            assert yield_pct == 0.0

    def test_calculate_annual_yield_no_price(self, service, sample_security):
        """Test calculating annual yield with no current price."""
        dividends = [Mock(amount=Decimal('2.50'))]
        
        with patch.object(service, '_get_recent_dividends', return_value=dividends):
            with patch.object(service, '_get_current_price', return_value=None):
                yield_pct = service.calculate_annual_yield(sample_security.id)
                assert yield_pct == 0.0

    def test_project_next_dividend(self, service, sample_security):
        """Test projecting next dividend payment."""
        # Mock historical dividends with quarterly pattern
        dividends = [
            Mock(amount=Decimal('2.50'), payment_date=datetime(2024, 3, 15)),
            Mock(amount=Decimal('2.40'), payment_date=datetime(2023, 12, 15)),
            Mock(amount=Decimal('2.30'), payment_date=datetime(2023, 9, 15)),
            Mock(amount=Decimal('2.20'), payment_date=datetime(2023, 6, 15))
        ]
        
        with patch.object(service, '_get_historical_dividends', return_value=dividends):
            projection = service.project_next_dividend(sample_security.id)
            
            assert projection is not None
            assert 'projected_amount' in projection
            assert 'projected_date' in projection
            assert 'confidence' in projection

    def test_project_next_dividend_insufficient_history(self, service, sample_security):
        """Test projecting dividend with insufficient history."""
        dividends = [Mock(amount=Decimal('2.50'))]  # Only one dividend
        
        with patch.object(service, '_get_historical_dividends', return_value=dividends):
            projection = service.project_next_dividend(sample_security.id)
            assert projection is None

    def test_calculate_dividend_growth_rate(self, service, sample_security):
        """Test calculating dividend growth rate."""
        # Mock dividends with growth pattern
        dividends = [
            Mock(amount=Decimal('2.50'), payment_date=datetime(2024, 3, 15)),
            Mock(amount=Decimal('2.40'), payment_date=datetime(2023, 3, 15)),
            Mock(amount=Decimal('2.30'), payment_date=datetime(2022, 3, 15)),
            Mock(amount=Decimal('2.20'), payment_date=datetime(2021, 3, 15))
        ]
        
        with patch.object(service, '_get_annual_dividends', return_value=dividends):
            growth_rate = service.calculate_dividend_growth_rate(sample_security.id, years=3)
            
            # Should show positive growth
            assert growth_rate > 0

    def test_get_dividend_calendar(self, service, mock_db_session):
        """Test getting dividend calendar."""
        # Mock upcoming dividends
        mock_dividends = [
            Mock(
                security=Mock(symbol='AAPL', name='Apple Inc.'),
                amount=Decimal('2.50'),
                ex_dividend_date=datetime.now() + timedelta(days=5),
                payment_date=datetime.now() + timedelta(days=10)
            )
        ]
        
        with patch.object(service, '_query_upcoming_dividends', return_value=mock_dividends):
            calendar = service.get_dividend_calendar(user_id=1, days_ahead=30)
            
            assert isinstance(calendar, list)
            assert len(calendar) == 1
            assert calendar[0]['symbol'] == 'AAPL'

    def test_calculate_portfolio_dividend_yield(self, service, sample_portfolio):
        """Test calculating portfolio dividend yield."""
        # Mock portfolio holdings and their yields
        holdings_data = [
            {'security_id': 1, 'market_value': Decimal('10000'), 'annual_dividends': Decimal('300')},
            {'security_id': 2, 'market_value': Decimal('5000'), 'annual_dividends': Decimal('200')}
        ]
        
        with patch.object(service, '_get_portfolio_holdings_with_dividends', return_value=holdings_data):
            yield_pct = service.calculate_portfolio_dividend_yield(sample_portfolio.id)
            
            # Expected: (300 + 200) / (10000 + 5000) = 3.33%
            assert yield_pct == pytest.approx(3.33, rel=0.01)

    def test_analyze_dividend_sustainability(self, service, sample_security):
        """Test analyzing dividend sustainability."""
        # Mock financial metrics
        metrics = {
            'payout_ratio': 0.6,
            'debt_to_equity': 0.4,
            'free_cash_flow': Decimal('1000000'),
            'dividend_coverage': 1.67
        }
        
        with patch.object(service, '_get_financial_metrics', return_value=metrics):
            analysis = service.analyze_dividend_sustainability(sample_security.id)
            
            assert 'sustainability_score' in analysis
            assert 'risk_factors' in analysis
            assert 'recommendations' in analysis

    def test_get_dividend_aristocrats(self, service):
        """Test getting dividend aristocrats (companies with 25+ years of increases)."""
        # Mock securities with long dividend history
        mock_securities = [
            Mock(id=1, symbol='KO', name='Coca-Cola'),
            Mock(id=2, symbol='JNJ', name='Johnson & Johnson')
        ]
        
        with patch.object(service, '_query_dividend_aristocrats', return_value=mock_securities):
            aristocrats = service.get_dividend_aristocrats()
            
            assert isinstance(aristocrats, list)
            assert len(aristocrats) == 2

    def test_create_dividend_alert(self, service, sample_security, mock_db_session):
        """Test creating dividend alert."""
        alert_data = {
            'security_id': sample_security.id,
            'user_id': 1,
            'alert_type': 'EX_DIVIDEND_DATE',
            'days_before': 3
        }
        
        with patch.object(service, '_save_alert') as mock_save:
            result = service.create_dividend_alert(**alert_data)
            
            mock_save.assert_called_once()
            assert result['status'] == 'created'

    def test_bulk_import_dividends(self, service, sample_portfolio, mock_db_session):
        """Test bulk importing dividends."""
        dividend_data = [
            {
                'portfolio_id': sample_portfolio.id,
                'security_id': 1,
                'amount': '2.50',
                'payment_date': '2024-03-15',
                'currency': 'USD'
            },
            {
                'portfolio_id': sample_portfolio.id,
                'security_id': 2,
                'amount': '1.75',
                'payment_date': '2024-03-20',
                'currency': 'USD'
            }
        ]
        
        with patch.object(service, '_validate_dividend_data', return_value=True):
            with patch.object(service, '_save_dividends') as mock_save:
                result = service.bulk_import_dividends(dividend_data)
                
                mock_save.assert_called_once()
                assert result['imported_count'] == 2

    def test_calculate_tax_implications(self, service, sample_portfolio):
        """Test calculating tax implications of dividends."""
        # Mock dividend data with tax info
        dividend_data = [
            {
                'amount': Decimal('100'),
                'payment_date': datetime(2024, 3, 15),
                'qualified': True
            },
            {
                'amount': Decimal('50'),
                'payment_date': datetime(2024, 6, 15),
                'qualified': False
            }
        ]
        
        with patch.object(service, '_get_portfolio_dividends', return_value=dividend_data):
            tax_analysis = service.calculate_tax_implications(sample_portfolio.id, tax_year=2024)
            
            assert 'qualified_dividends' in tax_analysis
            assert 'ordinary_dividends' in tax_analysis
            assert 'estimated_tax' in tax_analysis

    def test_generate_dividend_report(self, service, sample_portfolio):
        """Test generating comprehensive dividend report."""
        with patch.multiple(service,
                          calculate_portfolio_dividend_yield=Mock(return_value=3.5),
                          get_dividend_calendar=Mock(return_value=[]),
                          calculate_tax_implications=Mock(return_value={})):
            
            report = service.generate_dividend_report(sample_portfolio.id)
            
            assert 'yield' in report
            assert 'calendar' in report
            assert 'tax_analysis' in report
            assert 'summary' in report

    def test_optimize_dividend_strategy(self, service, sample_portfolio):
        """Test optimizing dividend strategy."""
        # Mock current holdings and recommendations
        current_yield = 2.5
        recommendations = [
            {'symbol': 'VTI', 'yield': 1.8, 'recommendation': 'BUY'},
            {'symbol': 'VXUS', 'yield': 2.2, 'recommendation': 'BUY'}
        ]
        
        with patch.object(service, 'calculate_portfolio_dividend_yield', return_value=current_yield):
            with patch.object(service, '_get_dividend_recommendations', return_value=recommendations):
                strategy = service.optimize_dividend_strategy(sample_portfolio.id, target_yield=4.0)
                
                assert 'current_yield' in strategy
                assert 'target_yield' in strategy
                assert 'recommendations' in strategy