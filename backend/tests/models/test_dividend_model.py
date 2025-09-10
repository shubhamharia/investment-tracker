import pytest
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from app.models import Dividend, Security, Platform
from app.constants import DECIMAL_PLACES

def test_dividend_creation(db_session):
    """Test basic dividend creation."""
    # Create test security and platform
    security = Security(ticker='AAPL', name='Apple Inc.', currency='USD')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create dividend
    dividend = Dividend(
        security_id=security.id,
        platform_id=platform.id,
        ex_date=date(2025, 1, 1),
        pay_date=date(2025, 1, 15),
        dividend_per_share=Decimal('0.88'),
        quantity_held=Decimal('100'),
        gross_dividend=Decimal('88.00'),
        withholding_tax=Decimal('13.20'),
        net_dividend=Decimal('74.80'),
        currency='USD'
    )
    
    db_session.add(dividend)
    db_session.commit()
    
    assert dividend.id is not None
    assert dividend.security_id == security.id
    assert dividend.platform_id == platform.id

def test_dividend_amount_calculation(db_session):
    """Test dividend amount calculations."""
    # Create test security and platform
    security = Security(ticker='MSFT', name='Microsoft Corp', currency='USD')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create dividend
    dividend = Dividend(
        security_id=security.id,
        platform_id=platform.id,
        ex_date=date(2025, 1, 1),
        dividend_per_share=Decimal('0.75'),
        quantity_held=Decimal('200'),
        currency='USD'
    )
    
    # Test calculation
    dividend.calculate_amounts()
    
    expected_gross = Decimal('150.00')
    expected_net = Decimal('150.00')  # No tax in this case
    
    assert dividend.gross_dividend.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}')) == expected_gross
    assert dividend.net_dividend.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}')) == expected_net

def test_dividend_withholding_tax(db_session):
    """Test dividend withholding tax calculations."""
    # Create test security and platform
    security = Security(ticker='BHP', name='BHP Group', currency='GBP')
    platform = Platform(name='Test Platform', currency='GBP')
    db_session.add_all([security, platform])
    db_session.commit()
    
    # Create dividend with withholding tax
    dividend = Dividend(
        security_id=security.id,
        platform_id=platform.id,
        ex_date=date(2025, 1, 1),
        dividend_per_share=Decimal('2.00'),
        quantity_held=Decimal('50'),
        withholding_tax=Decimal('15.00'),  # 15% tax
        currency='GBP'
    )
    
    # Test calculation
    dividend.calculate_amounts()
    
    expected_gross = Decimal('100.00')
    expected_net = Decimal('85.00')  # After 15% tax
    
    assert dividend.gross_dividend.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}')) == expected_gross
    assert dividend.net_dividend.quantize(Decimal(f'0.{"0" * DECIMAL_PLACES}')) == expected_net

def test_dividend_to_dict(db_session):
    """Test dividend to_dict method."""
    # Create test security and platform
    security = Security(ticker='VOD', name='Vodafone Group', currency='GBP')
    platform = Platform(name='Test Platform', currency='GBP')
    db_session.add_all([security, platform])
    db_session.commit()
    
    test_date = date(2025, 1, 1)
    test_pay_date = date(2025, 1, 15)
    
    # Create dividend
    dividend = Dividend(
        security_id=security.id,
        platform_id=platform.id,
        ex_date=test_date,
        pay_date=test_pay_date,
        dividend_per_share=Decimal('0.50'),
        quantity_held=Decimal('1000'),
        gross_dividend=Decimal('500.00'),
        withholding_tax=Decimal('0'),
        net_dividend=Decimal('500.00'),
        currency='GBP'
    )
    
    db_session.add(dividend)
    db_session.commit()
    
    # Get dictionary representation
    dividend_dict = dividend.to_dict()
    
    # Verify dictionary content
    assert dividend_dict['security_id'] == security.id
    assert dividend_dict['platform_id'] == platform.id
    assert dividend_dict['ex_date'] == test_date.isoformat()
    assert dividend_dict['pay_date'] == test_pay_date.isoformat()
    assert Decimal(dividend_dict['dividend_per_share']) == Decimal('0.50')
    assert Decimal(dividend_dict['quantity_held']) == Decimal('1000')
    assert Decimal(dividend_dict['gross_dividend']) == Decimal('500.00')
    assert Decimal(dividend_dict['net_dividend']) == Decimal('500.00')
    assert dividend_dict['currency'] == 'GBP'

def test_invalid_dividend_calculation(db_session):
    """Test handling of invalid dividend calculations."""
    # Create test security and platform
    security = Security(ticker='TEST', name='Test Corp', currency='USD')
    platform = Platform(name='Test Platform', currency='USD')
    db_session.add_all([security, platform])
    db_session.commit()

    # Test that negative dividend per share is rejected
    with pytest.raises(ValueError, match="Dividend per share must be positive"):
        Dividend(
            security_id=security.id,
            platform_id=platform.id,
            ex_date=date(2025, 1, 1),
            dividend_per_share=Decimal('-1.00'),  # Invalid negative value
            quantity_held=Decimal('100'),
            currency='USD'
        )
