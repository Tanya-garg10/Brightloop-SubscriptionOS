import pytest
from app import app, db, User, Customer, generate_password_hash
from datetime import datetime

@pytest.fixture
def client(app_context):
    with app.test_client() as client:
        yield client

def test_register_customer(client):
    """Test customer registration"""
    response = client.post('/api/register', json={
        'name': 'Test Customer',
        'email': 'test@example.com',
        'password': 'Test@1234',
        'company': 'Test Company'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'user' in data
    assert 'id' in data['user']

def test_register_invalid_password(client):
    """Test registration with weak password"""
    response = client.post('/api/register', json={
        'name': 'Test Customer',
        'email': 'test2@example.com',
        'password': 'weak',
        'company': 'Test Company'
    })
    assert response.status_code == 400

def test_register_duplicate_email(client):
    """Test registration with duplicate email"""
    client.post('/api/register', json={
        'name': 'Test Customer',
        'email': 'test@example.com',
        'password': 'Test@1234',
        'company': 'Test Company'
    })
    response = client.post('/api/register', json={
        'name': 'Another Customer',
        'email': 'test@example.com',
        'password': 'Test@1234',
        'company': 'Another Company'
    })
    assert response.status_code == 409

def test_login_success(client):
    """Test successful login"""
    # First register
    client.post('/api/register', json={
        'name': 'Test Customer',
        'email': 'test@example.com',
        'password': 'Test@1234',
        'company': 'Test Company'
    })

    # Then login
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'Test@1234'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'user' in data
    assert data['user']['email'] == 'test@example.com'

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/api/login', json={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401

def test_logout(client):
    """Test logout"""
    # Login first
    client.post('/api/register', json={
        'name': 'Test Customer',
        'email': 'test@example.com',
        'password': 'Test@1234',
        'company': 'Test Company'
    })
    client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'Test@1234'
    })

    # Logout
    response = client.post('/api/logout')
    assert response.status_code == 200
    data = response.get_json()
    assert data['ok'] == True

def test_forgot_password(client):
    """Test password reset request"""
    client.post('/api/register', json={
        'name': 'Test Customer',
        'email': 'test@example.com',
        'password': 'Test@1234',
        'company': 'Test Company'
    })

    response = client.post('/api/forgot', json={
        'email': 'test@example.com'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_me_endpoint_unauthenticated(client):
    """Test /api/me without authentication"""
    response = client.get('/api/me')
    assert response.status_code == 200
    data = response.get_json()
    assert data['user'] is None
