"""
Participants API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.services.blockchain_service import BlockchainService

router = APIRouter()

class ParticipantQuery(BaseModel):
    participant_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = 10
    offset: int = 0

# Dependencies
async def get_blockchain_service():
    service = BlockchainService()
    await service.initialize()
    return service

@router.get("/")
async def get_participants(
    participant_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get participants with optional filtering"""
    try:
        # Build query filters
        filters = {}
        if participant_type:
            filters["participant_type"] = participant_type
        if status:
            filters["status"] = status
        
        # Get participants from database
        cursor = blockchain_service.database.participants.find(filters).skip(offset).limit(limit)
        participants = []
        async for participant in cursor:
            participant["_id"] = str(participant["_id"])
            participants.append(participant)
        
        # Get total count
        total_count = await blockchain_service.database.participants.count_documents(filters)
        
        return {
            "participants": participants,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{address}")
async def get_participant_details(
    address: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get detailed participant information"""
    try:
        participant = await blockchain_service.database.participants.find_one({"address": address})
        if not participant:
            raise HTTPException(status_code=404, detail="Participant not found")
        
        participant["_id"] = str(participant["_id"])
        return participant
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/statistics/overview")
async def get_participant_statistics(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get participant statistics overview"""
    try:
        # Total participants
        total_participants = await blockchain_service.database.participants.count_documents({})
        
        # Participants by type
        type_stats = {}
        types = ["manufacturer", "transporter", "buyer", "retailer"]
        for ptype in types:
            count = await blockchain_service.database.participants.count_documents({"participant_type": ptype})
            type_stats[ptype] = count
        
        # Active participants (have products)
        pipeline = [
            {"$group": {"_id": "$manufacturer", "count": {"$sum": 1}}},
            {"$count": "active_manufacturers"}
        ]
        active_manufacturers = []
        async for result in blockchain_service.database.products.aggregate(pipeline):
            active_manufacturers.append(result)
        
        return {
            "total_participants": total_participants,
            "by_type": type_stats,
            "active_manufacturers": len(active_manufacturers) if active_manufacturers else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))