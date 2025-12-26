import pytest
import sys
import os
import importlib.util

# Manually import by loading the module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import main.py
main_spec = importlib.util.spec_from_file_location(
    "main",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "main.py")
)
main = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main)

# Import database.py
database_spec = importlib.util.spec_from_file_location(
    "database",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "database.py")
)
database = importlib.util.module_from_spec(database_spec)
database_spec.loader.exec_module(database)

flask_app = main.app
_db = database.db


@pytest.fixture(scope='function')
def app():
    """Create application for testing"""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['REDIS_URL'] = 'redis://localhost:6379/2'
    flask_app.config['JWT_SECRET_KEY'] = 'test-secret-key'

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Create database for testing"""
    return _db


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        'name': 'Test Product',
        'description': 'A test product',
        'price': 29.99,
        'stock': 100,
        'category': 'Electronics'
    }


@pytest.fixture
def auth_token():
    """Mock JWT token for testing"""
    import flask_jwt_extended
    return flask_jwt_extended.create_access_token(identity=1)
