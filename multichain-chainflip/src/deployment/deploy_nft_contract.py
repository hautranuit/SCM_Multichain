"""
Deploy ChainFLIP Product NFT Contract
"""
import asyncio
import os
import json
import time
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from solcx import compile_source, install_solc, set_solc_version

# Install and set Solidity compiler version
install_solc('0.8.20')
set_solc_version('0.8.20')

async def deploy_chainflip_nft_contract():
    """Deploy the ChainFLIP Product NFT contract to Base Sepolia"""
    try:
        print("🚀 Deploying ChainFLIP Product NFT Contract...")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv('/app/multichain-chainflip/backend/.env')
        
        # Network configuration
        rpc_url = os.getenv('BASE_SEPOLIA_RPC', 'https://sepolia.base.org')
        chain_id = int(os.getenv('BASE_SEPOLIA_CHAIN_ID', '84532'))
        private_key = os.getenv('DEPLOYER_PRIVATE_KEY')
        
        if not private_key:
            raise Exception("DEPLOYER_PRIVATE_KEY not found in environment")
        
        print(f"🔗 Connecting to Base Sepolia: {rpc_url}")
        print(f"⚡ Chain ID: {chain_id}")
        
        # Setup Web3 connection
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if not web3.is_connected():
            raise Exception("Failed to connect to Base Sepolia")
        
        print(f"✅ Connected to Base Sepolia, latest block: {web3.eth.block_number}")
        
        # Setup account
        account = Account.from_key(private_key)
        print(f"📝 Deployer account: {account.address}")
        
        # Check balance
        balance = web3.eth.get_balance(account.address)
        print(f"💰 Account balance: {Web3.from_wei(balance, 'ether')} ETH")
        
        if balance == 0:
            raise Exception("Deployer account has no ETH for gas fees")
        
        # Read and compile contract
        print("📄 Reading contract source...")
        with open('/app/multichain-chainflip/backend/ChainFLIPProductNFT.sol', 'r') as file:
            contract_source = file.read()
        
        print("🔨 Compiling contract...")
        
        # Prepare the contract with OpenZeppelin imports
        # For deployment, we need to handle OpenZeppelin dependencies
        # Using a simplified compilation approach
        compiled_sol = compile_source(
            contract_source,
            import_remappings=[
                "@openzeppelin/contracts/=https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.9.0/contracts/"
            ],
            optimize=True,
            optimize_runs=200
        )
        
        # Get contract interface
        contract_id, contract_interface = compiled_sol.popitem()
        print(f"✅ Contract compiled successfully: {contract_id}")
        
        # Get gas price
        gas_price = web3.eth.gas_price
        print(f"⛽ Current gas price: {Web3.from_wei(gas_price, 'gwei')} Gwei")
        
        # Prepare constructor parameters
        contract_name = "ChainFLIP Product NFT"
        contract_symbol = "CFPNFT"
        initial_owner = account.address
        
        # Create contract
        contract = web3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        print("🔧 Preparing deployment transaction...")
        
        # Build constructor transaction
        constructor_txn = contract.constructor(
            contract_name,
            contract_symbol,
            initial_owner
        ).build_transaction({
            'from': account.address,
            'gas': 3000000,  # Generous gas limit
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(account.address),
            'value': 0
        })
        
        print(f"📋 Transaction details:")
        print(f"   Gas limit: {constructor_txn['gas']}")
        print(f"   Gas price: {Web3.from_wei(constructor_txn['gasPrice'], 'gwei')} Gwei")
        print(f"   Estimated cost: {Web3.from_wei(constructor_txn['gas'] * constructor_txn['gasPrice'], 'ether')} ETH")
        
        # Sign and send transaction
        print("🔐 Signing transaction...")
        signed_txn = account.sign_transaction(constructor_txn)
        
        print("📤 Sending deployment transaction...")
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"✅ Transaction sent: {tx_hash_hex}")
        print("⏳ Waiting for confirmation...")
        
        # Wait for transaction receipt
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if tx_receipt.status == 1:
            contract_address = tx_receipt.contractAddress
            print(f"🎉 Contract deployed successfully!")
            print(f"📍 Contract address: {contract_address}")
            print(f"🧾 Transaction hash: {tx_hash_hex}")
            print(f"📦 Block number: {tx_receipt.blockNumber}")
            print(f"⛽ Gas used: {tx_receipt.gasUsed}")
            
            # Verify the contract is working
            print("🔍 Verifying contract deployment...")
            deployed_contract = web3.eth.contract(
                address=contract_address,
                abi=contract_interface['abi']
            )
            
            # Test basic functions
            try:
                name = deployed_contract.functions.name().call()
                symbol = deployed_contract.functions.symbol().call()
                version = deployed_contract.functions.VERSION().call()
                owner = deployed_contract.functions.owner().call()
                
                print(f"✅ Contract verification successful:")
                print(f"   Name: {name}")
                print(f"   Symbol: {symbol}")
                print(f"   Version: {version}")
                print(f"   Owner: {owner}")
                
                # Save deployment info
                deployment_info = {
                    "contract_name": "ChainFLIPProductNFT",
                    "contract_address": contract_address,
                    "transaction_hash": tx_hash_hex,
                    "block_number": tx_receipt.blockNumber,
                    "gas_used": tx_receipt.gasUsed,
                    "deployer": account.address,
                    "network": "Base Sepolia",
                    "chain_id": chain_id,
                    "deployment_timestamp": int(time.time()),
                    "contract_version": version,
                    "abi": contract_interface['abi']
                }
                
                # Save to file
                with open('/app/multichain-chainflip/backend/nft_deployment.json', 'w') as f:
                    json.dump(deployment_info, f, indent=2)
                
                print(f"💾 Deployment info saved to nft_deployment.json")
                
                return {
                    "success": True,
                    "contract_address": contract_address,
                    "transaction_hash": tx_hash_hex,
                    "deployment_info": deployment_info
                }
                
            except Exception as verify_error:
                print(f"⚠️ Contract verification failed: {verify_error}")
                return {
                    "success": True,
                    "contract_address": contract_address,
                    "transaction_hash": tx_hash_hex,
                    "verification_error": str(verify_error)
                }
        else:
            raise Exception(f"Contract deployment failed with status: {tx_receipt.status}")
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    result = asyncio.run(deploy_chainflip_nft_contract())
    print(f"\n🏁 Deployment result: {result}")