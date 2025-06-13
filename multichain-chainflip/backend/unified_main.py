"""
ChainFLIP Multi-Chain Unified Backend
Combines comprehensive route modules from app/main.py with network-status functionality from server.py
"""
import os
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import comprehensive route modules from app/main.py structure
from app.api.routes import blockchain, products, fl_system, ipfs_service, analytics, qr_routes, auth, participants, token_bridge, layerzero_oft, supply_chain
from app.core.config import get_settings
from app.core.database import init_database, close_database

# Import services from both implementations
from app.services.blockchain_service import BlockchainService
from app.services.fl_service import FederatedLearningService
from app.services.auth_service import AuthService
from app.services.blockchain_service import blockchain_service
from app.services.multichain_service import multichain_service
from app.services.crosschain_purchase_service import crosschain_purchase_service
from app.services.real_weth_bridge_service import real_weth_bridge_service
from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service

# Import additional routes from server.py
from app.api import participant_routes

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
load_dotenv()

# MongoDB connection (from server.py)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'chainflip_multichain')
db = client[db_name]

# Initialize FastAPI app with comprehensive configuration
app = FastAPI(
    title="ChainFLIP Multi-Chain Unified API",
    description="Complete Supply Chain Management with Multi-Chain Architecture, FL, IPFS, and Network Status",
    version="2.0.0"
)

# CORS middleware with comprehensive origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # Support both specific and wildcard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create additional API router for server.py functionality
api_router = APIRouter(prefix="/api")

# Pydantic models from server.py
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class NetworkStatus(BaseModel):
    """Network status response model"""
    hub_connected: bool
    l2_networks: dict
    participants: dict
    blockchain_stats: dict

