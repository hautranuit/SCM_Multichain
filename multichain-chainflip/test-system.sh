#!/bin/bash

echo "🧪 Testing ChainFLIP Multi-Chain System..."

# Function to check if service is running
check_service() {
    local service=$1
    local port=$2
    local path=$3
    
    echo -n "Testing $service on port $port... "
    
    if curl -s "http://localhost:$port$path" > /dev/null; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Check if services are running
echo "📊 Checking service status..."
supervisorctl status

echo ""
echo "🌐 Testing service endpoints..."

# Test backend
check_service "Backend API" 8001 "/api/health"

# Test frontend
check_service "Frontend" 3000 "/"

# Test IPFS service
check_service "IPFS Service" 8002 "/health"

echo ""
echo "🔧 Testing API endpoints..."

# Test backend API endpoints
echo -n "Testing products endpoint... "
if curl -s "http://localhost:8001/api/products" > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

echo -n "Testing blockchain status... "
if curl -s "http://localhost:8001/api/blockchain/status" > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

echo -n "Testing FL status... "
if curl -s "http://localhost:8001/api/federated-learning/status" > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

echo ""
echo "📱 Testing IPFS service..."

# Test IPFS endpoints
echo -n "Testing IPFS upload... "
response=$(curl -s -X POST "http://localhost:8002/upload" \
  -H "Content-Type: application/json" \
  -d '{"data": {"test": "data"}, "filename": "test.json"}')

if echo "$response" | grep -q "success"; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

echo ""
echo "🍃 Testing database connection..."
echo -n "Testing MongoDB... "
if mongo --eval "db.runCommand('ping').ok" > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED - MongoDB may not be running"
fi

echo ""
echo "📋 System Test Summary:"
echo "========================"

# Overall system health
healthy_services=0
total_services=4

if curl -s "http://localhost:8001/api/health" > /dev/null; then
    ((healthy_services++))
fi

if curl -s "http://localhost:3000" > /dev/null; then
    ((healthy_services++))
fi

if curl -s "http://localhost:8002/health" > /dev/null; then
    ((healthy_services++))
fi

if mongo --eval "db.runCommand('ping').ok" > /dev/null 2>&1; then
    ((healthy_services++))
fi

echo "🎯 Services healthy: $healthy_services/$total_services"

if [ $healthy_services -eq $total_services ]; then
    echo "✅ All systems operational!"
    echo ""
    echo "🌐 Access points:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8001/docs"
    echo "  IPFS Service: http://localhost:8002/health"
    echo ""
    echo "🚀 ChainFLIP Multi-Chain system is ready!"
else
    echo "⚠️ Some services are not responding properly"
    echo "📜 Check logs with: supervisorctl tail -f [service_name]"
    echo "🔄 Restart with: supervisorctl restart all"
fi

echo ""
echo "🔍 For detailed logs:"
echo "  supervisorctl tail -f backend"
echo "  supervisorctl tail -f frontend" 
echo "  supervisorctl tail -f ipfs-service"
