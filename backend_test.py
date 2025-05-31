#!/usr/bin/env python3
"""
ChainFLIP Multi-Chain Backend Test Script
Tests all backend API endpoints and functionality
"""
import requests
import json
import time
import random
import sys
from datetime import datetime, timedelta

# Backend URL
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test account with funds
TEST_ACCOUNT = "0x032041b4b356fEE1496805DD4749f181bC736FFA"

# Contract addresses
SUPPLY_CHAIN_NFT_CONTRACT = "0x60C466cF52cb9705974a89b72DeA045c45cb7572"
POLYGON_POS_HUB_CONTRACT = "0xFbD920b8Bb8Be7dC3b5976a63F515c88e2776a6E"
NFT_CORE_CONTRACT = "0x13Ef359e2F7f8e63c5613a41F85Db3f3023B23d0"

# Chain IDs
POLYGON_AMOY_CHAIN_ID = 80002
L2_CDK_CHAIN_ID = 2442

# Test data
test_metadata_cid = "bafkreiabcdefghijklmnopqrstuvwxyz1234567890"
test_qr_data = {
    "product_name": "Test Product",
    "manufacturer_location": "Test Location",
    "timestamp": datetime.now().isoformat()
}

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_subheader(text):
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * 50}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def test_endpoint(method, endpoint, data=None, expected_status=200, description=None):
    """Test an API endpoint and return the response"""
    url = f"{API_BASE}{endpoint}"
    
    if description:
        print(f"Testing: {description}")
    else:
        print(f"Testing endpoint: {method.upper()} {endpoint}")
    
    try:
        if method.lower() == "get":
            response = requests.get(url)
        elif method.lower() == "post":
            response = requests.post(url, json=data)
        elif method.lower() == "put":
            response = requests.put(url, json=data)
        elif method.lower() == "delete":
            response = requests.delete(url)
        else:
            print_error(f"Unsupported method: {method}")
            return None
        
        if response.status_code == expected_status:
            print_success(f"Status: {response.status_code}")
            try:
                return response.json()
            except:
                return response.text
        else:
            print_error(f"Expected status {expected_status}, got {response.status_code}")
            try:
                print_error(f"Response: {response.json()}")
            except:
                print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Request failed: {e}")
        return None

def test_health_endpoints():
    """Test health check endpoints"""
    print_header("Testing Health & Status Endpoints")
    
    # Main health endpoint
    result = test_endpoint("get", "/health", description="Main health check endpoint")
    if result and result.get("status") == "healthy":
        print_success("Main health check passed")
    else:
        print_error("Main health check failed")
    
    # QR service health endpoint
    result = test_endpoint("get", "/qr/health", description="QR service health check endpoint")
    if result and result.get("status") == "healthy":
        print_success("QR service health check passed")
    else:
        print_error("QR service health check failed")
    
    # Root endpoint
    result = test_endpoint("get", "", description="Root API endpoint")
    if result and "version" in result:
        print_success(f"Root API endpoint returned version: {result.get('version')}")
    else:
        print_error("Root API endpoint failed")

