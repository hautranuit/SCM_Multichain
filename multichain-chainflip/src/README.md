# ChainFLIP Multi-Chain Smart Contracts

## 🎯 Overview

This directory contains the specialized smart contracts for the ChainFLIP Multi-Chain Supply Chain Management System. The contracts implement 5 core algorithms across separate L2 chains for manufacturer, transporter, and buyer roles.

## 📁 Project Structure

```
contracts/
├── manufacturer-l2/          # Manufacturer chain contracts
│   └── ManufacturerChain.sol # Algorithm 4: Product Authenticity + Quality Control
├── transporter-l2/          # Transporter chain contracts  
│   └── TransporterChain.sol  # Algorithm 3: Supply Chain Consensus + Transport
├── buyer-l2/                # Buyer chain contracts
│   └── BuyerChain.sol        # Algorithm 5: Post Supply Chain + Marketplace
├── enhanced-hub/             # Central hub contract
│   └── EnhancedPolygonPoSHub.sol # FL Model Aggregation + Cross-chain Coordination
├── deployment/               # Deployment scripts
│   ├── deploy-hub.js         # Deploy hub contract
│   ├── deploy-manufacturer.js # Deploy manufacturer contract
│   ├── deploy-transporter.js # Deploy transporter contract
│   ├── deploy-buyer.js       # Deploy buyer contract
│   └── deploy-all.js         # Deploy all contracts
├── hardhat.config.js         # Hardhat configuration
├── package.json              # Dependencies and scripts
└── .env.example              # Environment variables template
```

## 🧠 5 Algorithms Implementation

### Algorithm 1: Payment Release and Incentive Mechanism
- **Manufacturer Chain**: Manufacturing incentives based on quality scores
- **Transporter Chain**: Transport incentives based on on-time delivery
- **Buyer Chain**: Buyer loyalty points and volume bonuses

### Algorithm 2: Dispute Resolution and Voting Mechanism
- **Transporter Chain**: Transport-related disputes with validator voting
- **Buyer Chain**: Purchase disputes with arbitrator voting system

### Algorithm 3: Supply Chain Consensus Algorithm
- **Transporter Chain**: Consensus voting for shipment approval
- **Manufacturer Chain**: Quality control consensus for product approval

### Algorithm 4: Product Authenticity Verification Using RFID and NFT
- **Manufacturer Chain**: Product minting, RFID verification, quality checks
- **Hub Contract**: Cross-chain product registration and verification

### Algorithm 5: Post Supply Chain Management for NFT-based Product Sale
- **Buyer Chain**: Marketplace listings, purchase management, delivery confirmation
- **Hub Contract**: Global product tracking and status updates

## 🔗 Multi-Chain Architecture

### Chain Specialization

1. **Polygon PoS (Hub Chain)**
   - Central coordination and FL model aggregation
   - Cross-chain transaction management
   - Global product registry

2. **Manufacturer L2 Chain (Chain ID: 2001)**
   - Product creation and minting
   - Quality control and approval
   - Manufacturing incentives

3. **Transporter L2 Chain (Chain ID: 2002)**
   - Shipment management and tracking
   - Transport consensus voting
   - Route optimization

4. **Buyer L2 Chain (Chain ID: 2003)**
   - Marketplace and sales
   - Purchase dispute resolution
   - Post-delivery management

## 🚀 Quick Start

### Prerequisites
- Node.js v18+
- Hardhat
- MetaMask or compatible wallet
- Test ETH on desired networks

### Installation

1. **Install dependencies:**
```bash
cd contracts
npm install
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your private keys and RPC URLs
```

3. **Compile contracts:**
```bash
npm run compile
```

### Deployment

#### Option 1: Deploy All Contracts (Recommended)
```bash
# Deploy to testnet (Polygon Amoy + Cardona)
npm run deploy:all:testnet

# Deploy to local networks
npm run deploy:all:local
```

#### Option 2: Deploy Individual Contracts
```bash
# 1. Deploy Hub first
npm run deploy:hub:amoy

# 2. Set HUB_CONTRACT_ADDRESS in .env, then deploy L2 contracts
npm run deploy:manufacturer:cardona
npm run deploy:transporter:cardona  
npm run deploy:buyer:cardona
```

### Network Configuration

#### Testnet Deployment
- **Hub**: Polygon Amoy (Chain ID: 80002)
- **L2 Contracts**: Polygon CDK Cardona (Chain ID: 2442)

