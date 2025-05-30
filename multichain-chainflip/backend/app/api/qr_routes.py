"""
QR Code API Routes for ChainFLIP Multi-Chain
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from ..services.qr_service import QRCodeService
from ..services.blockchain_service import BlockchainService
from ..core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/qr", tags=["QR Codes"])

settings = get_settings()

# Initialize QR service
qr_service = QRCodeService(
    aes_key=settings.aes_secret_key,
    hmac_key=settings.hmac_secret_key
)

# Pydantic models
class QRGenerationRequest(BaseModel):
    token_id: int = Field(..., description="NFT Token ID")
    chain_id: int = Field(..., description="Blockchain Chain ID")
    expiry_minutes: int = Field(default=60, ge=1, le=1440, description="QR expiry time in minutes")
    image_size: int = Field(default=300, ge=100, le=1000, description="QR image size in pixels")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class MultiChainQRRequest(BaseModel):
    token_id: int = Field(..., description="NFT Token ID")
    chain_data: Dict[int, str] = Field(..., description="Mapping of chain_id to CID")
    expiry_minutes: int = Field(default=60, ge=1, le=1440, description="QR expiry time in minutes")
    image_size: int = Field(default=300, ge=100, le=1000, description="QR image size in pixels")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class QRScanRequest(BaseModel):
    payload: str = Field(..., description="Scanned QR payload")
    expected_token_id: Optional[int] = Field(default=None, description="Expected token ID for validation")
    expected_chain_id: Optional[int] = Field(default=None, description="Expected chain ID for validation")

class QRResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/generate", response_model=QRResponse)
async def generate_qr_code(request: QRGenerationRequest):
    """
    Generate dynamic encrypted QR code for a token
    """
    try:
        # Get blockchain service to fetch CID
        blockchain_service = BlockchainService()
        
        # Get token CID from blockchain
        try:
            cid = await blockchain_service.get_token_cid(request.token_id, request.chain_id)
            if not cid:
                raise HTTPException(status_code=404, detail="Token CID not found on blockchain")
        except Exception as e:
            logger.error(f"Failed to fetch CID for token {request.token_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch token data from blockchain")
        
        # Generate QR code
        qr_data = qr_service.create_dynamic_qr(
            token_id=request.token_id,
            cid=cid,
            chain_id=request.chain_id,
            expiry_minutes=request.expiry_minutes,
            metadata=request.metadata,
            image_size=request.image_size
        )
        
        return QRResponse(success=True, data=qr_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QR generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"QR generation failed: {str(e)}")

@router.post("/generate-multi-chain", response_model=QRResponse)
async def generate_multi_chain_qr(request: MultiChainQRRequest):
    """
    Generate multi-chain QR code for a token across multiple chains
    """
    try:
        # Validate chain data
        if not request.chain_data:
            raise HTTPException(status_code=400, detail="Chain data cannot be empty")
        
        # Generate multi-chain QR code
        qr_data = qr_service.generate_multi_chain_qr(
            token_id=request.token_id,
            chain_data=request.chain_data,
            expiry_minutes=request.expiry_minutes,
            metadata=request.metadata,
            image_size=request.image_size
        )
        
        return QRResponse(success=True, data=qr_data)
        
    except Exception as e:
        logger.error(f"Multi-chain QR generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-chain QR generation failed: {str(e)}")

@router.post("/scan", response_model=QRResponse)
async def scan_qr_code(request: QRScanRequest):
    """
    Scan and validate QR code payload
    """
    try:
        # Validate scanned payload
        validation_result = qr_service.validate_qr_scan(
            scanned_payload=request.payload,
            expected_token_id=request.expected_token_id,
            expected_chain_id=request.expected_chain_id
        )
        
        if not validation_result["valid"]:
            return QRResponse(
                success=False, 
                error=f"QR validation failed: {', '.join(validation_result['validation_errors'])}"
            )
        
        return QRResponse(success=True, data=validation_result["payload_data"])
        
    except Exception as e:
        logger.error(f"QR scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"QR scan failed: {str(e)}")

@router.get("/token/{token_id}/generate", response_model=QRResponse)
async def generate_qr_for_token(
    token_id: int,
    chain_id: int = Query(..., description="Blockchain Chain ID"),
    expiry_minutes: int = Query(default=60, ge=1, le=1440, description="QR expiry time in minutes"),
    image_size: int = Query(default=300, ge=100, le=1000, description="QR image size in pixels")
):
    """
    Generate QR code for a specific token (GET endpoint for convenience)
    """
    try:
        # Create request object
        request = QRGenerationRequest(
            token_id=token_id,
            chain_id=chain_id,
            expiry_minutes=expiry_minutes,
            image_size=image_size
        )
        
        # Use the existing POST endpoint logic
        return await generate_qr_code(request)
        
    except Exception as e:
        logger.error(f"QR generation failed for token {token_id}: {e}")
        raise HTTPException(status_code=500, detail=f"QR generation failed: {str(e)}")

@router.post("/refresh", response_model=QRResponse)
async def refresh_qr_code(request: QRGenerationRequest):
    """
    Refresh an existing QR code with new expiry
    """
    try:
        # Add refresh metadata
        refresh_metadata = request.metadata or {}
        refresh_metadata.update({
            "refreshed_at": datetime.utcnow().isoformat(),
            "type": "refresh"
        })
        
        request.metadata = refresh_metadata
        
        # Generate new QR code
        return await generate_qr_code(request)
        
    except Exception as e:
        logger.error(f"QR refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"QR refresh failed: {str(e)}")

@router.get("/validate/{payload}", response_model=QRResponse)
async def quick_validate_qr(payload: str):
    """
    Quick validation of QR payload (GET endpoint)
    """
    try:
        validation_result = qr_service.validate_qr_scan(payload)
        
        if not validation_result["valid"]:
            return QRResponse(
                success=False, 
                error=f"QR validation failed: {', '.join(validation_result['validation_errors'])}"
            )
        
        return QRResponse(success=True, data=validation_result["payload_data"])
        
    except Exception as e:
        logger.error(f"QR quick validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"QR validation failed: {str(e)}")

@router.get("/health")
async def qr_service_health():
    """
    Health check for QR service
    """
    try:
        # Test encryption/decryption
        test_data = "test_payload"
        encrypted = qr_service.encrypt_data(test_data)
        decrypted = qr_service.decrypt_data(encrypted)
        
        if decrypted != test_data:
            raise Exception("Encryption/decryption test failed")
        
        # Test HMAC
        test_hmac = qr_service.generate_hmac(test_data)
        hmac_valid = qr_service.verify_hmac(test_data, test_hmac)
        
        if not hmac_valid:
            raise Exception("HMAC test failed")
        
        return {
            "status": "healthy",
            "service": "QR Code Service",
            "encryption": "working",
            "hmac": "working",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"QR service health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"QR service unhealthy: {str(e)}")

@router.get("/stats")
async def qr_service_stats():
    """
    Get QR service statistics and capabilities
    """
    return {
        "service": "ChainFLIP Dynamic QR Code Service",
        "version": "1.0.0",
        "features": [
            "AES-256-CBC encryption",
            "HMAC-SHA256 integrity verification", 
            "Dynamic expiry times",
            "Multi-chain support",
            "Base64 image generation",
            "Payload validation"
        ],
        "supported_chains": [
            "Polygon PoS (Amoy Testnet)",
            "L2 CDK (Cardona Testnet)"
        ],
        "max_expiry_minutes": 1440,
        "max_image_size": 1000,
        "encryption_algorithm": "AES-256-CBC",
        "integrity_algorithm": "HMAC-SHA256"
    }