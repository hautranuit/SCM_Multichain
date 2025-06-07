#!/usr/bin/env python3
"""
QR Code Scanner and Decryptor for SCM Multichain
Demonstrates how to scan and decrypt QR codes containing CID links
"""

import sys
import os
import json
import requests

# Add the backend directory to the Python path
sys.path.append('/app/backend')

from app.services.encryption_service import encryption_service

def decrypt_qr_code(encrypted_payload):
    """
    Decrypt a QR code payload to reveal product information and CID link
    """
    try:
        print("🔓 Decrypting QR code...")
        print(f"📱 Encrypted payload length: {len(encrypted_payload)}")
        print(f"📱 Encrypted payload preview: {encrypted_payload[:50]}...")
        print()
        
        # Decrypt the QR code
        decrypted_data = encryption_service.decrypt_qr_data(encrypted_payload)
        
        print("✅ QR Code decrypted successfully!")
        print("=" * 60)
        print("📦 PRODUCT INFORMATION:")
        print("=" * 60)
        
        # Display key information
        print(f"🆔 Token ID: {decrypted_data.get('token_id', 'N/A')}")
        print(f"📦 Product ID: {decrypted_data.get('product_id', 'N/A')}")
        print(f"📝 Product Name: {decrypted_data.get('name', 'N/A')}")
        print(f"🏭 Manufacturer: {decrypted_data.get('manufacturer', 'N/A')}")
        print(f"🔗 Blockchain: {decrypted_data.get('blockchain', 'N/A')}")
        print(f"⛓️ Chain ID: {decrypted_data.get('chain_id', 'N/A')}")
        print()
        
        print("=" * 60)
        print("🔗 IPFS & VERIFICATION LINKS:")
        print("=" * 60)
        print(f"📁 Metadata CID: {decrypted_data.get('cid', 'N/A')}")
        print(f"🌐 IPFS URL: {decrypted_data.get('ipfs_url', 'N/A')}")
        print(f"✅ Verify URL: {decrypted_data.get('verify_url', 'N/A')}")
        print()
        
        print("=" * 60)
        print("⏰ METADATA:")
        print("=" * 60)
        print(f"📅 Generated: {decrypted_data.get('generated_at', 'N/A')}")
        print(f"📋 Version: {decrypted_data.get('version', 'N/A')}")
        print()
        
        return decrypted_data
        
    except Exception as e:
        print(f"❌ Failed to decrypt QR code: {e}")
        return None

def fetch_metadata_from_ipfs(cid):
    """
    Fetch full product metadata from IPFS using the CID from QR code
    """
    try:
        ipfs_url = f"https://w3s.link/ipfs/{cid}"
        print(f"🌐 Fetching metadata from IPFS: {ipfs_url}")
        
        response = requests.get(ipfs_url, timeout=10)
        response.raise_for_status()
        
        metadata = response.json()
        
        print("✅ Metadata fetched successfully!")
        print("=" * 60)
        print("📋 FULL PRODUCT METADATA:")
        print("=" * 60)
        print(json.dumps(metadata, indent=2))
        
        return metadata
        
    except Exception as e:
        print(f"❌ Failed to fetch metadata from IPFS: {e}")
        return None

def scan_and_verify_product(encrypted_qr_payload):
    """
    Complete QR scanning workflow: decrypt QR → fetch metadata → verify
    """
    print("🔍 Starting QR Code Scanning and Verification Process")
    print("=" * 80)
    print()
    
    # Step 1: Decrypt QR code
    qr_data = decrypt_qr_code(encrypted_qr_payload)
    if not qr_data:
        return None
    
    # Step 2: Fetch full metadata from IPFS
    cid = qr_data.get('cid')
    if cid:
        metadata = fetch_metadata_from_ipfs(cid)
        
        if metadata:
            print()
            print("=" * 60)
            print("🔍 VERIFICATION SUMMARY:")
            print("=" * 60)
            
            # Cross-verify data
            qr_product_id = qr_data.get('product_id', '')
            metadata_product_id = metadata.get('uniqueProductID', '')
            
            if qr_product_id.strip() == metadata_product_id.strip():
                print("✅ Product ID verification: PASSED")
            else:
                print(f"❌ Product ID mismatch: QR='{qr_product_id}' vs Metadata='{metadata_product_id}'")
            
            qr_manufacturer = qr_data.get('manufacturer', '')
            metadata_manufacturer = metadata.get('manufacturerID', '')
            
            if qr_manufacturer == metadata_manufacturer:
                print("✅ Manufacturer verification: PASSED")
            else:
                print(f"❌ Manufacturer mismatch: QR='{qr_manufacturer}' vs Metadata='{metadata_manufacturer}'")
            
            # Check if images/videos are accessible
            image_cid = metadata.get('image_cid', '')
            video_cid = metadata.get('video_cid', '')
            
            if image_cid:
                print(f"🖼️ Product Image: https://w3s.link/ipfs/{image_cid}")
            else:
                print("📷 No product image available")
                
            if video_cid:
                print(f"🎥 Product Video: https://w3s.link/ipfs/{video_cid}")
            else:
                print("📹 No product video available")
            
            print()
            print("🎉 QR Code scanning and verification completed!")
            
            return {
                'qr_data': qr_data,
                'metadata': metadata,
                'verification_passed': True
            }
    
    return {'qr_data': qr_data, 'verification_passed': False}

def test_with_sample_data():
    """
    Test QR scanning with sample encrypted QR data
    This simulates scanning a real QR code
    """
    print("🧪 Testing QR Code Scanning with Sample Data")
    print("=" * 60)
    
    # Sample product data based on your GSK Panadol
    sample_token_id = "1749265684000"
    sample_metadata_cid = "bafkreia5xqjmcf7ueb7k8p9t2r6s1v4w0x3z5a8c1e4g7i0k3m6o9q2s5u8"  # Replace with actual CID
    sample_product_data = {
        "name": "GSK Panadol Extra red tablets",
        "uniqueProductID": "VD-21189-14",
        "manufacturerID": "0x032041b4b356fEE1496805DD4749f181bC736FFA",
        "productType": "Pharmaceuticals",
        "batchNumber": "BTH_P124",
        "manufacturingDate": "2025-03-02",
        "category": "Pharmaceuticals"
    }
    
    try:
        # Generate a sample QR code
        print("📦 Generating sample QR code...")
        qr_payload = encryption_service.create_qr_payload(
            token_id=sample_token_id,
            metadata_cid=sample_metadata_cid,
            product_data=sample_product_data
        )
        
        encrypted_qr = encryption_service.encrypt_qr_data(qr_payload)
        print(f"✅ Sample QR generated: {encrypted_qr[:50]}...")
        print()
        
        # Now scan it
        result = scan_and_verify_product(encrypted_qr)
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use provided encrypted QR payload
        encrypted_payload = sys.argv[1]
        print(f"🔍 Scanning provided QR code...")
        scan_and_verify_product(encrypted_payload)
    else:
        # Run test with sample data
        test_with_sample_data()
        
        print("\n" + "=" * 80)
        print("📋 USAGE INSTRUCTIONS:")
        print("=" * 80)
        print("To scan a real QR code:")
        print("python3 qr_scanner.py <encrypted_qr_payload>")
        print()
        print("Example:")
        print("python3 qr_scanner.py 'gAAAAABh4xKm9...'")
        print()
        print("Or use the /api/qr/decrypt endpoint:")
        print("curl -X POST http://localhost:8001/api/qr/decrypt \\")
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"encrypted_payload": "your_qr_payload_here"}\'')