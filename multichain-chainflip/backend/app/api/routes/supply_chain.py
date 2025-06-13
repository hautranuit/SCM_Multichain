"""
Supply Chain Orchestration API Routes
Handles cross-chain purchase flow and transportation consensus
"""
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...services.supply_chain_orchestrator import supply_chain_orchestrator
from ...core.database import get_database


router = APIRouter()


# === REQUEST MODELS ===

class PurchaseInitiationRequest(BaseModel):
    buyer_address: str = Field(..., description="Buyer's wallet address")
    buyer_chain: str = Field(..., description="Buyer's chain (e.g., 'optimism_sepolia')")
    product_id: str = Field(..., description="Product identifier")
    manufacturer_address: str = Field(..., description="Manufacturer's wallet address")
    manufacturer_chain: str = Field(..., description="Manufacturer's chain (e.g., 'base_sepolia')")
    delivery_address: str = Field(..., description="Delivery address")
    delivery_coordinates: List[float] = Field(..., description="[latitude, longitude] for delivery location")
    manufacturer_coordinates: List[float] = Field(..., description="[latitude, longitude] for manufacturer location")
    purchase_amount: float = Field(..., description="Purchase amount in ETH")

class ShippingInitiationRequest(BaseModel):
    request_id: str = Field(..., description="Purchase request ID")
    manufacturer_address: str = Field(..., description="Manufacturer's wallet address")
    estimated_delivery_time: int = Field(..., description="Estimated delivery time in hours")
    package_details: Dict = Field(..., description="Package details (weight, dimensions, etc.)")
    special_instructions: Optional[str] = Field(None, description="Special delivery instructions")

class TransporterPerformanceUpdate(BaseModel):
    transporter_address: str = Field(..., description="Transporter's wallet address")
    delivery_success: bool = Field(..., description="Whether delivery was successful")
    delivery_time_hours: float = Field(..., description="Actual delivery time in hours")
    expected_time_hours: float = Field(..., description="Expected delivery time in hours")
    package_condition: str = Field(..., description="Package condition: excellent, good, fair, poor")
    customer_rating: Optional[int] = Field(None, description="Customer rating 1-5")

class ValidationVoteRequest(BaseModel):
    batch_id: str = Field(..., description="Transportation batch ID")
    validator_address: str = Field(..., description="Validator's wallet address")
    vote: str = Field(..., description="Vote: approve or reject")
    reasoning: Optional[str] = Field(None, description="Reasoning for the vote")


# === DEPENDENCY INJECTION ===

async def get_orchestrator():
    """Get initialized supply chain orchestrator"""
    if supply_chain_orchestrator.database is None:
        await supply_chain_orchestrator.initialize()
    return supply_chain_orchestrator


# === PURCHASE FLOW ENDPOINTS ===

@router.post("/purchase/initiate", response_model=Dict)
async def initiate_purchase(
    request: PurchaseInitiationRequest,
    orchestrator = Depends(get_orchestrator)
):
    """
    Step 1: Initiate cross-chain purchase
    
    Flow: Buyer (OP Sepolia) → Hub (Polygon Amoy) → Manufacturer (Base Sepolia)
    """
    try:
        # Validate coordinates
        if len(request.delivery_coordinates) != 2 or len(request.manufacturer_coordinates) != 2:
            raise HTTPException(status_code=400, detail="Coordinates must be [latitude, longitude]")
        
        result = await orchestrator.initiate_purchase(
            buyer_address=request.buyer_address,
            buyer_chain=request.buyer_chain,
            product_id=request.product_id,
            manufacturer_address=request.manufacturer_address,
            manufacturer_chain=request.manufacturer_chain,
            delivery_address=request.delivery_address,
            delivery_coordinates=tuple(request.delivery_coordinates),
            manufacturer_coordinates=tuple(request.manufacturer_coordinates),
            purchase_amount=request.purchase_amount
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Purchase initiation failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Purchase initiation error: {str(e)}")


@router.post("/shipping/initiate", response_model=Dict)
async def initiate_shipping(
    request: ShippingInitiationRequest,
    orchestrator = Depends(get_orchestrator)
):
    """
    Step 2: Manufacturer initiates shipping process
    
    This happens after manufacturer receives cross-chain notification from Hub
    """
    try:
        result = await orchestrator.manufacturer_start_shipping(
            request_id=request.request_id,
            manufacturer_address=request.manufacturer_address,
            shipping_details={
                "estimated_delivery_time": request.estimated_delivery_time,
                "package_details": request.package_details,
                "special_instructions": request.special_instructions,
                "shipping_initiated_at": datetime.utcnow().isoformat()
            }
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Shipping initiation failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shipping initiation error: {str(e)}")


# === STATUS AND TRACKING ENDPOINTS ===

@router.get("/purchase/{request_id}/status", response_model=Dict)
async def get_purchase_status(
    request_id: str,
    orchestrator = Depends(get_orchestrator)
):
    """Get detailed status of a purchase request"""
    try:
        result = await orchestrator.get_purchase_status(request_id)
        
        if not result["found"]:
            raise HTTPException(status_code=404, detail="Purchase request not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status retrieval error: {str(e)}")


@router.get("/purchase/list", response_model=Dict)
async def list_purchase_requests(
    buyer_address: Optional[str] = Query(None, description="Filter by buyer address"),
    manufacturer_address: Optional[str] = Query(None, description="Filter by manufacturer address"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, description="Number of requests to return"),
    orchestrator = Depends(get_orchestrator)
):
    """List purchase requests with optional filtering"""
    try:
        # Build filter query
        filter_query = {}
        if buyer_address:
            filter_query["buyer_address"] = buyer_address
        if manufacturer_address:
            filter_query["manufacturer_address"] = manufacturer_address
        if status:
            filter_query["status"] = status
        
        # Get requests from database
        cursor = orchestrator.database["purchase_requests"].find(filter_query).sort(
            "timestamp", -1
        ).limit(limit)
        
        requests = await cursor.to_list(length=limit)
        
        # Format response
        formatted_requests = []
        for req in requests:
            formatted_requests.append({
                "request_id": req["request_id"],
                "buyer_address": req["buyer_address"],
                "buyer_chain": req["buyer_chain"],
                "manufacturer_address": req["manufacturer_address"],
                "manufacturer_chain": req["manufacturer_chain"],
                "product_id": req["product_id"],
                "status": req["status"],
                "distance_miles": req["distance_miles"],
                "purchase_amount": req["purchase_amount"],
                "timestamp": req["timestamp"].isoformat(),
                "transporters_required": orchestrator._get_transporters_required(req["distance_miles"])
            })
        
        return {
            "requests": formatted_requests,
            "count": len(formatted_requests),
            "filter": filter_query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request listing error: {str(e)}")


# === TRANSPORTER MANAGEMENT ENDPOINTS ===

@router.get("/transporters/leaderboard", response_model=List[Dict])
async def get_transporter_leaderboard(
    limit: int = Query(20, description="Number of transporters to return"),
    orchestrator = Depends(get_orchestrator)
):
    """Get transporter leaderboard by reputation score"""
    try:
        leaderboard = await orchestrator.get_transporter_leaderboard(limit)
        return leaderboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leaderboard retrieval error: {str(e)}")


@router.post("/transporters/update-performance", response_model=Dict)
async def update_transporter_performance(
    request: TransporterPerformanceUpdate,
    orchestrator = Depends(get_orchestrator)
):
    """Update transporter reputation based on delivery performance"""
    try:
        # Prepare performance metrics
        performance_metrics = {
            "success": request.delivery_success,
            "actual_delivery_hours": request.delivery_time_hours,
            "expected_delivery_hours": request.expected_time_hours,
            "package_condition": request.package_condition,
            "customer_rating": request.customer_rating
        }
        
        result = await orchestrator.update_transporter_reputation(
            transporter_address=request.transporter_address,
            performance_metrics=performance_metrics
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Performance update failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance update error: {str(e)}")


@router.get("/transporters/{address}/reputation", response_model=Dict)
async def get_transporter_reputation(
    address: str,
    orchestrator = Depends(get_orchestrator)
):
    """Get detailed reputation information for a transporter"""
    try:
        reputation_doc = await orchestrator.database["transporter_reputation"].find_one({
            "address": address
        })
        
        if not reputation_doc:
            raise HTTPException(status_code=404, detail="Transporter not found")
        
        # Calculate additional stats
        success_rate = 0
        if reputation_doc.get("total_deliveries", 0) > 0:
            success_rate = (reputation_doc.get("successful_deliveries", 0) / 
                          reputation_doc["total_deliveries"]) * 100
        
        return {
            "address": reputation_doc["address"],
            "reputation_score": reputation_doc["reputation_score"],
            "total_deliveries": reputation_doc.get("total_deliveries", 0),
            "successful_deliveries": reputation_doc.get("successful_deliveries", 0),
            "success_rate": success_rate,
            "status": reputation_doc.get("status", "unknown"),
            "created_at": reputation_doc.get("created_at", datetime.utcnow()).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reputation retrieval error: {str(e)}")


# === CONSENSUS AND VALIDATION ENDPOINTS ===

@router.get("/batches/{batch_id}/status", response_model=Dict)
async def get_batch_status(
    batch_id: str,
    orchestrator = Depends(get_orchestrator)
):
    """Get status of a transportation batch"""
    try:
        batch_doc = await orchestrator.database["transportation_batches"].find_one({
            "batch_id": batch_id
        })
        
        if not batch_doc:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Get consensus votes
        votes_doc = await orchestrator.database["consensus_votes"].find_one({
            "batch_id": batch_id
        })
        
        return {
            "batch_id": batch_doc["batch_id"],
            "status": batch_doc["status"],
            "transporters_count": len(batch_doc.get("transporters", [])),
            "validation_nodes_count": len(batch_doc.get("validation_nodes", [])),
            "consensus_result": batch_doc.get("consensus_result", {}),
            "consensus_votes": votes_doc.get("votes", []) if votes_doc else [],
            "created_at": batch_doc["created_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch status error: {str(e)}")


@router.post("/validation/vote", response_model=Dict)
async def submit_validation_vote(
    request: ValidationVoteRequest,
    orchestrator = Depends(get_orchestrator)
):
    """Submit a validation vote for a transportation batch"""
    try:
        # Verify batch exists
        batch_doc = await orchestrator.database["transportation_batches"].find_one({
            "batch_id": request.batch_id
        })
        
        if not batch_doc:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Verify validator is authorized
        if request.validator_address not in batch_doc.get("validation_nodes", []):
            raise HTTPException(status_code=403, detail="Validator not authorized for this batch")
        
        # Check if already voted
        existing_votes = await orchestrator.database["consensus_votes"].find_one({
            "batch_id": request.batch_id
        })
        
        if existing_votes:
            # Check if this validator already voted
            for vote in existing_votes.get("votes", []):
                if vote["validator"] == request.validator_address:
                    raise HTTPException(status_code=400, detail="Validator has already voted")
        
        # Add vote (this would integrate with the consensus mechanism)
        # For now, just record the vote
        vote_data = {
            "validator": request.validator_address,
            "vote": request.vote,
            "reasoning": request.reasoning,
            "timestamp": datetime.utcnow()
        }
        
        # Update or create votes document
        if existing_votes:
            await orchestrator.database["consensus_votes"].update_one(
                {"batch_id": request.batch_id},
                {"$push": {"votes": vote_data}}
            )
        else:
            await orchestrator.database["consensus_votes"].insert_one({
                "batch_id": request.batch_id,
                "votes": [vote_data],
                "timestamp": datetime.utcnow()
            })
        
        return {
            "success": True,
            "batch_id": request.batch_id,
            "validator": request.validator_address,
            "vote": request.vote,
            "timestamp": vote_data["timestamp"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vote submission error: {str(e)}")


# === STATISTICS AND ANALYTICS ENDPOINTS ===

@router.get("/analytics/dashboard", response_model=Dict)
async def get_analytics_dashboard(
    orchestrator = Depends(get_orchestrator)
):
    """Get supply chain analytics dashboard data"""
    try:
        # Get total statistics
        total_requests = await orchestrator.database["purchase_requests"].count_documents({})
        active_requests = await orchestrator.database["purchase_requests"].count_documents({
            "status": {"$in": ["pending_hub_coordination", "hub_coordinated", "shipping_initiated"]}
        })
        completed_requests = await orchestrator.database["purchase_requests"].count_documents({
            "status": "delivered"
        })
        
        # Get transporter statistics
        total_transporters = await orchestrator.database["transporter_reputation"].count_documents({})
        active_transporters = await orchestrator.database["transporter_reputation"].count_documents({
            "status": "available"
        })
        
        # Get average reputation score
        pipeline = [
            {"$group": {"_id": None, "avg_reputation": {"$avg": "$reputation_score"}}}
        ]
        avg_reputation_result = await orchestrator.database["transporter_reputation"].aggregate(pipeline).to_list(1)
        avg_reputation = avg_reputation_result[0]["avg_reputation"] if avg_reputation_result else 0
        
        # Get distance distribution
        distance_pipeline = [
            {
                "$bucket": {
                    "groupBy": "$distance_miles",
                    "boundaries": [0, 100, 250, 500, 750, 1000, float('inf')],
                    "default": "1000+",
                    "output": {"count": {"$sum": 1}}
                }
            }
        ]
        distance_distribution = await orchestrator.database["purchase_requests"].aggregate(distance_pipeline).to_list(10)
        
        return {
            "total_requests": total_requests,
            "active_requests": active_requests,
            "completed_requests": completed_requests,
            "completion_rate": (completed_requests / max(1, total_requests)) * 100,
            "total_transporters": total_transporters,
            "active_transporters": active_transporters,
            "average_reputation": round(avg_reputation, 3),
            "distance_distribution": distance_distribution,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


# === HEALTH AND STATUS ENDPOINTS ===

@router.get("/health", response_model=Dict)
async def health_check():
    """Health check for supply chain orchestration service"""
    try:
        # Test orchestrator initialization
        orchestrator = await get_orchestrator()
        
        # Test database connection
        await orchestrator.database["purchase_requests"].find_one()
        
        return {
            "status": "healthy",
            "service": "Supply Chain Orchestrator",
            "features": [
                "Cross-chain purchase coordination",
                "Hub-based message routing",
                "Reputation-based transporter selection",
                "Distance-based assignment",
                "Simplified consensus validation",
                "Performance tracking"
            ],
            "chains_supported": list(orchestrator.chains.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
