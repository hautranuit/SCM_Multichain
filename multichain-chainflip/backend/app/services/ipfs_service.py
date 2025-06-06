"""
W3Storage IPFS Service - Updated for ChainFLIP Multi-Chain
Uses Node.js w3up client via subprocess for reliable W3Storage uploads
"""
import json
import httpx
import os
import subprocess
import tempfile
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
        self.script_path = Path(__file__).parent.parent / "w3storage_upload.mjs"
        
        # Initialize and show credential status
        self._initialize_w3storage()
        
    def _initialize_w3storage(self):
        """Initialize W3Storage service and show credential status"""
        print(f"🔧 IPFS Service initialized with W3Storage")
        print(f"   Token present: {'✅' if self.w3storage_token else '❌'}")
        print(f"   Proof present: {'✅' if self.w3storage_proof else '❌'}")
        print(f"   Script path: {self.script_path}")
        
        if not self.w3storage_token:
            print(f"⚠️ WARNING: W3STORAGE_TOKEN not found in environment variables")
        else:
            print(f"✅ W3Storage token loaded (length: {len(self.w3storage_token)})")
            
        if not self.w3storage_proof:
            print(f"⚠️ WARNING: W3STORAGE_PROOF not found in environment variables")
        else:
            print(f"✅ W3Storage proof loaded (length: {len(self.w3storage_proof)})")
            
        print(f"🌐 IPFS Gateway: {self.ipfs_gateway}")
        
        # Check if Node.js script exists
        if not self.script_path.exists():
            print(f"⚠️ WARNING: W3Storage upload script not found at {self.script_path}")
        else:
            print(f"✅ W3Storage upload script found")
        
    async def upload_to_ipfs(self, data: Dict[str, Any]) -> str:
        """Upload data to IPFS using W3Storage via Node.js script"""
        try:
            print(f"📦 Uploading to IPFS via W3Storage...")
            
            # Convert data to JSON
            json_data = json.dumps(data, indent=2)
            
            # Only try W3Storage upload
            if not self.w3storage_token:
                raise Exception("W3Storage token not available")
            
            if not self.script_path.exists():
                raise Exception(f"W3Storage upload script not found at {self.script_path}")
            
            cid = await self._upload_via_nodejs(data)
            if cid:
                print(f"✅ W3Storage Upload Success - CID: {cid}")
                print(f"🔗 IPFS URL: {self.ipfs_gateway}{cid}")
                print(f"📄 Content Size: {len(json_data)} bytes")
                
                # Test accessibility
                await self._test_cid_accessibility(cid)
                return cid
            else:
                raise Exception("W3Storage upload failed - no CID returned")
            
        except Exception as e:
            print(f"❌ IPFS Upload Failed: {e}")
            raise Exception(f"IPFS upload failed: {e}")
    
    async def _upload_via_nodejs(self, data: Dict[str, Any]) -> Optional[str]:
        """Upload to W3Storage using Node.js w3up client"""
        try:
            # Create temporary file with JSON data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(data, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            try:
                # Set environment variables for the Node.js script
                env = os.environ.copy()
                env['W3STORAGE_TOKEN'] = self.w3storage_token
                env['W3STORAGE_PROOF'] = self.w3storage_proof
                
                # Run Node.js script
                result = subprocess.run([
                    'node', str(self.script_path), temp_file_path, 'metadata.json'
                ], 
                capture_output=True, 
                text=True, 
                env=env,
                timeout=60  # 60 second timeout
                )
                
                if result.returncode == 0:
                    # Parse the JSON output
                    try:
                        output_lines = result.stdout.strip().split('\n')
                        # Find the JSON output (last line usually)
                        json_output = None
                        for line in reversed(output_lines):
                            if line.strip().startswith('{'):
                                json_output = line.strip()
                                break
                        
                        if json_output:
                            response = json.loads(json_output)
                            if response.get('success'):
                                cid = response.get('cid')
                                print(f"✅ Node.js W3Storage upload success: {cid}")
                                return cid
                            else:
                                error_msg = response.get('error', 'Unknown error')
                                print(f"❌ Node.js W3Storage upload failed: {error_msg}")
                                return None
                        else:
                            print(f"❌ Could not parse Node.js output: {result.stdout}")
                            return None
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse Node.js response: {e}")
                        print(f"Raw output: {result.stdout}")
                        return None
                else:
                    print(f"❌ Node.js script failed with return code {result.returncode}")
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            print(f"❌ Node.js script timed out after 60 seconds")
            return None
        except Exception as e:
            print(f"❌ Error running Node.js script: {e}")
            return None
    
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
