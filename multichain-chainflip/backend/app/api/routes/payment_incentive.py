"""
Payment Incentive API Routes
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.payment_incentive_service import payment_incentive_service

router = APIRouter()

class CreateEscrowRequest(BaseModel):
    purchase_request_id: str
    buyer_address: str
    total_amount: float
    transporter_addresses: List[str]
    estimated_delivery_date: str  # ISO format

class DeliveryConfirmationRequest(BaseModel):
    purchase_request_id: str
    buyer_address: str
    delivery_confirmation: Dict
    transporter_metrics: List[Dict]

class DisputeRequest(BaseModel):
    purchase_request_id: str
    dispute_reason: str
    dispute_details: Dict

class IncentiveCalculationRequest(BaseModel):
    purchase_request_id: str
    transporter_address: str
    delivery_metrics: Dict

@router.post("/escrow/create")
async def create_escrow_payment(request: CreateEscrowRequest):
    """Create escrow payment for a purchase"""
    try:
        estimated_delivery = datetime.fromisoformat(request.estimated_delivery_date.replace('Z', '+00:00'))
        
        result = await payment_incentive_service.create_escrow_payment(
            purchase_request_id=request.purchase_request_id,
            buyer_address=request.buyer_address,
            total_amount=request.total_amount,
            transporter_addresses=request.transporter_addresses,
            estimated_delivery_date=estimated_delivery
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/release")
async def release_payment_on_delivery(request: DeliveryConfirmationRequest):
    """Release escrow payment when delivery is confirmed"""
    try:
        result = await payment_incentive_service.release_payment_on_delivery(
            purchase_request_id=request.purchase_request_id,
            buyer_address=request.buyer_address,
            delivery_confirmation=request.delivery_confirmation,
            transporter_metrics=request.transporter_metrics
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/incentive/calculate")
async def calculate_transporter_incentive(request: IncentiveCalculationRequest):
    """Calculate performance-based incentive for a transporter"""
    try:
        result = await payment_incentive_service.calculate_transporter_incentives(
            purchase_request_id=request.purchase_request_id,
            transporter_address=request.transporter_address,
            delivery_metrics=request.delivery_metrics
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dispute")
async def create_payment_dispute(request: DisputeRequest):
    """Create a payment dispute"""
    try:
        result = await payment_incentive_service.handle_dispute_payment(
            purchase_request_id=request.purchase_request_id,
            dispute_reason=request.dispute_reason,
            dispute_details=request.dispute_details
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{purchase_request_id}")
async def get_payment_status(purchase_request_id: str):
    """Get payment status for a purchase request"""
    try:
        result = await payment_incentive_service.get_payment_status(purchase_request_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transporter/{transporter_address}/earnings")
async def get_transporter_earnings(transporter_address: str, limit: Optional[int] = 50):
    """Get earnings history for a transporter"""
    try:
        result = await payment_incentive_service.get_transporter_earnings_history(
            transporter_address=transporter_address,
            limit=limit
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/platform")
async def get_platform_payment_analytics():
    """Get platform-wide payment analytics"""
    try:
        # Get statistics from payment incentive service
        total_payments = await payment_incentive_service.database["escrow_payments"].count_documents({})
        total_released = await payment_incentive_service.database["escrow_payments"].count_documents({"status": "released"})
        total_disputed = await payment_incentive_service.database["escrow_payments"].count_documents({"status": "disputed"})
        
        # Get total volume processed
        pipeline = [
            {"$group": {"_id": None, "total_volume": {"$sum": "$escrow_amount"}}}
        ]
        volume_result = await payment_incentive_service.database["escrow_payments"].aggregate(pipeline).to_list(length=1)
        total_volume = volume_result[0]["total_volume"] if volume_result else 0
        
        # Get average incentive multiplier
        incentive_pipeline = [
            {"$group": {"_id": None, "avg_multiplier": {"$avg": "$performance_multiplier"}}}
        ]
        incentive_result = await payment_incentive_service.database["transporter_incentives"].aggregate(incentive_pipeline).to_list(length=1)
        avg_incentive_multiplier = incentive_result[0]["avg_multiplier"] if incentive_result else 1.0
        
        return {
            "success": True,
            "total_payments": total_payments,
            "total_released": total_released,
            "total_disputed": total_disputed,
            "dispute_rate": (total_disputed / total_payments * 100) if total_payments > 0 else 0,
            "total_volume_processed": total_volume,
            "average_incentive_multiplier": avg_incentive_multiplier,
            "platform_fee_percentage": payment_incentive_service.platform_fee_percentage * 100,
            "auto_release_delay_days": payment_incentive_service.auto_release_delay.days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def payment_service_health():
    """Health check for payment service"""
    try:
        if payment_incentive_service.database is None:
            return {"status": "unhealthy", "error": "Database not connected"}
        
        # Test database connectivity
        test_result = await payment_incentive_service.database["escrow_payments"].find_one({}, {"_id": 1})
        
        return {
            "status": "healthy",
            "service": "payment_incentive_service",
            "database_connected": True,
            "platform_fee": f"{payment_incentive_service.platform_fee_percentage * 100}%",
            "initialized": True
        }
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}