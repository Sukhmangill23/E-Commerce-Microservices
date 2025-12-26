#!/bin/bash

echo "🚀 Testing E-Commerce Microservices"
echo "===================================="
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq not found. Install with: brew install jq"
    echo "Continuing without pretty printing..."
    JQ_CMD="cat"
else
    JQ_CMD="jq ."
fi

# Generate random username to avoid conflicts
RANDOM_USER="alice_$(date +%s)"

# 1. Health Checks
echo "1️⃣  Health Checks"
echo "-------------------"
echo "User Service:"
curl -s http://localhost:5001/health | $JQ_CMD
echo ""
echo "Product Service:"
curl -s http://localhost:5002/health | $JQ_CMD
echo ""
echo "Order Service:"
curl -s http://localhost:5003/health | $JQ_CMD
echo ""
echo ""

# 2. Register User
echo "2️⃣  Registering New User (${RANDOM_USER})"
echo "------------------------"
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:5001/api/users/register \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${RANDOM_USER}\",
    \"email\": \"${RANDOM_USER}@example.com\",
    \"password\": \"securepass123\"
  }")

echo "$REGISTER_RESPONSE" | $JQ_CMD

# Extract token
if command -v jq &> /dev/null; then
    TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.tokens.access_token')
else
    # Fallback: extract token without jq
    TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
fi

echo ""
echo "🔑 Access Token: ${TOKEN:0:50}..."
echo ""
echo ""

# 3. Create Products
echo "3️⃣  Creating Products"
echo "---------------------"

echo "Creating iPhone 15 Pro..."
PRODUCT1=$(curl -s -X POST http://localhost:5002/api/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "iPhone 15 Pro",
    "description": "Latest flagship with A17 Pro chip",
    "price": 999.99,
    "stock": 50,
    "category": "Electronics"
  }')
echo "$PRODUCT1" | $JQ_CMD
echo ""

echo "Creating MacBook Pro..."
PRODUCT2=$(curl -s -X POST http://localhost:5002/api/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "MacBook Pro 14",
    "description": "M3 Pro chip, 16GB RAM",
    "price": 1999.99,
    "stock": 30,
    "category": "Computers"
  }')
echo "$PRODUCT2" | $JQ_CMD
echo ""

echo "Creating AirPods Pro..."
PRODUCT3=$(curl -s -X POST http://localhost:5002/api/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "AirPods Pro 2",
    "description": "Active noise cancellation",
    "price": 249.99,
    "stock": 100,
    "category": "Audio"
  }')
echo "$PRODUCT3" | $JQ_CMD
echo ""
echo ""

# 4. Get All Products
echo "4️⃣  Listing All Products"
echo "------------------------"
curl -s http://localhost:5002/api/products | $JQ_CMD
echo ""
echo ""

# 5. Get Product Categories
echo "5️⃣  Getting Product Categories"
echo "-------------------------------"
curl -s http://localhost:5002/api/products/categories | $JQ_CMD
echo ""
echo ""

# 6. Create Order
echo "6️⃣  Creating Order"
echo "------------------"
ORDER=$(curl -s -X POST http://localhost:5003/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
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
  }')
echo "$ORDER" | $JQ_CMD
echo ""
echo ""

# 7. Get User Orders
echo "7️⃣  Getting User Orders"
echo "-----------------------"
curl -s http://localhost:5003/api/orders \
  -H "Authorization: Bearer $TOKEN" | $JQ_CMD
echo ""
echo ""

# 8. Get Order Stats
echo "8️⃣  Getting Order Statistics"
echo "-----------------------------"
curl -s http://localhost:5003/api/orders/stats \
  -H "Authorization: Bearer $TOKEN" | $JQ_CMD
echo ""
echo ""

# 9. Test Caching
echo "9️⃣  Testing Redis Caching"
echo "-------------------------"
echo "First request (cache miss):"
time curl -s http://localhost:5002/api/products > /dev/null
echo ""
echo "Second request (cache hit - should be faster):"
time curl -s http://localhost:5002/api/products > /dev/null
echo ""
echo ""

# 10. Test Rate Limiting
echo "🔟 Testing Rate Limiting"
echo "------------------------"
echo "Attempting 6 registrations rapidly (limit is 5 per minute):"
for i in {1..6}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:5001/api/users/register \
    -H "Content-Type: application/json" \
    -d "{
      \"username\": \"testuser_${RANDOM}_$i\",
      \"email\": \"user${RANDOM}_$i@example.com\",
      \"password\": \"password123\"
    }")
  echo "Request $i: HTTP $STATUS"
  if [ "$STATUS" == "429" ]; then
    echo "✅ Rate limiting working! Got 429 Too Many Requests"
    break
  fi
done
echo ""

echo "✅ All Tests Completed!"
echo "======================="
