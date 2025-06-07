"""
Simplified QR Routes for SCM Multichain
Uses single AES-256-CBC + HMAC encryption method with CID links
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)
router = APIRouter()

class QRDecryptRequest(BaseModel):
    encrypted_payload: str

class QRGenerateRequest(BaseModel):
    token_id: str
    metadata_cid: str
    product_data: Dict[str, Any]

@router.get("/health")
async def health_check():
    """Health check endpoint for QR service"""
    return {
        "status": "healthy",
        "service": "Simplified QR Code Service",
        "encryption": "AES-256-CBC + HMAC-SHA256",
        "features": ["CID-based QR codes", "32-byte random keys", "Product verification"]
    }

@router.post("/decrypt")
async def decrypt_qr_code(request: QRDecryptRequest):
    """
    Decrypt QR code payload to reveal CID link and product info
    """
    try:
        decrypted_data = encryption_service.decrypt_qr_data(request.encrypted_payload)
        
        return {
            "success": True,
            "data": decrypted_data,
            "message": "QR code decrypted successfully"
        }
        
    except Exception as e:
        logger.error(f"QR decryption failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to decrypt QR code: {str(e)}"
        )

@router.post("/generate")
async def generate_qr_code(request: QRGenerateRequest):
    """
    Generate encrypted QR code with CID link (primarily for testing)
    """
    try:
        qr_payload = encryption_service.create_qr_payload(
            token_id=request.token_id,
            metadata_cid=request.metadata_cid,
            product_data=request.product_data
        )
        
        encrypted_qr = encryption_service.encrypt_qr_data(qr_payload)
        qr_hash = encryption_service.generate_qr_hash(qr_payload)
        
        return {
            "success": True,
            "encrypted_qr_code": encrypted_qr,
            "qr_hash": qr_hash,
            "cid_url": f"https://w3s.link/ipfs/{request.metadata_cid}",
            "message": "QR code generated successfully"
        }
        
    except Exception as e:
        logger.error(f"QR generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate QR code: {str(e)}"
        )

@router.get("/info")
async def get_qr_service_info():
    """
    Get information about simplified QR service
    """
    return {
        "service": "ChainFLIP Simplified QR Code Service",
        "version": "2.0.0",
        "description": "Single encryption method with CID-based verification",
        "features": [
            "AES-256-CBC encryption",
            "HMAC-SHA256 integrity verification", 
            "32-byte random keys",
            "CID-based product links",
            "IPFS metadata access"
        ],
        "endpoints": [
            "POST /api/qr/decrypt - Decrypt QR payload",
            "POST /api/qr/generate - Generate QR (testing)",
            "GET /api/qr/health - Service health check",
            "GET /api/qr/info - Service information"
        ],
        "encryption": {
            "algorithm": "AES-256-CBC",
            "key_size": "256 bits (32 bytes)",
            "iv_size": "128 bits (16 bytes)", 
            "integrity": "HMAC-SHA256"
        }
    }