#### Local Development
- **Hub**: Localhost:8545 (Chain ID: 31337)
- **Manufacturer**: Localhost:8545 (Chain ID: 2001)
- **Transporter**: Localhost:8546 (Chain ID: 2002)
- **Buyer**: Localhost:8547 (Chain ID: 2003)

## 🔑 Key Features

### Enhanced Federated Learning Integration
- 5 specialized FL models across chains
- Real-time anomaly detection
- Cross-chain model aggregation
- Performance-based reputation scoring

### Advanced Incentive Mechanisms
- Quality-based manufacturing rewards
- On-time delivery bonuses
- Buyer loyalty programs
- Reputation-driven multipliers

### Comprehensive Dispute Resolution
- Multi-stage voting mechanisms
- Arbitrator assignment system
- Evidence management via IPFS
- Automated resolution execution

### Cross-Chain Coordination
- Hub-spoke architecture
- Transaction verification system
- State synchronization
- Event-driven updates

## 📋 Contract Interaction Examples

### Manufacturing Flow
```javascript
// 1. Mint product on manufacturer chain
await manufacturerContract.mintProduct(
  uniqueProductID,
  batchNumber,
  manufacturingDate,
  expirationDate,
  productType,
  manufacturerID,
  metadataCID,
  manufacturingCost
);

// 2. Perform quality check
await manufacturerContract.performQualityCheck(
  productId,
  passed,
  score,
  reportCID
);

// 3. Claim manufacturing incentive
await manufacturerContract.claimManufacturingIncentive();
```

### Transport Flow
```javascript
// 1. Create shipment
await transporterContract.createShipment(
  productTokenId,
  productHash,
  destination,
  startLocation,
  endLocation,
  distance,
  estimatedDeliveryTime
);

// 2. Submit consensus vote
await transporterContract.submitConsensusVote(
  shipmentId,
  approve,
  reason
);

// 3. Mark delivered
await transporterContract.markDelivered(shipmentId);
```

### Buyer Flow
```javascript
// 1. Create marketplace listing
await buyerContract.createMarketplaceListing(
  productTokenId,
  productHash,
  price,
  description,
  metadataCID,
  category
);

// 2. Make purchase
await buyerContract.createPurchase(
  listingId,
  deliveryLocation,
  { value: price }
);

// 3. Confirm delivery
await buyerContract.confirmDelivery(purchaseId);
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `PRIVATE_KEYS` | Comma-separated private keys | `key1,key2,key3` |
| `POLYGON_AMOY_RPC` | Polygon Amoy RPC URL | `https://polygon-amoy.drpc.org` |
| `L2_CDK_RPC` | L2 CDK RPC URL | `https://rpc.cardona.zkevm-rpc.com` |
| `HUB_CONTRACT_ADDRESS` | Deployed hub contract address | `0x123...` |

### Chain IDs
- Polygon Amoy: `80002`
- Polygon CDK Cardona: `2442`
- Manufacturer L2: `2001`
- Transporter L2: `2002`
- Buyer L2: `2003`

## 🧪 Testing

```bash
# Run contract tests
npm test

# Run with coverage
npm run test:coverage

# Test specific contract
npx hardhat test tests/ManufacturerChain.test.js
```

## 🔍 Contract Verification

```bash
# Verify on Polygon Amoy
npm run verify:amoy <CONTRACT_ADDRESS> <CONSTRUCTOR_ARGS>

# Verify on Cardona
npm run verify:cardona <CONTRACT_ADDRESS> <CONSTRUCTOR_ARGS>
```

## 📊 Deployment Output

After successful deployment, you'll get:
- Contract addresses for all chains
- Transaction hashes
- Gas usage reports
- Role assignments
- Funding confirmations

Save the `deployment-complete.json` file for integration with the backend!

## 🔗 Integration

The deployed contracts integrate with:
- **Backend**: FastAPI service with Web3 integration
- **Frontend**: React app with MetaMask connectivity
- **IPFS**: Decentralized storage for metadata
- **FL System**: TensorFlow.js model training

## 🆘 Troubleshooting

### Common Issues

1. **Insufficient Gas**: Increase gas limits in hardhat.config.js
2. **RPC Timeouts**: Use alternative RPC providers
3. **Private Key Errors**: Ensure proper format (without 0x prefix in .env)
4. **Contract Size**: Enable optimizer in solidity settings

### Support

For issues and questions:
- Check deployment logs in `deployment-*.json` files
- Verify network connectivity
- Ensure sufficient test ETH in deployer account
- Review hardhat.config.js network settings