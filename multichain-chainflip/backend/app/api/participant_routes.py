"""
Participant Management API Routes for ChainFLIP Multi-Chain
Handles role-based access control and participant registration
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from ..models.participant import (
    Participant, ParticipantCreate, ParticipantUpdate, ParticipantResponse,
    RoleVerificationRequest, RoleVerificationResponse, ParticipantRole, ParticipantStatus
)
from ..core.database import get_database
from ..core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/participants", tags=["Participants"])

settings = get_settings()

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

@router.post("/register", response_model=APIResponse)
async def register_participant(participant_data: ParticipantCreate):
    """
    Register a new participant with role verification
    """
    try:
        database = await get_database()
        
        # Check if wallet address already exists
        existing = await database.participants.find_one(
            {"wallet_address": participant_data.wallet_address}
        )
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Wallet address already registered"
            )
        
        # Validate role-specific requirements
        validation_result = await _validate_role_requirements(participant_data)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=validation_result["error"]
            )
        
        # Create participant
        participant = Participant(**participant_data.dict())
        
        # Auto-approve based on role and chain
        if participant_data.role == ParticipantRole.MANUFACTURER:
            if participant_data.chain_id == settings.base_sepolia_chain_id:
                # Manufacturers on Base Sepolia need manual approval
                participant.status = ParticipantStatus.PENDING
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Manufacturers can only register on Base Sepolia chain"
                )
        
        # Store in database
        result = await database.participants.insert_one(participant.dict())
        
        logger.info(f"Participant registered: {participant.wallet_address} as {participant.role}")
        
        return APIResponse(
            success=True,
            data={
                "participant_id": participant.id,
                "status": participant.status.value,
                "message": "Registration successful. Awaiting approval." if participant.status == ParticipantStatus.PENDING else "Registration approved."
            },
            message="Participant registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.get("/verify-role", response_model=RoleVerificationResponse)
async def verify_participant_role(
    wallet_address: str = Query(..., description="Wallet address to verify"),
    required_role: ParticipantRole = Query(..., description="Required role"),
    chain_id: Optional[int] = Query(None, description="Required chain ID")
):
    """
    Verify if a participant has the required role
    Critical for manufacturing access control
    """
    try:
        database = await get_database()
        
        # Find participant
        participant = await database.participants.find_one(
            {"wallet_address": wallet_address}
        )
        
        if not participant:
            return RoleVerificationResponse(
                wallet_address=wallet_address,
                has_role=False,
                participant_role=None,
                participant_status=None,
                chain_id=None,
                message="Participant not found"
            )
        
        # Check status
        if participant.get("status") != ParticipantStatus.ACTIVE.value:
            return RoleVerificationResponse(
                wallet_address=wallet_address,
                has_role=False,
                participant_role=ParticipantRole(participant.get("role")),
                participant_status=ParticipantStatus(participant.get("status")),
                chain_id=participant.get("chain_id"),
                message=f"Participant status is {participant.get('status')}"
            )
        
        # Check role
        has_required_role = participant.get("role") == required_role.value
        
        # Check chain ID if specified
        chain_match = True
        if chain_id is not None:
            chain_match = participant.get("chain_id") == chain_id
        
        # Special check for manufacturers on Base Sepolia
        if required_role == ParticipantRole.MANUFACTURER:
            if chain_id == settings.base_sepolia_chain_id:
                chain_match = participant.get("chain_id") == settings.base_sepolia_chain_id
            else:
                return RoleVerificationResponse(
                    wallet_address=wallet_address,
                    has_role=False,
                    participant_role=ParticipantRole(participant.get("role")),
                    participant_status=ParticipantStatus(participant.get("status")),
                    chain_id=participant.get("chain_id"),
                    message="Manufacturing only allowed on Base Sepolia chain"
                )
        
        has_role = has_required_role and chain_match
        
        # Update last activity
        if has_role:
            await database.participants.update_one(
                {"wallet_address": wallet_address},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
        
        return RoleVerificationResponse(
            wallet_address=wallet_address,
            has_role=has_role,
            participant_role=ParticipantRole(participant.get("role")),
            participant_status=ParticipantStatus(participant.get("status")),
            chain_id=participant.get("chain_id"),
            message="Role verified" if has_role else "Role verification failed"
        )
        
    except Exception as e:
        logger.error(f"Role verification error: {e}")
        raise HTTPException(status_code=500, detail=f"Role verification failed: {str(e)}")

@router.get("/", response_model=APIResponse)
async def get_participants(
    role: Optional[ParticipantRole] = Query(None, description="Filter by role"),
    status: Optional[ParticipantStatus] = Query(None, description="Filter by status"),
    chain_id: Optional[int] = Query(None, description="Filter by chain ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of participants to return")
):
    """
    Get list of participants with optional filters
    """
    try:
        database = await get_database()
        
        # Build filter
        filter_query = {}
        if role:
            filter_query["role"] = role.value
        if status:
            filter_query["status"] = status.value
        if chain_id:
            filter_query["chain_id"] = chain_id
        
        # Get participants
        cursor = database.participants.find(filter_query).limit(limit)
        participants = []
        
        async for participant in cursor:
            # Convert MongoDB document to response model
            participant["_id"] = str(participant["_id"])
            participant_response = ParticipantResponse(**participant)
            participants.append(participant_response.dict())
        
        return APIResponse(
            success=True,
            data={
                "participants": participants,
                "count": len(participants),
                "filters": {
                    "role": role.value if role else None,
                    "status": status.value if status else None,
                    "chain_id": chain_id
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Get participants error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get participants: {str(e)}")

@router.put("/{participant_id}/approve", response_model=APIResponse)
async def approve_participant(
    participant_id: str,
    approved_by: str = Query(..., description="Admin wallet address")
):
    """
    Approve a pending participant (admin only)
    """
    try:
        database = await get_database()
        
        # Find participant
        participant = await database.participants.find_one({"id": participant_id})
        if not participant:
            raise HTTPException(status_code=404, detail="Participant not found")
        
        # Update participant status
        result = await database.participants.update_one(
            {"id": participant_id},
            {
                "$set": {
                    "status": ParticipantStatus.ACTIVE.value,
                    "approved_by": approved_by,
                    "approved_date": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to approve participant")
        
        logger.info(f"Participant approved: {participant_id} by {approved_by}")
        
        return APIResponse(
            success=True,
            data={"participant_id": participant_id, "status": "active"},
            message="Participant approved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve participant error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve participant: {str(e)}")

@router.put("/{participant_id}", response_model=APIResponse)
async def update_participant(participant_id: str, update_data: ParticipantUpdate):
    """
    Update participant information
    """
    try:
        database = await get_database()
        
        # Find participant
        participant = await database.participants.find_one({"id": participant_id})
        if not participant:
            raise HTTPException(status_code=404, detail="Participant not found")
        
        # Prepare update data
        update_fields = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # Update participant
        result = await database.participants.update_one(
            {"id": participant_id},
            {"$set": update_fields}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to update participant")
        
        return APIResponse(
            success=True,
            data={"participant_id": participant_id, "updated_fields": list(update_fields.keys())},
            message="Participant updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update participant error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update participant: {str(e)}")

@router.get("/stats", response_model=APIResponse)
async def get_participant_stats():
    """
    Get participant statistics
    """
    try:
        database = await get_database()
        
        # Get counts by role
        role_stats = {}
        for role in ParticipantRole:
            count = await database.participants.count_documents({"role": role.value})
            role_stats[role.value] = count
        
        # Get counts by status
        status_stats = {}
        for status in ParticipantStatus:
            count = await database.participants.count_documents({"status": status.value})
            status_stats[status.value] = count
        
        # Get chain distribution
        chain_pipeline = [
            {"$group": {"_id": "$chain_id", "count": {"$sum": 1}}}
        ]
        chain_cursor = database.participants.aggregate(chain_pipeline)
        chain_stats = {}
        async for chain_data in chain_cursor:
            chain_stats[str(chain_data["_id"])] = chain_data["count"]
        
        total_participants = await database.participants.count_documents({})
        
        return APIResponse(
            success=True,
            data={
                "total_participants": total_participants,
                "by_role": role_stats,
                "by_status": status_stats,
                "by_chain": chain_stats
            }
        )
        
    except Exception as e:
        logger.error(f"Get participant stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

async def _validate_role_requirements(participant_data: ParticipantCreate) -> Dict[str, Any]:
    """
    Validate role-specific requirements
    """
    if participant_data.role == ParticipantRole.MANUFACTURER:
        if not participant_data.manufacturer_license:
            return {"valid": False, "error": "Manufacturing license required for manufacturer role"}
        if participant_data.chain_id != settings.base_sepolia_chain_id:
            return {"valid": False, "error": "Manufacturers must register on Base Sepolia chain"}
    
    elif participant_data.role == ParticipantRole.TRANSPORTER:
        if not participant_data.transport_license:
            return {"valid": False, "error": "Transport license required for transporter role"}
    
    elif participant_data.role == ParticipantRole.BUYER:
        if not participant_data.business_registration:
            return {"valid": False, "error": "Business registration required for buyer role"}
    
    return {"valid": True}
