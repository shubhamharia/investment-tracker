from .test_base import TestBase
import json

class TestAPI(TestBase):
    def test_health_check(self):
        response = self.client.get('/api/health')
        assert response.status_code == 200
        assert b'healthy' in response.data

    def test_platform_crud(self):
        # Create
        data = {'name': 'Test Platform', 'description': 'Test Description'}
        response = self.client.post('/api/platforms', 
                                  data=json.dumps(data),
                                  content_type='application/json')
        assert response.status_code == 201
        
        # Read
        platform_id = json.loads(response.data)['id']
        response = self.client.get(f'/api/platforms/{platform_id}')
        assert response.status_code == 200
        
        # Update
        update_data = {'name': 'Updated Platform'}
        response = self.client.put(f'/api/platforms/{platform_id}',
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        assert response.status_code == 200
        
        # Delete
        response = self.client.delete(f'/api/platforms/{platform_id}')
        assert response.status_code == 204