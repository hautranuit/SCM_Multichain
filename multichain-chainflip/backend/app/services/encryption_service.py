"""
Simplified QR Code Encryption Service for SCM Multichain
Implements AES-256-CBC + HMAC + 32-byte random key
QR contains product's CID link for IPFS metadata access
"""
import os
import json
import hmac
import hashlib
import secrets
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import time

class EncryptionService:
    def __init__(self):
        # Initialize with 32-byte random key for AES-256
        self.aes_key = self._get_or_create_aes_key()
        self.hmac_key = self._get_or_create_hmac_key()
        
    def _get_or_create_aes_key(self) -> bytes:
        """Get or generate 32-byte AES-256 key and auto-update .env file"""
        key_env = os.environ.get('QR_AES_KEY')
        if key_env:
            try:
                return bytes.fromhex(key_env)
            except ValueError:
                print(f"⚠️ Invalid QR_AES_KEY format, generating new key...")
        
        # Generate 32-byte random key for AES-256
        key = secrets.token_bytes(32)
        key_hex = key.hex()
        print(f"⚠️ Generated new AES-256 key: {key_hex}")
        
        # Auto-update .env file
        self._update_env_file('QR_AES_KEY', key_hex)
        
        return key
    
    def _get_or_create_hmac_key(self) -> bytes:
        """Get or generate 32-byte HMAC key and auto-update .env file"""
        key_env = os.environ.get('QR_HMAC_KEY')
        if key_env:
            try:
                return bytes.fromhex(key_env)
            except ValueError:
                print(f"⚠️ Invalid QR_HMAC_KEY format, generating new key...")
        
        # Generate 32-byte random key for HMAC
        key = secrets.token_bytes(32)
        key_hex = key.hex()
        print(f"⚠️ Generated new HMAC key: {key_hex}")
        
        # Auto-update .env file
        self._update_env_file('QR_HMAC_KEY', key_hex)
        
        return key
    
    def _update_env_file(self, key_name: str, key_value: str):
        """Auto-update .env file with new key value"""
        try:
            env_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
            
            # Read current .env file
            env_lines = []
            key_found = False
            
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
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
            
            # Write back to .env file
            with open(env_file_path, 'w') as f:
                f.writelines(env_lines)
            
            # Update environment variable for current session
            os.environ[key_name] = key_value
            
            print(f"✅ Auto-updated .env file: {key_name}={key_value}")
            
        except Exception as e:
            print(f"⚠️ Failed to auto-update .env file: {e}")
            print(f"📝 Please manually add to .env file: {key_name}={key_value}")
    
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
            
            print(f"✅ QR data encrypted successfully (length: {len(encrypted_payload)})")
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
            
            print(f"✅ QR data decrypted successfully")
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
        Create simplified QR payload containing product's CID link
        This is the main QR data structure for the SCM system
        """
        
        qr_data = {
            # Core identification
            "token_id": token_id,
            "cid": metadata_cid,  # Main IPFS CID link for metadata
            
            # Product essentials  
            "product_id": product_data.get("uniqueProductID", ""),
            "name": product_data.get("name", ""),
            "manufacturer": product_data.get("manufacturerID", ""),
            
            # Blockchain info
            "blockchain": "zkEVM Cardona",
            "chain_id": 2442,
            
            # Verification
            "ipfs_url": f"https://w3s.link/ipfs/{metadata_cid}",
            "verify_url": f"https://chainflip.app/verify/{token_id}",
            
            # Metadata
            "generated_at": int(time.time()),
            "version": "2.0"
        }
        
        return qr_data

# Global encryption service instance
encryption_service = EncryptionService()
