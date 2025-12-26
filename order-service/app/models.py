from datetime import datetime
import json
from .database import db  # Use relative import


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    products = db.Column(db.Text, nullable=False)  # JSON string
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_products(self):
        """Parse products JSON"""
        return json.loads(self.products)

    def set_products(self, products_list):
        """Set products as JSON"""
        self.products = json.dumps(products_list)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'products': self.get_products(),
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
