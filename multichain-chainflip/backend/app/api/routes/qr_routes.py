"""
QR Code API Routes for ChainFLIP Multi-Chain
Dynamic QR code generation, scanning, and validation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
from app.services.qr_service import QRCodeService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize QR service with environment variables
def get_qr_service() -> QRCodeService:
    """Get QR service instance with environment keys"""
    aes_key = os.getenv("AES_SECRET_KEY")
    hmac_key = os.getenv("HMAC_SECRET_KEY")
    
    if not aes_key or not hmac_key:
        raise HTTPException(
            status_code=500, 
            detail="QR service encryption keys not configured"
        )
    
    return QRCodeService(aes_key, hmac_key)

# Pydantic models for request/response
class QRGenerateRequest(BaseModel):
    token_id: int
    cid: str
    chain_id: int
    expiry_minutes: Optional[int] = 60
    metadata: Optional[Dict[str, Any]] = None
    image_size: Optional[int] = 300

class MultiChainQRRequest(BaseModel):
    token_id: int
    chain_data: Dict[int, str]  # chain_id -> cid mapping
    expiry_minutes: Optional[int] = 60
    metadata: Optional[Dict[str, Any]] = None
    image_size: Optional[int] = 300

class QRScanRequest(BaseModel):
    encrypted_payload: str
    expected_token_id: Optional[int] = None
    expected_chain_id: Optional[int] = None

class QRRefreshRequest(BaseModel):
    old_payload: str
    new_expiry_minutes: Optional[int] = 60

@router.get("/health")
async def health_check():
    """Health check endpoint for QR service"""
    try:
        # Test service initialization
        qr_service = get_qr_service()
        return {
            "status": "healthy",
            "service": "QR Code Service",
            "encryption": "AES-256-CBC + HMAC-SHA256"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR service unhealthy: {str(e)}")

@router.post("/generate")
async def generate_qr_code(
    request: QRGenerateRequest,
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Generate encrypted QR code for single-chain token
    """
    try:
        qr_data = qr_service.create_dynamic_qr(
            token_id=request.token_id,
            cid=request.cid,
            chain_id=request.chain_id,
            expiry_minutes=request.expiry_minutes,
            metadata=request.metadata,
            image_size=request.image_size
        )
        
        return {
            "success": True,
            "qr_data": qr_data,
            "message": "QR code generated successfully"
        }
        
    except Exception as e:
        logger.error(f"QR generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate QR code: {str(e)}"
        )

@router.post("/generate-multi-chain")
async def generate_multi_chain_qr(
    request: MultiChainQRRequest,
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Generate encrypted QR code for multi-chain token
    """
    try:
        qr_data = qr_service.generate_multi_chain_qr(
            token_id=request.token_id,
            chain_data=request.chain_data,
            expiry_minutes=request.expiry_minutes,
            metadata=request.metadata,
            image_size=request.image_size
        )
        
        return {
            "success": True,
            "qr_data": qr_data,
            "message": "Multi-chain QR code generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Multi-chain QR generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate multi-chain QR code: {str(e)}"
        )

@router.post("/scan")
async def scan_qr_code(
    request: QRScanRequest,
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Scan and validate QR code payload
    """
    try:
        validation_result = qr_service.validate_qr_scan(
            scanned_payload=request.encrypted_payload,
            expected_token_id=request.expected_token_id,
            expected_chain_id=request.expected_chain_id
        )
        
        if validation_result["valid"]:
            return {
                "success": True,
                "valid": True,
                "payload_data": validation_result["payload_data"],
                "message": "QR code scanned and validated successfully"
            }
        else:
            return {
                "success": False,
                "valid": False,
                "validation_errors": validation_result["validation_errors"],
                "message": "QR code validation failed"
            }
        
    except Exception as e:
        logger.error(f"QR scan failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to scan QR code: {str(e)}"
        )

@router.post("/refresh")
async def refresh_qr_code(
    request: QRRefreshRequest,
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Refresh expired QR code with new expiry time
    """
    try:
        # First decrypt the old payload to get original data
        try:
            old_data = qr_service.verify_and_decrypt_payload(request.old_payload)
        except ValueError as e:
            if "expired" in str(e).lower():
                # If expired, we can still decrypt to get the original data
                # Split and decrypt without expiry check
                parts = request.old_payload.split(':')
                hmac_value = parts[-1]
                encrypted_data = ':'.join(parts[:-1])
                
                if not qr_service.verify_hmac(encrypted_data, hmac_value):
                    raise ValueError("HMAC verification failed")
                
                import json
                decrypted_json = qr_service.decrypt_data(encrypted_data)
                old_data = json.loads(decrypted_json)
            else:
                raise e
        
        # Generate new QR with updated expiry
        if old_data.get("type") == "multi_chain":
            # Multi-chain refresh
            qr_data = qr_service.generate_multi_chain_qr(
                token_id=old_data["token_id"],
                chain_data=old_data["chain_data"],
                expiry_minutes=request.new_expiry_minutes,
                metadata=old_data.get("metadata")
            )
        else:
            # Single-chain refresh
            qr_data = qr_service.create_dynamic_qr(
                token_id=old_data["token_id"],
                cid=old_data["cid"],
                chain_id=old_data["chain_id"],
                expiry_minutes=request.new_expiry_minutes,
                metadata=old_data.get("metadata")
            )
        
        return {
            "success": True,
            "qr_data": qr_data,
            "message": "QR code refreshed successfully",
            "original_expiry": old_data.get("expires_at"),
            "new_expiry": qr_data["expires_at"]
        }
        
    except Exception as e:
        logger.error(f"QR refresh failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to refresh QR code: {str(e)}"
        )

@router.get("/verify/{encrypted_payload}")
async def verify_qr_payload(
    encrypted_payload: str,
    qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Quick verification endpoint for QR payload (GET request)
    """
    try:
        payload_data = qr_service.verify_and_decrypt_payload(encrypted_payload)
        
        return {
            "valid": True,
            "token_id": payload_data.get("token_id"),
            "chain_id": payload_data.get("chain_id"),
            "type": payload_data.get("type", "single_chain"),
            "expires_at": payload_data.get("expires_at"),
            "generated_at": payload_data.get("generated_at")
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

@router.get("/info")
async def get_qr_service_info():
    """
    Get information about QR service capabilities
    """
    return {
        "service": "ChainFLIP Dynamic QR Code Service",
        "version": "2.0.0",
        "features": [
            "AES-256-CBC encryption",
            "HMAC-SHA256 integrity verification",
            "Dynamic expiry management",
            "Multi-chain support",
            "Base64 image generation",
            "Payload validation"
        ],
        "supported_endpoints": [
            "POST /api/qr/generate - Generate single-chain QR",
            "POST /api/qr/generate-multi-chain - Generate multi-chain QR",
            "POST /api/qr/scan - Scan and validate QR",
            "POST /api/qr/refresh - Refresh expired QR",
            "GET /api/qr/verify/{payload} - Quick payload verification",
            "GET /api/qr/health - Service health check"
        ],
        "encryption": {
            "algorithm": "AES-256-CBC",
            "key_size": "256 bits",
            "iv_size": "128 bits",
            "integrity": "HMAC-SHA256"
        }
    }