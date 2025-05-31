#!/bin/bash
# 🚀 ChainFLIP Quick Setup Script for New Account
# Run this script to quickly setup the ChainFLIP project

echo "🚀 Starting ChainFLIP Multi-Chain Setup..."

# Variables - UPDATE WITH YOUR NEW JOB ID
NEW_JOB_ID="YOUR_NEW_JOB_ID_HERE"

# Navigate to project directory
cd /app/multichain-chainflip || exit

echo "📦 Installing Backend Dependencies..."
cd backend
pip install -r requirements.txt

echo "📦 Installing Frontend Dependencies..."
cd ../frontend
yarn install

echo "🗄️ Starting MongoDB..."
sudo mkdir -p /data/db
sudo mkdir -p /var/log/mongodb
sudo mongod --dbpath /data/db --fork --logpath /var/log/mongodb/mongod.log

# Wait for MongoDB to start
sleep 5

echo "🔧 Starting Backend Service..."
cd /app/multichain-chainflip/backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > backend.log 2>&1 &

# Wait for backend to start
sleep 10

echo "🌐 Updating Frontend Configuration..."
cd /app/multichain-chainflip/frontend

# Update the .env file with new job ID
sed -i "s/c78d28bc-ff93-4d99-b520-4c1490fed509/$NEW_JOB_ID/g" .env

echo "🚀 Starting Frontend Service..."
DANGEROUSLY_DISABLE_HOST_CHECK=true HOST=0.0.0.0 PORT=3000 nohup yarn start > frontend.log 2>&1 &

# Wait for frontend to start
sleep 20

echo "✅ Verifying Services..."

# Check backend health
echo "🔍 Backend Health Check:"
curl -s http://localhost:8001/api/health

echo ""
echo "🔍 Frontend Check:"
curl -s http://localhost:3000 | head -3

echo ""
echo "🎯 Setup Complete!"
echo ""
echo "📋 Access URLs (replace YOUR_NEW_JOB_ID with actual Job ID):"
echo "   Frontend: https://3000-$NEW_JOB_ID.ws-dev.emergent.ai"
echo "   Backend:  https://8001-$NEW_JOB_ID.ws-dev.emergent.ai"
echo ""
echo "📋 Local URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8001"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update NEW_JOB_ID variable in this script"
echo "   2. Run: bash setup.sh"
echo "   3. Test external URLs"
echo "   4. Run frontend testing"
echo ""
echo "📊 Project Status: 95% Complete - Just need external access fix!"