#!/usr/bin/env python3
"""
LayerZero OFT Contract Investigation Script
This script will help identify the exact issue with deployed LayerZero contracts
"""

import asyncio
import json
from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service

async def main():
    """Run comprehensive LayerZero contract investigation"""
    
    print("🔍 LayerZero OFT Contract Investigation")
    print("=" * 50)
    
    # Initialize the service
    try:
        await layerzero_oft_bridge_service.initialize()
        print("✅ LayerZero service initialized")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return
    
    # Chains to investigate
    chains = ["optimism_sepolia", "base_sepolia", "arbitrum_sepolia", "polygon_pos"]
    
    for chain in chains:
        print(f"\n{'='*60}")
        print(f"🔍 INVESTIGATING: {chain.upper()}")
        print(f"{'='*60}")
        
        # 1. Basic contract debug
        print(f"\n1️⃣ Basic Contract Debug")
        print("-" * 30)
        debug_result = await layerzero_oft_bridge_service.debug_oft_contract(chain)
        if debug_result["success"]:
            print(f"✅ Contract exists and responds")
            print(f"📍 Address: {debug_result.get('contract_address')}")
        else:
            print(f"❌ Basic debug failed: {debug_result.get('error')}")
            continue
        
        # 2. Deep contract investigation
        print(f"\n2️⃣ Deep Contract Investigation")
        print("-" * 30)
        investigation = await layerzero_oft_bridge_service.investigate_contract_implementation(chain)
        if investigation["success"]:
            results = investigation["investigation_results"]
            
            # Print key findings
            basic_info = results.get("basic_info", {})
            print(f"📦 Code size: {basic_info.get('code_size_bytes', 'N/A')} bytes")
            
            # LayerZero endpoints
            lz_endpoints = results.get("layerzero_endpoints", {})
            for endpoint_type, endpoint_result in lz_endpoints.items():
                if endpoint_result.get("status") == "works":
                    print(f"✅ {endpoint_type}: {endpoint_result.get('result')}")
                else:
                    print(f"❌ {endpoint_type}: Failed")
            
            # OFT patterns
            oft_patterns = results.get("oft_patterns", {})
            for pattern_name, pattern_result in oft_patterns.items():
                if pattern_result.get("status") == "works":
                    print(f"🔗 {pattern_name}: {pattern_result.get('result')}")
            
            # Proxy patterns
            proxy_patterns = results.get("proxy_patterns", {})
            for proxy_name, proxy_result in proxy_patterns.items():
                if proxy_result.get("status") == "works":
                    print(f"🔄 PROXY DETECTED - {proxy_name}: {proxy_result.get('result')}")
            
            # Initialization state
            init_state = results.get("initialization_state", {})
            peer_config = init_state.get("peer_base_sepolia", {})
            if peer_config.get("status") == "configured":
                print(f"✅ Peer configured for Base Sepolia: {peer_config.get('result')}")
            elif peer_config.get("status") == "not_configured":
                print(f"❌ CRITICAL: Peer NOT configured for Base Sepolia")
            
            # Print recommendations
            recommendations = investigation.get("recommendations", [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for rec in recommendations:
                    print(f"   {rec}")
        else:
            print(f"❌ Investigation failed: {investigation.get('error')}")
        
        # 3. Test send functionality (only for optimism_sepolia -> base_sepolia)
        if chain == "optimism_sepolia":
            print(f"\n3️⃣ Send Function Testing")
            print("-" * 30)
            send_test = await layerzero_oft_bridge_service.test_and_fix_layerzero_send(
                "optimism_sepolia", "base_sepolia"
            )
            
            if send_test["success"]:
                test_results = send_test["test_results"]
                working_config = send_test.get("working_configuration")
                
                print(f"🧪 Test results:")
                for test in test_results:
                    status_icon = "✅" if test["status"] == "success" else "❌"
                    print(f"   {status_icon} {test['test_name']}: {test['status']}")
                    if test["status"] == "failed":
                        print(f"      Error: {test.get('error', 'Unknown')}")
                
                if working_config:
                    print(f"\n🎉 WORKING CONFIGURATION FOUND!")
                    print(f"   Type: {working_config['type']}")
                    print(f"   Function: {working_config['send_function']}")
                    print(f"   Parameter format: {working_config.get('parameter_format', 'N/A')}")
                    
                    fix_code = send_test.get("fix_code")
                    if fix_code:
                        print(f"\n🔧 Required code fix:")
                        print(fix_code)
                else:
                    print(f"\n❌ NO WORKING CONFIGURATION FOUND")
                    print(f"   Recommendation: {send_test.get('recommendation')}")
            else:
                print(f"❌ Send test failed: {send_test.get('error')}")
    
    print(f"\n{'='*60}")
    print("🎯 INVESTIGATION COMPLETE")
    print(f"{'='*60}")
    
    print("\n📋 NEXT STEPS:")
    print("1. Review the investigation results above")
    print("2. Check for proxy contracts and their implementations")
    print("3. Verify peer configurations for cross-chain transfers")
    print("4. Test different LayerZero function signatures")
    print("5. If no working configuration found, consider contract redeployment")
    
    print("\n🔗 Block Explorer Links:")
    contracts = layerzero_oft_bridge_service.oft_contracts
    for chain_name, config in contracts.items():
        if config.get('address'):
            if chain_name == "optimism_sepolia":
                explorer = f"https://sepolia-optimism.etherscan.io/address/{config['address']}"
            elif chain_name == "arbitrum_sepolia":
                explorer = f"https://sepolia.arbiscan.io/address/{config['address']}"
            elif chain_name == "polygon_pos":
                explorer = f"https://amoy.polygonscan.com/address/{config['address']}"
            elif chain_name == "base_sepolia":
                explorer = f"https://sepolia.basescan.org/address/{config['address']}"
            else:
                explorer = f"Contract: {config['address']}"
            
            print(f"   {chain_name}: {explorer}")

if __name__ == "__main__":
    asyncio.run(main())