def test_blockchain_integration():
    """Test blockchain integration endpoints"""
    print_header("Testing Blockchain Integration")
    
    # Blockchain status
    print_subheader("Testing blockchain status")
    result = test_endpoint("get", "/blockchain/status", description="Blockchain network status")
    if result:
        if "polygon_pos" in result and result["polygon_pos"].get("connected"):
            print_success(f"Connected to Polygon PoS (Chain ID: {result['polygon_pos'].get('chain_id')})")
            print_success(f"Latest block: {result['polygon_pos'].get('latest_block')}")
        else:
            print_error("Not connected to Polygon PoS")
        
        if "l2_cdk" in result and result["l2_cdk"].get("connected"):
            print_success(f"Connected to L2 CDK (Chain ID: {result['l2_cdk'].get('chain_id')})")
            print_success(f"Latest block: {result['l2_cdk'].get('latest_block')}")
        else:
            print_warning("Not connected to L2 CDK (expected if not configured)")
    
    # Register participant
    print_subheader("Testing participant registration")
    participant_data = {
        "address": TEST_ACCOUNT,
        "participant_type": "manufacturer",
        "chain_id": POLYGON_AMOY_CHAIN_ID
    }
    result = test_endpoint("post", "/blockchain/participants/register", 
                          data=participant_data, 
                          description="Register participant")
    
    if result and result.get("success"):
        print_success("Participant registration successful")
        participant = result.get("participant", {})
        print(f"Participant address: {participant.get('address')}")
        print(f"Participant type: {participant.get('participant_type')}")
    else:
        print_warning("Participant registration failed or participant already exists")
    
    # Mint product NFT
    print_subheader("Testing product NFT minting")
    product_data = {
        "manufacturer": TEST_ACCOUNT,
        "metadata_cid": test_metadata_cid,
        "initial_qr_data": test_qr_data
    }
    result = test_endpoint("post", "/blockchain/products/mint", 
                          data=product_data, 
                          description="Mint product NFT")
    
    if result and result.get("success"):
        print_success("Product NFT minting successful")
        product = result.get("product", {})
        token_id = product.get("token_id")
        print(f"Token ID: {token_id}")
        print(f"Manufacturer: {product.get('manufacturer')}")
        print(f"Metadata CID: {product.get('metadata_cid')}")
        
        # Test get product by token ID
        if token_id:
            print_subheader(f"Testing get product by token ID: {token_id}")
            result = test_endpoint("get", f"/blockchain/products/{token_id}", 
                                  description="Get product by token ID")
            if result:
                print_success("Product retrieval successful")
                print(f"Current owner: {result.get('current_owner')}")
                print(f"Status: {result.get('status')}")
            
            # Test product transfer
            print_subheader("Testing product transfer")
            transfer_data = {
                "token_id": token_id,
                "from_address": TEST_ACCOUNT,
                "to_address": "0x1234567890123456789012345678901234567890",  # Dummy address
                "transport_data": {
                    "transport_type": "truck",
                    "departure_time": datetime.now().isoformat(),
                    "estimated_arrival": (datetime.now() + timedelta(days=2)).isoformat(),
                    "temperature": 22.5,
                    "humidity": 45.0
                }
            }
            result = test_endpoint("post", "/blockchain/products/transfer", 
                                  data=transfer_data, 
                                  description="Transfer product")
            if result and result.get("success"):
                print_success("Product transfer successful")
            else:
                print_error("Product transfer failed")
    else:
        print_error("Product NFT minting failed")
    
    # Test get participant products
    print_subheader(f"Testing get participant products for {TEST_ACCOUNT}")
    result = test_endpoint("get", f"/blockchain/participants/{TEST_ACCOUNT}/products", 
                          description="Get participant products")
    if result:
        print_success(f"Found {result.get('count', 0)} products for participant")
    
    # Test cross-chain messaging
    print_subheader("Testing cross-chain messaging")
    message_data = {
        "source_chain": POLYGON_AMOY_CHAIN_ID,
        "target_chain": L2_CDK_CHAIN_ID,
        "message_data": {
            "message_type": "product_verification",
            "token_id": "123456789",
            "timestamp": datetime.now().isoformat()
        }
    }
    result = test_endpoint("post", "/blockchain/cross-chain/message", 
                          data=message_data, 
                          description="Send cross-chain message")
    if result and result.get("success"):
        print_success("Cross-chain message sent successfully")
        print(f"Message ID: {result.get('message_id')}")
    else:
        print_error("Cross-chain message failed")

