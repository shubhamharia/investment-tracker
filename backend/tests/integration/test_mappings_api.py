import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta


class TestMappingsAPI:
    """Test security mappings API endpoints."""

    def test_get_all_mappings(self, client, auth_headers, sample_security_mapping):
        """Test getting all security mappings."""
        response = client.get('/api/mappings', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_mappings_unauthorized(self, client):
        """Test getting mappings without authentication."""
        response = client.get('/api/mappings')
        assert response.status_code == 401

    def test_get_mapping_by_id(self, client, auth_headers, sample_security_mapping):
        """Test getting specific mapping by ID."""
        response = client.get(f'/api/mappings/{sample_security_mapping.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == sample_security_mapping.id
        assert data['platform_symbol'] == sample_security_mapping.platform_symbol

    def test_get_mapping_not_found(self, client, auth_headers):
        """Test getting non-existent mapping."""
        response = client.get('/api/mappings/99999', headers=auth_headers)
        assert response.status_code == 404

    def test_create_mapping(self, client, auth_headers, sample_security, sample_platform):
        """Test creating a new security mapping."""
        mapping_data = {
            'security_id': sample_security.id,
            'platform_id': sample_platform.id,
            'platform_symbol': 'APPL',  # Different from actual symbol
            'platform_name': 'Apple Inc',
            'mapping_type': 'MANUAL'
        }
        
        response = client.post('/api/mappings', json=mapping_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['platform_symbol'] == 'APPL'
        assert data['mapping_type'] == 'MANUAL'

    def test_create_mapping_duplicate(self, client, auth_headers, sample_security_mapping):
        """Test creating duplicate mapping."""
        mapping_data = {
            'security_id': sample_security_mapping.security_id,
            'platform_id': sample_security_mapping.platform_id,
            'platform_symbol': sample_security_mapping.platform_symbol,
            'mapping_type': 'EXACT'
        }
        
        response = client.post('/api/mappings', json=mapping_data, headers=auth_headers)
        assert response.status_code == 400

    def test_create_mapping_invalid_security(self, client, auth_headers, sample_platform):
        """Test creating mapping with invalid security."""
        mapping_data = {
            'security_id': 99999,  # Non-existent security
            'platform_id': sample_platform.id,
            'platform_symbol': 'INVALID',
            'mapping_type': 'MANUAL'
        }
        
        response = client.post('/api/mappings', json=mapping_data, headers=auth_headers)
        assert response.status_code == 400

    def test_create_mapping_missing_fields(self, client, auth_headers):
        """Test creating mapping with missing required fields."""
        mapping_data = {
            'platform_symbol': 'AAPL'
            # Missing security_id, platform_id, mapping_type
        }
        
        response = client.post('/api/mappings', json=mapping_data, headers=auth_headers)
        assert response.status_code == 400

    def test_update_mapping(self, client, auth_headers, sample_security_mapping):
        """Test updating an existing mapping."""
        update_data = {
            'platform_symbol': 'APPLE',
            'mapping_type': 'FUZZY'
        }
        
        response = client.put(f'/api/mappings/{sample_security_mapping.id}', json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['platform_symbol'] == 'APPLE'
        assert data['mapping_type'] == 'FUZZY'

    def test_update_mapping_not_found(self, client, auth_headers):
        """Test updating non-existent mapping."""
        update_data = {
            'platform_symbol': 'UPDATED'
        }
        
        response = client.put('/api/mappings/99999', json=update_data, headers=auth_headers)
        assert response.status_code == 404

    def test_delete_mapping(self, client, auth_headers, sample_security_mapping):
        """Test deleting a mapping."""
        response = client.delete(f'/api/mappings/{sample_security_mapping.id}', headers=auth_headers)
        assert response.status_code == 200

    def test_delete_mapping_not_found(self, client, auth_headers):
        """Test deleting non-existent mapping."""
        response = client.delete('/api/mappings/99999', headers=auth_headers)
        assert response.status_code == 404

    def test_get_mappings_by_security(self, client, auth_headers, sample_security, sample_security_mapping):
        """Test getting mappings for specific security."""
        response = client.get(f'/api/securities/{sample_security.id}/mappings', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_mappings_by_platform(self, client, auth_headers, sample_platform, sample_security_mapping):
        """Test getting mappings for specific platform."""
        response = client.get(f'/api/platforms/{sample_platform.id}/mappings', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_search_mappings_by_symbol(self, client, auth_headers, sample_security_mapping):
        """Test searching mappings by platform symbol."""
        response = client.get(f'/api/mappings/search?symbol={sample_security_mapping.platform_symbol}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_search_mappings_by_type(self, client, auth_headers, sample_security_mapping):
        """Test searching mappings by mapping type."""
        response = client.get('/api/mappings/search?type=EXACT', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_validate_mapping(self, client, auth_headers, sample_security, sample_platform):
        """Test validating a potential mapping."""
        validation_data = {
            'security_id': sample_security.id,
            'platform_id': sample_platform.id,
            'platform_symbol': 'AAPL'
        }
        
        response = client.post('/api/mappings/validate', json=validation_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'is_valid' in data
        assert 'confidence_score' in data

    def test_auto_create_mappings(self, client, auth_headers, sample_security, sample_platform):
        """Test auto-creating mappings for a platform."""
        auto_mapping_data = {
            'platform_id': sample_platform.id,
            'confidence_threshold': 0.8
        }
        
        response = client.post('/api/mappings/auto-create', json=auto_mapping_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'created_count' in data
        assert 'suggestions' in data

    def test_bulk_import_mappings(self, client, auth_headers, sample_security, sample_platform):
        """Test bulk importing mappings."""
        mappings_data = {
            'mappings': [
                {
                    'security_id': sample_security.id,
                    'platform_id': sample_platform.id,
                    'platform_symbol': 'AAPL_US',
                    'mapping_type': 'EXACT'
                },
                {
                    'security_id': sample_security.id,
                    'platform_id': sample_platform.id,
                    'platform_symbol': 'APPLE',
                    'mapping_type': 'FUZZY'
                }
            ]
        }
        
        response = client.post('/api/mappings/bulk', json=mappings_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert 'imported_count' in data
        assert 'errors' in data

    def test_export_mappings(self, client, auth_headers, sample_security_mapping):
        """Test exporting mappings to CSV."""
        response = client.get('/api/mappings/export', headers=auth_headers)
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'

    def test_get_mapping_statistics(self, client, auth_headers):
        """Test getting mapping statistics."""
        response = client.get('/api/mappings/statistics', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_mappings' in data
        assert 'by_type' in data
        assert 'by_platform' in data

    def test_suggest_mappings(self, client, auth_headers, sample_security):
        """Test getting mapping suggestions for a security."""
        response = client.get(f'/api/mappings/suggest/{sample_security.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_verify_mappings(self, client, auth_headers, sample_security_mapping):
        """Test verifying existing mappings."""
        verify_data = {
            'mapping_ids': [sample_security_mapping.id]
        }
        
        response = client.post('/api/mappings/verify', json=verify_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'verified_count' in data
        assert 'issues' in data

    def test_get_orphaned_securities(self, client, auth_headers):
        """Test getting securities without mappings."""
        response = client.get('/api/mappings/orphaned', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_mapping_conflicts(self, client, auth_headers):
        """Test getting mapping conflicts."""
        response = client.get('/api/mappings/conflicts', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_resolve_mapping_conflict(self, client, auth_headers, sample_security_mapping):
        """Test resolving a mapping conflict."""
        resolution_data = {
            'preferred_mapping_id': sample_security_mapping.id,
            'action': 'KEEP_PREFERRED'
        }
        
        response = client.post(f'/api/mappings/conflicts/{sample_security_mapping.id}/resolve', 
                             json=resolution_data, headers=auth_headers)
        assert response.status_code == 200

    def test_admin_get_all_mappings(self, client, admin_auth_headers):
        """Test admin getting all mappings across all users."""
        response = client.get('/api/mappings/admin/all', headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)

    def test_non_admin_cannot_access_admin_endpoints(self, client, auth_headers):
        """Test non-admin cannot access admin mapping endpoints."""
        response = client.get('/api/mappings/admin/all', headers=auth_headers)
        assert response.status_code == 403