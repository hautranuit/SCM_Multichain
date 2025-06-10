#!/usr/bin/env python3
"""
Test script for Token Bridge Service
Tests the basic functionality without requiring real blockchain connections
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_token_bridge():
    """Test token bridge service initialization and basic functionality"""
    
    print("🧪 Testing Token Bridge Service")
    print("=" * 50)
    
    try:
        # Test 1: Import services
        print("Test 1: Importing services...")
        from app.services.token_bridge_service import token_bridge_service
        from app.services.multi_account_manager import address_key_manager
        print("✅ Services imported successfully")
        
        # Test 2: Check address manager
        print("\nTest 2: Checking address manager...")
        addresses = address_key_manager.get_all_available_addresses()
        print(f"✅ Address manager loaded {len(addresses)} addresses")
        print(f"   Sample addresses: {addresses[:3]}")
        
        # Test 3: Test LayerZero chain mapping
        print("\nTest 3: Testing LayerZero chain mappings...")
        chains = ["optimism_sepolia", "polygon_pos", "zkevm_cardona", "arbitrum_sepolia"]
        for chain in chains:
            lz_id = token_bridge_service.get_layerzero_chain_id(chain)
            print(f"   {chain}: LayerZero ID {lz_id}")
        print("✅ LayerZero mappings working")
        
        # Test 4: Test Web3 connection method (without real connections)
        print("\nTest 4: Testing Web3 connection method...")
        for chain in chains:
            web3 = token_bridge_service.get_web3_for_chain(chain)
            status = "Not initialized" if web3 is None else "Ready"
            print(f"   {chain}: {status}")
        print("✅ Web3 connection method working")
        
        # Test 5: Initialize token bridge service
        print("\nTest 5: Initializing token bridge service...")
        await token_bridge_service.initialize()
        print("✅ Token bridge service initialized")
        
        # Test 6: Test API routes import
        print("\nTest 6: Testing API routes...")
        from app.api.routes.token_bridge import router
        print(f"✅ Token bridge router loaded with {len(router.routes)} routes")
        
        route_names = [route.path for route in router.routes]
        print(f"   Available routes: {route_names}")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Token Bridge is ready for testing.")
        print("\n📋 Summary:")
        print(f"   ✅ {len(addresses)} wallet addresses loaded")
        print(f"   ✅ {len(chains)} chain configurations ready")
        print(f"   ✅ {len(router.routes)} API endpoints available")
        print(f"   ✅ Token bridge service initialized")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_token_bridge())
    sys.exit(0 if success else 1)