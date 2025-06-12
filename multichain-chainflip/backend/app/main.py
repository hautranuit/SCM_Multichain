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

from app.api.routes import blockchain, products, fl_system, ipfs_service, analytics, qr_routes, auth, participants, layerzero_oft
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
