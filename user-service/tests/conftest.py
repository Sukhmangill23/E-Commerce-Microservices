import pytest
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Now we can import normally
from app.main import app as flask_app
from app.database import db as _db


@pytest.fixture(scope='function')
def app():
    """Create application for testing"""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['REDIS_URL'] = 'redis://localhost:6379/1'
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
def sample_user_data():
    """Sample user data for testing"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }
