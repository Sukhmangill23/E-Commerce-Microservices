from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis

db = SQLAlchemy()
redis_client = FlaskRedis()

def init_db(app):
    db.init_app(app)
    redis_client.init_app(app)

    with app.app_context():
        db.create_all()