def test_federated_learning():
    """Test federated learning endpoints"""
    print_header("Testing Federated Learning System")
    
    # FL status
    print_subheader("Testing FL system status")
    result = test_endpoint("get", "/federated-learning/status", description="FL system status")
    if result and "models" in result:
        print_success("FL system status retrieved successfully")
        
        # Print anomaly detection model info
        anomaly_model = result.get("models", {}).get("anomaly_detection", {})
        print(f"Anomaly detection model:")
        print(f"  Training rounds: {anomaly_model.get('training_rounds', 0)}")
        print(f"  Last updated: {anomaly_model.get('last_updated', 'N/A')}")
        print(f"  Active participants: {anomaly_model.get('active_participants', 0)}")
        
        # Print counterfeit detection model info
        counterfeit_model = result.get("models", {}).get("counterfeit_detection", {})
        print(f"Counterfeit detection model:")
        print(f"  Training rounds: {counterfeit_model.get('training_rounds', 0)}")
        print(f"  Last updated: {counterfeit_model.get('last_updated', 'N/A')}")
        print(f"  Active participants: {counterfeit_model.get('active_participants', 0)}")
    else:
        print_error("Failed to retrieve FL system status")
    
    # Test anomaly detection
    print_subheader("Testing anomaly detection")
    anomaly_data = {
        "product_data": {
            "token_id": "123456789",
            "transport_duration": 86400,  # 24 hours in seconds
            "temperature_readings": [20.1, 20.3, 20.2, 20.5, 35.7, 20.1],  # Anomaly in temperature
            "humidity_readings": [45, 46, 45, 47, 46],
            "location_jumps": 0,
            "participant_reputation": 95,
            "product_age_days": 10,
            "handover_frequency": 0.5
        }
    }
    result = test_endpoint("post", "/federated-learning/detect/anomaly", 
                          data=anomaly_data, 
                          description="Detect anomaly")
    if result:
        if "error" in result:
            print_warning(f"Anomaly detection returned error: {result.get('error')}")
            print_warning("This is expected if the model hasn't been trained yet")
        else:
            print_success("Anomaly detection successful")
            print(f"Is anomaly: {result.get('is_anomaly', False)}")
            print(f"Anomaly score: {result.get('anomaly_score', 0)}")
            print(f"Confidence: {result.get('confidence', 0)}")
    
    # Test counterfeit detection
    print_subheader("Testing counterfeit detection")
    counterfeit_data = {
        "product_data": {
            "token_id": "123456789",
            "qr_code_complexity": 0.8,
            "metadata_consistency": 0.9,
            "participant_verification_score": 0.95,
            "product_history_length": 5,
            "cryptographic_signature_strength": 0.9,
            "ipfs_metadata_integrity": 1.0,
            "transport_chain_consistency": 0.95
        }
    }
    result = test_endpoint("post", "/federated-learning/detect/counterfeit", 
                          data=counterfeit_data, 
                          description="Detect counterfeit")
    if result:
        if "error" in result:
            print_warning(f"Counterfeit detection returned error: {result.get('error')}")
            print_warning("This is expected if the model hasn't been trained yet")
        else:
            print_success("Counterfeit detection successful")
            print(f"Is counterfeit: {result.get('is_counterfeit', False)}")
            print(f"Counterfeit probability: {result.get('counterfeit_probability', 0)}")
            print(f"Confidence: {result.get('confidence', 0)}")
    
    # Test model aggregation endpoints
    print_subheader("Testing model aggregation endpoints")
    result = test_endpoint("post", "/federated-learning/aggregate/anomaly", 
                          description="Aggregate anomaly models")
    if result:
        if "error" in result:
            print_warning(f"Anomaly model aggregation returned error: {result.get('error')}")
            print_warning("This is expected if there aren't enough local models")
        else:
            print_success("Anomaly model aggregation successful")
    
    result = test_endpoint("post", "/federated-learning/aggregate/counterfeit", 
                          description="Aggregate counterfeit models")
    if result:
        if "error" in result:
            print_warning(f"Counterfeit model aggregation returned error: {result.get('error')}")
            print_warning("This is expected if there aren't enough local models")
        else:
            print_success("Counterfeit model aggregation successful")
    
    # Test global model info endpoints
    print_subheader("Testing global model info endpoints")
    result = test_endpoint("get", "/federated-learning/models/anomaly/global", 
                          description="Get global anomaly model info")
    if result:
        print_success("Global anomaly model info retrieved")
        print(f"Model type: {result.get('model_type')}")
        print(f"Features: {result.get('features')}")
        print(f"Training rounds: {result.get('training_rounds')}")
    
    result = test_endpoint("get", "/federated-learning/models/counterfeit/global", 
                          description="Get global counterfeit model info")
    if result:
        print_success("Global counterfeit model info retrieved")
        print(f"Model type: {result.get('model_type')}")
        print(f"Features: {result.get('features')}")
        print(f"Training rounds: {result.get('training_rounds')}")

def test_ipfs_integration():
    """Test IPFS integration endpoints"""
    print_header("Testing IPFS Integration")
    
    # Test IPFS upload
    print_subheader("Testing IPFS upload endpoint")
    # Since we can't easily create a multipart form request with a file in this script,
    # we'll just check if the endpoint is available
    try:
        url = f"{API_BASE}/ipfs/upload"
        response = requests.get(url)
        if response.status_code == 405:  # Method Not Allowed (expected for GET on POST endpoint)
            print_success("IPFS upload endpoint exists (returns 405 for GET method)")
        else:
            print_warning(f"Unexpected status code for IPFS upload endpoint: {response.status_code}")
    except Exception as e:
        print_error(f"IPFS upload endpoint check failed: {e}")
    
    # Test IPFS retrieval
    print_subheader("Testing IPFS retrieval endpoint")
    test_cid = "bafkreiabcdefghijklmnopqrstuvwxyz1234567890"
    result = test_endpoint("get", f"/ipfs/{test_cid}", description="Get IPFS content")
    if result:
        print_success("IPFS retrieval endpoint working")
        print(f"Gateway URL: {result.get('gateway_url')}")
    
    # Test QR generation
    print_subheader("Testing QR code generation via IPFS")
    qr_data = {
        "product_id": "123456789",
        "metadata": {
            "product_name": "Test Product",
            "manufacturer": "Test Manufacturer",
            "timestamp": datetime.now().isoformat()
        }
    }
    result = test_endpoint("post", "/ipfs/qr/generate", 
                          data=qr_data, 
                          description="Generate QR code")
    if result and result.get("success"):
        print_success("QR code generation successful")
        print(f"QR hash: {result.get('qr_hash')}")
        print(f"Encrypted data CID: {result.get('encrypted_data_cid')}")
    else:
        print_error("QR code generation failed")

def test_qr_service():
    """Test QR code service endpoints"""
    print_header("Testing QR Code Services")
    
    # Test QR service info
    print_subheader("Testing QR service info")
    result = test_endpoint("get", "/qr/info", description="QR service info")
    if result and "service" in result:
        print_success("QR service info retrieved successfully")
        print(f"Service: {result.get('service')}")
        print(f"Version: {result.get('version')}")
        print(f"Encryption: {result.get('encryption', {}).get('algorithm')}")
    
    # Test QR generation
    print_subheader("Testing QR code generation")
    qr_data = {
        "token_id": 123456789,
        "cid": test_metadata_cid,
        "chain_id": POLYGON_AMOY_CHAIN_ID,
        "expiry_minutes": 60,
        "metadata": {
            "product_name": "Test Product",
            "manufacturer": "Test Manufacturer",
            "batch_id": "BATCH-2024-001"
        }
    }
    result = test_endpoint("post", "/qr/generate", 
                          data=qr_data, 
                          description="Generate QR code")
    
    if result and result.get("success"):
        print_success("QR code generation successful")
        print(f"Token ID: {result.get('qr_data', {}).get('token_id')}")
        print(f"Expires at: {result.get('qr_data', {}).get('expires_at')}")
        
        # Store encrypted payload for later tests
        encrypted_payload = result.get("qr_data", {}).get("encrypted_payload")
        if encrypted_payload:
            # Test QR verification
            print_subheader("Testing QR code verification")
            result = test_endpoint("get", f"/qr/verify/{encrypted_payload}", 
                                  description="Verify QR payload")
            if result and result.get("valid"):
                print_success("QR code verification successful")
                print(f"Token ID: {result.get('token_id')}")
                print(f"Chain ID: {result.get('chain_id')}")
                print(f"Expires at: {result.get('expires_at')}")
            else:
                print_error("QR code verification failed")
            
            # Test QR scanning
            print_subheader("Testing QR code scanning")
            scan_data = {
                "encrypted_payload": encrypted_payload,
                "expected_token_id": 123456789,
                "expected_chain_id": POLYGON_AMOY_CHAIN_ID
            }
            result = test_endpoint("post", "/qr/scan", 
                                  data=scan_data, 
                                  description="Scan QR code")
            if result and result.get("success") and result.get("valid"):
                print_success("QR code scanning successful")
                payload_data = result.get("payload_data", {})
                print(f"Token ID: {payload_data.get('token_id')}")
                print(f"CID: {payload_data.get('cid')}")
                print(f"Chain ID: {payload_data.get('chain_id')}")
            else:
                print_error("QR code scanning failed")
            
            # Test QR refresh
            print_subheader("Testing QR code refresh")
            refresh_data = {
                "old_payload": encrypted_payload,
                "new_expiry_minutes": 120
            }
            result = test_endpoint("post", "/qr/refresh", 
                                  data=refresh_data, 
                                  description="Refresh QR code")
            if result and result.get("success"):
                print_success("QR code refresh successful")
                print(f"Original expiry: {result.get('original_expiry')}")
                print(f"New expiry: {result.get('new_expiry')}")
            else:
                print_error("QR code refresh failed")
    else:
        print_error("QR code generation failed")
    
    # Test multi-chain QR generation
    print_subheader("Testing multi-chain QR code generation")
    multi_chain_data = {
        "token_id": 987654321,
        "chain_data": {
            str(POLYGON_AMOY_CHAIN_ID): test_metadata_cid,
            str(L2_CDK_CHAIN_ID): "bafkreizyxwvutsrqponmlkjihgfedcba0987654321"
        },
        "expiry_minutes": 60,
        "metadata": {
            "product_name": "Multi-Chain Test Product",
            "manufacturer": "Test Manufacturer",
            "batch_id": "BATCH-2024-002"
        }
    }
    result = test_endpoint("post", "/qr/generate-multi-chain", 
                          data=multi_chain_data, 
                          description="Generate multi-chain QR code")
    
    if result and result.get("success"):
        print_success("Multi-chain QR code generation successful")
        print(f"Token ID: {result.get('qr_data', {}).get('token_id')}")
        print(f"Chain count: {result.get('qr_data', {}).get('chain_count')}")
        print(f"Expires at: {result.get('qr_data', {}).get('expires_at')}")
    else:
        print_error("Multi-chain QR code generation failed")

