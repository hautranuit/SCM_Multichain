"""
W3Storage IPFS Service - Updated for ChainFLIP Multi-Chain
Uses Mock Upload when W3Storage credentials are not available
"""
import json
import httpx
import os
import subprocess
import tempfile
import base64
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
from app.core.config import get_settings

settings = get_settings()

class IPFSService:
    def __init__(self):
        # W3Storage configuration
        self.w3storage_token = settings.w3storage_token
        self.w3storage_proof = settings.w3storage_proof
        self.ipfs_gateway = settings.ipfs_gateway
        
        # Path to Node.js upload script
        self.script_path = Path(__file__).parent.parent.parent / "w3storage_upload.mjs"
        
        # Initialize and show credential status
        self._initialize_w3storage()
        
    def _initialize_w3storage(self):
        """Initialize W3Storage service and show credential status"""
        print(f"🔧 IPFS Service initialized")
        
        # Check W3Storage credentials
        has_token = bool(self.w3storage_token and self.w3storage_token.strip())
        has_proof = bool(self.w3storage_proof and self.w3storage_proof.strip())
        
        print(f"   W3Storage Token: {'✅' if has_token else '❌'}")
        print(f"   W3Storage Proof: {'✅' if has_proof else '❌'}")
        print(f"   Script path: {self.script_path}")
        
        if not has_token or not has_proof:
            print(f"❌ W3Storage credentials missing")
            print(f"💡 Please check your .env file for W3STORAGE_TOKEN and W3STORAGE_PROOF")
            print(f"🚨 WARNING: Product creation will FAIL without valid credentials")
        else:
            print(f"✅ W3Storage credentials loaded")
            # Quick validation of proof format
            if has_proof:
                proof_len = len(self.w3storage_proof)
                if proof_len < 100:
                    print(f"⚠️ Warning: W3Storage proof seems too short ({proof_len} chars)")
                elif "Unexpected end of data" in str(self.w3storage_proof):
                    print(f"⚠️ Warning: W3Storage proof may be corrupted")
                else:
                    print(f"✅ W3Storage proof appears valid ({proof_len} chars)")
            
        print(f"🌐 IPFS Gateway: {self.ipfs_gateway}")
        
        # Check if Node.js script exists
        if not self.script_path.exists():
            print(f"❌ ERROR: W3Storage upload script not found at {self.script_path}")
            print(f"🚨 WARNING: Product creation will FAIL without upload script")
        else:
            print(f"✅ W3Storage upload script found")
        
    async def upload_to_ipfs(self, data: Dict[str, Any]) -> str:
        """Upload data to IPFS using W3Storage - FAIL if upload fails"""
        try:
            print(f"📦 Uploading to IPFS...")
            
            # Convert data to JSON
            json_data = json.dumps(data, indent=2)
            print(f"📄 Content Size: {len(json_data)} bytes")
            
            # Check if W3Storage is properly configured
            if not self.w3storage_token or not self.w3storage_proof:
                raise Exception("W3Storage credentials are missing. Please check your .env file for W3STORAGE_TOKEN and W3STORAGE_PROOF")
            
            if not self.script_path.exists():
                raise Exception(f"W3Storage upload script not found at {self.script_path}")
            
            # Try W3Storage upload - NO FALLBACK TO MOCK
            cid = await self._upload_via_nodejs(data)
            if cid:
                print(f"✅ W3Storage Upload Success - CID: {cid}")
                print(f"🔗 IPFS URL: {self.ipfs_gateway}{cid}")
                
                # Test accessibility
                await self._test_cid_accessibility(cid)
                return cid
            else:
                raise Exception("W3Storage upload failed - check your credentials and network connection")
            
        except Exception as e:
            print(f"❌ IPFS Upload Failed: {e}")
            print(f"🚨 CRITICAL: Product creation will fail because IPFS upload is required")
            print(f"💡 To fix: Check your W3Storage credentials and network connection")
            raise Exception(f"IPFS Upload Failed: {str(e)}")
    
    async def _mock_upload(self, data: Dict[str, Any]) -> str:
        """Generate a mock CID for testing purposes"""
        try:
            # Create a consistent hash-based CID for the data
            json_str = json.dumps(data, sort_keys=True)
            hash_object = hashlib.sha256(json_str.encode())
            hex_dig = hash_object.hexdigest()
            
            # Create a mock CID that looks realistic
            mock_cid = f"bafybei{hex_dig[:46]}"
            
            print(f"📦 Mock Upload - Generated CID: {mock_cid}")
            print(f"🔗 Mock IPFS URL: {self.ipfs_gateway}{mock_cid}")
            print(f"ℹ️ This is a mock upload for testing purposes")
            
            return mock_cid
            
        except Exception as e:
            print(f"❌ Mock upload failed: {e}")
            # Fallback to a simple static CID
            return "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"
    
    async def _upload_via_nodejs(self, data: Dict[str, Any]) -> Optional[str]:
        """Upload to W3Storage using Node.js w3up client with improved credential handling"""
        try:
            # Create temporary file with JSON data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(data, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            # Create temporary files for credentials to avoid environment variable corruption
            with tempfile.NamedTemporaryFile(mode='w', suffix='.token', delete=False) as token_file:
                token_file.write(self.w3storage_token)
                token_file_path = token_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.proof', delete=False) as proof_file:
                proof_file.write(self.w3storage_proof)
                proof_file_path = proof_file.name
            
            try:
                # Set minimal environment - pass credential file paths instead of content
                env = os.environ.copy()
                env['W3STORAGE_TOKEN_FILE'] = token_file_path
                env['W3STORAGE_PROOF_FILE'] = proof_file_path
                
                # Run Node.js script with credential file paths
                result = subprocess.run([
                    'node', str(self.script_path), temp_file_path, 'metadata.json'
                ], 
                capture_output=True, 
                text=True, 
                encoding='utf-8',  # Explicitly use UTF-8 encoding
                errors='replace',  # Replace any problematic characters
                env=env,
                timeout=60  # 60 second timeout
                )
                
                # Log both stdout and stderr for debugging
                if result.stderr:
                    print(f"🔍 Node.js stderr: {result.stderr}")
                
                if result.returncode == 0:
                    # Parse the JSON output - the script should output clean JSON to stdout
                    try:
                        stdout_clean = result.stdout.strip()
                        if stdout_clean:
                            response = json.loads(stdout_clean)
                            if response.get('success'):
                                cid = response.get('cid')
                                print(f"✅ Node.js W3Storage upload success: {cid}")
                                return cid
                            else:
                                error_msg = response.get('error', 'Unknown error')
                                raise Exception(f"W3Storage upload failed: {error_msg}")
                        else:
                            raise Exception("W3Storage script returned empty output")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse W3Storage response as JSON: {e}")
                        print(f"📄 Raw stdout: {result.stdout}")
                        print(f"📄 Raw stderr: {result.stderr}")
                        raise Exception(f"Failed to parse W3Storage response: {e}. Raw output: {result.stdout}")
                else:
                    error_output = result.stderr if result.stderr else "Unknown error"
                    print(f"❌ W3Storage script failed with return code {result.returncode}")
                    print(f"📄 stderr: {error_output}")
                    print(f"📄 stdout: {result.stdout}")
                    
                    # Check for common error patterns
                    if "Unexpected end of data" in error_output:
                        raise Exception("W3Storage credentials appear to be corrupted during transfer. Using file-based credential passing to avoid corruption.")
                    elif "ENOTFOUND" in error_output or "network" in error_output.lower():
                        raise Exception("Network error connecting to W3Storage. Check your internet connection")
                    else:
                        raise Exception(f"W3Storage script failed: {error_output}")
                    
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_file_path)
                    os.unlink(token_file_path)
                    os.unlink(proof_file_path)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            raise Exception("W3Storage script timed out after 60 seconds")
        except Exception as e:
            raise Exception(f"Error running W3Storage script: {e}")
    
    async def _test_cid_accessibility(self, cid: str):
        """Test if CID is accessible via IPFS gateways"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                test_url = f"{self.ipfs_gateway}{cid}"
                response = await client.head(test_url)
                
                if response.status_code == 200:
                    print(f"✅ CID accessible at: {test_url}")
                else:
                    print(f"⚠️ CID not yet accessible: {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️ CID accessibility test failed: {e}")
    
    async def get_from_ipfs(self, cid: str) -> Dict[str, Any]:
        """Retrieve data from IPFS using CID"""
        try:
            # If it's a mock CID, return mock data
            if cid.startswith("bafybei") and len(cid) == 59:
                return {
                    "cid": cid,
                    "status": "mock_retrieval",
                    "message": f"Mock IPFS data for CID: {cid}",
                    "data": {
                        "mock": True,
                        "cid": cid,
                        "timestamp": "2024-12-19T13:00:00Z"
                    }
                }
            
            # Try IPFS gateways
            gateways = [
                f"https://ipfs.io/ipfs/{cid}",
                f"https://cloudflare-ipfs.com/ipfs/{cid}",
                f"https://gateway.pinata.cloud/ipfs/{cid}",
                f"https://dweb.link/ipfs/{cid}"
            ]
            
            for gateway_url in gateways:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.get(gateway_url)
                        
                        if response.status_code == 200:
                            data = response.json()
                            print(f"✅ IPFS Retrieval Success from {gateway_url}")
                            return data
                        else:
                            continue
                            
                except Exception as gateway_error:
                    print(f"⚠️ Gateway {gateway_url} error: {gateway_error}")
                    continue
            
            return {
                "cid": cid,
                "status": "retrieval_failed",
                "message": f"Unable to retrieve data from IPFS CID: {cid}"
            }
            
        except Exception as e:
            print(f"❌ IPFS Retrieval Error: {e}")
            return {"cid": cid, "status": "error", "message": f"IPFS retrieval failed: {e}"}

# Global IPFS service instance
ipfs_service = IPFSService()