"""
Shipping API Routes
Handles all shipping-related operations for the comprehensive workflow
"""
import time
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.services.shipping_service import shipping_service

router = APIRouter()

# Pydantic models for request/response validation
class ShippingInfoRequest(BaseModel):
    name: str
    phone: str
    email: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    delivery_instructions: Optional[str] = ""
    signature_required: bool = True

class ShippingStartRequest(BaseModel):
    distance_miles: int

class TransporterAssignmentRequest(BaseModel):
    transporter_addresses: List[str]

class HandoffRequest(BaseModel):
    handoff_message: str

class DeliveryConfirmationRequest(BaseModel):
    qr_verification_data: Dict[str, Any]

@router.post("/shipping/collect-info/{purchase_id}")
async def collect_shipping_information(purchase_id: str, shipping_info: ShippingInfoRequest):
    """Collect shipping information from buyer during purchase process"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        # Convert Pydantic model to dict and add purchase_id
        shipping_data = shipping_info.dict()
        shipping_data["purchase_id"] = purchase_id
        
        result = await shipping_service.collect_shipping_information({
            "purchase_id": purchase_id,
            "buyer": shipping_data.get("email"),  # Use email as buyer identifier
            "shipping_info": shipping_data
        })
        
        if result["success"]:
            return {"success": True, "message": "Shipping information collected successfully", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect shipping information: {str(e)}")

@router.get("/shipping/manufacturer/{address}/requests")
async def get_manufacturer_shipping_requests(address: str):
    """Get shipping requests waiting for manufacturer to start shipping"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        requests = await shipping_service.get_manufacturer_shipping_requests(address)
        return {"success": True, "shipping_requests": requests, "count": len(requests)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shipping requests: {str(e)}")

@router.post("/shipping/start/{purchase_id}")
async def start_shipping_process(purchase_id: str, shipping_start: ShippingStartRequest, manufacturer_address: str):
    """Manufacturer starts shipping process with distance calculation"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        result = await shipping_service.start_shipping_process(
            manufacturer_address, 
            purchase_id, 
            shipping_start.distance_miles
        )
        
        if result["success"]:
            return {"success": True, "message": "Shipping process started successfully", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start shipping process: {str(e)}")

@router.post("/shipping/assign-transporters/{shipping_id}")
async def assign_transporters(shipping_id: str, assignment: TransporterAssignmentRequest):
    """Hub admin assigns transporters to shipping request"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        result = await shipping_service.assign_transporters(
            shipping_id, 
            assignment.transporter_addresses
        )
        
        if result["success"]:
            return {"success": True, "message": "Transporters assigned successfully", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign transporters: {str(e)}")

@router.post("/shipping/handoff/{shipping_id}")
async def process_transporter_handoff(shipping_id: str, current_transporter: str, handoff: HandoffRequest):
    """Process handoff between transporters"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        result = await shipping_service.process_transporter_handoff(
            current_transporter, 
            shipping_id, 
            handoff.handoff_message
        )
        
        if result["success"]:
            return {"success": True, "message": "Handoff processed successfully", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process handoff: {str(e)}")

@router.get("/shipping/transporter/{address}/assignments")
async def get_transporter_assignments(address: str):
    """Get transporter assignments for a specific address"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        # Query database for assignments
        assignments = await shipping_service.database.transporter_assignments.find({
            "transporter": address
        }).sort("assigned_at", -1).to_list(100)
        
        return {"success": True, "assignments": assignments, "count": len(assignments)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transporter assignments: {str(e)}")

@router.post("/shipping/confirm-delivery/{shipping_id}")
async def confirm_delivery(shipping_id: str, buyer_address: str, confirmation: DeliveryConfirmationRequest):
    """Buyer confirms delivery after QR verification"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        result = await shipping_service.confirm_delivery(
            buyer_address, 
            shipping_id, 
            confirmation.qr_verification_data
        )
        
        if result["success"]:
            return {"success": True, "message": "Delivery confirmed successfully", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to confirm delivery: {str(e)}")

@router.get("/shipping/status/{shipping_id}")
async def get_shipping_status(shipping_id: str):
    """Get detailed shipping status"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        # Get shipping record
        shipping_record = await shipping_service.database.shipping_records.find_one({
            "shipping_id": shipping_id
        })
        
        if not shipping_record:
            raise HTTPException(status_code=404, detail="Shipping record not found")
        
        # Get assignments
        assignments = await shipping_service.database.transporter_assignments.find({
            "shipping_id": shipping_id
        }).sort("stage_number", 1).to_list(100)
        
        # Get shipping request info
        shipping_request = await shipping_service.database.shipping_requests.find_one({
            "shipping_id": shipping_id
        })
        
        return {
            "success": True,
            "shipping_record": shipping_record,
            "assignments": assignments,
            "shipping_request": shipping_request,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shipping status: {str(e)}")

@router.get("/shipping/hub/pending-assignments")
async def get_hub_pending_assignments():
    """Get pending transporter assignments for Hub admin"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        # Get shipping records waiting for transporter assignment
        pending_records = await shipping_service.database.shipping_records.find({
            "status": "transporter_selection"
        }).sort("created_at", -1).to_list(100)
        
        return {"success": True, "pending_assignments": pending_records, "count": len(pending_records)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending assignments: {str(e)}")

@router.get("/shipping/analytics/overview")
async def get_shipping_analytics():
    """Get shipping analytics overview"""
    try:
        if shipping_service.database is None:
            await shipping_service.initialize()
        
        # Get various stats
        total_shipments = await shipping_service.database.shipping_records.count_documents({})
        pending_shipments = await shipping_service.database.shipping_records.count_documents({
            "status": {"$in": ["transporter_selection", "transporters_assigned", "in_transit"]}
        })
        completed_shipments = await shipping_service.database.shipping_records.count_documents({
            "status": "delivered"
        })
        
        # Get recent activity
        recent_shipments = await shipping_service.database.shipping_records.find({}).sort(
            "created_at", -1
        ).limit(10).to_list(10)
        
        return {
            "success": True,
            "analytics": {
                "total_shipments": total_shipments,
                "pending_shipments": pending_shipments,
                "completed_shipments": completed_shipments,
                "completion_rate": round((completed_shipments / max(total_shipments, 1)) * 100, 2)
            },
            "recent_activity": recent_shipments,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shipping analytics: {str(e)}")