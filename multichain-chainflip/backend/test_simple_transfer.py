"""
Simple ETH Transfer Test
Test basic blockchain transaction capabilities without WETH complexity
"""
import os
import time
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_simple_eth_transfer():
    """Test a simple ETH transfer to identify RPC issues"""
    
    print("🧪 === SIMPLE ETH TRANSFER TEST ===")
    
    # Test different RPC endpoints
    rpc_endpoints = [
        ("Primary OP Sepolia", "https://sepolia.optimism.io"),
        ("Alchemy OP Sepolia", "https://opt-sepolia.g.alchemy.com/v2/demo"),
        ("Alternative OP", "https://optimism-sepolia.drpc.org"),
        ("Public RPC", "https://sepolia.optimism.io/rpc")
    ]
    
    # Account details from .env
    private_key = "5e76179b71fb77d8820a8d5752fdc36974d464b2fe9df7798c9dddeb2002dc32"
    
    for rpc_name, rpc_url in rpc_endpoints:
        print(f"\n🔍 Testing RPC: {rpc_name} ({rpc_url})")
        
        try:
            # Connect to RPC
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not web3.is_connected():
                print(f"❌ {rpc_name} - Connection failed")
                continue
            
            print(f"✅ {rpc_name} - Connected successfully")
            
            # Get basic network info
            chain_id = web3.eth.chain_id
            latest_block = web3.eth.block_number
            gas_price = web3.eth.gas_price
            
            print(f"   Chain ID: {chain_id}")
            print(f"   Latest Block: {latest_block}")
            print(f"   Gas Price: {Web3.from_wei(gas_price, 'gwei')} gwei")
            
            # Create account from private key
            account = web3.eth.account.from_key(private_key)
            print(f"   Account: {account.address}")
            
            # Check balance
            balance = web3.eth.get_balance(account.address)
            balance_eth = Web3.from_wei(balance, 'ether')
            print(f"   Balance: {balance_eth} ETH")
            
            if balance < Web3.to_wei(0.001, 'ether'):
                print(f"⚠️ {rpc_name} - Insufficient balance for test")
                continue
            
            # Create a simple transaction (send to self)
            nonce = web3.eth.get_transaction_count(account.address)
            transaction = {
                'to': account.address,  # Send to self
                'value': Web3.to_wei(0.0001, 'ether'),  # Very small amount
                'gas': 21000,
                'gasPrice': Web3.to_wei(2, 'gwei'),  # Higher gas price
                'nonce': nonce,
                'chainId': chain_id
            }
            
            print(f"   Transaction: {transaction}")
            
            # Test gas estimation
            try:
                estimated_gas = web3.eth.estimate_gas(transaction)
                print(f"   ✅ Gas estimation works: {estimated_gas}")
            except Exception as e:
                print(f"   ❌ Gas estimation failed: {e}")
                continue
            
            # Sign transaction
            try:
                signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
                print(f"   ✅ Transaction signed successfully")
                print(f"   Raw TX: {signed_txn.raw_transaction.hex()}")
            except Exception as e:
                print(f"   ❌ Transaction signing failed: {e}")
                continue
            
            # Submit transaction
            try:
                print(f"   🚀 Submitting transaction...")
                tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
                tx_hash_hex = tx_hash.hex()
                print(f"   📡 Transaction submitted: {tx_hash_hex}")
                
                # Immediate check
                try:
                    immediate_tx = web3.eth.get_transaction(tx_hash)
                    print(f"   ✅ Transaction found immediately: {bool(immediate_tx)}")
                except Exception as e:
                    print(f"   ❌ Transaction NOT found immediately: {e}")
                
                # Wait a bit and check again
                time.sleep(3)
                try:
                    pending_tx = web3.eth.get_transaction(tx_hash)
                    print(f"   ✅ Transaction found after 3s: {bool(pending_tx)}")
                except Exception as e:
                    print(f"   ❌ Transaction NOT found after 3s: {e}")
                
                # Try to wait for confirmation (with shorter timeout)
                try:
                    print(f"   ⏳ Waiting for confirmation (30s timeout)...")
                    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                    print(f"   ✅ Transaction confirmed!")
                    print(f"     Block: {receipt.blockNumber}")
                    print(f"     Gas Used: {receipt.gasUsed}")
                    print(f"     Status: {receipt.status}")
                    
                    # Block explorer link
                    explorer_url = f"https://sepolia-optimism.etherscan.io/tx/{tx_hash_hex}"
                    print(f"   🌐 Block Explorer: {explorer_url}")
                    
                    print(f"   🎉 {rpc_name} - REAL TRANSACTION SUCCESS!")
                    return True  # Found working RPC
                    
                except Exception as e:
                    print(f"   ❌ Transaction confirmation failed: {e}")
                    print(f"   🌐 Check manually: https://sepolia-optimism.etherscan.io/tx/{tx_hash_hex}")
            
            except Exception as e:
                print(f"   ❌ Transaction submission failed: {e}")
                continue
                
        except Exception as e:
            print(f"❌ {rpc_name} - General error: {e}")
            continue
    
    print(f"\n❌ All RPC endpoints failed - this indicates a broader issue")
    return False

if __name__ == "__main__":
    test_simple_eth_transfer()
