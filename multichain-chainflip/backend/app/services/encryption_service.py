"""
Encryption Service for QR Code Data
Implements AES-256 encryption with HMAC verification
"""
import os
import json
import hmac
import hashlib
import secrets
from typing import Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class EncryptionService:
    def __init__(self):
        # Get or generate encryption key
        self.encryption_key = self._get_or_create_key()
        
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or generate new one"""
        key_env = os.environ.get('QR_ENCRYPTION_KEY')
        if key_env:
            return base64.urlsafe_b64decode(key_env.encode())
        else:
            # Generate new key for demo
            key = Fernet.generate_key()
            print(f"⚠️ Generated new encryption key: {base64.urlsafe_b64encode(key).decode()}")
            print("📝 Add this to your .env file as QR_ENCRYPTION_KEY")
            return key
    
    def encrypt_qr_data(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Encrypt QR data using AES-256 + HMAC
        Returns: (encrypted_payload, qr_hash)
        """
        try:
            # Convert data to JSON
            json_data = json.dumps(data, separators=(',', ':'))
            
            # Create Fernet cipher
            cipher = Fernet(self.encryption_key)
            
            # Encrypt the data
            encrypted_data = cipher.encrypt(json_data.encode())
            
            # Create HMAC for integrity verification
            hmac_key = self.encryption_key[:32]  # Use first 32 bytes for HMAC
            qr_hash = hmac.new(
                hmac_key,
                encrypted_data,
                hashlib.sha256
            ).hexdigest()
            
            # Encode encrypted data as base64 for transport
            encrypted_payload = base64.urlsafe_b64encode(encrypted_data).decode()
            
            return encrypted_payload, qr_hash
            
        except Exception as e:
            raise Exception(f"QR encryption failed: {e}")
    
    def decrypt_qr_data(self, encrypted_payload: str, qr_hash: str) -> Dict[str, Any]:
        """Decrypt and verify QR data"""
        try:
            # Decode from base64
            encrypted_data = base64.urlsafe_b64decode(encrypted_payload.encode())
            
            # Verify HMAC
            hmac_key = self.encryption_key[:32]
            expected_hash = hmac.new(
                hmac_key,
                encrypted_data,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_hash, qr_hash):
                raise Exception("QR code integrity verification failed")
            
            # Decrypt the data
            cipher = Fernet(self.encryption_key)
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Parse JSON
            data = json.loads(decrypted_data.decode())
            
            return data
            
        except Exception as e:
            raise Exception(f"QR decryption failed: {e}")
    
    def generate_qr_hash(self, data: Dict[str, Any]) -> str:
        """Generate a hash for QR data without encryption"""
        try:
            # Convert data to JSON
            json_data = json.dumps(data, separators=(',', ':'), sort_keys=True)
            
            # Create hash
            hash_value = hashlib.sha256(json_data.encode()).hexdigest()
            
            return hash_value
            
        except Exception as e:
            raise Exception(f"QR hash generation failed: {e}")
    
    def generate_qr_payload(self, token_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate QR code payload with all necessary information"""
        import time
        
        qr_data = {
            "token_id": token_id,
            "product_id": product_data.get("uniqueProductID", ""),
            "batch_number": product_data.get("batchNumber", ""),
            "manufacturer": product_data.get("manufacturerID", ""),
            "product_type": product_data.get("productType", ""),
            "manufacturing_date": product_data.get("manufacturingDate", ""),
            "expiration_date": product_data.get("expirationDate", ""),
            "blockchain": "polygon",
            "chain_id": "80002",  # Polygon Amoy testnet
            "verification_url": f"https://chainflip.app/verify/{token_id}",
            "timestamp": int(time.time()),
            "version": "1.0"
        }
        
        return qr_data

# Global encryption service instance
encryption_service = EncryptionService()
