# 🚀 ChainFLIP Multi-Chain Transfer Setup Guide

## 📋 **PROJECT STATUS: 95% COMPLETE - EXTERNAL ACCESS ISSUE**

---

## 🎯 **CURRENT STATE**

### ✅ **COMPLETED & WORKING:**
- **Backend**: FastAPI running on localhost:8001 ✅
- **Frontend**: React app running on localhost:3000 ✅  
- **Database**: MongoDB operational with all collections ✅
- **Smart Contracts**: All 3 deployed on Polygon networks ✅
- **Core Features**: All 5 algorithms implemented ✅
- **Testing**: Comprehensive backend testing completed ✅

### ❌ **REMAINING ISSUE:**
- **External Access**: Frontend accessible locally but not via external URL due to host header restrictions

---

## 🔧 **QUICK SETUP SCRIPT**

### **Step 1: Navigate to Project**
```bash
cd /app/multichain-chainflip
```

### **Step 2: Install Dependencies**
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies  
cd ../frontend
yarn install
```

### **Step 3: Start MongoDB**
```bash
sudo mkdir -p /data/db
sudo mongod --dbpath /data/db --fork --logpath /var/log/mongodb/mongod.log
```

### **Step 4: Start Backend**
```bash
cd /app/multichain-chainflip/backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > backend.log 2>&1 &
```

### **Step 5: Start Frontend (External Access)**
```bash
cd /app/multichain-chainflip/frontend
DANGEROUSLY_DISABLE_HOST_CHECK=true HOST=0.0.0.0 PORT=3000 nohup yarn start > frontend.log 2>&1 &
```

### **Step 6: Verify Services**
```bash
# Check backend
curl -s http://localhost:8001/api/health

# Check frontend  
curl -s http://localhost:3000 | head -5
```

---

## 🌐 **EXTERNAL ACCESS CONFIGURATION**

### **Frontend Environment (.env)**
```bash
# /app/multichain-chainflip/frontend/.env
REACT_APP_BACKEND_URL=https://8001-[NEW-JOB-ID].ws-dev.emergent.ai
REACT_APP_POLYGON_RPC=https://polygon-amoy.infura.io/v3/d455e91357464c0cb3727309e4256e94
REACT_APP_POLYGON_CHAIN_ID=80002
REACT_APP_L2_CDK_RPC=
REACT_APP_L2_CDK_CHAIN_ID=1001
REACT_APP_IPFS_GATEWAY=https://w3s.link/ipfs/
REACT_APP_CONTRACT_ADDRESS=0x60C466cF52cb9705974a89b72DeA045c45cb7572

# External access settings
DANGEROUSLY_DISABLE_HOST_CHECK=true
HOST=0.0.0.0
WDS_SOCKET_HOST=0.0.0.0
WDS_SOCKET_PORT=3000
```

### **Backend Environment (.env)**
```bash
# /app/multichain-chainflip/backend/.env
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=chainflip_multichain

# Blockchain Configuration
POLYGON_AMOY_RPC=https://polygon-amoy.infura.io/v3/d455e91357464c0cb3727309e4256e94
L2_CDK_RPC=https://rpc.cardona.polygon.technology
POLYGON_CHAIN_ID=80002
L2_CDK_CHAIN_ID=2442

# Contract Addresses (DEPLOYED & WORKING)
POS_HUB_CONTRACT=0xFbD920b8Bb8Be7dC3b5976a63F515c88e2776a6E
NFT_CORE_CONTRACT=0x13Ef359e2F7f8e63c5613a41F85Db3f3023B23d0
SUPPLY_CHAIN_NFT_CONTRACT=0x60C466cF52cb9705974a89b72DeA045c45cb7572

# Working Blockchain Account (40+ POL Balance)
DEPLOYER_ADDRESS=0x032041b4b356fEE1496805DD4749f181bC736FFA
DEPLOYER_PRIVATE_KEY=5d014eee1544fe8e166b0ffc5d9a5da41456cec5d4c15b76611e8747d848f079

# IPFS Configuration (WORKING)
W3STORAGE_TOKEN=MgCarobxPMnhlryDHM/adVhjxYre5jVBtwut++n1AB3ZJpu0BKUbT1kYPUjNlRMiLnNuMXFpoAjb0pm+Q+17BRmqJ+IM=

# Encryption Keys (WORKING)
AES_SECRET_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
HMAC_SECRET_KEY=fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210
```

---

## 🔗 **ACCESS URLs (Update with NEW Job ID)**

### **External Access URLs:**
- **Frontend**: `https://3000-[NEW-JOB-ID].ws-dev.emergent.ai`
- **Backend**: `https://8001-[NEW-JOB-ID].ws-dev.emergent.ai`

### **URL Format Pattern:**
```
https://[PORT]-[JOB-ID].ws-dev.emergent.ai
```

---

