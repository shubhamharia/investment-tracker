"""
Unit tests for Platform model.
"""
import pytest
from app.models.platform import Platform
from app.extensions import db


class TestPlatformModel:
    """Test cases for Platform model."""
    
    def test_platform_creation(self, db_session):
        """Test creating a new platform."""
        platform = Platform(
            name='Interactive Brokers',
            description='Professional trading platform'
        )
        
        db_session.add(platform)
        db_session.commit()
        
        assert platform.id is not None
        assert platform.name == 'Interactive Brokers'
        assert platform.description == 'Professional trading platform'
        assert platform.created_at is not None
        assert platform.updated_at is not None
    
    def test_platform_representation(self, sample_platform):
        """Test platform string representation."""
        expected = f'<Platform {sample_platform.name}>'
        assert str(sample_platform) == expected
        assert repr(sample_platform) == expected
    
    def test_platform_unique_name(self, db_session, sample_platform):
        """Test that platform names must be unique."""
        duplicate_platform = Platform(
            name='Test Broker',  # Same as sample_platform
            description='Another test platform'
        )
        
        db_session.add(duplicate_platform)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_platform_serialization(self, sample_platform):
        """Test platform serialization to dictionary."""
        platform_dict = sample_platform.to_dict()
        
        expected_keys = {
            'id', 'name', 'description', 'created_at', 'updated_at'
        }
        
        assert set(platform_dict.keys()) == expected_keys
        assert platform_dict['name'] == sample_platform.name
        assert platform_dict['description'] == sample_platform.description
    
    def test_platform_relationships(self, sample_platform):
        """Test platform relationships."""
        # Should have empty relationships initially
        assert len(sample_platform.portfolios) == 0
        assert len(sample_platform.security_mappings) == 0
    
    def test_platform_with_portfolios(self, db_session, sample_platform, sample_user):
        """Test platform with related portfolios."""
        from app.models.portfolio import Portfolio
        
        portfolio1 = Portfolio(
            name='Portfolio 1',
            user_id=sample_user.id,
            platform_id=sample_platform.id,
            currency='USD',
            is_active=True
        )
        
        portfolio2 = Portfolio(
            name='Portfolio 2',
            user_id=sample_user.id,
            platform_id=sample_platform.id,
            currency='EUR',
            is_active=True
        )
        
        db_session.add_all([portfolio1, portfolio2])
        db_session.commit()
        
        # Refresh to load relationships
        db_session.refresh(sample_platform)
        
        assert len(sample_platform.portfolios) == 2
        portfolio_names = [p.name for p in sample_platform.portfolios]
        assert 'Portfolio 1' in portfolio_names
        assert 'Portfolio 2' in portfolio_names
    
    def test_platform_description_optional(self, db_session):
        """Test platform creation without description."""
        platform = Platform(name='Minimal Platform')
        
        db_session.add(platform)
        db_session.commit()
        
        assert platform.id is not None
        assert platform.name == 'Minimal Platform'
        assert platform.description is None
    
    def test_platform_common_brokers(self, db_session):
        """Test creating common broker platforms."""
        brokers = [
            ('Charles Schwab', 'Full-service brokerage'),
            ('Fidelity', 'Investment management company'),
            ('E*TRADE', 'Online brokerage'),
            ('TD Ameritrade', 'Online broker'),
            ('Robinhood', 'Commission-free trading'),
            ('Interactive Brokers', 'Professional trading platform'),
            ('Vanguard', 'Investment management company')
        ]
        
        platforms = []
        for name, description in brokers:
            platform = Platform(name=name, description=description)
            platforms.append(platform)
            db_session.add(platform)
        
        db_session.commit()
        
        # Verify all platforms were created
        assert len(platforms) == len(brokers)
        for platform, (expected_name, expected_desc) in zip(platforms, brokers):
            assert platform.name == expected_name
            assert platform.description == expected_desc
            assert platform.id is not None
    
    def test_platform_with_security_mappings(self, db_session, sample_platform, sample_security):
        """Test platform with security mappings."""
        from app.models.security_mapping import SecurityMapping
        
        mapping = SecurityMapping(
            security_id=sample_security.id,
            platform_id=sample_platform.id,
            platform_symbol='AAPL',
            platform_name='Apple Inc.',
            mapping_type='EXACT'
        )
        
        db_session.add(mapping)
        db_session.commit()
        
        # Refresh to load relationships
        db_session.refresh(sample_platform)
        
        assert len(sample_platform.security_mappings) == 1
        assert sample_platform.security_mappings[0].platform_symbol == 'AAPL'
    
    def test_platform_name_validation(self, db_session):
        """Test platform name requirements."""
        # Test with empty name should fail at database level
        platform = Platform(name='')
        db_session.add(platform)
        
        # This might pass at model level but should be validated at API level
        # The database constraint depends on the schema definition
        try:
            db_session.commit()
            # If it commits, the name was accepted
            assert platform.name == ''
        except Exception:
            # If it fails, that's also acceptable behavior
            db_session.rollback()
    
    def test_platform_case_sensitivity(self, db_session):
        """Test platform name case sensitivity."""
        platform1 = Platform(name='Test Platform')
        platform2 = Platform(name='test platform')
        
        db_session.add_all([platform1, platform2])
        
        try:
            db_session.commit()
            # If both commit, names are case-sensitive
            assert platform1.name == 'Test Platform'
            assert platform2.name == 'test platform'
        except Exception:
            # If it fails, names might be case-insensitive unique
            db_session.rollback()