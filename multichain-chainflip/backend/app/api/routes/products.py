"""
Products API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.services.blockchain_service import BlockchainService
from app.services.fl_service import FederatedLearningService
from app.services.ownership_verification_service import OwnershipVerificationService

router = APIRouter()

class ProductAnalysis(BaseModel):
    token_id: str
    analysis_type: str  # "anomaly", "counterfeit", "full"

class ProductQuery(BaseModel):
    manufacturer: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    limit: int = 10
    offset: int = 0

# Dependencies
async def get_blockchain_service():
    service = BlockchainService()
    await service.initialize()
    return service

async def get_fl_service():
    service = FederatedLearningService()
    await service.initialize()
    return service

async def get_ownership_verification_service(blockchain_service: BlockchainService = Depends(get_blockchain_service)):
    """Create ownership verification service with blockchain connections"""
    # Get available web3 connections from blockchain service
    web3_connections = {}
    contract_addresses = {}
    
    # Only add connections that actually exist in the blockchain service
    if hasattr(blockchain_service, 'pos_web3') and blockchain_service.pos_web3:
        web3_connections["polygon_amoy"] = blockchain_service.pos_web3
        contract_addresses["polygon_amoy"] = getattr(blockchain_service, 'polygon_contract_address', None)
    
    if hasattr(blockchain_service, 'manufacturer_web3') and blockchain_service.manufacturer_web3:
        web3_connections["base_sepolia"] = blockchain_service.manufacturer_web3
        contract_addresses["base_sepolia"] = getattr(blockchain_service, 'base_contract_address', None)
    
    # Note: For now, we'll create the service with limited connections
    # On-chain verification can be enhanced later when all chain connections are available
    return OwnershipVerificationService(
        database=blockchain_service.database,
        web3_connections=web3_connections,
        contract_addresses=contract_addresses
    )

@router.get("/")
async def get_products(
    manufacturer: Optional[str] = None,
    owner: Optional[str] = None,
    status: Optional[str] = None,
    user_role: Optional[str] = None,
    wallet_address: Optional[str] = None,
    view_type: Optional[str] = None,  # "marketplace", "owned", "created"
    verify_on_chain: bool = False,  # NEW: Optional on-chain verification for "owned" view
    limit: int = 100,  # Increased limit to show more products
    offset: int = 0,
    blockchain_service: BlockchainService = Depends(get_blockchain_service),
    ownership_service: OwnershipVerificationService = Depends(get_ownership_verification_service)
):
    """Get products with role-based filtering following Algorithm 5"""
    try:
        # Build query filters based on user role and view type
        filters = {}
        
        # Apply role-based filtering for buyers following Algorithm 5
        if user_role == "buyer" and wallet_address:
            if view_type == "marketplace":
                # Algorithm 5: Show available products for purchase (exclude owned, sold, and purchased)
                filters["$and"] = [
                    {"status": {"$nin": ["sold", "purchased_waiting_shipping"]}},  # UPDATED
                    {"current_owner": {"$ne": wallet_address}},  # Not owned by buyer
                    {"manufacturer": {"$ne": wallet_address}},  # Not created by buyer
                    {"buyer": {"$ne": wallet_address}}  # NEW: Not purchased by buyer
                ]
            elif view_type == "owned":
                # ENHANCED: Use ownership verification service for "My Products" tab
                print(f"🔍 Getting owned products for buyer {wallet_address} (verify_on_chain={verify_on_chain})")
                owned_products = await ownership_service.get_owned_products_for_buyer(
                    wallet_address, verify_on_chain=verify_on_chain
                )
                
                # Apply offset and limit to owned products
                total_owned = len(owned_products)
                paginated_products = owned_products[offset:offset + limit]
                
                print(f"✅ Found {total_owned} owned products, returning {len(paginated_products)} (offset={offset}, limit={limit})")
                
                # Format response for owned products
                response = {
                    "products": paginated_products,
                    "total_count": total_owned,
                    "limit": limit,
                    "offset": offset,
                    "filtered_by": f"buyer_owned_enhanced",
                    "count": len(paginated_products),
                    "on_chain_verified": verify_on_chain
                }
                return response
                
            elif view_type == "orders":
                # NEW: Show products purchased by the buyer (their orders)
                filters["$or"] = [
                    {"buyer": wallet_address},  # Products purchased by this buyer
                    {"$and": [
                        {"current_owner": wallet_address},  # Products owned by buyer
                        {"status": {"$in": ["order_pending", "shipped", "delivered"]}}  # With order status
                    ]}
                ]
            else:
                # Default for buyers: marketplace view
                filters["$and"] = [
                    {"status": {"$nin": ["sold", "purchased_waiting_shipping"]}},  # UPDATED
                    {"current_owner": {"$ne": wallet_address}},
                    {"manufacturer": {"$ne": wallet_address}},
                    {"buyer": {"$ne": wallet_address}}  # NEW: Not purchased by buyer
                ]
        elif user_role == "manufacturer" and wallet_address:
            # Show products created by this manufacturer
            filters["manufacturer"] = wallet_address
        elif user_role == "transporter" and wallet_address:
            # Show products in shipping status or assigned to transporter
            filters["$or"] = [
                {"status": "shipping"},
                {"transporter": wallet_address},
                {"shipping_assigned_to": wallet_address}
            ]
        else:
            # Apply legacy filters for other roles
            if manufacturer:
                filters["manufacturer"] = manufacturer
            if owner:
                filters["current_owner"] = owner
            if status:
                filters["status"] = status
        
        print(f"🔍 Product query filters for {user_role} ({wallet_address}): {filters}")
        
        # Get products from database - sorted by creation time (newest first)
        cursor = blockchain_service.database.products.find(filters).sort("created_at", -1).skip(offset).limit(limit)
        products = []
        async for product in cursor:
            product["_id"] = str(product["_id"])
            # Ensure proper field mapping for frontend
            if "mint_params" in product:
                mp = product["mint_params"]
                if "imageCID" in mp:
                    product["image_cid"] = mp["imageCID"]
                if "videoCID" in mp:
                    product["video_cid"] = mp["videoCID"]
                if "name" in mp:
                    product["name"] = mp["name"]
                if "description" in mp:
                    product["description"] = mp["description"]
                if "category" in mp:
                    product["category"] = mp["category"]
                if "price" in mp:
                    product["price"] = mp["price"]
                if "batchNumber" in mp:
                    product["batchNumber"] = mp["batchNumber"]
            products.append(product)
        
        # Get total count
        total_count = await blockchain_service.database.products.count_documents(filters)
        
        response = {
            "products": products,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "filtered_by": f"{user_role}_{view_type}" if user_role and view_type else user_role,
            "count": len(products)
        }
        
        print(f"✅ Returning {len(products)} products for {user_role}")
        return response
        
    except Exception as e:
        print(f"Error fetching products: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/buyer/{buyer_address}/purchases")
async def get_buyer_purchases(
    buyer_address: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get purchase history for buyer - Algorithm 1 & 5 integration"""
    try:
        # Get purchase records from blockchain service
        cursor = blockchain_service.database.purchases.find({"buyer": buyer_address}).sort("purchase_timestamp", -1)
        purchases = []
        async for purchase in cursor:
            purchase["_id"] = str(purchase["_id"])
            
            # Get product details for each purchase
            if purchase.get("product_id"):
                product = await blockchain_service.database.products.find_one({"token_id": purchase["product_id"]})
                if product:
                    product["_id"] = str(product["_id"])
                    purchase["product_details"] = product
            
            purchases.append(purchase)
        
        return {
            "buyer": buyer_address,
            "total_purchases": len(purchases),
            "purchases": purchases,
            "algorithm_1_status": "Payment processing tracked",
            "algorithm_5_status": "Post supply chain management active"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/buyer/{buyer_address}/purchases/waiting-shipping")
async def get_buyer_purchases_waiting_shipping(
    buyer_address: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get buyer's purchases that are waiting for shipping to start"""
    try:
        # Get purchases in waiting shipping status
        cursor = blockchain_service.database.purchases.find({
            "buyer": buyer_address,
            "status": "paid_waiting_shipping"
        }).sort("created_at", -1)
        
        purchases = []
        async for purchase in cursor:
            purchase["_id"] = str(purchase["_id"])
            
            # Get product details
            if purchase.get("product_id"):
                product = await blockchain_service.database.products.find_one({
                    "token_id": purchase["product_id"]
                })
                if product:
                    product["_id"] = str(product["_id"])
                    purchase["product_details"] = product
            
            purchases.append(purchase)
        
        return {
            "buyer": buyer_address,
            "total_waiting_shipping": len(purchases),
            "purchases": purchases,
            "status": "waiting_for_manufacture_shipping"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/buyer/{buyer_address}/owned-products")
async def get_buyer_owned_products(
    buyer_address: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get products currently owned by buyer"""
    try:
        # Get products where current_owner is the buyer
        cursor = blockchain_service.database.products.find({"current_owner": buyer_address}).sort("last_updated", -1)
        products = []
        async for product in cursor:
            product["_id"] = str(product["_id"])
            products.append(product)
        
        return {
            "buyer": buyer_address,
            "owned_products": products,
            "total_owned": len(products)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{token_id}")
async def get_product_details(
    token_id: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get detailed product information"""
    product = await blockchain_service.get_product_by_token_id(token_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
    
    # Ensure proper field mapping for frontend
    if "mint_params" in product:
        mp = product["mint_params"]
        if "imageCID" in mp:
            product["image_cid"] = mp["imageCID"]
        if "videoCID" in mp:
            product["video_cid"] = mp["videoCID"]
        if "name" in mp:
            product["name"] = mp["name"]
        if "description" in mp:
            product["description"] = mp["description"]
        if "category" in mp:
            product["category"] = mp["category"]
        if "price" in mp:
            product["price"] = mp["price"]
        if "batchNumber" in mp:
            product["batchNumber"] = mp["batchNumber"]
    
    return product

@router.get("/{token_id}/history")
async def get_product_history(
    token_id: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get product transport history"""
    product = await blockchain_service.get_product_by_token_id(token_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "token_id": token_id,
        "transport_history": product.get("transport_history", []),
        "current_owner": product.get("current_owner"),
        "status": product.get("status")
    }

@router.post("/{token_id}/analyze")
async def analyze_product(
    token_id: str,
    analysis_data: ProductAnalysis,
    blockchain_service: BlockchainService = Depends(get_blockchain_service),
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Analyze product for anomalies and counterfeits"""
    try:
        # Get product data
        product = await blockchain_service.get_product_by_token_id(token_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        results = {"token_id": token_id}
        
        if analysis_data.analysis_type in ["anomaly", "full"]:
            # Perform anomaly detection
            anomaly_result = await fl_service.detect_anomaly(product)
            results["anomaly_detection"] = anomaly_result
        
        if analysis_data.analysis_type in ["counterfeit", "full"]:
            # Perform counterfeit detection
            counterfeit_result = await fl_service.detect_counterfeit(product)
            results["counterfeit_detection"] = counterfeit_result
        
        # Update product with analysis results
        update_data = {}
        if "anomaly_detection" in results:
            update_data["last_anomaly_check"] = results["anomaly_detection"]
        if "counterfeit_detection" in results:
            update_data["last_counterfeit_check"] = results["counterfeit_detection"]
        
        if update_data:
            await blockchain_service.database.products.update_one(
                {"token_id": token_id},
                {"$set": update_data}
            )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{token_id}/qr")
async def get_product_qr(
    token_id: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get current QR code data for product"""
    product = await blockchain_service.get_product_by_token_id(token_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "token_id": token_id,
        "qr_data": product.get("qr_data", {}),
        "last_updated": product.get("last_updated")
    }

@router.get("/statistics/overview")
async def get_product_statistics(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get product statistics overview"""
    try:
        # Total products
        total_products = await blockchain_service.database.products.count_documents({})
        
        # Products by status
        status_stats = {}
        statuses = ["manufactured", "in_transit", "delivered", "sold"]
        for status in statuses:
            count = await blockchain_service.database.products.count_documents({"status": status})
            status_stats[status] = count
        
        # Products by manufacturer (top 10)
        pipeline = [
            {"$group": {"_id": "$manufacturer", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        manufacturer_stats = []
        async for result in blockchain_service.database.products.aggregate(pipeline):
            manufacturer_stats.append({
                "manufacturer": result["_id"],
                "product_count": result["count"]
            })
        
        return {
            "total_products": total_products,
            "by_status": status_stats,
            "top_manufacturers": manufacturer_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/anomalies/recent")
async def get_recent_anomalies(
    limit: int = 10,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get recent anomaly detections"""
    try:
        cursor = blockchain_service.database.anomalies.find().sort("detected_at", -1).limit(limit)
        anomalies = []
        async for anomaly in cursor:
            anomaly["_id"] = str(anomaly["_id"])
            if "detected_at" in anomaly and hasattr(anomaly["detected_at"], "isoformat"):
                anomaly["detected_at"] = anomaly["detected_at"].isoformat()
            anomalies.append(anomaly)
        
        return {"recent_anomalies": anomalies}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/counterfeits/recent")
async def get_recent_counterfeits(
    limit: int = 10,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get recent counterfeit detections"""
    try:
        cursor = blockchain_service.database.counterfeits.find().sort("detected_at", -1).limit(limit)
        counterfeits = []
        async for counterfeit in cursor:
            counterfeit["_id"] = str(counterfeit["_id"])
            if "detected_at" in counterfeit and hasattr(counterfeit["detected_at"], "isoformat"):
                counterfeit["detected_at"] = counterfeit["detected_at"].isoformat()
            counterfeits.append(counterfeit)
        
        return {"recent_counterfeits": counterfeits}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# BUYER PURCHASES ENDPOINTS
# ==========================================

@router.get("/buyer/{buyer_address}/purchases")
async def get_buyer_purchases(
    buyer_address: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get all purchases made by a buyer"""
    try:
        from app.core.database import get_database
        database = await get_database()
        
        # Get purchases from purchases collection
        purchases = []
        async for purchase in database.purchases.find({"buyer": buyer_address}).sort("created_at", -1):
            purchase["_id"] = str(purchase["_id"])
            
            # Get product details
            product = await database.products.find_one({"token_id": purchase["product_id"]})
            if product:
                purchase["product_details"] = {
                    "name": product.get("name", "Unknown Product"),
                    "category": product.get("category"),
                    "description": product.get("description"),
                    "image_url": product.get("image_url"),
                    "manufacturer": product.get("manufacturer")
                }
            
            purchases.append(purchase)
        
        return {
            "success": True,
            "purchases": purchases,
            "count": len(purchases)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch purchases: {str(e)}")

@router.get("/buyer/{buyer_address}/purchases/waiting-shipping")
async def get_buyer_waiting_shipping_purchases(
    buyer_address: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get purchases that are waiting for shipping/delivery initiation"""
    try:
        from app.core.database import get_database
        database = await get_database()
        
        # Get orders from delivery queue that are waiting for manufacturer action
        purchases = []
        async for order in database.delivery_queue.find({
            "buyer": buyer_address,
            "status": "waiting_for_delivery_initiation"
        }).sort("order_timestamp", -1):
            order["_id"] = str(order["_id"])
            
            # Get product details
            product = await database.products.find_one({"token_id": order["product_id"]})
            if product:
                order["product_details"] = {
                    "name": product.get("name", "Unknown Product"),
                    "category": product.get("category"),
                    "description": product.get("description"),
                    "image_url": product.get("image_url"),
                    "manufacturer": product.get("manufacturer")
                }
            
            # Format order as purchase for frontend compatibility
            purchase = {
                "purchase_id": order["order_id"],
                "product_id": order["product_id"],
                "buyer": order["buyer"],
                "seller": order.get("seller"),
                "manufacturer": order.get("manufacturer"),
                "amount_eth": order["price_eth"],
                "status": "paid_waiting_shipping",
                "created_at": order["order_timestamp"],
                "buyer_chain": order["cross_chain_details"].get("buyer_chain"),
                "escrow_id": order["escrow_id"],
                "product_details": order.get("product_details"),
                "delivery_status": order.get("delivery_status", "pending_manufacturer_action")
            }
            
            purchases.append(purchase)
        
        return {
            "success": True,
            "purchases": purchases,
            "count": len(purchases)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch waiting shipping purchases: {str(e)}")

@router.get("/buyer/{buyer_address}/purchase-status/{purchase_id}")
async def get_purchase_status(
    buyer_address: str,
    purchase_id: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get detailed status of a specific purchase"""
    try:
        from app.core.database import get_database
        database = await get_database()
        
        # Check purchase record
        purchase = await database.purchases.find_one({
            "purchase_id": purchase_id,
            "buyer": buyer_address
        })
        
        if not purchase:
            # Check in delivery queue
            order = await database.delivery_queue.find_one({
                "order_id": purchase_id,
                "buyer": buyer_address
            })
            
            if not order:
                raise HTTPException(status_code=404, detail="Purchase not found")
                
            return {
                "success": True,
                "purchase_id": purchase_id,
                "status": order.get("status"),
                "delivery_status": order.get("delivery_status"),
                "order_details": order
            }
        
        return {
            "success": True,
            "purchase_id": purchase_id,
            "status": purchase.get("status"),
            "purchase_details": purchase
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get purchase status: {str(e)}")