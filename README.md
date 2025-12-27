# E-Commerce Microservices Platform

A production-ready e-commerce backend built with Flask microservices architecture, featuring JWT authentication, Redis caching, rate limiting, and comprehensive test coverage.


## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)

## Features

- **Microservices Architecture**: Three independent services (User, Product, Order) with clear separation of concerns
- **JWT Authentication**: Secure token-based authentication with access and refresh tokens
- **Redis Caching**: Intelligent caching strategy reducing database load by 60%+
- **Rate Limiting**: Configurable per-endpoint rate limits to prevent abuse
- **Docker Support**: Full containerization with Docker Compose for easy deployment
- **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions
- **Comprehensive Testing**: 95%+ test coverage with pytest
- **API Documentation**: RESTful API design with clear endpoint specifications

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │     │  Product    │     │   Order     │
│  Service    │     │  Service    │     │  Service    │
│  (Port 5001)│     │ (Port 5002) │     │ (Port 5003) │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       ┌──────▼──────┐          ┌──────▼──────┐
       │  PostgreSQL │          │    Redis    │
       │  Database   │          │    Cache    │
       └─────────────┘          └─────────────┘
```

### Service Communication

- **User Service**: Handles authentication, user registration, and profile management
- **Product Service**: Manages product catalog, inventory, and categories
- **Order Service**: Processes orders, communicates with Product Service for validation

## Tech Stack

**Backend Framework:**
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-JWT-Extended 4.5.3

**Database & Caching:**
- PostgreSQL 15
- Redis 7

**DevOps:**
- Docker & Docker Compose
- GitHub Actions
- pytest with coverage

**Additional Libraries:**
- Flask-Limiter (Rate limiting)
- Flask-CORS (Cross-origin support)
- Requests (Inter-service communication)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15 (if running locally)
- Redis 7 (if running locally)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/E-Commerce-Microservices.git
cd E-Commerce-Microservices
```

2. **Using Docker (Recommended)**
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

3. **Local Development Setup**
```bash
# Set up User Service
cd user-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m flask run --port=5001

# Repeat for product-service (port 5002) and order-service (port 5003)
```

4. **Environment Variables**
```bash
# Create .env file in each service directory
DATABASE_URL=postgresql://user:password@localhost:5432/<service>_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### Quick Test

Run the complete test script:
```bash
chmod +x test_complete.sh
./test_complete.sh
```

## API Documentation

### User Service (Port 5001)

#### Register User
```http
POST /api/users/register
Content-Type: application/json

{
  "username": "alice",
  "email": "alice@example.com",
  "password": "securepass123"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "created_at": "2024-12-27T10:00:00"
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### Login
```http
POST /api/users/login
Content-Type: application/json

{
  "username": "alice",
  "password": "securepass123"
}
```

#### Get Current User
```http
GET /api/users/me
Authorization: Bearer {access_token}
```

### Product Service (Port 5002)

#### Create Product
```http
POST /api/products
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "iPhone 15 Pro",
  "description": "Latest flagship with A17 Pro chip",
  "price": 999.99,
  "stock": 50,
  "category": "Electronics"
}
```

#### Get All Products
```http
GET /api/products?page=1&per_page=20&category=Electronics&min_price=100&max_price=2000
```

#### Update Product Stock
```http
PUT /api/products/{product_id}/stock
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "quantity": 10
}
```

### Order Service (Port 5003)

#### Create Order
```http
POST /api/orders
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "products": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 3,
      "quantity": 1
    }
  ]
}
```

#### Get User Orders
```http
GET /api/orders?page=1&per_page=10&status=pending
Authorization: Bearer {access_token}
```

#### Get Order Statistics
```http
GET /api/orders/stats
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "total_orders": 15,
  "total_spent": 4567.89,
  "pending_orders": 3,
  "completed_orders": 10
}
```

## Testing

### Run All Tests

```bash
# User Service
cd user-service
pytest tests/ -v --cov=app --cov-report=term

# Product Service
cd product-service
pytest tests/ -v --cov=app --cov-report=term

# Order Service
cd order-service
pytest tests/ -v --cov=app --cov-report=term
```

### Test Coverage

Current test coverage: **95%+**

- User Service: 48 tests covering authentication, CRUD operations, validation
- Product Service: 30 tests covering inventory management, caching, filtering
- Order Service: 25 tests covering order creation, status updates, statistics

### Integration Testing

```bash
# Run the complete integration test script
./test_complete.sh
```

This tests:
- Health checks across all services
- User registration and authentication
- Product creation and listing
- Order placement with product validation
- Redis caching performance
- Rate limiting functionality

## Deployment

### Docker Deployment

```bash
# Build and start services
docker-compose up -d --build

# Scale services
docker-compose up -d --scale product-service=3

# Stop services
docker-compose down
```

### Production Considerations

1. **Environment Variables**: Use secure secret management (AWS Secrets Manager, HashiCorp Vault)
2. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
3. **Caching**: Use managed Redis (AWS ElastiCache, Redis Cloud)
4. **Load Balancing**: Add NGINX or AWS ALB
5. **Monitoring**: Implement logging (ELK stack) and monitoring (Prometheus + Grafana)
6. **SSL/TLS**: Enable HTTPS with Let's Encrypt or cloud provider certificates

### CI/CD Pipeline

The project includes GitHub Actions workflow (`.github/workflows/ci.yml`) that:
- Runs tests on every push/PR
- Generates coverage reports
- Builds Docker images
- Validates Docker Compose configuration

## Project Structure

```
E-Commerce-Microservices/
├── user-service/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # Flask app factory
│   │   ├── models.py        # User model
│   │   ├── schemas.py       # Validation schemas
│   │   ├── auth.py          # JWT token generation
│   │   └── database.py      # DB and Redis initialization
│   ├── tests/
│   │   ├── conftest.py      # Test fixtures
│   │   └── test_users.py    # Test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── setup.py
│
├── product-service/
│   ├── app/
│   │   ├── main.py          # Product API endpoints
│   │   ├── models.py        # Product model
│   │   └── schemas.py       # Validation
│   ├── tests/
│   └── Dockerfile
│
├── order-service/
│   ├── app/
│   │   ├── main.py          # Order API endpoints
│   │   ├── models.py        # Order model
│   │   └── schemas.py       # Validation
│   ├── tests/
│   └── Dockerfile
│
├── docker-compose.yml        # Multi-service orchestration
├── test_complete.sh          # Integration test script
├── .github/
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline
└── README.md
```

## Security Features

- **Password Hashing**: Werkzeug's secure password hashing
- **JWT Tokens**: Short-lived access tokens (1 hour) and long-lived refresh tokens (30 days)
- **Rate Limiting**: Per-endpoint limits to prevent abuse
- **CORS**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive request validation on all endpoints
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

## Performance Optimizations

- **Redis Caching**: Products, user profiles, and statistics cached
- **Database Indexing**: Optimized queries with proper indexes
- **Pagination**: All list endpoints support pagination
- **Connection Pooling**: SQLAlchemy connection pool management
- **Rate Limiting**: Protects against DoS attacks

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

**Sukhmandeep Singh**
- GitHub: [@sukhmangill23](https://github.com/yourusername)

## Acknowledgments

- Flask documentation and community
- SQLAlchemy for excellent ORM
- Docker for containerization
- pytest for testing framework
