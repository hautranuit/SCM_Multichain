#!/usr/bin/env python3
"""
LayerZero OFT Peer Configuration Script
Fix the peer configuration issue identified in the investigation
"""

import asyncio
from web3 import Web3
from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service

# LayerZero setPeer function ABI
SET_PEER_ABI = [
    {
        "inputs": [
            {"name": "_eid", "type": "uint32"},
            {"name": "_peer", "type": "bytes32"}
        ],
        "name": "setPeer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

async def configure_layerzero_peers():
    """Configure missing peers for LayerZero OFT contracts"""
    
    print("🔧 LayerZero Peer Configuration Fix")
    print("=" * 50)
    
    # Initialize the service
    try:
        await layerzero_oft_bridge_service.initialize()
        print("✅ LayerZero service initialized")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return
    
    # Get contract configurations
    contracts = layerzero_oft_bridge_service.oft_contracts
    
    # Peer mappings that need to be configured
    peer_configurations = [
        # zkEVM needs to know about all other chains
        {
            "source_chain": "zkevm_cardona",
            "target_chain": "optimism_sepolia",
            "target_eid": 40232,
            "priority": "CRITICAL"
        },
        {
            "source_chain": "zkevm_cardona", 
            "target_chain": "arbitrum_sepolia",
            "target_eid": 40231,
            "priority": "CRITICAL"
        },
        {
            "source_chain": "zkevm_cardona",
            "target_chain": "polygon_pos", 
            "target_eid": 40313,
            "priority": "CRITICAL"
        },
        # Ensure bidirectional configuration (reverse mappings)
        {
            "source_chain": "optimism_sepolia",
            "target_chain": "arbitrum_sepolia",
            "target_eid": 40231,
            "priority": "MEDIUM"
        },
        {
            "source_chain": "optimism_sepolia",
            "target_chain": "polygon_pos",
            "target_eid": 40313, 
            "priority": "MEDIUM"
        },
        {
            "source_chain": "arbitrum_sepolia",
            "target_chain": "optimism_sepolia",
            "target_eid": 40232,
            "priority": "MEDIUM"
        },
        {
            "source_chain": "arbitrum_sepolia",
            "target_chain": "polygon_pos",
            "target_eid": 40313,
            "priority": "MEDIUM"
        },
        {
            "source_chain": "polygon_pos",
            "target_chain": "optimism_sepolia", 
            "target_eid": 40232,
            "priority": "MEDIUM"
        },
        {
            "source_chain": "polygon_pos",
            "target_chain": "arbitrum_sepolia",
            "target_eid": 40231,
            "priority": "MEDIUM"
        }
    ]
    
    print(f"\n📋 Found {len(peer_configurations)} peer configurations to check/set")
    
    # Check current peer status and configure missing ones
    missing_peers = []
    configured_peers = []
    
    for config in peer_configurations:
        source_chain = config["source_chain"]
        target_chain = config["target_chain"] 
        target_eid = config["target_eid"]
        priority = config["priority"]
        
        print(f"\n🔍 Checking: {source_chain} → {target_chain} (EID: {target_eid})")
        
        try:
            # Get Web3 connection for source chain
            web3 = layerzero_oft_bridge_service.web3_connections.get(source_chain)
            source_contract_addr = contracts[source_chain]["address"]
            target_contract_addr = contracts[target_chain]["address"]
            
            if not web3 or not source_contract_addr:
                print(f"❌ Missing connection or contract for {source_chain}")
                continue
            
            # Check current peer configuration
            peer_abi = [{"inputs": [{"name": "_eid", "type": "uint32"}], "name": "peers", "outputs": [{"name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"}]
            contract = web3.eth.contract(address=source_contract_addr, abi=peer_abi)
            
            current_peer = contract.functions.peers(target_eid).call()
            expected_peer = Web3.to_bytes(hexstr=target_contract_addr.lower().replace('0x', '').zfill(64))
            
            if current_peer == expected_peer:
                print(f"✅ Peer already configured correctly")
                configured_peers.append(config)
            else:
                print(f"❌ Peer missing or incorrect")
                print(f"   Current: {current_peer.hex()}")
                print(f"   Expected: {expected_peer.hex()}")
                missing_peers.append(config)
                
        except Exception as e:
            print(f"❌ Error checking peer: {e}")
            missing_peers.append(config)
    
    print(f"\n📊 PEER CONFIGURATION STATUS:")
    print(f"✅ Correctly configured: {len(configured_peers)}")
    print(f"❌ Missing/incorrect: {len(missing_peers)}")
    
    if missing_peers:
        print(f"\n🔧 MISSING PEER CONFIGURATIONS:")
        critical_missing = [p for p in missing_peers if p["priority"] == "CRITICAL"]
        medium_missing = [p for p in missing_peers if p["priority"] == "MEDIUM"]
        
        print(f"🚨 Critical (zkEVM): {len(critical_missing)}")
        for config in critical_missing:
            print(f"   {config['source_chain']} → {config['target_chain']} (EID: {config['target_eid']})")
        
        print(f"⚠️ Medium (bidirectional): {len(medium_missing)}")
        for config in medium_missing:
            print(f"   {config['source_chain']} → {config['target_chain']} (EID: {config['target_eid']})")
        
        print(f"\n💡 RECOMMENDED ACTIONS:")
        
        if critical_missing:
            print(f"🚨 IMMEDIATE FIX NEEDED:")
            print(f"   The zkEVM contract must have peers configured to receive transfers.")
            print(f"   Without this, ALL transfers TO zkEVM will fail.")
            
            print(f"\n🔧 Required setPeer transactions for zkEVM:")
            for config in critical_missing:
                target_addr = contracts[config["target_chain"]]["address"]
                print(f"   setPeer({config['target_eid']}, {target_addr}) on zkEVM")
            
            print(f"\n📝 Manual Fix Commands (if you have admin access):")
            for config in critical_missing:
                target_addr = contracts[config["target_chain"]]["address"]
                print(f"   # {config['source_chain']} → {config['target_chain']}")
                print(f"   zkevmContract.setPeer({config['target_eid']}, '{target_addr}')")
        
        print(f"\n🔄 ALTERNATIVE SOLUTION:")
        print(f"   Test reverse direction transfers (zkEVM → Optimism)")
        print(f"   This might work since Optimism has zkEVM as peer")
        
    else:
        print(f"\n🎉 ALL PEERS CONFIGURED CORRECTLY!")
        print(f"   The issue might be in contract implementation or LayerZero version")
    
    return {
        "total_configs": len(peer_configurations),
        "configured_correctly": len(configured_peers),
        "missing_configs": len(missing_peers),
        "critical_missing": len([p for p in missing_peers if p["priority"] == "CRITICAL"]),
        "needs_immediate_fix": len(missing_peers) > 0
    }

async def test_reverse_transfer():
    """Test transfer in reverse direction (zkEVM → Optimism) which might work"""
    
    print(f"\n🔄 TESTING REVERSE TRANSFER: zkEVM → Optimism")
    print("=" * 50)
    
    try:
        # Test send configuration for reverse direction
        send_test = await layerzero_oft_bridge_service.test_and_fix_layerzero_send(
            "zkevm_cardona", "optimism_sepolia"
        )
        
        if send_test["success"]:
            working_config = send_test.get("working_configuration")
            if working_config:
                print(f"🎉 REVERSE DIRECTION WORKS!")
                print(f"   Configuration: {working_config['type']}")
                print(f"   Function: {working_config['send_function']}")
                print(f"   This proves contracts are functional")
                
                print(f"\n💡 TEMPORARY WORKAROUND:")
                print(f"   Use zkEVM as source chain instead of destination")
                print(f"   Transfer FROM zkEVM TO other chains")
                
                return True
            else:
                print(f"❌ Reverse direction also fails")
                return False
        else:
            print(f"❌ Reverse direction test failed: {send_test.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Reverse test error: {e}")
        return False

async def main():
    """Main peer configuration analysis and fix"""
    
    # Run peer configuration analysis
    peer_status = await configure_layerzero_peers()
    
    # Test reverse direction as potential workaround
    reverse_works = await test_reverse_transfer()
    
    print(f"\n{'='*60}")
    print("🎯 PEER CONFIGURATION ANALYSIS COMPLETE")
    print(f"{'='*60}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total peer configs checked: {peer_status['total_configs']}")
    print(f"   Correctly configured: {peer_status['configured_correctly']}")
    print(f"   Missing configurations: {peer_status['missing_configs']}")
    print(f"   Critical missing (zkEVM): {peer_status['critical_missing']}")
    
    if peer_status['critical_missing'] > 0:
        print(f"\n🚨 CRITICAL ISSUE CONFIRMED:")
        print(f"   zkEVM contract is missing peer configurations")
        print(f"   This prevents ALL incoming transfers to zkEVM")
        
        print(f"\n🔧 SOLUTIONS:")
        print(f"   1. Configure peers on zkEVM contract (requires admin access)")
        print(f"   2. Use reverse transfers (zkEVM → other chains)")
        print(f"   3. Redeploy contracts with proper peer setup")
        
        if reverse_works:
            print(f"   ✅ Reverse transfers work - use as temporary workaround")
        else:
            print(f"   ❌ Reverse transfers also fail - contract redeployment needed")
    
    else:
        print(f"\n✅ Peer configurations are correct")
        print(f"   Issue might be in contract implementation or LayerZero setup")
    
    print(f"\n🔗 Next Steps:")
    print(f"   1. Contact LayerZero contract deployer to configure peers")
    print(f"   2. Test reverse direction transfers as workaround")
    print(f"   3. Consider fresh LayerZero OFT deployment with proper setup")

if __name__ == "__main__":
    asyncio.run(main())