def test_analytics_monitoring():
    """Test analytics and monitoring endpoints"""
    print_header("Testing Analytics & Monitoring")
    
    # Dashboard analytics
    print_subheader("Testing dashboard analytics")
    result = test_endpoint("get", "/analytics/dashboard", description="Dashboard analytics")
    if result and "overview" in result:
        print_success("Dashboard analytics retrieved successfully")
        overview = result.get("overview", {})
        print(f"Total products: {overview.get('total_products', 0)}")
        print(f"Total participants: {overview.get('total_participants', 0)}")
        print(f"Total transactions: {overview.get('total_transactions', 0)}")
    else:
        print_error("Failed to retrieve dashboard analytics")
    
    # Supply chain flow
    print_subheader("Testing supply chain flow analytics")
    result = test_endpoint("get", "/analytics/supply-chain/flow", description="Supply chain flow")
    if result:
        print_success("Supply chain flow analytics retrieved successfully")
        status_distribution = result.get("status_distribution", [])
        if status_distribution:
            print("Status distribution:")
            for status in status_distribution:
                print(f"  {status.get('status')}: {status.get('count')}")
    else:
        print_error("Failed to retrieve supply chain flow analytics")
    
    # Participant activity
    print_subheader("Testing participant activity analytics")
    result = test_endpoint("get", "/analytics/participants/activity", description="Participant activity")
    if result:
        print_success("Participant activity analytics retrieved successfully")
        top_participants = result.get("top_participants", [])
        if top_participants:
            print("Top participants:")
            for participant in top_participants[:3]:  # Show top 3
                print(f"  {participant.get('address')}: {participant.get('product_count')} products")
    else:
        print_error("Failed to retrieve participant activity analytics")
    
    # Security threats
    print_subheader("Testing security threat analytics")
    result = test_endpoint("get", "/analytics/security/threats", description="Security threats")
    if result:
        print_success("Security threat analytics retrieved successfully")
        anomaly_trend = result.get("anomaly_trend", [])
        if anomaly_trend:
            print("Recent anomaly trend:")
            for day in anomaly_trend[:3]:  # Show last 3 days
                print(f"  {day.get('date')}: {day.get('anomalies')} anomalies")
    else:
        print_error("Failed to retrieve security threat analytics")
    
    # Performance metrics
    print_subheader("Testing performance metrics")
    result = test_endpoint("get", "/analytics/performance/metrics", description="Performance metrics")
    if result:
        print_success("Performance metrics retrieved successfully")
        network = result.get("network", {})
        if "polygon_pos" in network:
            print(f"Polygon PoS connected: {network['polygon_pos'].get('connected')}")
            print(f"Latest block: {network['polygon_pos'].get('latest_block')}")
    else:
        print_error("Failed to retrieve performance metrics")

