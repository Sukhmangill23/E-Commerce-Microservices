from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os

from .database import db, redis_client, init_db
from .models import Product
from .schemas import validate_product

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/product_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Initialize extensions
init_db(app)
jwt = JWTManager(app)
CORS(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=app.config['REDIS_URL']
)


# Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'product-service'}), 200


@app.route('/api/products', methods=['GET'])
@limiter.limit("50 per minute")
def get_products():
    """Get all products with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    # Build query
    query = Product.query

    if category:
        query = query.filter_by(category=category)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Try cache for simple queries
    cache_key = f"products:page:{page}:per_page:{per_page}"
    if not any([category, min_price, max_price]):
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return jsonify(eval(cached_result.decode())), 200

    # Paginate
    products = query.paginate(page=page, per_page=per_page, error_out=False)

    result = {
        'products': [product.to_dict() for product in products.items],
        'total': products.total,
        'page': products.page,
        'pages': products.pages
    }

    # Cache result for 5 minutes
    if not any([category, min_price, max_price]):
        redis_client.setex(cache_key, 300, str(result))

    return jsonify(result), 200


@app.route('/api/products/<int:product_id>', methods=['GET'])
@limiter.limit("100 per minute")
def get_product(product_id):
    """Get product by ID"""
    # Try cache first
    cache_key = f"product:{product_id}"
    cached_product = redis_client.get(cache_key)
    if cached_product:
        return jsonify({'product': eval(cached_product.decode())}), 200

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Cache for 10 minutes
    redis_client.setex(cache_key, 600, str(product.to_dict()))

    return jsonify({'product': product.to_dict()}), 200


@app.route('/api/products', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def create_product():
    """Create a new product"""
    data = request.get_json()

    # Validate input
    errors = validate_product(data)
    if errors:
        return jsonify({'errors': errors}), 400

    # Create product
    product = Product(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        stock=data.get('stock', 0),
        category=data.get('category', 'General')
    )

    db.session.add(product)
    db.session.commit()

    # Invalidate cache
    redis_client.delete('products:page:*')

    return jsonify({
        'message': 'Product created successfully',
        'product': product.to_dict()
    }), 201


@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per minute")
def update_product(product_id):
    """Update a product"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()

    # Validate input
    errors = validate_product(data)
    if errors:
        return jsonify({'errors': errors}), 400

    # Update product
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = data['price']
    if 'stock' in data:
        product.stock = data['stock']
    if 'category' in data:
        product.category = data['category']

    db.session.commit()

    # Invalidate cache
    redis_client.delete(f"product:{product_id}")
    redis_client.delete('products:page:*')

    return jsonify({
        'message': 'Product updated successfully',
        'product': product.to_dict()
    }), 200


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per minute")
def delete_product(product_id):
    """Delete a product"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    db.session.delete(product)
    db.session.commit()

    # Invalidate cache
    redis_client.delete(f"product:{product_id}")
    redis_client.delete('products:page:*')

    return jsonify({'message': 'Product deleted successfully'}), 200


@app.route('/api/products/<int:product_id>/stock', methods=['PUT'])
@jwt_required()
@limiter.limit("30 per minute")
def update_stock(product_id):
    """Update product stock"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()

    if 'quantity' not in data:
        return jsonify({'error': 'Quantity is required'}), 400

    quantity = data['quantity']
    if not isinstance(quantity, int):
        return jsonify({'error': 'Quantity must be an integer'}), 400

    # Update stock
    product.stock += quantity

    if product.stock < 0:
        return jsonify({'error': 'Insufficient stock'}), 400

    db.session.commit()

    # Invalidate cache
    redis_client.delete(f"product:{product_id}")

    return jsonify({
        'message': 'Stock updated successfully',
        'product': product.to_dict()
    }), 200


@app.route('/api/products/categories', methods=['GET'])
@limiter.limit("50 per minute")
def get_categories():
    """Get all unique categories"""
    cache_key = "product:categories"
    cached_categories = redis_client.get(cache_key)

    if cached_categories:
        return jsonify({'categories': eval(cached_categories.decode())}), 200

    categories = db.session.query(Product.category).distinct().all()
    category_list = [cat[0] for cat in categories if cat[0]]

    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, str(category_list))

    return jsonify({'categories': category_list}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
