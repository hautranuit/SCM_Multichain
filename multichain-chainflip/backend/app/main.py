"""
ChainFLIP Multi-Chain Backend
FastAPI backend coordinating Polygon PoS hub and L2 CDK participants
"""
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv

from app.api.routes import blockchain, products, fl_system, ipfs_service, analytics, qr_routes, auth, participants, layerzero_oft, supply_chain, enhanced_consensus, payment_incentive, enhanced_authenticity, post_supply_chain, nft_transfers
from app.core.config import get_settings
from app.core.database import init_database, close_database
from app.services.blockchain_service import BlockchainService
from app.services.fl_service import FederatedLearningService
from app.services.auth_service import AuthService

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="ChainFLIP Multi-Chain API",
    description="Advanced Supply Chain Management with Multi-Chain Architecture, FL, and IPFS",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["blockchain"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(participants.router, prefix="/api/participants", tags=["participants"])
app.include_router(fl_system.router, prefix="/api/federated-learning", tags=["federated-learning"])
app.include_router(ipfs_service.router, prefix="/api/ipfs", tags=["ipfs"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(qr_routes.router, prefix="/api/qr", tags=["qr-codes"])
app.include_router(layerzero_oft.router, prefix="/api/layerzero-oft", tags=["layerzero-oft"])
app.include_router(supply_chain.router, prefix="/api/supply-chain", tags=["supply-chain"])
app.include_router(enhanced_consensus.router, prefix="/api/enhanced-consensus", tags=["enhanced-consensus"])
app.include_router(payment_incentive.router, prefix="/api/payment", tags=["payment-incentive"])
app.include_router(enhanced_authenticity.router, prefix="/api/enhanced-authenticity", tags=["enhanced-authenticity"])
app.include_router(post_supply_chain.router, prefix="/api/post-supply-chain", tags=["post-supply-chain"])
app.include_router(nft_transfers.router, prefix="/api/nft", tags=["nft-transfers"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 ChainFLIP Multi-Chain Backend Starting...")
    
    # Initialize database first
    db_instance = await init_database()
    print(f"📊 Database initialized: {db_instance}")
    
    # Initialize authentication service and admin account
    auth_service = AuthService(db_instance)
    await auth_service.initialize_admin()
    
    # Initialize blockchain services
    blockchain_service = BlockchainService()
    await blockchain_service.initialize()
    
    # Initialize FL service
    fl_service = FederatedLearningService()
    await fl_service.initialize()
    
    # Initialize LayerZero OFT Bridge Service
    from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service
    await layerzero_oft_bridge_service.initialize()
    print("🌉 LayerZero OFT Bridge Service initialized")
    
    # Initialize Enhanced Consensus Services
    from app.services.scc_consensus_service import scc_consensus_service
    from app.services.dispute_resolution_service import dispute_resolution_service
    await scc_consensus_service.initialize()
    await dispute_resolution_service.initialize()
    print("🔗 Enhanced Consensus and Dispute Resolution Services initialized")
    
    # Initialize Payment Incentive Service
    from app.services.payment_incentive_service import payment_incentive_service
    await payment_incentive_service.initialize()
    print("💰 Payment Incentive Service initialized")
    
    # Initialize Post Supply Chain Service (Algorithm 5)
    try:
        from app.services.post_supply_chain_service import post_supply_chain_service
        await post_supply_chain_service.initialize()
        print("🛍️ Post Supply Chain Service initialized")
    except Exception as e:
        print(f"⚠️ Post Supply Chain Service initialization warning: {e}")
    
    # Initialize Direct LayerZero Messaging Service
    try:
        from app.services.direct_layerzero_messaging_service import direct_layerzero_messaging_service
        await direct_layerzero_messaging_service.initialize()
        print("🌐 Direct LayerZero Messaging Service initialized")
    except Exception as e:
        print(f"⚠️ Direct LayerZero Messaging Service initialization warning: {e}")
    
    # Initialize NFT Transfer Orchestrator
    try:
        from app.services.nft_transfer_orchestrator import nft_transfer_orchestrator
        await nft_transfer_orchestrator.initialize()
        print("🔄 NFT Transfer Orchestrator initialized")
    except Exception as e:
        print(f"⚠️ NFT Transfer Orchestrator initialization warning: {e}")
    
    print("✅ ChainFLIP Backend Initialized Successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    print("🔄 ChainFLIP Backend Shutting Down...")
    await close_database()
    print("✅ ChainFLIP Backend Shutdown Complete")

@app.get("/")
async def root():
    return {
        "message": "ChainFLIP Multi-Chain Supply Chain Management API",
        "version": "2.0.0",
        "architecture": "Polygon PoS Hub + L2 CDK Participants",
        "features": [
            "Multi-chain product tracking",
            "Federated Learning for anomaly detection",
            "IPFS decentralized storage",
            "Dynamic encrypted QR codes",
            "Cross-chain asset management"
        ]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "ChainFLIP backend is running"}

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
