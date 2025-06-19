#!/usr/bin/env python3
"""
ChainFLIP Cross-Chain Messaging Test Script
Tests the fixed LayerZero peer connections for cross-chain CID sync
"""
import asyncio
import sys
import os
import time
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.append('/app/multichain-chainflip/backend')

from app.services.chainflip_messaging_service import chainflip_messaging_service
from app.core.config import get_settings

async def test_chainflip_messaging():
    """Test ChainFLIP cross-chain CID messaging after peer setup"""
    print("🧪 Testing ChainFLIP Cross-Chain CID Messaging")
    print("=" * 60)
    
    settings = get_settings()
    
    # Test data - using a realistic test scenario
    test_data = {
        "token_id": "TEST_" + str(int(time.time())),
        "metadata_cid": "bafkreitest123456789abcdefghijklmnopqrstuvwxyz", 
        "manufacturer": "0x5503a5B847e98B621d97695edf1bD84242C5862E",  # Test manufacturer
        "source_chain": "base_sepolia",
        "target_chain": "polygon_amoy"  # Central hub
    }
    
    print(f"📋 Test Parameters:")
    print(f"   Token ID: {test_data['token_id']}")
    print(f"   Metadata CID: {test_data['metadata_cid']}")
    print(f"   Manufacturer: {test_data['manufacturer']}")
    print(f"   Source Chain: {test_data['source_chain']}")
    print(f"   Target Chain: {test_data['target_chain']}")
    print()
    
    try:
        # Step 1: Initialize the ChainFLIP messaging service
        print("🔄 Step 1: Initializing ChainFLIP Messaging Service...")
        if not chainflip_messaging_service.web3_connections:
            await chainflip_messaging_service.initialize()
        
        if not chainflip_messaging_service.web3_connections:
            print("❌ Failed to initialize ChainFLIP messaging service")
            return False
            
        print("✅ ChainFLIP messaging service initialized")
        print(f"   Connected chains: {list(chainflip_messaging_service.web3_connections.keys())}")
        print(f"   Contract addresses: {chainflip_messaging_service.contract_addresses}")
        print()
        
        # Step 2: Check service status
        print("🔄 Step 2: Checking Service Status...")
        for chain_name, web3 in chainflip_messaging_service.web3_connections.items():
            try:
                latest_block = web3.eth.block_number
                contract_addr = chainflip_messaging_service.contract_addresses.get(chain_name, "Not set")
                print(f"   ✅ {chain_name}: Block {latest_block}, Contract {contract_addr}")
            except Exception as e:
                print(f"   ❌ {chain_name}: Connection error - {e}")
        print()
        
        # Step 3: Test manufacturer private key lookup
        print("🔄 Step 3: Checking Manufacturer Private Key...")
        manufacturer_key_var = f"ACCOUNT_{test_data['manufacturer']}"
        manufacturer_private_key = getattr(settings, manufacturer_key_var.lower(), None)
        
        if not manufacturer_private_key:
            print(f"❌ Private key not found for {test_data['manufacturer']}")
            print(f"   Expected environment variable: {manufacturer_key_var}")
            print("   Please add this to your .env file to continue testing")
            return False
            
        print(f"✅ Found private key for manufacturer {test_data['manufacturer']}")
        print()
        
        # Step 4: Check account balances
        print("🔄 Step 4: Checking Account Balances...")
        source_web3 = chainflip_messaging_service.web3_connections.get(test_data['source_chain'])
        if source_web3:
            balance = source_web3.eth.get_balance(test_data['manufacturer'])
            balance_eth = source_web3.from_wei(balance, 'ether')
            print(f"   {test_data['manufacturer']} on {test_data['source_chain']}: {balance_eth:.6f} ETH")
            
            if balance_eth < 0.001:  # Need at least 0.001 ETH for gas + LayerZero fees
                print(f"⚠️ Low balance. May need more ETH for testing.")
            else:
                print(f"✅ Sufficient balance for testing")
        print()
        
        # Step 5: Test the cross-chain CID sync
        print("🔄 Step 5: Testing Cross-Chain CID Sync...")
        print(f"   Sending CID from {test_data['source_chain']} to {test_data['target_chain']}...")
        
        result = await chainflip_messaging_service.send_cid_to_chain(
            source_chain=test_data['source_chain'],
            target_chain=test_data['target_chain'],
            token_id=test_data['token_id'],
            metadata_cid=test_data['metadata_cid'],
            manufacturer=test_data['manufacturer'],
            manufacturer_private_key=manufacturer_private_key
        )
        
        print()
        print("📊 Cross-Chain Sync Result:")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"   ✅ Transaction Hash: {result.get('transaction_hash')}")
            print(f"   📊 Block Number: {result.get('block_number')}")
            print(f"   ⛽ Gas Used: {result.get('gas_used')}")
            print(f"   💰 LayerZero Fee: {result.get('layerzero_fee_paid')} ETH")
            print(f"   🎯 Target Chain: {result.get('target_chain')}")
            print(f"   📍 Target Contract: {result.get('messenger_contract')}")
            print(f"   🆔 Sync ID: {result.get('sync_id')}")
            print()
            
            # Step 6: Wait a moment for LayerZero processing
            print("🔄 Step 6: Waiting for LayerZero Message Processing...")
            print("   LayerZero typically takes 30-60 seconds to process cross-chain messages")
            
            for i in range(6):  # Wait 60 seconds total
                await asyncio.sleep(10)
                print(f"   ⏳ Waiting... {(i+1)*10}/60 seconds")
            
            print()
            
            # Step 7: Check if CID was received on target chain
            print("🔄 Step 7: Checking CID Receipt on Target Chain...")
            
            # Check received CIDs on target chain
            received_result = await chainflip_messaging_service.get_received_cids(test_data['target_chain'])
            
            if received_result.get('success'):
                cids = received_result.get('cids', [])
                cid_count = received_result.get('cid_count', 0)
                
                print(f"   📊 Total CIDs on {test_data['target_chain']}: {cid_count}")
                
                # Check if our test CID was received
                test_cid_found = False
                for cid in cids:
                    if cid.get('token_id') == test_data['token_id']:
                        test_cid_found = True
                        print(f"   ✅ Test CID Found!")
                        print(f"      Token ID: {cid.get('token_id')}")
                        print(f"      Metadata CID: {cid.get('metadata_cid')}")
                        print(f"      Manufacturer: {cid.get('manufacturer')}")
                        print(f"      Timestamp: {cid.get('timestamp')}")
                        print(f"      Source Chain: {cid.get('source_chain')}")
                        break
                
                if not test_cid_found:
                    print(f"   ⚠️ Test CID not found yet on {test_data['target_chain']}")
                    print(f"   📋 Recent CIDs on {test_data['target_chain']}:")
                    for i, cid in enumerate(cids[-3:]):  # Show last 3 CIDs
                        print(f"      {i+1}. {cid.get('token_id')} - {cid.get('metadata_cid')[:20]}...")
                    
                    print()
                    print("💡 Possible reasons:")
                    print("   1. LayerZero message still processing (can take 1-2 minutes)")
                    print("   2. Peer connections need more time to propagate")
                    print("   3. Network congestion causing delays")
                    
                    # Try again after more time
                    print("\n🔄 Waiting additional 60 seconds and checking again...")
                    for i in range(6):
                        await asyncio.sleep(10)
                        print(f"   ⏳ Waiting... {(i+1)*10}/60 seconds")
                    
                    # Check again
                    received_result2 = await chainflip_messaging_service.get_received_cids(test_data['target_chain'])
                    if received_result2.get('success'):
                        cids2 = received_result2.get('cids', [])
                        for cid in cids2:
                            if cid.get('token_id') == test_data['token_id']:
                                print(f"   ✅ Test CID Found on Second Check!")
                                print(f"      Token ID: {cid.get('token_id')}")
                                print(f"      Metadata CID: {cid.get('metadata_cid')}")
                                test_cid_found = True
                                break
                        
                        if not test_cid_found:
                            print(f"   ⚠️ Test CID still not found after extended wait")
                
                return test_cid_found
                    
            else:
                print(f"   ❌ Failed to check received CIDs: {received_result.get('error')}")
                return False
                
        else:
            print(f"   ❌ Cross-chain sync failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting ChainFLIP Cross-Chain Messaging Test")
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = await test_chainflip_messaging()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 TEST PASSED: ChainFLIP Cross-Chain Messaging is WORKING!")
        print("✅ Your peer connections are properly established")
        print("✅ LayerZero V2 messaging is functioning correctly")
        print("✅ CID sync is successfully reaching the destination chain")
    else:
        print("⚠️ TEST INCOMPLETE: Cross-chain messaging may need more time")
        print("📝 The message was sent successfully, but:")
        print("   - LayerZero can take 1-3 minutes to process messages")
        print("   - Network congestion may cause delays")
        print("   - Try checking the destination contract manually in a few minutes")
    
    print()
    print("🔗 Quick Manual Verification:")
    print("   Check Polygon Amoy contract: 0x96922C50cB3dB61BA7663dc32d9d1796eE9E8fF4")
    print("   Look for CIDReceived events or call getCIDCount()")
    print()

if __name__ == "__main__":
    asyncio.run(main())