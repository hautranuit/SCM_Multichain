#!/bin/bash

echo "🚀 Setting up ChainFLIP Multi-Chain System..."

# Create necessary directories
mkdir -p /var/log/supervisor
mkdir -p /var/log/mongodb
mkdir -p /data/db

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y python3-pip nodejs npm mongodb supervisor

# Install yarn globally
npm install -g yarn

# Setup Python environment for backend
echo "🐍 Setting up Python backend..."
cd /app/multichain-chainflip/backend
pip3 install -r requirements.txt

# Setup Node.js environment for frontend
echo "⚛️ Setting up React frontend..."
cd /app/multichain-chainflip/frontend
yarn install

# Setup IPFS service
echo "📡 Setting up IPFS service..."
cd /app/multichain-chainflip/ipfs-service
yarn install

# Setup supervisor
echo "🔧 Configuring supervisor..."
cp /app/multichain-chainflip/supervisord.conf /etc/supervisor/conf.d/chainflip.conf

# Start MongoDB
echo "🍃 Starting MongoDB..."
service mongodb start

# Start supervisor
echo "🎛️ Starting services with supervisor..."
service supervisor start
supervisorctl reread
supervisorctl update
supervisorctl start all

echo "✅ ChainFLIP Multi-Chain System setup complete!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8001"
echo "📡 IPFS Service: http://localhost:8002"
echo ""
echo "📊 Check service status: supervisorctl status"
echo "📜 View logs: supervisorctl tail -f [service_name]"
