#!/bin/bash

echo "🚀 Starting ChainFLIP Multi-Chain System..."

# Check if setup has been run
if [ ! -f "/etc/supervisor/conf.d/chainflip.conf" ]; then
    echo "⚠️ System not set up. Running setup first..."
    bash /app/multichain-chainflip/setup.sh
fi

# Start all services
echo "🎛️ Starting all services..."
supervisorctl start all

echo ""
echo "✅ ChainFLIP Multi-Chain System is starting!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8001/docs (Swagger UI)"
echo "📡 IPFS Service: http://localhost:8002/health"
echo ""
echo "📊 Check status: supervisorctl status"
echo "🛑 Stop services: supervisorctl stop all"
echo "📜 View logs: supervisorctl tail -f [backend|frontend|ipfs-service]"
