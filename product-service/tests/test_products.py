import pytest
import json
from flask_jwt_extended import create_access_token


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'product-service'


def test_get_products_empty(client):
    """Test get products when database is empty"""
    response = client.get('/api/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['products'] == []
    assert data['total'] == 0


def test_create_product_success(client, app, sample_product_data):
    """Test successful product creation"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    response = client.post(
        '/api/products',
        data=json.dumps(sample_product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'product' in data
    assert data['product']['name'] == sample_product_data['name']
    assert data['product']['price'] == sample_product_data['price']


def test_create_product_no_auth(client, sample_product_data):
    """Test create product without authentication"""
    response = client.post(
        '/api/products',
        data=json.dumps(sample_product_data),
        content_type='application/json'
    )

    assert response.status_code == 401


def test_create_product_missing_name(client, app):
    """Test create product with missing name"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    product_data = {
        'price': 29.99,
        'stock': 100
    }

    response = client.post(
        '/api/products',
        data=json.dumps(product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'errors' in data


def test_create_product_short_name(client, app):
    """Test create product with too short name"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    product_data = {
        'name': 'AB',  # Too short
        'price': 29.99,
        'stock': 100
    }

    response = client.post(
        '/api/products',
        data=json.dumps(product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400


def test_create_product_negative_price(client, app):
    """Test create product with negative price"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    product_data = {
        'name': 'Test Product',
        'price': -10.00,
        'stock': 100
    }

    response = client.post(
        '/api/products',
        data=json.dumps(product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400


def test_create_product_negative_stock(client, app):
    """Test create product with negative stock"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    product_data = {
        'name': 'Test Product',
        'price': 29.99,
        'stock': -5
    }

    response = client.post(
        '/api/products',
        data=json.dumps(product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400


def test_get_products_with_data(client, app, sample_product_data):
    """Test get products after creating some"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create a product
    client.post(
        '/api/products',
        data=json.dumps(sample_product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # Get products
    response = client.get('/api/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['products']) == 1
    assert data['total'] == 1


def test_get_product_by_id(client, app, sample_product_data):
    """Test get product by ID"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create a product
    create_response = client.post(
        '/api/products',
        data=json.dumps(sample_product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    product_id = json.loads(create_response.data)['product']['id']

    # Get product by ID
    response = client.get(f'/api/products/{product_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['product']['id'] == product_id


def test_get_product_not_found(client):
    """Test get product with non-existent ID"""
    response = client.get('/api/products/999')
    assert response.status_code == 404


def test_update_product(client, app, sample_product_data):
    """Test update product"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create a product
    create_response = client.post(
        '/api/products',
        data=json.dumps(sample_product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    product_id = json.loads(create_response.data)['product']['id']

    # Update product
    update_data = {
        'name': 'Updated Product',
        'price': 39.99,
        'stock': 50
    }

    response = client.put(
        f'/api/products/{product_id}',
        data=json.dumps(update_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['product']['name'] == 'Updated Product'
    assert data['product']['price'] == 39.99


def test_update_product_not_found(client, app):
    """Test update non-existent product"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    update_data = {
        'name': 'Updated Product',
        'price': 39.99
    }

    response = client.put(
        '/api/products/999',
        data=json.dumps(update_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 404


def test_delete_product(client, app, sample_product_data):
    """Test delete product"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create a product
    create_response = client.post(
        '/api/products',
        data=json.dumps(sample_product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    product_id = json.loads(create_response.data)['product']['id']

    # Delete product
    response = client.delete(
        f'/api/products/{product_id}',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200

    # Verify product is deleted
    get_response = client.get(f'/api/products/{product_id}')
    assert get_response.status_code == 404


def test_update_stock(client, app, sample_product_data):
    """Test update product stock"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create a product
    create_response = client.post(
        '/api/products',
        data=json.dumps(sample_product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    product_id = json.loads(create_response.data)['product']['id']

    # Update stock (add 10)
    stock_data = {'quantity': 10}
    response = client.put(
        f'/api/products/{product_id}/stock',
        data=json.dumps(stock_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['product']['stock'] == sample_product_data['stock'] + 10


def test_update_stock_insufficient(client, app, sample_product_data):
    """Test update stock with quantity that would make it negative"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create a product
    create_response = client.post(
        '/api/products',
        data=json.dumps(sample_product_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    product_id = json.loads(create_response.data)['product']['id']

    # Try to reduce stock by more than available
    stock_data = {'quantity': -200}  # More than available
    response = client.put(
        f'/api/products/{product_id}/stock',
        data=json.dumps(stock_data),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    assert response.status_code == 400


def test_get_categories(client, app, sample_product_data):
    """Test get product categories"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create products with different categories
    product1 = sample_product_data.copy()
    product1['category'] = 'Electronics'
    client.post(
        '/api/products',
        data=json.dumps(product1),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    product2 = sample_product_data.copy()
    product2['name'] = 'Another Product'
    product2['category'] = 'Books'
    client.post(
        '/api/products',
        data=json.dumps(product2),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # Get categories
    response = client.get('/api/products/categories')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'Electronics' in data['categories']
    assert 'Books' in data['categories']


def test_filter_products_by_category(client, app, sample_product_data):
    """Test filter products by category"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create products
    product1 = sample_product_data.copy()
    product1['category'] = 'Electronics'
    client.post(
        '/api/products',
        data=json.dumps(product1),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    product2 = sample_product_data.copy()
    product2['name'] = 'Book Product'
    product2['category'] = 'Books'
    client.post(
        '/api/products',
        data=json.dumps(product2),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # Filter by Electronics
    response = client.get('/api/products?category=Electronics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 1
    assert data['products'][0]['category'] == 'Electronics'


def test_filter_products_by_price_range(client, app, sample_product_data):
    """Test filter products by price range"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create products with different prices
    product1 = sample_product_data.copy()
    product1['price'] = 10.00
    client.post(
        '/api/products',
        data=json.dumps(product1),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    product2 = sample_product_data.copy()
    product2['name'] = 'Expensive Product'
    product2['price'] = 100.00
    client.post(
        '/api/products',
        data=json.dumps(product2),
        content_type='application/json',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # Filter by price range
    response = client.get('/api/products?min_price=50&max_price=150')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == 1
    assert data['products'][0]['price'] == 100.00


def test_pagination(client, app, sample_product_data):
    """Test product pagination"""
    with app.app_context():
        access_token = create_access_token(identity='1')

    # Create multiple products
    for i in range(5):
        product = sample_product_data.copy()
        product['name'] = f'Product {i}'
        client.post(
            '/api/products',
            data=json.dumps(product),
            content_type='application/json',
            headers={'Authorization': f'Bearer {access_token}'}
        )

    # Get first page with 2 items per page
    response = client.get('/api/products?page=1&per_page=2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['products']) == 2
    assert data['total'] == 5
    assert data['pages'] == 3