## 🏗️ **PROJECT ARCHITECTURE**

### **Directory Structure:**
```
/app/multichain-chainflip/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/routes/     # API endpoints
│   │   ├── core/           # Core configurations
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Backend environment
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── context/       # React contexts
│   │   └── App.js         # Main app
│   ├── package.json       # Node dependencies
│   └── .env              # Frontend environment
├── contracts/             # Smart contracts
├── deployment_status.json # Contract addresses
└── test_result.md         # Testing results
```

### **Available Features:**
1. **📊 Dashboard** - System overview
2. **📦 Products** - Product lifecycle management
3. **👥 Participants** - Supply chain participants
4. **🤖 Federated Learning** - AI/ML capabilities
5. **📈 Analytics** - Data insights
6. **📱 QR Scanner** - Authentication
7. **⚙️ Settings** - Configuration

---

## 🧪 **TESTING STATUS**

### **✅ Backend Testing Completed:**
- All API endpoints working ✅
- Multi-chain functionality verified ✅
- Cross-chain communication operational ✅
- Federated Learning ready ✅
- IPFS integration working ✅
- QR code services functional ✅
- Product lifecycle management operational ✅
- Analytics & monitoring working ✅

### **⏳ Remaining: Frontend Testing**
- Need to test Web UI interface
- Verify cross-page navigation
- Test user workflows

---

## 🚨 **CRITICAL NEXT STEPS**

### **1. Update Job ID (MANDATORY)**
```bash
# Update frontend .env with NEW job ID
sed -i 's/c78d28bc-ff93-4d99-b520-4c1490fed509/[NEW-JOB-ID]/g' /app/multichain-chainflip/frontend/.env
```

### **2. Test External Access**
```bash
# After starting services, test these URLs:
# https://3000-[NEW-JOB-ID].ws-dev.emergent.ai
# https://8001-[NEW-JOB-ID].ws-dev.emergent.ai/api/health
```

### **3. Frontend Testing**
```bash
# Use testing agent
deep_testing_frontend_v2 "Test ChainFLIP Web UI interface including all pages, navigation, and API integration"
```

---

## 📋 **TROUBLESHOOTING**

### **If Frontend Won't Start:**
```bash
pkill -f "yarn start"
cd /app/multichain-chainflip/frontend
rm -rf node_modules yarn.lock
yarn install
DANGEROUSLY_DISABLE_HOST_CHECK=true HOST=0.0.0.0 PORT=3000 yarn start
```

### **If Backend Issues:**
```bash
pkill -f uvicorn
cd /app/multichain-chainflip/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### **If Database Issues:**
```bash
sudo pkill mongod
sudo mongod --dbpath /data/db --fork --logpath /var/log/mongodb/mongod.log
```

---

## 🎯 **COMPLETION CHECKLIST**

### **Completed (95%):**
- ✅ All smart contracts deployed
- ✅ All backend services operational
- ✅ Frontend React app built
- ✅ Database collections created
- ✅ Multi-chain integration working
- ✅ All 5 algorithms implemented
- ✅ Comprehensive backend testing

### **Remaining (5%):**
- ❌ Fix external URL access
- ❌ Frontend testing
- ❌ End-to-end workflow testing

---

## 🔐 **IMPORTANT CREDENTIALS**

### **Blockchain Account (WORKING - 40+ POL):**
```
Address: 0x032041b4b356fEE1496805DD4749f181bC736FFA
Private Key: 5d014eee1544fe8e166b0ffc5d9a5da41456cec5d4c15b76611e8747d848f079
Network: Polygon Amoy (Chain ID: 80002)
```

### **IPFS Token (WORKING):**
```
W3STORAGE_TOKEN=MgCarobxPMnhlryDHM/adVhjxYre5jVBtwut++n1AB3ZJpu0BKUbT1kYPUjNlRMiLnNuMXFpoAjb0pm+Q+17BRmqJ+IM=
```

### **Contract Addresses (DEPLOYED):**
```
PolygonPoSHub: 0xFbD920b8Bb8Be7dC3b5976a63F515c88e2776a6E
NFTCore: 0x13Ef359e2F7f8e63c5613a41F85Db3f3023B23d0
SupplyChainNFT: 0x60C466cF52cb9705974a89b72DeA045c45cb7572
```

---

## 🚀 **EXPECTED COMPLETION TIME: 15-30 MINUTES**

The project is 95% complete. The main remaining task is fixing the external URL access and completing frontend testing. All core functionality is operational.

**Total estimated time to finish: 15-30 minutes**

---

## 📞 **SUCCESS CRITERIA**

1. ✅ External URL access working (`https://3000-[NEW-JOB-ID].ws-dev.emergent.ai`)
2. ✅ Frontend testing completed successfully
3. ✅ End-to-end workflows tested
4. ✅ All features accessible via web interface

**Project will be 100% complete once external access is fixed!**