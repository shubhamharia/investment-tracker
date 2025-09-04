from models.security import Security

def test_security_model():
    security = Security(name="Test Security", symbol="TS")
    assert security.name == "Test Security"
    assert security.symbol == "TS"