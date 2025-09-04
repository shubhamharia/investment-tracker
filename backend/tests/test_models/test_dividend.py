import pytest
from backend.models import Dividend

def test_dividend_creation():
    dividend = Dividend(amount=100, date='2023-01-01')
    assert dividend.amount == 100
    assert dividend.date == '2023-01-01'

def test_dividend_str():
    dividend = Dividend(amount=100, date='2023-01-01')
    assert str(dividend) == 'Dividend(amount=100, date=2023-01-01)'