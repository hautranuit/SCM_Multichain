"""
Products API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.services.blockchain_service import BlockchainService
from app.services.fl_service import FederatedLearningService

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

@router.get("/")
async def get_products(
    manufacturer: Optional[str] = None,
    owner: Optional[str] = None,
    status: Optional[str] = None,
    user_role: Optional[str] = None,
    wallet_address: Optional[str] = None,
    view_type: Optional[str] = None,  # "marketplace", "owned", "created"
    limit: int = 100,  # Increased limit to show more products
    offset: int = 0,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get products with role-based filtering following Algorithm 5"""
    try:
        # Build query filters based on user role and view type
        filters = {}
        
        # Apply role-based filtering for buyers following Algorithm 5
        if user_role == "buyer" and wallet_address:
            if view_type == "marketplace":
                # Algorithm 5: Show available products for purchase (exclude owned and sold)
                filters["$and"] = [
                    {"status": {"$ne": "sold"}},  # Not sold
                    {"current_owner": {"$ne": wallet_address}},  # Not owned by buyer
                    {"manufacturer": {"$ne": wallet_address}}  # Not created by buyer
                ]
            elif view_type == "owned":
                # Show products owned by the buyer
                filters["current_owner"] = wallet_address
            else:
                # Default for buyers: marketplace view
                filters["$and"] = [
                    {"status": {"$ne": "sold"}},
                    {"current_owner": {"$ne": wallet_address}},
                    {"manufacturer": {"$ne": wallet_address}}
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