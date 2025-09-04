import pytest
from models.holding import Holding

def test_holding_creation():
    holding = Holding(name="Test Holding", quantity=10)
    assert holding.name == "Test Holding"
    assert holding.quantity == 10

def test_holding_quantity_update():
    holding = Holding(name="Test Holding", quantity=10)
    holding.update_quantity(5)
    assert holding.quantity == 15

def test_holding_str():
    holding = Holding(name="Test Holding", quantity=10)
    assert str(holding) == "Holding(Test Holding, 10)"