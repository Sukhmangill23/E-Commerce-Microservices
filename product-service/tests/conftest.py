import pytest
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(scope='function')
def app():
    """Create application for testing"""
    from app.main import create_app
    from app.database import db as _db, redis_client

    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'REDIS_URL': 'redis://localhost:6379/2',  # Different Redis DB
        'JWT_SECRET_KEY': 'test-secret-key',
        'RATELIMIT_ENABLED': False,
        'AUTO_CREATE_TABLES': False,  # Disable auto-creation in tests
    }

    flask_app = create_app(test_config)

    with flask_app.app_context():
        # Explicitly create tables in test fixture
        _db.create_all()

        # Clear Redis cache before each test
        try:
            redis_client.flushdb()
        except:
            pass

        yield flask_app

        # Properly clean up
        _db.session.rollback()
        _db.session.remove()
        _db.drop_all()

        # Clear Redis after test
        try:
            redis_client.flushdb()
        except:
            pass


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Create database for testing"""
    from app.database import db as _db
    return _db


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    import random
    random_suffix = random.randint(1000, 9999)
    return {
        'name': f'Test Product {random_suffix}',
        'description': 'A test product',
        'price': 29.99,
        'stock': 100,
        'category': 'Electronics'
    }


@pytest.fixture
def auth_token(app):
    """Mock JWT token for testing"""
    with app.app_context():
        from flask_jwt_extended import create_access_token
        return create_access_token(identity='1')
