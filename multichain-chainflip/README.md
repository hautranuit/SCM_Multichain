# ChainFLIP Multi-Chain Supply Chain Management

## 🌟 Overview

ChainFLIP 2.0 is an advanced multi-chain supply chain management system that combines:

- **Multi-Chain Architecture**: Polygon PoS Hub + L2 CDK Participants
- **Federated Learning**: Supply Chain Anomaly Detection & Counterfeit Detection
- **IPFS Integration**: Decentralized storage with Web3.Storage
- **Dynamic QR Codes**: Encrypted QR codes for product authentication
- **Advanced Analytics**: Real-time performance monitoring

## 🏗️ Architecture

### Multi-Chain Design
- **Polygon PoS Hub**: Central registry, participant management, global FL aggregation
- **L2 CDK Participants**: High-frequency operations, local business logic, local FL training
- **FxPortal Bridge**: Cross-chain communication and asset transfer

### Technology Stack
- **Backend**: FastAPI, Python, Web3.py
- **Frontend**: React, Tailwind CSS, ethers.js
- **Blockchain**: Solidity smart contracts
- **Database**: MongoDB
- **IPFS**: Web3.Storage
- **ML**: TensorFlow, scikit-learn

## 🚀 Quick Start

### Prerequisites
- Ubuntu/Debian Linux system
- 4GB+ RAM
- Internet connection

### Installation

1. **Clone and setup**:
```bash
cd /app/multichain-chainflip
chmod +x setup.sh start.sh
./setup.sh
```

2. **Start the system**:
```bash
./start.sh
```

3. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/docs
- IPFS Service: http://localhost:8002/health

## 📋 Services

### Backend API (Port 8001)
- **Blockchain Operations**: `/api/blockchain/*`
- **Product Management**: `/api/products/*`
- **Federated Learning**: `/api/federated-learning/*`
- **IPFS Integration**: `/api/ipfs/*`
- **Analytics**: `/api/analytics/*`

### Frontend Dashboard (Port 3000)
- **Dashboard**: System overview and analytics
- **Products**: Product management and tracking
- **Participants**: Network participant management
- **Federated Learning**: AI model training interface
- **QR Scanner**: Product authentication
- **Analytics**: Performance metrics

### IPFS Service (Port 8002)
- **File Upload**: `/upload`
- **QR Generation**: `/qr/generate`
- **QR Decryption**: `/qr/decrypt`
- **Metadata Management**: `/product/metadata`

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
```bash
# Database
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=chainflip_multichain

# Blockchain
POLYGON_POS_RPC=https://polygon-amoy.infura.io/v3/YOUR_KEY
DEPLOYER_PRIVATE_KEY=your_private_key
POS_HUB_CONTRACT=deployed_contract_address

# IPFS
W3STORAGE_TOKEN=your_w3storage_token
W3STORAGE_PROOF=your_w3storage_proof

# Encryption
AES_SECRET_KEY=your_aes_key
HMAC_SECRET_KEY=your_hmac_key
```

**Frontend** (`.env`):
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_POLYGON_RPC=https://polygon-amoy.infura.io/v3/YOUR_KEY
REACT_APP_CONTRACT_ADDRESS=deployed_contract_address
```

## 🛠️ Service Management

```bash
# Check status
supervisorctl status

# Start all services
supervisorctl start all

# Stop all services
supervisorctl stop all

# Restart specific service
supervisorctl restart backend

# View logs
supervisorctl tail -f backend
supervisorctl tail -f frontend
supervisorctl tail -f ipfs-service
```

## 🔍 Key Features

### 1. Multi-Chain Product Tracking
- Products minted on Polygon PoS Hub
- High-frequency updates on L2 CDK
- Cross-chain synchronization

### 2. Federated Learning
- **Anomaly Detection**: Unusual transport patterns, temperature variations
- **Counterfeit Detection**: Product authenticity verification
- Privacy-preserving collaborative training

### 3. Dynamic QR Codes
- AES-256 encryption
- Time-based expiration
- IPFS metadata storage
- Mobile-friendly scanning

### 4. Advanced Analytics
- Real-time performance metrics
- Security threat monitoring
- Participant activity tracking
- FL model performance

## 📊 API Examples

### Register Participant
```bash
curl -X POST "http://localhost:8001/api/blockchain/participants/register" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0x742d35Cc6235C3F23fE82fcDc533C09B7B6a8C0d",
    "participant_type": "manufacturer",
    "chain_id": 80002
  }'
```

### Mint Product
```bash
curl -X POST "http://localhost:8001/api/blockchain/products/mint" \
  -H "Content-Type: application/json" \
  -d '{
    "manufacturer": "0x742d35Cc6235C3F23fE82fcDc533C09B7B6a8C0d",
    "metadata_cid": "bafkreiqrstuvwxyz1234567890",
    "initial_qr_data": {
      "productId": "PROD-001",
      "batchNumber": "BATCH-001"
    }
  }'
```

### Generate QR Code
```bash
curl -X POST "http://localhost:8002/qr/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "productId": "PROD-001",
      "manufacturer": "0x742d35Cc6235C3F23fE82fcDc533C09B7B6a8C0d"
    },
    "options": {
      "size": 400,
      "validityHours": 24
    }
  }'
```

## 🔒 Security Features

- **End-to-End Encryption**: AES-256 for sensitive data
- **Smart Contract Security**: Audited and verified contracts
- **Multi-Signature Support**: Enhanced wallet security
- **Rate Limiting**: API protection
- **Input Validation**: Comprehensive data validation

## 🚀 Development

### Adding New Features

1. **Backend**: Add new API routes in `/app/api/routes/`
2. **Frontend**: Create new pages in `/src/pages/`
3. **Smart Contracts**: Add contracts in `/contracts/`
4. **Services**: Extend services in `/app/services/`

### Testing

```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests
cd frontend && yarn test

# Smart contract tests
cd contracts/polygon-pos-hub && npx hardhat test
```

## 📈 Monitoring

### Health Checks
- Backend: http://localhost:8001/api/health
- IPFS Service: http://localhost:8002/health
- Frontend: Check if port 3000 responds

### Logs
```bash
# System logs
tail -f /var/log/supervisor/*.log

# Application logs
supervisorctl tail -f backend
supervisorctl tail -f frontend
supervisorctl tail -f ipfs-service
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues and support:
1. Check logs: `supervisorctl tail -f [service]`
2. Verify configuration: Check `.env` files
3. Restart services: `supervisorctl restart all`
4. Check network connectivity
5. Verify blockchain RPC endpoints

---

**ChainFLIP 2.0** - Multi-Chain Supply Chain Management with AI-Powered Security
