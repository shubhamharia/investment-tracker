"""
Unit tests for Portfolio Performance model.
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from app.models.portfolio_performance import PortfolioPerformance
from app.extensions import db


class TestPortfolioPerformanceModel:
    """Test cases for PortfolioPerformance model."""
    
    def test_portfolio_performance_creation(self, db_session, sample_portfolio):
        """Test creating a new portfolio performance record."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('10000.00'),
            total_cost=Decimal('9500.00'),
            cash_value=Decimal('500.00'),
            unrealized_gain_loss=Decimal('500.00'),
            realized_gain_loss=Decimal('0.00'),
            dividend_income=Decimal('50.00')
        )
        
        db_session.add(performance)
        db_session.commit()
        
        assert performance.id is not None
        assert performance.portfolio_id == sample_portfolio.id
        assert performance.total_value == Decimal('10000.00')
        assert performance.unrealized_gain_loss == Decimal('500.00')
    
    def test_portfolio_performance_representation(self, db_session, sample_portfolio):
        """Test portfolio performance string representation."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('15000.00'),
            total_cost=Decimal('14000.00'),
            unrealized_gain_loss=Decimal('1000.00')
        )
        
        db_session.add(performance)
        db_session.commit()
        
        expected = f'<PortfolioPerformance {performance.portfolio.name} {performance.date}: ${performance.total_value}>'
        assert str(performance) == expected
    
    def test_portfolio_performance_relationships(self, db_session, sample_portfolio):
        """Test portfolio performance relationships."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('8000.00'),
            total_cost=Decimal('8200.00'),
            unrealized_gain_loss=Decimal('-200.00')
        )
        
        db_session.add(performance)
        db_session.commit()
        
        assert performance.portfolio is not None
        assert performance.portfolio.id == performance.portfolio_id
        assert performance.portfolio.name == sample_portfolio.name
    
    def test_portfolio_performance_serialization(self, db_session, sample_portfolio):
        """Test portfolio performance serialization to dictionary."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('12500.00'),
            total_cost=Decimal('12000.00'),
            unrealized_gain_loss=Decimal('500.00'),
            dividend_income=Decimal('75.00')
        )
        
        db_session.add(performance)
        db_session.commit()
        
        perf_dict = performance.to_dict()
        
        expected_keys = {
            'id', 'portfolio_id', 'date', 'total_value', 'total_cost',
            'cash_value', 'unrealized_gain_loss', 'realized_gain_loss',
            'dividend_income', 'created_at'
        }
        
        assert set(perf_dict.keys()) == expected_keys
        assert float(perf_dict['total_value']) == float(performance.total_value)
        assert float(perf_dict['unrealized_gain_loss']) == float(performance.unrealized_gain_loss)
    
    def test_portfolio_performance_return_calculation(self, db_session, sample_portfolio):
        """Test return percentage calculation."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('11000.00'),
            total_cost=Decimal('10000.00'),
            unrealized_gain_loss=Decimal('1000.00')
        )
        
        db_session.add(performance)
        db_session.commit()
        
        # Return percentage = (total_value - total_cost) / total_cost * 100
        return_pct = (performance.total_value - performance.total_cost) / performance.total_cost * 100
        expected_return = Decimal('10.00')  # 10%
        
        assert return_pct == expected_return
    
    def test_portfolio_performance_time_series(self, db_session, sample_portfolio):
        """Test time series of portfolio performance."""
        base_value = Decimal('10000.00')
        performances = []
        
        for i in range(5):
            day_offset = i
            current_value = base_value + Decimal(str(i * 100))
            
            performance = PortfolioPerformance(
                portfolio_id=sample_portfolio.id,
                date=date(2023, 1, 1 + day_offset),
                total_value=current_value,
                total_cost=base_value,
                unrealized_gain_loss=current_value - base_value
            )
            performances.append(performance)
            db_session.add(performance)
        
        db_session.commit()
        
        assert len(performances) == 5
        
        # Verify progression
        for i, perf in enumerate(performances):
            expected_value = base_value + Decimal(str(i * 100))
            assert perf.total_value == expected_value
    
    def test_portfolio_performance_unique_constraint(self, db_session, sample_portfolio):
        """Test unique constraint on portfolio_id + date."""
        test_date = date(2023, 6, 15)
        
        perf1 = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=test_date,
            total_value=Decimal('5000.00'),
            total_cost=Decimal('4800.00'),
            unrealized_gain_loss=Decimal('200.00')
        )
        
        perf2 = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=test_date,  # Same portfolio and date
            total_value=Decimal('5100.00'),
            total_cost=Decimal('4800.00'),
            unrealized_gain_loss=Decimal('300.00')
        )
        
        db_session.add(perf1)
        db_session.commit()
        
        db_session.add(perf2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_portfolio_performance_negative_values(self, db_session, sample_portfolio):
        """Test portfolio performance with losses."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('8500.00'),
            total_cost=Decimal('10000.00'),
            unrealized_gain_loss=Decimal('-1500.00'),  # Loss
            realized_gain_loss=Decimal('-250.00')      # Realized loss
        )
        
        db_session.add(performance)
        db_session.commit()
        
        assert performance.unrealized_gain_loss < 0
        assert performance.realized_gain_loss < 0
        assert performance.total_value < performance.total_cost
    
    def test_portfolio_performance_cash_component(self, db_session, sample_portfolio):
        """Test portfolio performance with cash holdings."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('12000.00'),
            total_cost=Decimal('11000.00'),
            cash_value=Decimal('2000.00'),  # Cash portion
            unrealized_gain_loss=Decimal('1000.00')
        )
        
        db_session.add(performance)
        db_session.commit()
        
        # Securities value = total_value - cash_value
        securities_value = performance.total_value - performance.cash_value
        expected_securities = Decimal('10000.00')
        
        assert securities_value == expected_securities
        assert performance.cash_value > 0
    
    def test_portfolio_performance_dividend_tracking(self, db_session, sample_portfolio):
        """Test dividend income tracking."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('9500.00'),
            total_cost=Decimal('9000.00'),
            dividend_income=Decimal('125.50'),  # Quarterly dividends
            unrealized_gain_loss=Decimal('500.00')
        )
        
        db_session.add(performance)
        db_session.commit()
        
        assert performance.dividend_income == Decimal('125.50')
        
        # Total return includes dividends
        total_return = performance.unrealized_gain_loss + performance.dividend_income
        expected_total = Decimal('625.50')
        
        assert total_return == expected_total
    
    def test_portfolio_performance_benchmark_comparison(self, db_session, sample_portfolio):
        """Test performance vs benchmark."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('11500.00'),
            total_cost=Decimal('10000.00'),
            unrealized_gain_loss=Decimal('1500.00'),
            benchmark_return=Decimal('8.50')  # S&P 500 return %
        )
        
        db_session.add(performance)
        db_session.commit()
        
        # Portfolio return
        portfolio_return = (performance.total_value - performance.total_cost) / performance.total_cost * 100
        expected_portfolio_return = Decimal('15.00')  # 15%
        
        assert portfolio_return == expected_portfolio_return
        
        # Outperformance vs benchmark
        if hasattr(performance, 'benchmark_return'):
            outperformance = portfolio_return - performance.benchmark_return
            assert outperformance == Decimal('6.50')  # 6.5% outperformance
    
    def test_portfolio_performance_risk_metrics(self, db_session, sample_portfolio):
        """Test risk metrics in performance tracking."""
        performance = PortfolioPerformance(
            portfolio_id=sample_portfolio.id,
            date=date.today(),
            total_value=Decimal('10800.00'),
            total_cost=Decimal('10000.00'),
            volatility=Decimal('12.5'),     # Annualized volatility %
            sharpe_ratio=Decimal('1.25'),   # Risk-adjusted return
            max_drawdown=Decimal('-5.2')    # Maximum decline %
        )
        
        db_session.add(performance)
        db_session.commit()
        
        # Check risk metrics if they exist on the model
        if hasattr(performance, 'sharpe_ratio'):
            assert performance.sharpe_ratio == Decimal('1.25')
        if hasattr(performance, 'volatility'):
            assert performance.volatility == Decimal('12.5')
        if hasattr(performance, 'max_drawdown'):
            assert performance.max_drawdown == Decimal('-5.2')