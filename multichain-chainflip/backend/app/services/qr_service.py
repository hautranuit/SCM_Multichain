"""
Dynamic QR Code Service for ChainFLIP Multi-Chain
Handles encrypted QR code generation with AES encryption and HMAC verification
"""

import base64
import qrcode
import io
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend
import os
import secrets
import json
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QRCodeService:
    def __init__(self, aes_key: str, hmac_key: str):
        """
        Initialize QR Code service with encryption keys
        
        Args:
            aes_key: 64-character hex string for AES-256
            hmac_key: 64-character hex string for HMAC
        """
        if len(aes_key) != 64 or len(hmac_key) != 64:
            raise ValueError("AES and HMAC keys must be 64-character hex strings")
            
        self.aes_key = bytes.fromhex(aes_key)
        self.hmac_key = bytes.fromhex(hmac_key)
        
    def encrypt_data(self, plaintext: str) -> str:
        """
        Encrypt data using AES-256-CBC with random IV
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            String in format "iv:ciphertext" (both hex encoded)
        """
        try:
            iv = secrets.token_bytes(16)  # 16 bytes for AES-256-CBC
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            
            # Pad plaintext to multiple of 16 bytes (PKCS7 padding)
            plaintext_bytes = plaintext.encode('utf-8')
            padding_length = 16 - (len(plaintext_bytes) % 16)
            padded_plaintext = plaintext_bytes + bytes([padding_length] * padding_length)
            
            ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
            
            return f"{iv.hex()}:{ciphertext.hex()}"
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data encrypted with encrypt_data
        
        Args:
            encrypted_data: String in format "iv:ciphertext"
            
        Returns:
            Decrypted plaintext
        """
        try:
            iv_hex, ciphertext_hex = encrypted_data.split(':', 1)
            iv = bytes.fromhex(iv_hex)
            ciphertext = bytes.fromhex(ciphertext_hex)
            
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove PKCS7 padding
            padding_length = padded_plaintext[-1]
            plaintext = padded_plaintext[:-padding_length]
            
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def generate_hmac(self, data: str) -> str:
        """
        Generate HMAC for data integrity verification
        
        Args:
            data: Data to generate HMAC for
            
        Returns:
            HMAC as hex string
        """
        try:
            h = hmac.HMAC(self.hmac_key, hashes.SHA256(), backend=default_backend())
            h.update(data.encode('utf-8'))
            return h.finalize().hex()
        except Exception as e:
            logger.error(f"HMAC generation failed: {e}")
            raise
    
    def verify_hmac(self, data: str, expected_hmac: str) -> bool:
        """
        Verify HMAC for data integrity
        
        Args:
            data: Original data
            expected_hmac: Expected HMAC as hex string
            
        Returns:
            True if HMAC is valid
        """
        try:
            h = hmac.HMAC(self.hmac_key, hashes.SHA256(), backend=default_backend())
            h.update(data.encode('utf-8'))
            h.verify(bytes.fromhex(expected_hmac))
            return True
        except Exception as e:
            logger.warning(f"HMAC verification failed: {e}")
            return False
    
    def create_dynamic_qr_payload(self, token_id: int, cid: str, chain_id: int, 
                                  expiry_minutes: int = 60, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create dynamic QR code payload with encryption and metadata
        
        Args:
            token_id: NFT token ID
            cid: IPFS CID for product data
            chain_id: Blockchain chain ID
            expiry_minutes: QR code expiry time in minutes
            metadata: Additional metadata to include
            
        Returns:
            Dict containing encrypted payload and verification data
        """
        try:
            # Create base payload
            expiry_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
            
            payload_data = {
                "token_id": token_id,
                "cid": cid,
                "chain_id": chain_id,
                "generated_at": datetime.utcnow().isoformat(),
                "expires_at": expiry_time.isoformat(),
                "metadata": metadata or {}
            }
            
            # Convert to JSON string
            payload_json = json.dumps(payload_data, sort_keys=True)
            
            # Encrypt the payload
            encrypted_payload = self.encrypt_data(payload_json)
            
            # Generate HMAC for integrity
            payload_hmac = self.generate_hmac(encrypted_payload)
            
            # Final QR payload format: encrypted_data:hmac
            final_payload = f"{encrypted_payload}:{payload_hmac}"
            
            return {
                "encrypted_payload": final_payload,
                "token_id": token_id,
                "chain_id": chain_id,
                "expires_at": expiry_time.isoformat(),
                "payload_length": len(final_payload)
            }
            
        except Exception as e:
            logger.error(f"QR payload creation failed: {e}")
            raise
    
    def verify_and_decrypt_payload(self, encrypted_payload: str) -> Dict[str, Any]:
        """
        Verify and decrypt QR code payload
        
        Args:
            encrypted_payload: Full encrypted payload from QR code
            
        Returns:
            Decrypted payload data
            
        Raises:
            ValueError: If payload is invalid or expired
        """
        try:
            # Split encrypted data and HMAC
            if encrypted_payload.count(':') < 2:
                raise ValueError("Invalid payload format")
            
            # Last part is HMAC, everything before is encrypted data
            parts = encrypted_payload.split(':')
            hmac_value = parts[-1]
            encrypted_data = ':'.join(parts[:-1])
            
            # Verify HMAC
            if not self.verify_hmac(encrypted_data, hmac_value):
                raise ValueError("HMAC verification failed - payload may be tampered")
            
            # Decrypt data
            decrypted_json = self.decrypt_data(encrypted_data)
            payload_data = json.loads(decrypted_json)
            
            # Check expiry
            expiry_time = datetime.fromisoformat(payload_data['expires_at'])
            if datetime.utcnow() > expiry_time:
                raise ValueError("QR code has expired")
            
            return payload_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise ValueError("Invalid payload data format")
        except Exception as e:
            logger.error(f"Payload verification failed: {e}")
            raise
    
    def generate_qr_image(self, payload: str, size: int = 300) -> str:
        """
        Generate QR code image from payload
        
        Args:
            payload: Data to encode in QR code
            size: Image size in pixels
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize if needed
            if size != 300:
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return img_base64
            
        except Exception as e:
            logger.error(f"QR image generation failed: {e}")
            raise
    
    def create_dynamic_qr(self, token_id: int, cid: str, chain_id: int, 
                          expiry_minutes: int = 60, metadata: Optional[Dict] = None,
                          image_size: int = 300) -> Dict[str, Any]:
        """
        Create complete dynamic QR code with image
        
        Args:
            token_id: NFT token ID
            cid: IPFS CID for product data
            chain_id: Blockchain chain ID
            expiry_minutes: QR code expiry time in minutes
            metadata: Additional metadata to include
            image_size: QR code image size in pixels
            
        Returns:
            Dict containing QR data and base64 image
        """
        try:
            # Create encrypted payload
            qr_data = self.create_dynamic_qr_payload(
                token_id, cid, chain_id, expiry_minutes, metadata
            )
            
            # Generate QR image
            qr_image_base64 = self.generate_qr_image(
                qr_data["encrypted_payload"], image_size
            )
            
            return {
                **qr_data,
                "qr_image_base64": qr_image_base64,
                "image_size": image_size,
                "format": "PNG"
            }
            
        except Exception as e:
            logger.error(f"Dynamic QR creation failed: {e}")
            raise
    
    def validate_qr_scan(self, scanned_payload: str, expected_token_id: Optional[int] = None,
                          expected_chain_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate a scanned QR code payload
        
        Args:
            scanned_payload: Payload from scanned QR code
            expected_token_id: Expected token ID for validation
            expected_chain_id: Expected chain ID for validation
            
        Returns:
            Validation result with decrypted data
        """
        try:
            # Decrypt and verify payload
            payload_data = self.verify_and_decrypt_payload(scanned_payload)
            
            validation_result = {
                "valid": True,
                "payload_data": payload_data,
                "validation_errors": []
            }
            
            # Additional validations
            if expected_token_id is not None and payload_data.get("token_id") != expected_token_id:
                validation_result["validation_errors"].append("Token ID mismatch")
                validation_result["valid"] = False
            
            if expected_chain_id is not None and payload_data.get("chain_id") != expected_chain_id:
                validation_result["validation_errors"].append("Chain ID mismatch")
                validation_result["valid"] = False
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "payload_data": None,
                "validation_errors": [str(e)]
            }

    def generate_multi_chain_qr(self, token_id: int, chain_data: Dict[int, str], 
                                expiry_minutes: int = 60, metadata: Optional[Dict] = None,
                                image_size: int = 300) -> Dict[str, Any]:
        """
        Generate QR code for multi-chain token
        
        Args:
            token_id: NFT token ID
            chain_data: Dict mapping chain_id to CID
            expiry_minutes: QR code expiry time in minutes
            metadata: Additional metadata
            image_size: QR code image size
            
        Returns:
            Multi-chain QR code data
        """
        try:
            expiry_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
            
            payload_data = {
                "token_id": token_id,
                "type": "multi_chain",
                "chain_data": chain_data,
                "generated_at": datetime.utcnow().isoformat(),
                "expires_at": expiry_time.isoformat(),
                "metadata": metadata or {}
            }
            
            payload_json = json.dumps(payload_data, sort_keys=True)
            encrypted_payload = self.encrypt_data(payload_json)
            payload_hmac = self.generate_hmac(encrypted_payload)
            final_payload = f"{encrypted_payload}:{payload_hmac}"
            
            qr_image_base64 = self.generate_qr_image(final_payload, image_size)
            
            return {
                "encrypted_payload": final_payload,
                "token_id": token_id,
                "chain_count": len(chain_data),
                "expires_at": expiry_time.isoformat(),
                "qr_image_base64": qr_image_base64,
                "image_size": image_size,
                "format": "PNG"
            }
            
        except Exception as e:
            logger.error(f"Multi-chain QR creation failed: {e}")
            raise