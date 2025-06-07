from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime

# Import all route modules
from app.api import participant_routes
from app.services import blockchain_service, multichain_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'chainflip_multichain')
db = client[db_name]

# Create the main app without a prefix
app = FastAPI(title="ChainFLIP Multi-Chain Backend", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
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
    
# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "ChainFLIP Multi-Chain Backend API", "version": "2.0.0"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.get("/health")
async def health_check():
    """Enhanced health check with connection testing"""
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
        if not blockchain_service.database:
            await blockchain_service.initialize()
        
        # Test zkEVM Cardona (Manufacturer chain)
        if blockchain_service.manufacturer_web3:
            try:
                latest_block = blockchain_service.manufacturer_web3.eth.block_number
                blockchain_status["zkevm_cardona"] = {"connected": True, "latest_block": latest_block}
            except Exception as e:
                blockchain_status["zkevm_cardona"] = {"connected": False, "error": str(e)}
        else:
            blockchain_status["zkevm_cardona"] = {"connected": False, "error": "Not initialized"}
        
        # Test Polygon Hub
        if blockchain_service.pos_web3:
            try:
                latest_block = blockchain_service.pos_web3.eth.block_number
                blockchain_status["polygon_hub"] = {"connected": True, "latest_block": latest_block}
            except Exception as e:
                blockchain_status["polygon_hub"] = {"connected": False, "error": str(e)}
                # Try fallback
                try:
                    from web3 import Web3
                    fallback_rpc = os.getenv("POLYGON_POS_RPC_FALLBACK", "https://polygon-amoy.g.alchemy.com/v2/demo")
                    fallback_web3 = Web3(Web3.HTTPProvider(fallback_rpc))
                    if fallback_web3.is_connected():
                        latest_block = fallback_web3.eth.block_number
                        blockchain_status["polygon_hub"] = {"connected": True, "latest_block": latest_block, "via": "fallback"}
                except Exception:
                    pass
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

@api_router.get("/products/", response_model=List[Dict])
async def get_products(
    user_role: Optional[str] = Query(None, description="User role for filtering"),
    wallet_address: Optional[str] = Query(None, description="User wallet address"),
    limit: int = Query(50, description="Number of products to return")
):
    """Get products with optional role-based filtering"""
    try:
        # Initialize blockchain service if needed
        if not blockchain_service.database:
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
                    # Check if they are the current owner or involved in shipping
                    current_owner = product.get('current_owner', '')
                    if current_owner == wallet_address:
                        include_product = True
                    
                    # Also check if they have any shipping records for this product
                    # (In a full implementation, you'd check a shipping/transport collection)
                    
                elif user_role == 'buyer':
                    # Buyers see products they own or have ordered
                    current_owner = product.get('current_owner', '')
                    if current_owner == wallet_address:
                        include_product = True
                    
                    # Also check if they have any purchase records for this product
                    # (In a full implementation, you'd check a purchases collection)
                
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

# Keep the old endpoint for backwards compatibility
@api_router.get("/products/all")
async def get_all_products_legacy():
    """Legacy endpoint - get all products without filtering"""
    try:
        if not blockchain_service.database:
            await blockchain_service.initialize()
        
        products = await blockchain_service.get_all_products()
        return {"products": products, "count": len(products)}
        
    except Exception as e:
        logger.error(f"Products fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")

@api_router.get("/network-status", response_model=dict)
async def get_network_status():
    """Get comprehensive network status"""
    try:
        # Initialize services if needed
        if not blockchain_service.database:
            await blockchain_service.initialize()
        
        # Get network stats
        network_stats = await blockchain_service.get_network_stats()
        
        # Get multichain stats if available
        multichain_stats = {}
        try:
            if not multichain_service.database:
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
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Include all route modules
app.include_router(api_router)
app.include_router(participant_routes.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("🚀 Starting ChainFLIP Multi-Chain Backend...")
        
        # Initialize blockchain service
        await blockchain_service.initialize()
        
        # Initialize multichain service
        try:
            await multichain_service.initialize()
        except Exception as e:
            logger.warning(f"Multichain service initialization warning: {e}")
        
        logger.info("✅ Backend services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
