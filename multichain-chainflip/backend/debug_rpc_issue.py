"""
RPC Debugging Script - Comprehensive transaction issue diagnosis
Tests different scenarios to identify why transactions aren't reaching blockchain
"""
import os
import time
import asyncio
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_all_scenarios():
    """Run comprehensive RPC and transaction tests"""
    
    print("🔍 === COMPREHENSIVE RPC DEBUGGING ===")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Primary OP Sepolia RPC",
            "rpc": "https://sepolia.optimism.io",
            "description": "Official Optimism Sepolia RPC"
        },
        {
            "name": "Alchemy OP Sepolia",
            "rpc": "https://opt-sepolia.g.alchemy.com/v2/demo",
            "description": "Alchemy public demo endpoint"
        },
        {
            "name": "DRPC OP Sepolia",
            "rpc": "https://optimism-sepolia.drpc.org",
            "description": "DRPC public endpoint"
        },
        {
            "name": "Alternative OP RPC",
            "rpc": "https://sepolia.optimism.io/rpc",
            "description": "Alternative OP endpoint"
        }
    ]
    
    # Account from .env
    private_key = "5e76179b71fb77d8820a8d5752fdc36974d464b2fe9df7798c9dddeb2002dc32"
    
    working_rpcs = []
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"🧪 TESTING: {scenario['name']}")
        print(f"🌐 RPC: {scenario['rpc']}")
        print(f"📝 Description: {scenario['description']}")
        print(f"{'='*60}")
        
        try:
            result = await test_rpc_scenario(scenario['rpc'], private_key, scenario['name'])
            if result['success']:
                working_rpcs.append(scenario)
                print(f"✅ {scenario['name']} - WORKING!")
            else:
                print(f"❌ {scenario['name']} - FAILED: {result['error']}")
                
        except Exception as e:
            print(f"❌ {scenario['name']} - EXCEPTION: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    
    if working_rpcs:
        print(f"✅ Working RPCs ({len(working_rpcs)}):")
        for rpc in working_rpcs:
            print(f"   - {rpc['name']}: {rpc['rpc']}")
    else:
        print(f"❌ NO WORKING RPCs FOUND")
        print(f"🔍 This indicates a systematic issue:")
        print(f"   1. Network connectivity problems")
        print(f"   2. Private key/account issues")
        print(f"   3. Web3 library configuration")
        print(f"   4. Firewall/proxy blocking requests")

async def test_rpc_scenario(rpc_url: str, private_key: str, rpc_name: str) -> dict:
    """Test a specific RPC endpoint comprehensively"""
    
    result = {
        "success": False,
        "rpc_url": rpc_url,
        "tests": {},
        "error": None,
        "transaction_hash": None
    }
    
    try:
        # Test 1: Basic Connection
        print(f"🔍 Test 1: Basic Connection")
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not web3.is_connected():
            result["error"] = "Connection failed"
            print(f"   ❌ Connection failed")
            return result
        
        print(f"   ✅ Connected successfully")
        result["tests"]["connection"] = True
        
        # Test 2: Network Information
        print(f"🔍 Test 2: Network Information")
        try:
            chain_id = web3.eth.chain_id
            latest_block = web3.eth.block_number
            gas_price = web3.eth.gas_price
            
            print(f"   ✅ Chain ID: {chain_id}")
            print(f"   ✅ Latest Block: {latest_block}")
            print(f"   ✅ Gas Price: {Web3.from_wei(gas_price, 'gwei')} gwei")
            
            result["tests"]["network_info"] = True
            
            if chain_id != 11155420:
                result["error"] = f"Wrong chain ID: {chain_id} (expected 11155420)"
                print(f"   ❌ Wrong chain ID: {chain_id}")
                return result
                
        except Exception as e:
            result["error"] = f"Network info failed: {e}"
            print(f"   ❌ Network info failed: {e}")
            return result
        
        # Test 3: Account Setup
        print(f"🔍 Test 3: Account Setup")
        try:
            account = web3.eth.account.from_key(private_key)
            balance = web3.eth.get_balance(account.address)
            balance_eth = Web3.from_wei(balance, 'ether')
            nonce = web3.eth.get_transaction_count(account.address)
            
            print(f"   ✅ Account: {account.address}")
            print(f"   ✅ Balance: {balance_eth} ETH")
            print(f"   ✅ Nonce: {nonce}")
            
            result["tests"]["account_setup"] = True
            
            if balance < Web3.to_wei(0.001, 'ether'):
                result["error"] = f"Insufficient balance: {balance_eth} ETH"
                print(f"   ❌ Insufficient balance")
                return result
                
        except Exception as e:
            result["error"] = f"Account setup failed: {e}"
            print(f"   ❌ Account setup failed: {e}")
            return result
        
        # Test 4: Transaction Preparation
        print(f"🔍 Test 4: Transaction Preparation")
        try:
            # Create minimal transaction
            transaction = {
                'to': account.address,  # Self-transfer
                'value': Web3.to_wei(0.0001, 'ether'),
                'gas': 21000,
                'gasPrice': max(gas_price, Web3.to_wei(1, 'gwei')),
                'nonce': nonce,
                'chainId': chain_id
            }
            
            # Test gas estimation
            estimated_gas = web3.eth.estimate_gas(transaction)
            print(f"   ✅ Gas estimation: {estimated_gas}")
            
            # Test transaction signing
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
            print(f"   ✅ Transaction signed")
            print(f"   📄 Raw TX: {signed_txn.raw_transaction.hex()[:66]}...")
            
            result["tests"]["transaction_prep"] = True
            
        except Exception as e:
            result["error"] = f"Transaction preparation failed: {e}"
            print(f"   ❌ Transaction preparation failed: {e}")
            return result
        
        # Test 5: Transaction Submission
        print(f"🔍 Test 5: Transaction Submission")
        try:
            print(f"   🚀 Submitting transaction...")
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            result["transaction_hash"] = tx_hash_hex
            
            print(f"   📡 Transaction submitted: {tx_hash_hex}")
            
            # Immediate verification
            try:
                immediate_tx = web3.eth.get_transaction(tx_hash)
                if immediate_tx:
                    print(f"   ✅ Transaction found immediately")
                    result["tests"]["immediate_lookup"] = True
                else:
                    print(f"   ❌ Transaction NOT found immediately")
                    result["tests"]["immediate_lookup"] = False
            except Exception as e:
                print(f"   ❌ Immediate lookup failed: {e}")
                result["tests"]["immediate_lookup"] = False
            
            # Wait and check again
            print(f"   ⏳ Waiting 5 seconds...")
            await asyncio.sleep(5)
            
            try:
                delayed_tx = web3.eth.get_transaction(tx_hash)
                if delayed_tx:
                    print(f"   ✅ Transaction found after delay")
                    result["tests"]["delayed_lookup"] = True
                else:
                    print(f"   ❌ Transaction NOT found after delay")
                    result["tests"]["delayed_lookup"] = False
            except Exception as e:
                print(f"   ❌ Delayed lookup failed: {e}")
                result["tests"]["delayed_lookup"] = False
            
            result["tests"]["transaction_submission"] = True
            
        except Exception as e:
            result["error"] = f"Transaction submission failed: {e}"
            print(f"   ❌ Transaction submission failed: {e}")
            return result
        
        # Test 6: Confirmation Attempt
        print(f"🔍 Test 6: Confirmation Attempt")
        try:
            print(f"   ⏳ Waiting for confirmation (60s timeout)...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            print(f"   ✅ Transaction confirmed!")
            print(f"   📦 Block: {receipt.blockNumber}")
            print(f"   ⛽ Gas Used: {receipt.gasUsed}")
            print(f"   ✅ Status: {'Success' if receipt.status == 1 else 'Failed'}")
            
            # Generate block explorer link
            explorer_url = f"https://sepolia-optimism.etherscan.io/tx/{tx_hash_hex}"
            print(f"   🌐 Explorer: {explorer_url}")
            
            result["tests"]["confirmation"] = True
            result["success"] = True
            
            print(f"   🎉 COMPLETE SUCCESS - Real blockchain transaction!")
            
        except Exception as e:
            print(f"   ⚠️ Confirmation timeout: {e}")
            print(f"   🌐 Check manually: https://sepolia-optimism.etherscan.io/tx/{tx_hash_hex}")
            
            # Even if confirmation times out, submission might have worked
            if result["tests"].get("immediate_lookup") or result["tests"].get("delayed_lookup"):
                result["success"] = True
                print(f"   ✅ Transaction was submitted successfully (check explorer)")
            else:
                result["error"] = "Transaction not found on blockchain"
                print(f"   ❌ Transaction appears to be fake")
    
    except Exception as e:
        result["error"] = f"General error: {e}"
        print(f"❌ General error: {e}")
    
    return result

def print_debug_summary(results):
    """Print a comprehensive summary of debugging results"""
    
    print(f"\n{'='*80}")
    print(f"🔍 DEBUGGING SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n📊 RPC Test Results:")
    for rpc_name, result in results.items():
        status = "✅ WORKING" if result['success'] else "❌ FAILED"
        print(f"   {rpc_name}: {status}")
        if not result['success']:
            print(f"      Error: {result.get('error', 'Unknown')}")
        if result.get('transaction_hash'):
            print(f"      TX Hash: {result['transaction_hash']}")
    
    working_count = sum(1 for r in results.values() if r['success'])
    print(f"\n📈 Success Rate: {working_count}/{len(results)} RPCs working")
    
    if working_count == 0:
        print(f"\n🚨 CRITICAL ISSUE IDENTIFIED:")
        print(f"   No RPC endpoints are successfully submitting transactions")
        print(f"   This suggests one of the following:")
        print(f"   1. Network/firewall blocking outbound connections")
        print(f"   2. Private key or account configuration issue")
        print(f"   3. Web3 library or Python environment issue")
        print(f"   4. All test RPCs are experiencing issues")
        
        print(f"\n🔧 RECOMMENDED NEXT STEPS:")
        print(f"   1. Test with a different private key/account")
        print(f"   2. Try from a different network location")
        print(f"   3. Check firewall/proxy settings")
        print(f"   4. Test with a different Web3 library version")
    
    elif working_count < len(results):
        print(f"\n⚠️ PARTIAL SUCCESS:")
        print(f"   Some RPCs work, others don't")
        print(f"   Use the working RPCs in your .env configuration")
    
    else:
        print(f"\n🎉 ALL RPCS WORKING:")
        print(f"   The issue might be specific to the WETH contract calls")
        print(f"   Check the WETH contract addresses and ABI")

if __name__ == "__main__":
    asyncio.run(test_all_scenarios())
