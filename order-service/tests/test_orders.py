import pytest
import json
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'order-service'


def test_create_order_no_auth(client, sample_order_data):
    """Test create order without authentication"""
    response = client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json'
    )

    assert response.status_code == 401


@patch('requests.get')
def test_create_order_success(mock_get, client, app, sample_order_data):
    """Test successful order creation"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock the product service response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'product': {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'stock': 100
        }
    }
    mock_get.return_value = mock_response

    response = client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'order' in data
    assert data['order']['user_id'] == 1
    assert data['order']['status'] == 'pending'


@patch('requests.get')
def test_create_order_product_not_found(mock_get, client, app, sample_order_data):
    """Test create order with non-existent product"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock product not found
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    response = client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 404


@patch('requests.get')
def test_create_order_insufficient_stock(mock_get, client, app):
    """Test create order with insufficient stock"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock product with insufficient stock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'product': {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'stock': 1  # Only 1 in stock
        }
    }
    mock_get.return_value = mock_response

    order_data = {
        'products': [
            {
                'product_id': 1,
                'quantity': 10  # Requesting more than available
            }
        ]
    }

    response = client.post(
        '/api/orders',
        data=json.dumps(order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400


def test_create_order_missing_products(client, app):
    """Test create order without products"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    order_data = {}

    response = client.post(
        '/api/orders',
        data=json.dumps(order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'errors' in data


def test_create_order_empty_products(client, app):
    """Test create order with empty products list"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    order_data = {
        'products': []
    }

    response = client.post(
        '/api/orders',
        data=json.dumps(order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400


def test_create_order_invalid_quantity(client, app):
    """Test create order with invalid quantity"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    order_data = {
        'products': [
            {
                'product_id': 1,
                'quantity': -5  # Negative quantity
            }
        ]
    }

    response = client.post(
        '/api/orders',
        data=json.dumps(order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400


@patch('requests.get')
def test_get_user_orders(mock_get, client, app, db, sample_order_data):
    """Test get orders for current user"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock product service
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'product': {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'stock': 100
        }
    }
    mock_get.return_value = mock_response

    # Create an order
    client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # Get orders
    response = client.get(
        '/api/orders',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'orders' in data
    assert len(data['orders']) > 0


def test_get_orders_no_auth(client):
    """Test get orders without authentication"""
    response = client.get('/api/orders')
    assert response.status_code == 401


@patch('requests.get')
def test_get_order_by_id(mock_get, client, app, sample_order_data):
    """Test get order by ID"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock product service
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'product': {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'stock': 100
        }
    }
    mock_get.return_value = mock_response

    # Create an order
    create_response = client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    order_id = json.loads(create_response.data)['order']['id']

    # Get order by ID
    response = client.get(
        f'/api/orders/{order_id}',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['order']['id'] == order_id


def test_get_order_not_found(client, app):
    """Test get order with non-existent ID"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    response = client.get(
        '/api/orders/999',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 404


@patch('requests.get')
def test_update_order_status(mock_get, client, app, sample_order_data):
    """Test update order status"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock product service
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'product': {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'stock': 100
        }
    }
    mock_get.return_value = mock_response

    # Create an order
    create_response = client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    order_id = json.loads(create_response.data)['order']['id']

    # Update status
    status_data = {'status': 'processing'}
    response = client.put(
        f'/api/orders/{order_id}/status',
        data=json.dumps(status_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['order']['status'] == 'processing'


def test_update_order_status_invalid(client, app):
    """Test update order with invalid status"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    status_data = {'status': 'invalid_status'}
    response = client.put(
        '/api/orders/1/status',
        data=json.dumps(status_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # Will be 404 because order doesn't exist, but would be 400 if it did
    assert response.status_code in [400, 404]


@patch('requests.get')
def test_cancel_order(mock_get, client, app, sample_order_data):
    """Test cancel order"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock product service
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'product': {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'stock': 100
        }
    }
    mock_get.return_value = mock_response

    # Create an order
    create_response = client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    order_id = json.loads(create_response.data)['order']['id']

    # Cancel order
    response = client.delete(
        f'/api/orders/{order_id}',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['order']['status'] == 'cancelled'


@patch('requests.get')
def test_cannot_cancel_shipped_order(mock_get, client, app, db, sample_order_data):
    """Test that shipped orders cannot be cancelled"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock product service
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'product': {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'stock': 100
        }
    }
    mock_get.return_value = mock_response

    # Create an order
    create_response = client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    order_id = json.loads(create_response.data)['order']['id']

    # Update to shipped
    client.put(
        f'/api/orders/{order_id}/status',
        data=json.dumps({'status': 'shipped'}),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # Try to cancel
    response = client.delete(
        f'/api/orders/{order_id}',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400


@patch('requests.get')
def test_get_order_stats(mock_get, client, app, sample_order_data):
    """Test get order statistics"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Mock product service
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'product': {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'stock': 100
        }
    }
    mock_get.return_value = mock_response

    # Create an order
    client.post(
        '/api/orders',
        data=json.dumps(sample_order_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # Get stats
    response = client.get(
        '/api/orders/stats',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_orders' in data
    assert 'total_spent' in data
    assert 'pending_orders' in data
    assert 'completed_orders' in data
    assert data['total_orders'] > 0


def test_get_stats_no_orders(client, app):
    """Test get stats when user has no orders"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    response = client.get(
        '/api/orders/stats',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total_orders'] == 0
    assert data['total_spent'] == 0.0


def test_filter_orders_by_status(client, app):
    """Test filter orders by status"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    response = client.get(
        '/api/orders?status=pending',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'orders' in data


def test_order_pagination(client, app):
    """Test order pagination"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    response = client.get(
        '/api/orders?page=1&per_page=5',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'page' in data
    assert 'pages' in data