# Include all comprehensive route modules from app/main.py
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["blockchain"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(participants.router, prefix="/api/participants", tags=["participants"])
app.include_router(fl_system.router, prefix="/api/federated-learning", tags=["federated-learning"])
app.include_router(ipfs_service.router, prefix="/api/ipfs", tags=["ipfs"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(qr_routes.router, prefix="/api/qr", tags=["qr-codes"])
app.include_router(token_bridge.router, prefix="/api/token-bridge", tags=["token-bridge"])
app.include_router(layerzero_oft.router, prefix="/api/layerzero-oft", tags=["layerzero-oft"])
app.include_router(supply_chain.router, prefix="/api/supply-chain", tags=["supply-chain"])

# Include additional routes from server.py
app.include_router(participant_routes.router)

# Additional endpoints from server.py that aren't in app/main.py routes

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    """Create a status check entry"""
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    """Get all status check entries"""
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.get("/products/", response_model=List[Dict])
async def get_products_with_filtering(
    user_role: Optional[str] = Query(None, description="User role for filtering"),
    wallet_address: Optional[str] = Query(None, description="User wallet address"),
    limit: int = Query(50, description="Number of products to return")
):
    """Get products with optional role-based filtering"""
    try:
        # Initialize blockchain service if needed
        if blockchain_service.database is None:
            await blockchain_service.initialize()
        
        # Get all products
        all_products = await blockchain_service.get_all_products(limit)
        
        # Apply role-based filtering if user_role and wallet_address are provided
        if user_role and wallet_address:
            filtered_products = []
            
            for product in all_products:
                include_product = False
                
                if user_role == 'manufacturer':
                    # Manufacturers see products they created
                    if product.get('manufacturer') == wallet_address:
                        include_product = True
                
                elif user_role == 'transporter':
                    # Transporters see products they are shipping or have shipped
                    current_owner = product.get('current_owner', '')
                    if current_owner == wallet_address:
                        include_product = True
                    
                    # Check if they are assigned as transporter for this product
                    transporter_address = product.get('transporter', '')
                    if transporter_address == wallet_address:
                        include_product = True
                    
                elif user_role == 'buyer':
                    # Buyers see products they own or have ordered
                    current_owner = product.get('current_owner', '')
                    if current_owner == wallet_address:
                        include_product = True
                
                elif user_role == 'admin':
                    # Admins see all products
                    include_product = True
                
                if include_product:
                    filtered_products.append(product)
            
            return {"products": filtered_products, "count": len(filtered_products), "filtered_by": user_role}
        
        # Return all products if no filtering
        return {"products": all_products, "count": len(all_products)}
        
    except Exception as e:
        logger.error(f"Products fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")

@api_router.get("/products/all")
async def get_all_products_legacy():
    """Legacy endpoint - get all products without filtering"""
    try:
        if blockchain_service.database is None:
            await blockchain_service.initialize()
        
        products = await blockchain_service.get_all_products()
        return {"products": products, "count": len(products)}
        
    except Exception as e:
        logger.error(f"Products fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")

@api_router.get("/network-status", response_model=dict)
async def get_network_status():
    """Get comprehensive network status - THE KEY ENDPOINT FROM SERVER.PY"""
    try:
        # Initialize services if needed
        if blockchain_service.database is None:
            await blockchain_service.initialize()
        
        # Get network stats
        network_stats = await blockchain_service.get_network_stats()
        
        # Get multichain stats if available
        multichain_stats = {}
        try:
            if multichain_service.database is None:
                await multichain_service.initialize()
            multichain_stats = await multichain_service.get_chain_stats()
        except Exception as e:
            print(f"⚠️ Multichain stats error: {e}")
        
        return {
            "success": True,
            "data": {
                "blockchain_stats": network_stats,
                "multichain_stats": multichain_stats,
                "timestamp": datetime.utcnow().isoformat()
            },
            "multichain": {
                "polygon_pos_hub": {
                    "connected": network_stats.get("hub_connected", False),
                    "details": network_stats.get("hub_connection_details", {}),
                    "bridge_status": network_stats.get("bridge_status", {})
                },
                "statistics": {
                    "total_products": network_stats.get("total_products", 0),
                    "total_transactions": network_stats.get("total_verifications", 0),
                    "total_disputes": 0  # Can be added later
                }
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@api_router.get("/health")
async def enhanced_health_check():
    """Enhanced health check with connection testing from server.py"""
    try:
        # Test database connection
        await db.status_checks.find_one()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Test blockchain connections
    blockchain_status = {}
    try:
        # Initialize blockchain service if not already done
        if blockchain_service.database is None:
            await blockchain_service.initialize()
        
        # Test Base Sepolia (Manufacturer chain)
        if blockchain_service.manufacturer_web3:
            try:
                latest_block = blockchain_service.manufacturer_web3.eth.block_number
                blockchain_status["base_sepolia"] = {"connected": True, "latest_block": latest_block}
            except Exception as e:
                blockchain_status["base_sepolia"] = {"connected": False, "error": str(e)}
        else:
            blockchain_status["base_sepolia"] = {"connected": False, "error": "Not initialized"}
        
        # Test Polygon Hub
        if blockchain_service.pos_web3:
            try:
                latest_block = blockchain_service.pos_web3.eth.block_number
                blockchain_status["polygon_hub"] = {"connected": True, "latest_block": latest_block}
            except Exception as e:
                blockchain_status["polygon_hub"] = {"connected": False, "error": str(e)}
                # Try fallback RPC
                try:
                    from web3 import Web3
                    fallback_rpc = os.getenv("POLYGON_POS_RPC_FALLBACK", "https://polygon-amoy.g.alchemy.com/v2/demo")
                    fallback_web3 = Web3(Web3.HTTPProvider(fallback_rpc))
                    if fallback_web3.is_connected():
                        latest_block = fallback_web3.eth.block_number
                        blockchain_status["polygon_hub"] = {"connected": True, "latest_block": latest_block, "via": "fallback"}
                except Exception:
                    blockchain_status["polygon_hub"] = {"connected": False, "error": "Both primary and fallback failed"}
        else:
            blockchain_status["polygon_hub"] = {"connected": False, "error": "Not initialized"}
            
    except Exception as e:
        blockchain_status = {"error": str(e)}
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "blockchain": blockchain_status,
        "role_verification": os.getenv("ENABLE_ROLE_VERIFICATION", "true").lower() == "true"
    }

# Include the additional API router
app.include_router(api_router)

# Root endpoint combining both implementations
@app.get("/")
async def root():
    """Unified root endpoint"""
    return {
        "message": "ChainFLIP Multi-Chain Unified Supply Chain Management API",
        "version": "2.0.0",
        "architecture": "Polygon PoS Hub + L2 CDK Participants",
        "features": [
            "Multi-chain product tracking",
            "Federated Learning for anomaly detection", 
            "IPFS decentralized storage",
            "Dynamic encrypted QR codes",
            "Cross-chain asset management",
            "Network status monitoring",
            "Role-based access control",
            "Bridge connectivity testing",
            "Comprehensive analytics",
            "Supply chain orchestration",
            "Hub-coordinated cross-chain purchases",
            "Reputation-based transporter selection",
            "Distance-based delivery assignment",
            "Simplified consensus validation"
        ],
        "endpoints": {
            "auth": "/api/auth/*",
            "blockchain": "/api/blockchain/*", 
            "products": "/api/products/*",
            "participants": "/api/participants/*",
            "federated_learning": "/api/federated-learning/*",
            "ipfs": "/api/ipfs/*",
            "analytics": "/api/analytics/*",
            "qr_codes": "/api/qr/*",
            "token_bridge": "/api/token-bridge/*",
            "layerzero_oft": "/api/layerzero-oft/*",
            "supply_chain": "/api/supply-chain/*",
            "network_status": "/api/network-status",
            "health": "/api/health"
        }
    }

# Simple health endpoint from app/main.py
@app.get("/api/health/simple")
async def simple_health_check():
    """Simple health check from app/main.py"""
    return {"status": "healthy", "message": "ChainFLIP unified backend is running"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def unified_startup_event():
    """Unified startup event combining both initialization strategies"""
    try:
        logger.info("🚀 Starting ChainFLIP Multi-Chain Unified Backend...")
        
        # Initialize database first (from app/main.py approach)
        db_instance = await init_database()
        logger.info(f"📊 Database initialized: {db_instance}")
        
        # Initialize authentication service and admin account
        auth_service = AuthService(db_instance)
        await auth_service.initialize_admin()
        
        # Initialize blockchain services (from both approaches)
        logger.info("🔗 Initializing blockchain services...")
        
        # Initialize the global blockchain service instance
        await blockchain_service.initialize()
        
        # Initialize multichain service  
        try:
            await multichain_service.initialize()
        except Exception as e:
            logger.warning(f"Multichain service initialization warning: {e}")
        
        # Initialize cross-chain purchase service
        try:
            await crosschain_purchase_service.initialize()
            logger.info("✅ Cross-chain purchase service initialized")
        except Exception as e:
            logger.warning(f"Cross-chain purchase service initialization warning: {e}")
        
        # Initialize real WETH bridge service
        try:
            await real_weth_bridge_service.initialize()
            logger.info("✅ Real WETH bridge service initialized")
        except Exception as e:
            logger.warning(f"Real WETH bridge service initialization warning: {e}")
        
        # Initialize LayerZero OFT bridge service (new)
        try:
            await layerzero_oft_bridge_service.initialize()
            logger.info("✅ LayerZero OFT bridge service initialized")
        except Exception as e:
            logger.warning(f"LayerZero OFT bridge service initialization warning: {e}")
        
        # Initialize Supply Chain Orchestrator (new)
        try:
            from app.services.supply_chain_orchestrator import supply_chain_orchestrator
            await supply_chain_orchestrator.initialize()
            logger.info("✅ Supply Chain Orchestrator initialized")
        except Exception as e:
            logger.warning(f"Supply Chain Orchestrator initialization warning: {e}")
        
        # Initialize FL service (from app/main.py)
        try:
            fl_service = FederatedLearningService()
            await fl_service.initialize()
            logger.info("✅ Federated Learning service initialized")
        except Exception as e:
            logger.warning(f"FL service initialization warning: {e}")
        
        logger.info("✅ ChainFLIP Unified Backend Initialized Successfully")
        logger.info("🌐 All endpoints available:")
        logger.info("   - Comprehensive API routes from app/main.py")
        logger.info("   - Network status endpoint from server.py")
        logger.info("   - Enhanced health checks and monitoring")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

@app.on_event("shutdown")
async def unified_shutdown_event():
    """Unified shutdown event"""
    logger.info("🔄 ChainFLIP Unified Backend Shutting Down...")
    
    # Close database connections from both approaches
    try:
        await close_database()
        client.close()
    except Exception as e:
        logger.warning(f"Database closure warning: {e}")
    
    logger.info("✅ ChainFLIP Unified Backend Shutdown Complete")

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "unified_main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )