from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os
import requests

from .database import db, redis_client, init_db
from .models import Order
from .schemas import validate_order

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/order_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Service URLs
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:5002')

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
    return jsonify({'status': 'healthy', 'service': 'order-service'}), 200


@app.route('/api/orders', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def create_order():
    """Create a new order"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    # Override user_id with authenticated user
    data['user_id'] = current_user_id

    # Validate input
    errors = validate_order(data)
    if errors:
        return jsonify({'errors': errors}), 400

    # Verify products exist and calculate total
    total_amount = 0
    products_with_details = []

    for item in data['products']:
        product_id = item['product_id']
        quantity = item['quantity']

        # Call Product Service to get product details
        try:
            response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/{product_id}", timeout=5)
            if response.status_code != 200:
                return jsonify({'error': f'Product {product_id} not found'}), 404

            product = response.json()['product']

            # Check stock
            if product['stock'] < quantity:
                return jsonify({'error': f'Insufficient stock for product {product_id}'}), 400

            item_total = product['price'] * quantity
            total_amount += item_total

            products_with_details.append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'subtotal': item_total
            })

        except requests.RequestException as e:
            return jsonify({'error': 'Product service unavailable'}), 503

    # Create order
    order = Order(
        user_id=current_user_id,
        total_amount=round(total_amount, 2),
        status='pending'
    )
    order.set_products(products_with_details)

    db.session.add(order)
    db.session.commit()

    # Invalidate user stats cache
    redis_client.delete(f"order:stats:{current_user_id}")

    return jsonify({
        'message': 'Order created successfully',
        'order': order.to_dict()
    }), 201


@app.route('/api/orders', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def get_orders():
    """Get orders for current user"""
    current_user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')

    # Build query
    query = Order.query.filter_by(user_id=current_user_id)

    if status:
        query = query.filter_by(status=status)

    # Paginate
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'orders': [order.to_dict() for order in orders.items],
        'total': orders.total,
        'page': orders.page,
        'pages': orders.pages
    }), 200


@app.route('/api/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get order by ID"""
    current_user_id = int(get_jwt_identity())

    order = Order.query.filter_by(id=order_id, user_id=current_user_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    return jsonify({'order': order.to_dict()}), 200


@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per minute")
def update_order_status(order_id):
    """Update order status"""
    current_user_id = int(get_jwt_identity())

    order = Order.query.filter_by(id=order_id, user_id=current_user_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    data = request.get_json()

    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400

    order.status = data['status']
    db.session.commit()

    # Invalidate stats cache if order is completed
    if data['status'] in ['delivered', 'cancelled']:
        redis_client.delete(f"order:stats:{current_user_id}")

    return jsonify({
        'message': 'Order status updated successfully',
        'order': order.to_dict()
    }), 200


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per minute")
def cancel_order(order_id):
    """Cancel an order"""
    current_user_id = int(get_jwt_identity())

    order = Order.query.filter_by(id=order_id, user_id=current_user_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    if order.status not in ['pending', 'processing']:
        return jsonify({'error': 'Cannot cancel order in current status'}), 400

    order.status = 'cancelled'
    db.session.commit()

    # Invalidate cache
    redis_client.delete(f"order:stats:{current_user_id}")

    return jsonify({
        'message': 'Order cancelled successfully',
        'order': order.to_dict()
    }), 200


@app.route('/api/orders/stats', methods=['GET'])
@jwt_required()
def get_order_stats():
    """Get order statistics for current user"""
    current_user_id = int(get_jwt_identity())

    # Cache key
    cache_key = f"order:stats:{current_user_id}"
    cached_stats = redis_client.get(cache_key)

    if cached_stats:
        return jsonify(eval(cached_stats.decode())), 200

    # Calculate stats
    total_orders = Order.query.filter_by(user_id=current_user_id).count()
    total_spent = db.session.query(db.func.sum(Order.total_amount)).filter_by(
        user_id=current_user_id
    ).scalar() or 0

    pending_orders = Order.query.filter_by(user_id=current_user_id, status='pending').count()
    completed_orders = Order.query.filter_by(user_id=current_user_id, status='delivered').count()

    stats = {
        'total_orders': total_orders,
        'total_spent': round(float(total_spent), 2),
        'pending_orders': pending_orders,
        'completed_orders': completed_orders
    }

    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, str(stats))

    return jsonify(stats), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
