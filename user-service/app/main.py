from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os

from .database import db, redis_client, init_db
from .models import User
from .schemas import validate_user_registration, validate_user_login
from .auth import generate_tokens

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/user_db'
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
    return jsonify({'status': 'healthy', 'service': 'user-service'}), 200


@app.route('/api/users/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Register a new user"""
    data = request.get_json()

    # Validate input
    errors = validate_user_registration(data)
    if errors:
        return jsonify({'errors': errors}), 400

    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409

    # Create user
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    # Generate tokens
    tokens = generate_tokens(user.id)

    # Cache user data in Redis
    redis_client.setex(
        f"user:{user.id}",
        3600,  # 1 hour
        str(user.to_dict())
    )

    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'tokens': tokens
    }), 201


@app.route('/api/users/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login user"""
    data = request.get_json()

    # Validate input
    errors = validate_user_login(data)
    if errors:
        return jsonify({'errors': errors}), 400

    # Find user
    user = None
    if data.get('username'):
        user = User.query.filter_by(username=data['username']).first()
    elif data.get('email'):
        user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate tokens
    tokens = generate_tokens(user.id)

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'tokens': tokens
    }), 200


@app.route('/api/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user profile"""
    user_id = int(get_jwt_identity())

    # Try cache first
    cached_user = redis_client.get(f"user:{user_id}")
    if cached_user:
        return jsonify({'user': eval(cached_user.decode())}), 200

    # Get from database
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Cache result
    redis_client.setex(f"user:{user_id}", 3600, str(user.to_dict()))

    return jsonify({'user': user.to_dict()}), 200


@app.route('/api/users', methods=['GET'])
@jwt_required()
@limiter.limit("20 per minute")
def get_users():
    """Get all users (admin endpoint)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    users = User.query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'users': [user.to_dict() for user in users.items],
        'total': users.total,
        'page': users.page,
        'pages': users.pages
    }), 200


@app.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get user by ID"""
    # Try cache first
    cached_user = redis_client.get(f"user:{user_id}")
    if cached_user:
        return jsonify({'user': eval(cached_user.decode())}), 200

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Cache result
    redis_client.setex(f"user:{user_id}", 3600, str(user.to_dict()))

    return jsonify({'user': user.to_dict()}), 200


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per minute")
def update_user(user_id):
    """Update user"""
    current_user_id = int(get_jwt_identity())

    # Users can only update their own profile
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    if 'email' in data:
        user.email = data['email']

    db.session.commit()

    # Invalidate cache
    redis_client.delete(f"user:{user_id}")

    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("5 per minute")
def delete_user(user_id):
    """Delete user"""
    current_user_id = int(get_jwt_identity())

    # Users can only delete their own account
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    # Invalidate cache
    redis_client.delete(f"user:{user_id}")

    return jsonify({'message': 'User deleted successfully'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
