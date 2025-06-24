"""
Enhanced QR Code Encryption Service for SCM Multichain
Generates fresh encryption keys on each startup for new products
Each product stores the session keys used to create it
"""
import os
import json
import hmac
import hashlib
import secrets
from typing import Dict, Any, Tuple, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import time

class EncryptionService:
    def __init__(self):
        print("🔑 Initializing Enhanced Encryption Service with Product-Specific Keys...")
        
        # Generate default session keys (used as fallback)
        self.session_aes_key = secrets.token_bytes(32)
        self.session_hmac_key = secrets.token_bytes(32)
        
        # Current active keys (used for fallback)
        self.aes_key = self.session_aes_key
        self.hmac_key = self.session_hmac_key
        
        # Convert to hex for storage
        self.session_keys = {
            "aes_key": self.session_aes_key.hex(),
            "hmac_key": self.session_hmac_key.hex(),
            "generated_at": int(time.time()),
            "session_id": secrets.token_hex(16)
        }
        
        print(f"✅ Fresh session keys generated:")
        print(f"   Session ID: {self.session_keys['session_id']}")
        print(f"   AES Key: {self.session_keys['aes_key'][:32]}...")
        print(f"   HMAC Key: {self.session_keys['hmac_key'][:32]}...")
        
        # Update .env file with current session keys (for reference)
        self._update_env_file('QR_AES_KEY', self.session_keys['aes_key'])
        self._update_env_file('QR_HMAC_KEY', self.session_keys['hmac_key'])
        self._update_env_file('SESSION_ID', self.session_keys['session_id'])
        
    def generate_product_specific_keys(self, product_id: str, manufacturer: str) -> Dict[str, str]:
        """
        Generate unique encryption keys for each product during NFT minting
        This ensures each product has its own encryption keys for QR code security
        """
        try:
            print(f"🔑 Generating product-specific encryption keys for Product ID: {product_id}")
            
            # Create a unique seed based on product data and timestamp
            seed_data = f"{product_id}-{manufacturer}-{int(time.time())}-{secrets.token_hex(16)}"
            seed_hash = hashlib.sha256(seed_data.encode()).digest()
            
            # Generate unique AES and HMAC keys for this product
            product_aes_key = secrets.token_bytes(32)
            product_hmac_key = secrets.token_bytes(32)
            
            # Create unique session ID for this product
            product_session_id = hashlib.sha256(f"PRODUCT-{product_id}-{manufacturer}".encode()).hexdigest()[:16]
            
            # Store the product-specific keys
            product_keys = {
                "aes_key": product_aes_key.hex(),
                "hmac_key": product_hmac_key.hex(),
                "generated_at": int(time.time()),
                "session_id": product_session_id,
                "product_id": product_id,
                "manufacturer": manufacturer,
                "key_type": "product_specific"
            }
            
            print(f"✅ Product-specific keys generated:")
            print(f"   Product ID: {product_id}")
            print(f"   Session ID: {product_session_id}")
            print(f"   AES Key: {product_keys['aes_key'][:32]}...")
            print(f"   HMAC Key: {product_keys['hmac_key'][:32]}...")
            
            return product_keys
            
        except Exception as e:
            print(f"❌ Failed to generate product-specific keys: {e}")
            raise Exception(f"Product key generation failed: {e}")
    
    def encrypt_qr_data_with_product_keys(self, data: Dict[str, Any], product_keys: Dict[str, str]) -> str:
        """
        Encrypt QR data using specific product keys
        """
        try:
            # Temporarily set the product keys
            original_aes = self.aes_key
            original_hmac = self.hmac_key
            
            # Set the product-specific keys
            self.aes_key = bytes.fromhex(product_keys["aes_key"])
            self.hmac_key = bytes.fromhex(product_keys["hmac_key"])
            
            print(f"🔐 Encrypting QR data with product-specific keys (Session: {product_keys.get('session_id', 'unknown')})")
            
            # Encrypt the data
            encrypted_payload = self.encrypt_qr_data(data)
            
            # Restore original keys
            self.aes_key = original_aes
            self.hmac_key = original_hmac
            
            print(f"✅ QR data encrypted successfully with product-specific keys")
            return encrypted_payload
            
        except Exception as e:
            # Restore original keys in case of error
            self.aes_key = original_aes
            self.hmac_key = original_hmac
            raise Exception(f"QR encryption with product keys failed: {e}")
    
    def create_product_qr_payload(self, token_id: str, metadata_cid: str, product_data: Dict[str, Any], product_keys: Dict[str, str]) -> Dict[str, Any]:
        """
        Create QR payload with product-specific session information
        """
        
        # ✅ DEBUG: Log incoming product data
        print(f"🔍 DEBUG Product QR Creation:")
        print(f" Token ID: {token_id}")
        print(f" Product Data Keys: {list(product_data.keys())}")
        print(f" BatchNumber in data: {product_data.get('batchNumber', 'MISSING')}")
        print(f" ProductType in data: {product_data.get('productType', 'MISSING')}")
        print(f" Category in data: {product_data.get('category', 'MISSING')}")
        print(f" ManufacturingDate in data: {product_data.get('manufacturingDate', 'MISSING')}")
        
        qr_data = {
            # Core identification
            "token_id": token_id,
            "cid": metadata_cid,  # Main IPFS CID link for metadata
            
            # Product essentials  
            "product_id": product_data.get("uniqueProductID", ""),
            "name": product_data.get("name", ""),
            "manufacturer": product_data.get("manufacturerID", ""),
            
            # ✅ SECURITY FIX: Include all important verification fields
            "batchNumber": product_data.get("batchNumber", ""),
            "productType": product_data.get("productType", ""),
            "category": product_data.get("category", ""),
            "manufacturingDate": product_data.get("manufacturingDate", ""),
            "expirationDate": product_data.get("expirationDate", ""),
            "location": product_data.get("location", ""),
            
            # Blockchain info
            "blockchain": "Base Sepolia",
            "chain_id": 84532,
            
            # Verification
            "ipfs_url": f"https://w3s.link/ipfs/{metadata_cid}",
            "verify_url": f"https://chainflip.app/verify/{token_id}",
            
            # Product-specific session info
            "session_id": product_keys["session_id"],
            "key_type": "product_specific",
            
            # Metadata
            "generated_at": int(time.time()),
            "version": "3.0"  # Updated version for product-specific keys
        }
        
        # ✅ DEBUG: Log final QR data
        print(f"🔍 DEBUG Final Product QR Keys: {list(qr_data.keys())}")
        print(f" BatchNumber in QR: {qr_data.get('batchNumber', 'MISSING')}")
        print(f" ProductType in QR: {qr_data.get('productType', 'MISSING')}")
        print(f" Category in QR: {qr_data.get('category', 'MISSING')}")
        print(f" ManufacturingDate in QR: {qr_data.get('manufacturingDate', 'MISSING')}")
        
        return qr_data
        """Get the current session keys for storing with new products"""
        return self.session_keys.copy()
    
    def set_keys_for_verification(self, product_keys: Dict[str, str]):
        """Set specific keys for verification of a specific product"""
        self.aes_key = bytes.fromhex(product_keys["aes_key"])
        self.hmac_key = bytes.fromhex(product_keys["hmac_key"])
        print(f"🔑 Using stored keys from session: {product_keys.get('session_id', 'unknown')}")
    
    def reset_to_session_keys(self):
        """Reset to current session keys"""
        self.aes_key = self.session_aes_key
        self.hmac_key = self.session_hmac_key
        print(f"🔑 Reset to current session keys")
    
    def get_current_session_keys(self):
        """Get the current session keys for storing with new products"""
        return self.session_keys.copy()
    
    def _update_env_file(self, key_name: str, key_value: str):
        """Update .env file with current session keys for reference using atomic write"""
        try:
            import tempfile
            import shutil
            
            # Try multiple possible .env file locations
            possible_env_paths = [
                os.path.join(os.path.dirname(__file__), '..', '..', '.env'),
                os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'),
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.getcwd(), 'backend', '.env')
            ]
            
            env_file_path = None
            for path in possible_env_paths:
                if os.path.exists(path):
                    env_file_path = path
                    break
            
            if not env_file_path:
                # Create .env file in the most likely location
                env_file_path = possible_env_paths[0]
                os.makedirs(os.path.dirname(env_file_path), exist_ok=True)
                print(f"📝 Creating new .env file: {env_file_path}")
            
            # Read current .env file
            env_lines = []
            key_found = False
            
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    env_lines = f.readlines()
                
                # Update existing key or mark if not found
                for i, line in enumerate(env_lines):
                    if line.strip().startswith(f'{key_name}='):
                        env_lines[i] = f'{key_name}={key_value}\n'
                        key_found = True
                        break
            
            # Add new key if not found
            if not key_found:
                env_lines.append(f'{key_name}={key_value}\n')
            
            # Use atomic write with temporary file to prevent corruption
            env_dir = os.path.dirname(env_file_path)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                           dir=env_dir, delete=False) as temp_file:
                temp_file.writelines(env_lines)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Force write to disk
                temp_file_path = temp_file.name
            
            # Atomic move - this is the crucial part that prevents corruption
            if os.name == 'nt':  # Windows
                # On Windows, we need to remove the target first
                if os.path.exists(env_file_path):
                    os.replace(temp_file_path, env_file_path)
                else:
                    shutil.move(temp_file_path, env_file_path)
            else:  # Unix/Linux
                os.replace(temp_file_path, env_file_path)
            
            # Update environment variable for current session
            os.environ[key_name] = key_value
            
        except Exception as e:
            print(f"⚠️ Failed to update .env file: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except:
                pass
    
    def encrypt_qr_data_for_product(self, data: Dict[str, Any]) -> Tuple[str, Dict[str, str]]:
        """
        Encrypt QR data using current session keys and return both encrypted data and keys used
        """
        try:
            # Use current session keys
            encrypted_payload = self.encrypt_qr_data(data)
            
            # Return both encrypted data and the keys used
            return encrypted_payload, self.get_current_session_keys()
            
        except Exception as e:
            raise Exception(f"QR encryption for product failed: {e}")
    
    def decrypt_qr_data_with_stored_keys(self, encrypted_payload: str, stored_keys: Dict[str, str]) -> Dict[str, Any]:
        """
        Decrypt QR data using keys stored with the product
        """
        try:
            # Temporarily set the stored keys
            original_aes = self.aes_key
            original_hmac = self.hmac_key
            
            # Set the stored keys
            self.aes_key = bytes.fromhex(stored_keys["aes_key"])
            self.hmac_key = bytes.fromhex(stored_keys["hmac_key"])
            
            print(f"🔓 Decrypting with stored session keys (Session: {stored_keys.get('session_id', 'unknown')})")
            
            # Decrypt the data
            decrypted_data = self.decrypt_qr_data(encrypted_payload)
            
            # Restore original keys
            self.aes_key = original_aes
            self.hmac_key = original_hmac
            
            print(f"✅ QR data decrypted successfully with stored keys")
            return decrypted_data
            
        except Exception as e:
            # Restore original keys in case of error
            self.aes_key = original_aes
            self.hmac_key = original_hmac
            raise Exception(f"QR decryption with stored keys failed: {e}")
    
    def encrypt_qr_data(self, data: Dict[str, Any]) -> str:
        """
        Encrypt QR data using AES-256-CBC + HMAC
        Returns: encrypted_payload (base64 encoded)
        """
        try:
            # Convert data to JSON
            json_data = json.dumps(data, separators=(',', ':'))
            
            # Generate random 16-byte IV for AES-256-CBC
            iv = secrets.token_bytes(16)
            
            # Pad data to 16-byte boundary (PKCS7 padding)
            plaintext_bytes = json_data.encode('utf-8')
            padding_length = 16 - (len(plaintext_bytes) % 16)
            padded_plaintext = plaintext_bytes + bytes([padding_length] * padding_length)
            
            # Encrypt using AES-256-CBC
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
            
            # Create HMAC for integrity verification
            combined_data = iv + ciphertext
            hmac_signature = hmac.new(
                self.hmac_key,
                combined_data,
                hashlib.sha256
            ).digest()
            
            # Combine IV + ciphertext + HMAC
            final_payload = iv + ciphertext + hmac_signature
            
            # Encode as base64 for QR code
            encrypted_payload = base64.urlsafe_b64encode(final_payload).decode('ascii')
            
            return encrypted_payload
            
        except Exception as e:
            raise Exception(f"QR encryption failed: {e}")
    
    def decrypt_qr_data(self, encrypted_payload: str) -> Dict[str, Any]:
        """Decrypt and verify QR data"""
        try:
            # Decode from base64
            payload_bytes = base64.urlsafe_b64decode(encrypted_payload.encode('ascii'))
            
            # Extract components: IV (16) + ciphertext + HMAC (32)
            if len(payload_bytes) < 48:  # Minimum: 16 (IV) + 16 (min ciphertext) + 32 (HMAC)
                raise Exception("Invalid payload length")
            
            iv = payload_bytes[:16]
            hmac_signature = payload_bytes[-32:]
            ciphertext = payload_bytes[16:-32]
            
            # Verify HMAC
            combined_data = iv + ciphertext
            expected_hmac = hmac.new(
                self.hmac_key,
                combined_data,
                hashlib.sha256
            ).digest()
            
            if not hmac.compare_digest(expected_hmac, hmac_signature):
                raise Exception("QR code integrity verification failed")
            
            # Decrypt using AES-256-CBC
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove PKCS7 padding
            padding_length = padded_plaintext[-1]
            plaintext = padded_plaintext[:-padding_length]
            
            # Parse JSON
            data = json.loads(plaintext.decode('utf-8'))
            
            return data
            
        except Exception as e:
            raise Exception(f"QR decryption failed: {e}")
    
    def generate_qr_hash(self, data: Dict[str, Any]) -> str:
        """Generate a simple hash for QR data identification"""
        try:
            json_data = json.dumps(data, separators=(',', ':'), sort_keys=True)
            hash_value = hashlib.sha256(json_data.encode()).hexdigest()
            return hash_value[:16]  # First 16 characters for shorter hash
        except Exception as e:
            raise Exception(f"QR hash generation failed: {e}")
    
    def create_qr_payload(self, token_id: str, metadata_cid: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive QR payload containing all verification fields
        This includes all important fields needed for Algorithm 4 verification
        """
        
        # ✅ DEBUG: Log incoming product data
        print(f"🔍 DEBUG QR Creation:")
        print(f" Token ID: {token_id}")
        print(f" Product Data Keys: {list(product_data.keys())}")
        print(f" BatchNumber in data: {product_data.get('batchNumber', 'MISSING')}")
        print(f" ProductType in data: {product_data.get('productType', 'MISSING')}")
        print(f" Category in data: {product_data.get('category', 'MISSING')}")
        print(f" ManufacturingDate in data: {product_data.get('manufacturingDate', 'MISSING')}")
        
        qr_data = {
            # Core identification
            "token_id": token_id,
            "cid": metadata_cid,  # Main IPFS CID link for metadata
            
            # Product essentials  
            "product_id": product_data.get("uniqueProductID", ""),
            "name": product_data.get("name", ""),
            "manufacturer": product_data.get("manufacturerID", ""),
            
            # ✅ SECURITY FIX: Include all important verification fields
            "batchNumber": product_data.get("batchNumber", ""),
            "productType": product_data.get("productType", ""),
            "category": product_data.get("category", ""),
            "manufacturingDate": product_data.get("manufacturingDate", ""),
            "expirationDate": product_data.get("expirationDate", ""),
            "location": product_data.get("location", ""),
            
            # Blockchain info
            "blockchain": "Base Sepolia",
            "chain_id": 84532,
            
            # Verification
            "ipfs_url": f"https://w3s.link/ipfs/{metadata_cid}",
            "verify_url": f"https://chainflip.app/verify/{token_id}",
            
            # Session info
            "session_id": self.session_keys["session_id"],
            "key_type": "product_specific",
            
            # Metadata
            "generated_at": int(time.time()),
            "version": "3.0"  # Updated version to indicate comprehensive data
        }
        
        # ✅ DEBUG: Log final QR data
        print(f"🔍 DEBUG Final QR Keys: {list(qr_data.keys())}")
        print(f" BatchNumber in QR: {qr_data.get('batchNumber', 'MISSING')}")
        print(f" ProductType in QR: {qr_data.get('productType', 'MISSING')}")
        print(f" Category in QR: {qr_data.get('category', 'MISSING')}")
        print(f" ManufacturingDate in QR: {qr_data.get('manufacturingDate', 'MISSING')}")
        
        return qr_data

# Global encryption service instance
encryption_service = EncryptionService()
