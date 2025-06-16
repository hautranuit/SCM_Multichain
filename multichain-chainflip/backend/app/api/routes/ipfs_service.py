"""
IPFS Service API Routes
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json
import base64
import subprocess
import tempfile
import os
from pathlib import Path
from datetime import datetime

from app.services.ipfs_service import ipfs_service

router = APIRouter()

class FileUploadRequest(BaseModel):
    fileData: str
    filename: str
    mimeType: Optional[str] = None

@router.post("/upload")
async def upload_to_ipfs(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """Upload file to IPFS via Web3.Storage"""
    try:
        # Read file content
        content = await file.read()
        
        # Create data structure for upload
        file_data = {
            "filename": file.filename,
            "content": base64.b64encode(content).decode('utf-8'),
            "content_type": file.content_type,
            "size": len(content),
            "metadata": json.loads(metadata) if metadata else {}
        }
        
        # Upload to IPFS
        cid = await ipfs_service.upload_to_ipfs(file_data)
        
        return {
            "success": True,
            "cid": cid,
            "filename": file.filename,
            "size": len(content),
            "ipfsUrl": f"{ipfs_service.ipfs_gateway}{cid}",
            "metadata": file_data["metadata"]
        }
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-file")
async def upload_file_to_ipfs(request: FileUploadRequest):
    """Upload file data to IPFS via Web3.Storage with proper MIME type handling"""
    try:
        print(f"📁 Uploading file: {request.filename}")
        
        # Remove data URL prefix if present and decode base64
        file_data = request.fileData
        if file_data.startswith('data:'):
            # Extract base64 part
            file_data = file_data.split(',')[1]
        
        # Decode base64 content
        try:
            file_content = base64.b64decode(file_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 data: {e}")
        
        # Detect MIME type if not provided
        mime_type = request.mimeType
        if not mime_type:
            extension = request.filename.lower().split('.')[-1]
            mime_types = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'mp4': 'video/mp4',
                'webm': 'video/webm',
                'avi': 'video/avi',
                'mov': 'video/quicktime'
            }
            mime_type = mime_types.get(extension, 'application/octet-stream')
        
        print(f"📄 File details: {request.filename} ({mime_type}, {len(file_content)} bytes)")
        
        # Upload file directly to W3Storage using Node.js script
        cid = await upload_binary_to_w3storage(file_content, request.filename, mime_type)
        
        if not cid:
            raise HTTPException(status_code=500, detail="Failed to upload to IPFS")
        
        ipfs_url = f"{ipfs_service.ipfs_gateway}{cid}"
        print(f"✅ File uploaded successfully: {ipfs_url}")
        
        return {
            "success": True,
            "cid": cid,
            "filename": request.filename,
            "mimeType": mime_type,
            "ipfsUrl": ipfs_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def upload_binary_to_w3storage(file_content: bytes, filename: str, mime_type: str) -> Optional[str]:
    """Upload binary file directly to W3Storage using file-based credentials"""
    try:
        # Create temporary file for the binary content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Create temporary files for credentials to avoid environment variable corruption
        with tempfile.NamedTemporaryFile(mode='w', suffix='.token', delete=False) as token_file:
            token_file.write(ipfs_service.w3storage_token)
            token_file_path = token_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.proof', delete=False) as proof_file:
            proof_file.write(ipfs_service.w3storage_proof)
            proof_file_path = proof_file.name
        
        try:
            # Find the W3Storage upload script
            script_path = Path(__file__).parent.parent.parent.parent / "w3storage_upload.mjs"
            
            if not script_path.exists():
                print(f"❌ W3Storage script not found at: {script_path}")
                return None
            
            # Set environment variables with credential file paths
            env = os.environ.copy()
            env['W3STORAGE_TOKEN_FILE'] = token_file_path
            env['W3STORAGE_PROOF_FILE'] = proof_file_path
            
            # Run Node.js script
            result = subprocess.run([
                'node', str(script_path), temp_file_path, filename
            ], 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            env=env,
            timeout=60
            )
            
            if result.returncode == 0:
                try:
                    stdout_clean = result.stdout.strip()
                    if stdout_clean:
                        response = json.loads(stdout_clean)
                        if response.get('success'):
                            cid = response.get('cid')
                            print(f"✅ Binary file uploaded to W3Storage: {cid}")
                            return cid
                        else:
                            print(f"❌ W3Storage upload failed: {response.get('error')}")
                            return None
                    else:
                        print(f"❌ Empty response from W3Storage script")
                        return None
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse W3Storage response: {e}")
                    print(f"Raw output: {result.stdout}")
                    return None
            else:
                print(f"❌ W3Storage script failed: {result.stderr}")
                return None
                
        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_file_path)
                os.unlink(token_file_path)
                os.unlink(proof_file_path)
            except OSError:
                pass
                
    except Exception as e:
        print(f"❌ Binary upload error: {e}")
        return None

@router.get("/{cid}")
async def get_from_ipfs(cid: str):
    """Retrieve content from IPFS"""
    try:
        return {
            "cid": cid,
            "gateway_url": f"{ipfs_service.ipfs_gateway}{cid}",
            "status": "available"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/qr/generate")
async def generate_encrypted_qr(
    product_id: str,
    metadata_cid: str,
    qr_data: Dict[str, Any]
):
    """Generate encrypted QR code for product with IPFS metadata reference"""
    try:
        # Enhanced QR data with IPFS reference
        enhanced_qr_data = {
            "product_id": product_id,
            "metadata_cid": metadata_cid,
            "timestamp": datetime.utcnow().isoformat(),
            "qr_version": "2.0",
            **qr_data
        }
        
        # This will integrate with the existing QR generation system
        # For now, return the structure - the actual encryption will be handled by the QR service
        return {
            "success": True,
            "product_id": product_id,
            "metadata_cid": metadata_cid,
            "qr_data": enhanced_qr_data,
            "ipfs_url": f"{ipfs_service.ipfs_gateway}{metadata_cid}",
            "message": "QR data prepared for encryption and generation"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/qr/scan-and-decrypt")
async def scan_and_decrypt_qr(
    encrypted_qr_data: str,
    user_type: str  # "transporter" or "buyer"
):
    """Decrypt QR code data and return appropriate information based on user type"""
    try:
        # This will integrate with the existing QR decryption system
        # For now, mock the decryption process
        
        # In real implementation, this would decrypt the QR data
        # and extract the metadata_cid to fetch current product info
        
        if user_type == "transporter":
            return {
                "success": True,
                "user_type": "transporter",
                "product_id": "extracted_from_qr",
                "current_metadata_cid": "extracted_from_qr",
                "permissions": ["update_location", "view_shipping_history"],
                "next_action": "Use /transporter/location-update endpoint"
            }
        elif user_type == "buyer":
            return {
                "success": True,
                "user_type": "buyer", 
                "product_id": "extracted_from_qr",
                "current_metadata_cid": "extracted_from_qr",
                "permissions": ["view_product_info", "confirm_receipt"],
                "next_action": "Use /buyer/product-info endpoint"
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid user type")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
