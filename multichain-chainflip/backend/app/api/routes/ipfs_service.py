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
    """Upload binary file directly to W3Storage"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Find the W3Storage upload script
            script_path = Path(__file__).parent.parent.parent.parent / "w3storage_upload.mjs"
            
            if not script_path.exists():
                print(f"❌ W3Storage script not found at: {script_path}")
                return None
            
            # Set environment variables
            env = os.environ.copy()
            env['W3STORAGE_TOKEN'] = ipfs_service.w3storage_token
            env['W3STORAGE_PROOF'] = ipfs_service.w3storage_proof
            
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
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
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
    metadata: Dict[str, Any]
):
    """Generate encrypted QR code for product"""
    try:
        # This will integrate with the existing QR generation system
        return {
            "success": True,
            "product_id": product_id,
            "qr_code_url": f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "qr_hash": "0x1234567890abcdef",
            "encrypted_data_cid": "bafkreiqrstuvwxyz0987654321"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/qr/decrypt")
async def decrypt_qr_data(
    qr_hash: str,
    private_key: str
):
    """Decrypt QR code data"""
    try:
        # This will integrate with the existing QR decryption system
        return {
            "success": True,
            "decrypted_data": {
                "product_id": "12345",
                "timestamp": "2024-01-01T00:00:00Z",
                "location": "Manufacturing Plant A"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
