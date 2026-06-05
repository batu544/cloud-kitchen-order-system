import pytest
import json
from flask import Flask, g
from unittest.mock import MagicMock

# Import admin_bp after mocking or mock the functions it uses
from src.api.admin import admin_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(admin_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_user_with_phone_as_username(client, mocker):
    # Mock JWT decoding to return an admin user
    mocker.patch('src.middleware.auth_middleware.extract_token_from_header', return_value='valid-token')
    mocker.patch('src.middleware.auth_middleware.decode_jwt_token', return_value={'user_id': 1, 'role': 'admin'})
    
    # Mock AuthService.register_user
    mock_auth_service = mocker.patch('src.services.auth_service.AuthService.register_user')
    mock_auth_service.return_value = (True, "Registration successful", {
        'user_id': 123,
        'username': '1234567890',
        'role': 'customer',
        'cust_id': 456,
        'token': 'mock-token'
    })
    
    payload = {
        'cust_name': 'Test User',
        'cust_phone_number': '1234567890',
        'email': 'test@example.com'
    }
    
    response = client.post('/api/admin/users', 
                           data=json.dumps(payload),
                           headers={'Authorization': 'Bearer valid-token'},
                           content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
    # Should ALWAYS use phone as username even if email is provided
    assert data['data']['username'] == '1234567890'

def test_create_user_missing_fields(client, mocker):
    mocker.patch('src.middleware.auth_middleware.extract_token_from_header', return_value='valid-token')
    mocker.patch('src.middleware.auth_middleware.decode_jwt_token', return_value={'user_id': 1, 'role': 'admin'})
    
    payload = {
        'cust_name': 'Test User',
        # missing phone number which is required
    }
    
    response = client.post('/api/admin/users', 
                           data=json.dumps(payload),
                           headers={'Authorization': 'Bearer valid-token'},
                           content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert "Missing required fields" in data['message']

def test_create_user_not_admin(client, mocker):
    mocker.patch('src.middleware.auth_middleware.extract_token_from_header', return_value='valid-token')
    mocker.patch('src.middleware.auth_middleware.decode_jwt_token', return_value={'user_id': 2, 'role': 'customer'})
    
    payload = {
        'cust_name': 'Test User',
        'cust_phone_number': '1234567890'
    }
    
    response = client.post('/api/admin/users', 
                           data=json.dumps(payload),
                           headers={'Authorization': 'Bearer valid-token'},
                           content_type='application/json')
    
    assert response.status_code == 403
    data = json.loads(response.data)
    assert data['success'] is False
    assert "Admin access required" in data['message']
