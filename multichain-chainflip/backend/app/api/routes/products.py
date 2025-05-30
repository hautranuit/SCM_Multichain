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
def get_blockchain_service():
    return BlockchainService()

def get_fl_service():
    return FederatedLearningService()

@router.get("/")
async def get_products(
    manufacturer: Optional[str] = None,
    owner: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get products with optional filtering"""
    try:
        # Build query filters
        filters = {}
        if manufacturer:
            filters["manufacturer"] = manufacturer
        if owner:
            filters["current_owner"] = owner
        if status:
            filters["status"] = status
        
        # Get products from database
        cursor = blockchain_service.database.products.find(filters).skip(offset).limit(limit)
        products = []
        async for product in cursor:
            product["_id"] = str(product["_id"])
            products.append(product)
        
        # Get total count
        total_count = await blockchain_service.database.products.count_documents(filters)
        
        return {
            "products": products,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
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
            counterfeit["detected_at"] = counterfeit["detected_at"].isoformat()
            counterfeits.append(counterfeit)
        
        return {"recent_counterfeits": counterfeits}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