def test_product_lifecycle():
    """Test product lifecycle management endpoints"""
    print_header("Testing Product Lifecycle Management")
    
    # Get products
    print_subheader("Testing product listing")
    result = test_endpoint("get", "/products?limit=5", description="List products")
    if result and "products" in result:
        print_success(f"Retrieved {len(result.get('products', []))} products")
        print(f"Total count: {result.get('total_count', 0)}")
        
        # If we have products, test product details endpoint
        products = result.get("products", [])
        if products:
            token_id = products[0].get("token_id")
            if token_id:
                print_subheader(f"Testing product details for token ID: {token_id}")
                result = test_endpoint("get", f"/products/{token_id}", 
                                      description="Get product details")
                if result:
                    print_success("Product details retrieved successfully")
                    print(f"Manufacturer: {result.get('manufacturer')}")
                    print(f"Current owner: {result.get('current_owner')}")
                    print(f"Status: {result.get('status')}")
                
                # Test product history
                print_subheader(f"Testing product history for token ID: {token_id}")
                result = test_endpoint("get", f"/products/{token_id}/history", 
                                      description="Get product history")
                if result:
                    print_success("Product history retrieved successfully")
                    transport_history = result.get("transport_history", [])
                    print(f"Transport history entries: {len(transport_history)}")
                
                # Test product QR
                print_subheader(f"Testing product QR for token ID: {token_id}")
                result = test_endpoint("get", f"/products/{token_id}/qr", 
                                      description="Get product QR")
                if result:
                    print_success("Product QR retrieved successfully")
                    print(f"Last updated: {result.get('last_updated')}")
                
                # Test product analysis
                print_subheader(f"Testing product analysis for token ID: {token_id}")
                analysis_data = {
                    "token_id": token_id,
                    "analysis_type": "full"
                }
                result = test_endpoint("post", f"/products/{token_id}/analyze", 
                                      data=analysis_data,
                                      description="Analyze product")
                if result:
                    print_success("Product analysis completed")
                    if "anomaly_detection" in result:
                        anomaly = result.get("anomaly_detection", {})
                        print(f"Anomaly detected: {anomaly.get('is_anomaly', False)}")
                        print(f"Anomaly score: {anomaly.get('anomaly_score', 0)}")
                    
                    if "counterfeit_detection" in result:
                        counterfeit = result.get("counterfeit_detection", {})
                        print(f"Counterfeit detected: {counterfeit.get('is_counterfeit', False)}")
                        print(f"Counterfeit probability: {counterfeit.get('counterfeit_probability', 0)}")
    else:
        print_error("Failed to retrieve products")
    
    # Product statistics
    print_subheader("Testing product statistics")
    result = test_endpoint("get", "/products/statistics/overview", 
                          description="Get product statistics")
    if result:
        print_success("Product statistics retrieved successfully")
        print(f"Total products: {result.get('total_products', 0)}")
        
        by_status = result.get("by_status", {})
        if by_status:
            print("Products by status:")
            for status, count in by_status.items():
                print(f"  {status}: {count}")
    else:
        print_error("Failed to retrieve product statistics")
    
    # Recent anomalies
    print_subheader("Testing recent anomalies")
    result = test_endpoint("get", "/products/anomalies/recent", 
                          description="Get recent anomalies")
    if result:
        print_success("Recent anomalies retrieved successfully")
        anomalies = result.get("recent_anomalies", [])
        print(f"Recent anomalies count: {len(anomalies)}")
    else:
        print_error("Failed to retrieve recent anomalies")
    
    # Recent counterfeits
    print_subheader("Testing recent counterfeits")
    result = test_endpoint("get", "/products/counterfeits/recent", 
                          description="Get recent counterfeits")
    if result:
        print_success("Recent counterfeits retrieved successfully")
        counterfeits = result.get("recent_counterfeits", [])
        print(f"Recent counterfeits count: {len(counterfeits)}")
    else:
        print_error("Failed to retrieve recent counterfeits")

def main():
    """Main test function"""
    print_header("ChainFLIP Multi-Chain Backend Test")
    print(f"Testing backend at: {BACKEND_URL}")
    print(f"SupplyChainNFT contract: {SUPPLY_CHAIN_NFT_CONTRACT}")
    print(f"PolygonPoSHub contract: {POLYGON_POS_HUB_CONTRACT}")
    print(f"NFTCore contract: {NFT_CORE_CONTRACT}")
    print(f"Test account: {TEST_ACCOUNT}")
    
    # Run all tests
    test_health_endpoints()
    test_blockchain_integration()
    test_federated_learning()
    test_ipfs_integration()
    test_qr_service()
    test_analytics_monitoring()
    test_product_lifecycle()
    
    print_header("Test Summary")
    print("All backend tests completed. Check the output above for detailed results.")

if __name__ == "__main__":
    main()
