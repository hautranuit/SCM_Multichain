"""
Enhanced Product Authenticity Verification API Routes
Algorithm 4 Enhancement with batch processing and detailed verification status
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from app.services.blockchain_service import blockchain_service

router = APIRouter()


class SingleVerificationRequest(BaseModel):
    product_id: str
    qr_data: Any  # Can be string, dict, or list
    current_owner: str
    return_detailed: Optional[bool] = False
    context: Optional[Dict] = None


class BatchVerificationRequest(BaseModel):
    verification_requests: List[Dict]  # List of SingleVerificationRequest-like dicts
    batch_context: Optional[Dict] = None


@router.post("/authenticity/verify")
async def verify_product_authenticity(request: SingleVerificationRequest):
    """
    Enhanced single product authenticity verification
    Algorithm 4 with improved error handling and detailed status
    """
    try:
        # Prepare verification context
        verification_context = {
            "return_detailed": request.return_detailed,
            "api_request": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if request.context:
            verification_context.update(request.context)
        
        # Perform verification
        result = await blockchain_service.verify_product_authenticity(
            product_id=request.product_id,
            qr_data=request.qr_data,
            current_owner=request.current_owner,
            verification_context=verification_context
        )
        
        return {
            "success": True,
            "verification_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/authenticity/verify-batch")
async def verify_batch_authenticity(request: BatchVerificationRequest):
    """
    Enhanced batch product authenticity verification
    Algorithm 4 with batch processing capabilities
    """
    try:
        if len(request.verification_requests) == 0:
            raise HTTPException(status_code=400, detail="No verification requests provided")
        
        if len(request.verification_requests) > 50:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 50 products")
        
        # Add batch context to each request
        enhanced_requests = []
        for req in request.verification_requests:
            enhanced_req = dict(req)
            if "context" not in enhanced_req:
                enhanced_req["context"] = {}
            enhanced_req["context"].update(request.batch_context or {})
            enhanced_req["context"]["api_batch_request"] = True
            enhanced_requests.append(enhanced_req)
        
        # Perform batch verification
        batch_result = await blockchain_service.verify_multiple_products_authenticity(enhanced_requests)
        
        return {
            "success": True,
            "batch_result": batch_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch verification failed: {str(e)}")


@router.get("/authenticity/analytics")
async def get_verification_analytics(
    time_range_days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get verification analytics and status indicators
    Algorithm 4 Enhancement: Verification Status Dashboard
    """
    try:
        analytics = await blockchain_service.get_verification_analytics(time_range_days)
        
        return {
            "success": True,
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")


@router.get("/authenticity/product/{product_id}/history")
async def get_product_verification_history(product_id: str):
    """
    Get verification history for a specific product
    Algorithm 4 Enhancement: Historical verification tracking
    """
    try:
        # Initialize blockchain service if needed
        if blockchain_service.database is None:
            await blockchain_service.initialize()
        
        # Get verification history from database
        verification_cursor = blockchain_service.database.verification_history.find({
            "product_id": product_id
        }).sort("timestamp", -1).limit(50)
        
        verifications = await verification_cursor.to_list(length=50)
        
        # Format results
        history = []
        for verification in verifications:
            history.append({
                "verification_id": verification.get("verification_id", ""),
                "verifier": verification.get("verifier", ""),
                "result": verification.get("result", ""),
                "timestamp": verification.get("timestamp", "").isoformat() if hasattr(verification.get("timestamp", ""), "isoformat") else str(verification.get("timestamp", "")),
                "details": verification.get("verification_details", {}),
                "session_info": verification.get("session_info", {})
            })
        
        return {
            "success": True,
            "product_id": product_id,
            "verification_history": history,
            "total_verifications": len(history),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/authenticity/verifier/{verifier_address}/summary")
async def get_verifier_summary(verifier_address: str):
    """
    Get verification summary for a specific verifier
    Algorithm 4 Enhancement: Verifier performance tracking
    """
    try:
        # Initialize blockchain service if needed
        if blockchain_service.database is None:
            await blockchain_service.initialize()
        
        # Get verifier's verification history
        verification_cursor = blockchain_service.database.verification_history.find({
            "verifier": verifier_address
        }).sort("timestamp", -1)
        
        verifications = await verification_cursor.to_list(length=None)
        
        # Calculate summary statistics
        summary = {
            "verifier_address": verifier_address,
            "total_verifications": len(verifications),
            "authentic_verifications": 0,
            "non_authentic_verifications": 0,
            "error_verifications": 0,
            "success_rate": 0,
            "recent_activity": [],
            "verification_trends": {
                "last_7_days": 0,
                "last_30_days": 0,
                "all_time": len(verifications)
            }
        }
        
        # Process verifications
        from datetime import timedelta
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        for verification in verifications:
            result = verification.get("result", "")
            timestamp = verification.get("timestamp")
            
            # Count by result type
            if result == "authentic":
                summary["authentic_verifications"] += 1
            elif result in ["manufacturer_mismatch", "ownership_mismatch", "product_data_mismatch"]:
                summary["non_authentic_verifications"] += 1
            else:
                summary["error_verifications"] += 1
            
            # Count recent activity
            if isinstance(timestamp, datetime):
                if timestamp >= seven_days_ago:
                    summary["verification_trends"]["last_7_days"] += 1
                if timestamp >= thirty_days_ago:
                    summary["verification_trends"]["last_30_days"] += 1
            
            # Add to recent activity (last 10)
            if len(summary["recent_activity"]) < 10:
                summary["recent_activity"].append({
                    "product_id": verification.get("product_id", ""),
                    "result": result,
                    "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
                })
        
        # Calculate success rate
        if summary["total_verifications"] > 0:
            summary["success_rate"] = (summary["authentic_verifications"] / summary["total_verifications"]) * 100
        
        return {
            "success": True,
            "verifier_summary": summary,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verifier summary failed: {str(e)}")


@router.get("/authenticity/health")
async def verification_service_health():
    """
    Health check for enhanced verification service
    Algorithm 4 Enhancement: Service monitoring
    """
    try:
        # Check database connectivity
        if blockchain_service.database is None:
            await blockchain_service.initialize()
        
        # Test verification functionality with a simple check
        test_result = await blockchain_service.database.verification_history.find_one({}, {"_id": 1})
        
        # Check encryption service
        encryption_available = hasattr(blockchain_service, 'encryption_service')
        
        # Check IPFS service
        ipfs_available = hasattr(blockchain_service, 'ipfs_service')
        
        return {
            "status": "healthy",
            "service": "enhanced_authenticity_verification",
            "algorithm": "Algorithm 4 Enhanced",
            "capabilities": {
                "single_verification": True,
                "batch_verification": True,
                "detailed_results": True,
                "analytics": True,
                "history_tracking": True
            },
            "services": {
                "database_connected": True,
                "encryption_service": encryption_available,
                "ipfs_service": ipfs_available
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }