"""
NFT Product Transfer API Routes
Handles cross-chain NFT transfers through transporter chain with escrow management
"""
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...services.nft_transfer_orchestrator import nft_transfer_orchestrator
from ...core.database import get_database


router = APIRouter()


# === REQUEST MODELS ===

class NFTTransferInitiationRequest(BaseModel):
    purchase_request_id: str = Field(..., description="Related purchase request ID")
    product_id: str = Field(..., description="Product identifier")
    manufacturer_address: str = Field(..., description="Manufacturer's wallet address")
    transporter_addresses: List[str] = Field(..., description="List of transporter addresses in order")
    buyer_address: str = Field(..., description="Final buyer's wallet address")
    purchase_amount: float = Field(..., description="Purchase amount for escrow (in ETH)")
    product_metadata: Dict = Field(..., description="Product metadata for NFT")

class TransferStepExecutionRequest(BaseModel):
    transfer_id: str = Field(..., description="NFT transfer ID")
    executor_address: str = Field(..., description="Address executing the transfer step")

class EscrowReleaseRequest(BaseModel):
    escrow_id: str = Field(..., description="Escrow ID to release")
    buyer_confirmation: bool = Field(..., description="Buyer confirmation of delivery")

class NFTOwnershipVerificationRequest(BaseModel):
    token_id: str = Field(..., description="NFT token ID")
    claimed_owner: str = Field(..., description="Address claiming ownership")
    chain: str = Field(..., description="Blockchain where ownership is claimed")


# === DEPENDENCY INJECTION ===

async def get_nft_orchestrator():
    """Get initialized NFT transfer orchestrator"""
    if nft_transfer_orchestrator.database is None:
        await nft_transfer_orchestrator.initialize()
    return nft_transfer_orchestrator


# === NFT TRANSFER FLOW ENDPOINTS ===

@router.post("/nft/initiate-transfer", response_model=Dict)
async def initiate_nft_transfer(
    request: NFTTransferInitiationRequest,
    orchestrator = Depends(get_nft_orchestrator)
):
    """
    Initiate complete NFT transfer flow
    
    1. Mint NFT on manufacturer chain
    2. Create escrow on buyer chain  
    3. Plan transfer route through transporters
    4. Set up for step-by-step execution
    """
    try:
        # Validate transporters list
        if not request.transporter_addresses:
            raise HTTPException(status_code=400, detail="At least one transporter address required")
        
        if len(request.transporter_addresses) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 transporters allowed")
        
        # Validate purchase amount
        if request.purchase_amount <= 0:
            raise HTTPException(status_code=400, detail="Purchase amount must be positive")
        
        result = await orchestrator.initiate_nft_transfer_flow(
            purchase_request_id=request.purchase_request_id,
            product_id=request.product_id,
            manufacturer_address=request.manufacturer_address,
            transporter_addresses=request.transporter_addresses,
            buyer_address=request.buyer_address,
            purchase_amount=request.purchase_amount,
            product_metadata=request.product_metadata
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "NFT transfer initiation failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NFT transfer initiation error: {str(e)}")


@router.post("/nft/execute-step", response_model=Dict)
async def execute_transfer_step(
    request: TransferStepExecutionRequest,
    orchestrator = Depends(get_nft_orchestrator)
):
    """
    Execute the next step in the NFT transfer chain
    Called by transporters to move NFT to next holder
    """
    try:
        result = await orchestrator.execute_next_transfer_step(request.transfer_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Transfer step execution failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transfer step execution error: {str(e)}")


@router.get("/nft/transfer/{transfer_id}/status", response_model=Dict)
async def get_nft_transfer_status(
    transfer_id: str,
    orchestrator = Depends(get_nft_orchestrator)
):
    """Get detailed status of an NFT transfer"""
    try:
        result = await orchestrator.get_transfer_status(transfer_id)
        
        if not result["found"]:
            raise HTTPException(status_code=404, detail="NFT transfer not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transfer status retrieval error: {str(e)}")


@router.get("/nft/transfers/list", response_model=Dict)
async def list_nft_transfers(
    buyer_address: Optional[str] = Query(None, description="Filter by buyer address"),
    manufacturer_address: Optional[str] = Query(None, description="Filter by manufacturer address"),
    status: Optional[str] = Query(None, description="Filter by transfer status"),
    limit: int = Query(20, description="Number of transfers to return"),
    orchestrator = Depends(get_nft_orchestrator)
):
    """List NFT transfers with optional filtering"""
    try:
        # Build filter query
        filter_query = {}
        if buyer_address:
            filter_query["buyer_address"] = buyer_address
        if manufacturer_address:
            filter_query["manufacturer_address"] = manufacturer_address
        if status:
            filter_query["status"] = status
        
        # Get transfers from database
        cursor = orchestrator.database["nft_transfers"].find(filter_query).sort(
            "created_at", -1
        ).limit(limit)
        
        transfers = await cursor.to_list(length=limit)
        
        # Format response
        formatted_transfers = []
        for transfer in transfers:
            formatted_transfers.append({
                "transfer_id": transfer["transfer_id"],
                "token_id": transfer["token_id"],
                "product_id": transfer["product_id"],
                "manufacturer_address": transfer["manufacturer_address"],
                "buyer_address": transfer["buyer_address"],
                "status": transfer["status"],
                "current_step": transfer["current_step"],
                "total_steps": transfer["total_steps"],
                "progress_percentage": (transfer["current_step"] / transfer["total_steps"]) * 100,
                "purchase_amount": transfer["purchase_amount"],
                "escrow_id": transfer["escrow_id"],
                "created_at": transfer["created_at"].isoformat(),
                "transporter_count": len(transfer["transporter_addresses"])
            })
        
        return {
            "transfers": formatted_transfers,
            "count": len(formatted_transfers),
            "filter": filter_query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transfer listing error: {str(e)}")


# === ESCROW MANAGEMENT ENDPOINTS ===

@router.post("/nft/escrow/release", response_model=Dict)
async def release_escrow(
    request: EscrowReleaseRequest,
    orchestrator = Depends(get_nft_orchestrator)
):
    """
    Release escrow funds after successful NFT delivery
    Can be called by buyer or automatically by system
    """
    try:
        # Get escrow details
        escrow_doc = await orchestrator.database["nft_escrows"].find_one({
            "escrow_id": request.escrow_id
        })
        
        if not escrow_doc:
            raise HTTPException(status_code=404, detail="Escrow not found")
        
        if escrow_doc["status"] != "locked":
            raise HTTPException(status_code=400, detail=f"Escrow not in locked state: {escrow_doc['status']}")
        
        # Update release conditions
        await orchestrator.database["nft_escrows"].update_one(
            {"escrow_id": request.escrow_id},
            {
                "$set": {
                    "release_conditions.buyer_confirmation": request.buyer_confirmation,
                    "buyer_confirmation_at": datetime.utcnow()
                }
            }
        )
        
        # Release escrow if conditions are met
        if request.buyer_confirmation:
            result = await orchestrator.release_escrow(request.escrow_id)
            
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result.get("error", "Escrow release failed"))
            
            return result
        else:
            return {
                "success": True,
                "message": "Buyer confirmation recorded, but escrow not released",
                "escrow_id": request.escrow_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escrow release error: {str(e)}")


@router.get("/nft/escrow/{escrow_id}/status", response_model=Dict)
async def get_escrow_status(
    escrow_id: str,
    orchestrator = Depends(get_nft_orchestrator)
):
    """Get detailed escrow status"""
    try:
        escrow_doc = await orchestrator.database["nft_escrows"].find_one({
            "escrow_id": escrow_id
        })
        
        if not escrow_doc:
            raise HTTPException(status_code=404, detail="Escrow not found")
        
        # Calculate time remaining
        current_time = datetime.utcnow().timestamp()
        time_remaining = max(0, escrow_doc["expires_at"] - current_time)
        
        return {
            "escrow_id": escrow_doc["escrow_id"],
            "buyer_address": escrow_doc["buyer_address"],
            "token_id": escrow_doc["token_id"],
            "purchase_amount": escrow_doc["purchase_amount"],
            "status": escrow_doc["status"],
            "escrow_chain": escrow_doc["escrow_chain"],
            "created_at": escrow_doc["created_at"].isoformat(),
            "expires_at": datetime.fromtimestamp(escrow_doc["expires_at"]).isoformat(),
            "time_remaining_seconds": int(time_remaining),
            "release_conditions": escrow_doc["release_conditions"],
            "transaction_hash": escrow_doc.get("transaction_hash"),
            "release_transaction": escrow_doc.get("release_transaction")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escrow status error: {str(e)}")


# === NFT OWNERSHIP AND VERIFICATION ===

@router.post("/nft/verify-ownership", response_model=Dict)
async def verify_nft_ownership(
    request: NFTOwnershipVerificationRequest,
    orchestrator = Depends(get_nft_orchestrator)
):
    """
    Verify NFT ownership on a specific chain
    Used to confirm legitimate holders during transfer
    """
    try:
        # Get latest ownership record from history
        ownership_doc = await orchestrator.database["nft_ownership_history"].find_one(
            {"token_id": request.token_id},
            sort=[("timestamp", -1)]
        )
        
        if not ownership_doc:
            return {
                "verified": False,
                "error": "No ownership history found for this NFT",
                "token_id": request.token_id
            }
        
        # Check if claimed owner matches recorded owner
        ownership_match = (
            ownership_doc["owner_address"].lower() == request.claimed_owner.lower() and
            ownership_doc["chain"] == request.chain
        )
        
        return {
            "verified": ownership_match,
            "token_id": request.token_id,
            "recorded_owner": ownership_doc["owner_address"],
            "recorded_chain": ownership_doc["chain"],
            "claimed_owner": request.claimed_owner,
            "claimed_chain": request.chain,
            "last_transfer": ownership_doc["timestamp"].isoformat(),
            "last_action": ownership_doc["action"],
            "transaction_hash": ownership_doc["transaction_hash"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ownership verification error: {str(e)}")


@router.get("/nft/{token_id}/ownership-history", response_model=Dict)
async def get_nft_ownership_history(
    token_id: str,
    limit: int = Query(50, description="Number of ownership records to return"),
    orchestrator = Depends(get_nft_orchestrator)
):
    """Get complete ownership history for an NFT"""
    try:
        cursor = orchestrator.database["nft_ownership_history"].find(
            {"token_id": token_id}
        ).sort("timestamp", -1).limit(limit)
        
        history = await cursor.to_list(length=limit)
        
        if not history:
            raise HTTPException(status_code=404, detail="No ownership history found for this NFT")
        
        # Format history records
        formatted_history = []
        for record in history:
            formatted_history.append({
                "owner_address": record["owner_address"],
                "chain": record["chain"],
                "action": record["action"],
                "transaction_hash": record["transaction_hash"],
                "timestamp": record["timestamp"].isoformat(),
                "block_number": record.get("block_number")
            })
        
        return {
            "token_id": token_id,
            "current_owner": history[0]["owner_address"] if history else None,
            "current_chain": history[0]["chain"] if history else None,
            "total_transfers": len(history),
            "history": formatted_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ownership history error: {str(e)}")


# === ANALYTICS AND REPORTING ===

@router.get("/nft/analytics/dashboard", response_model=Dict)
async def get_nft_analytics_dashboard(
    orchestrator = Depends(get_nft_orchestrator)
):
    """Get NFT transfer analytics dashboard data"""
    try:
        # Get transfer statistics
        total_transfers = await orchestrator.database["nft_transfers"].count_documents({})
        active_transfers = await orchestrator.database["nft_transfers"].count_documents({
            "status": {"$in": ["minted", "escrowed", "in_transit"]}
        })
        completed_transfers = await orchestrator.database["nft_transfers"].count_documents({
            "status": "delivered"
        })
        failed_transfers = await orchestrator.database["nft_transfers"].count_documents({
            "status": "failed"
        })
        
        # Get escrow statistics
        total_escrows = await orchestrator.database["nft_escrows"].count_documents({})
        locked_escrows = await orchestrator.database["nft_escrows"].count_documents({
            "status": "locked"
        })
        released_escrows = await orchestrator.database["nft_escrows"].count_documents({
            "status": "released"
        })
        
        # Calculate escrow value
        escrow_pipeline = [
            {"$match": {"status": "locked"}},
            {"$group": {"_id": None, "total_value": {"$sum": "$purchase_amount"}}}
        ]
        escrow_value_result = await orchestrator.database["nft_escrows"].aggregate(escrow_pipeline).to_list(1)
        total_escrow_value = escrow_value_result[0]["total_value"] if escrow_value_result else 0
        
        # Get average transfer time for completed transfers
        completed_with_time = await orchestrator.database["nft_transfers"].find({
            "status": "delivered",
            "completed_at": {"$exists": True}
        }).to_list(100)
        
        transfer_times = []
        for transfer in completed_with_time:
            if "completed_at" in transfer and "created_at" in transfer:
                duration = (transfer["completed_at"] - transfer["created_at"]).total_seconds() / 3600  # hours
                transfer_times.append(duration)
        
        avg_transfer_time = sum(transfer_times) / len(transfer_times) if transfer_times else 0
        
        return {
            "total_transfers": total_transfers,
            "active_transfers": active_transfers,
            "completed_transfers": completed_transfers,
            "failed_transfers": failed_transfers,
            "completion_rate": (completed_transfers / max(1, total_transfers)) * 100,
            "failure_rate": (failed_transfers / max(1, total_transfers)) * 100,
            "total_escrows": total_escrows,
            "locked_escrows": locked_escrows,
            "released_escrows": released_escrows,
            "total_escrow_value_eth": total_escrow_value,
            "average_transfer_time_hours": round(avg_transfer_time, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


# === HEALTH CHECK ===

@router.get("/nft/health", response_model=Dict)
async def nft_health_check():
    """Health check for NFT transfer service"""
    try:
        # Test orchestrator initialization
        orchestrator = await get_nft_orchestrator()
        
        # Test database connection
        await orchestrator.database["nft_transfers"].find_one()
        
        return {
            "status": "healthy",
            "service": "NFT Transfer Orchestrator",
            "features": [
                "Cross-chain NFT transfers",
                "Escrow management",
                "Transporter chain routing",
                "Ownership verification",
                "Automatic delivery confirmation",
                "LayerZero integration"
            ],
            "supported_chains": list(orchestrator.nft_chains.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }