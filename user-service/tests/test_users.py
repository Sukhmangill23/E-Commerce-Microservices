import pytest
import json


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'user-service'


def test_register_user_success(client, sample_user_data):
    """Test successful user registration"""
    response = client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'user' in data
    assert 'tokens' in data
    assert data['user']['username'] == sample_user_data['username']
    assert data['user']['email'] == sample_user_data['email']
    assert 'access_token' in data['tokens']
    assert 'refresh_token' in data['tokens']


def test_register_user_missing_username(client):
    """Test registration with missing username"""
    data = {
        'email': 'test@example.com',
        'password': 'password123'
    }

    response = client.post(
        '/api/users/register',
        data=json.dumps(data),
        content_type='application/json'
    )

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert 'errors' in response_data


def test_register_user_missing_email(client):
    """Test registration with missing email"""
    data = {
        'username': 'testuser',
        'password': 'password123'
    }

    response = client.post(
        '/api/users/register',
        data=json.dumps(data),
        content_type='application/json'
    )

    assert response.status_code == 400


def test_register_user_short_password(client):
    """Test registration with short password"""
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': '123'
    }

    response = client.post(
        '/api/users/register',
        data=json.dumps(data),
        content_type='application/json'
    )

    assert response.status_code == 400


def test_register_user_invalid_email(client):
    """Test registration with invalid email"""
    data = {
        'username': 'testuser',
        'email': 'invalidemail',
        'password': 'password123'
    }

    response = client.post(
        '/api/users/register',
        data=json.dumps(data),
        content_type='application/json'
    )

    assert response.status_code == 400


def test_register_duplicate_username(client, sample_user_data):
    """Test registration with duplicate username"""
    # Register first user
    client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    # Try to register again with same username
    response = client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    assert response.status_code == 409
    data = json.loads(response.data)
    assert 'error' in data


def test_register_duplicate_email(client, sample_user_data):
    """Test registration with duplicate email"""
    # Register first user
    client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    # Try to register with different username but same email
    duplicate_data = sample_user_data.copy()
    duplicate_data['username'] = 'different_user'

    response = client.post(
        '/api/users/register',
        data=json.dumps(duplicate_data),
        content_type='application/json'
    )

    assert response.status_code == 409


def test_login_success(client, sample_user_data):
    """Test successful login"""
    # Register user first
    client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    # Login
    login_data = {
        'username': sample_user_data['username'],
        'password': sample_user_data['password']
    }

    response = client.post(
        '/api/users/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'tokens' in data
    assert 'access_token' in data['tokens']
    assert 'refresh_token' in data['tokens']


def test_login_with_email(client, sample_user_data):
    """Test login with email instead of username"""
    # Register user first
    client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    # Login with email
    login_data = {
        'email': sample_user_data['email'],
        'password': sample_user_data['password']
    }

    response = client.post(
        '/api/users/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )

    assert response.status_code == 200


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    login_data = {
        'username': 'nonexistent',
        'password': 'wrongpassword'
    }

    response = client.post(
        '/api/users/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )

    assert response.status_code == 401


def test_login_wrong_password(client, sample_user_data):
    """Test login with correct username but wrong password"""
    # Register user
    client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    # Try login with wrong password
    login_data = {
        'username': sample_user_data['username'],
        'password': 'wrongpassword'
    }

    response = client.post(
        '/api/users/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )

    assert response.status_code == 401


def test_get_current_user(client, sample_user_data):
    """Test get current user endpoint"""
    # Register and get token
    reg_response = client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    tokens = json.loads(reg_response.data)['tokens']
    access_token = tokens['access_token']

    # Get current user
    response = client.get(
        '/api/users/me',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['user']['username'] == sample_user_data['username']
    assert data['user']['email'] == sample_user_data['email']


def test_get_current_user_no_token(client):
    """Test get current user without token"""
    response = client.get('/api/users/me')
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test get current user with invalid token"""
    response = client.get(
        '/api/users/me',
        headers={'Authorization': 'Bearer invalid_token'}
    )
    assert response.status_code == 422


def test_update_user(client, sample_user_data):
    """Test update user"""
    # Register
    reg_response = client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    data = json.loads(reg_response.data)
    user_id = data['user']['id']
    access_token = data['tokens']['access_token']

    # Update user email
    update_data = {'email': 'newemail@example.com'}
    response = client.put(
        f'/api/users/{user_id}',
        data=json.dumps(update_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    updated_data = json.loads(response.data)
    assert updated_data['user']['email'] == 'newemail@example.com'


def test_update_other_user_forbidden(client, sample_user_data):
    """Test that user cannot update another user's profile"""
    # Register first user
    reg_response = client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    access_token = json.loads(reg_response.data)['tokens']['access_token']

    # Try to update user ID 999 (doesn't exist or is different user)
    update_data = {'email': 'hacker@example.com'}
    response = client.put(
        '/api/users/999',
        data=json.dumps(update_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 403


def test_delete_user(client, sample_user_data):
    """Test delete user"""
    # Register
    reg_response = client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    data = json.loads(reg_response.data)
    user_id = data['user']['id']
    access_token = data['tokens']['access_token']

    # Delete user
    response = client.delete(
        f'/api/users/{user_id}',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200

    # Verify user is deleted by trying to get profile
    get_response = client.get(
        '/api/users/me',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert get_response.status_code == 404


def test_get_users_list(client, sample_user_data):
    """Test get users list endpoint"""
    # Register a user
    reg_response = client.post(
        '/api/users/register',
        data=json.dumps(sample_user_data),
        content_type='application/json'
    )

    access_token = json.loads(reg_response.data)['tokens']['access_token']

    # Get users list
    response = client.get(
        '/api/users',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'users' in data
    assert len(data['users']) > 0
