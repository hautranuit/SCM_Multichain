"""
Official LayerZero OFT Bridge Service
Uses official @layerzerolabs/oft-evm interfaces to eliminate the 0x3ee5aeb5 error
Updated with NEW contracts that include deposit/withdraw functionality
"""
import asyncio
import json
import time
from decimal import Decimal
from typing import Dict, List, Optional, Any
from web3 import Web3
from eth_account import Account
from app.core.config import get_settings
from app.core.database import get_database

settings = get_settings()

def convert_decimals_to_float(obj):
    """Recursively convert all Decimal objects to float for MongoDB compatibility"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_decimals_to_float(item) for item in obj)
    else:
        return obj

# Official LayerZero V2 OFT ABI (from @layerzerolabs/oft-evm)
OFFICIAL_LAYERZERO_OFT_ABI = [
    # Official LayerZero OFT send function
    {
        "inputs": [
            {"name": "_sendParam", "type": "tuple", "components": [
                {"name": "dstEid", "type": "uint32"},
                {"name": "to", "type": "bytes32"},
                {"name": "amountLD", "type": "uint256"},
                {"name": "minAmountLD", "type": "uint256"},
                {"name": "extraOptions", "type": "bytes"},
                {"name": "composeMsg", "type": "bytes"},
                {"name": "oftCmd", "type": "bytes"}
            ]},
            {"name": "_fee", "type": "tuple", "components": [
                {"name": "nativeFee", "type": "uint256"},
                {"name": "lzTokenFee", "type": "uint256"}
            ]},
            {"name": "_refundAddress", "type": "address"}
        ],
        "name": "send",
        "outputs": [
            {"name": "receipt", "type": "tuple", "components": [
                {"name": "guid", "type": "bytes32"},
                {"name": "nonce", "type": "uint64"},
                {"name": "fee", "type": "tuple", "components": [
                    {"name": "nativeFee", "type": "uint256"},
                    {"name": "lzTokenFee", "type": "uint256"}
                ]}
            ]}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    # Official LayerZero OFT quoteSend function
    {
        "inputs": [
            {"name": "_sendParam", "type": "tuple", "components": [
                {"name": "dstEid", "type": "uint32"},
                {"name": "to", "type": "bytes32"},
                {"name": "amountLD", "type": "uint256"},
                {"name": "minAmountLD", "type": "uint256"},
                {"name": "extraOptions", "type": "bytes"},
                {"name": "composeMsg", "type": "bytes"},
                {"name": "oftCmd", "type": "bytes"}
            ]},
            {"name": "_payInLzToken", "type": "bool"}
        ],
        "name": "quoteSend",
        "outputs": [
            {"name": "fee", "type": "tuple", "components": [
                {"name": "nativeFee", "type": "uint256"},
                {"name": "lzTokenFee", "type": "uint256"}
            ]}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    # NEW: Deposit function - Users can deposit ETH to get cfWETH
    {
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    # NEW: Withdraw function - Users can withdraw cfWETH to get ETH
    {
        "inputs": [{"name": "amount", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # NEW: Get contract ETH balance
    {
        "inputs": [],
        "name": "getContractBalance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    # Standard ERC20 and OFT functions
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol", 
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "endpoint",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "_eid", "type": "uint32"}],
        "name": "peers",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    # Admin mint function (for initial setup only)
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable", 
        "type": "function"
    }
]

class LayerZeroOFTBridgeService:
    def __init__(self):
        self.database = None
        
        # Multi-chain Web3 connections
        self.web3_connections = {}
        
        # Separated Architecture Configuration: ChainFlipOFT + ETHWrapper (UPDATED ADDRESSES)
        self.oft_contracts = {
            "optimism_sepolia": {
                "oft_address": "0x6478eAB366A16d96ae910fd16F6770DDa1845648",
                "wrapper_address": "0x5428793EBd36693c993D6B3f8f2641C46121ec29",
                "rpc": settings.optimism_sepolia_rpc,
                "chain_id": 11155420,
                "layerzero_eid": 40232,
                "layerzero_endpoint": "0x6EDCE65403992e310A62460808c4b910D972f10f",
            },
            "arbitrum_sepolia": {
                "oft_address": "0x441C06d8548De93d64072F781e15E16A7c316b67",
                "wrapper_address": "0x5952569276eA7f7eF95B910EAd0a67067A518188",
                "rpc": settings.arbitrum_sepolia_rpc,
                "chain_id": 421614,
                "layerzero_eid": 40231,
                "layerzero_endpoint": "0x6EDCE65403992e310A62460808c4b910D972f10f",
            },
            "polygon_amoy": {
                "oft_address": "0x865F1Dac1d8E17f492FFce578095b49f3D604ad4",
                "wrapper_address": "0xA471c665263928021AF5aa7852724b6f757005e1",
                "rpc": settings.polygon_pos_rpc,
                "chain_id": 80002,
                "layerzero_eid": 40267,
                "layerzero_endpoint": "0x6EDCE65403992e310A62460808c4b910D972f10f",
            }
            # Cardona removed due to LayerZero V2 compatibility issues
        }
        
        # Contract instances
        self.oft_instances = {}
        
        # Account for signing transactions
        self.current_account = None
        
    async def initialize(self):
        """Initialize LayerZero OFT bridge service with official interfaces"""
        self.database = await get_database()
        
        # Initialize account
        from app.services.multi_account_manager import address_key_manager
        deployer_account_info = address_key_manager.get_account_info_for_address('0x032041b4b356fEE1496805DD4749f181bC736FFA')
        if deployer_account_info:
            self.current_account = deployer_account_info['account']
            print(f"🔑 Official LayerZero OFT Bridge using account: {self.current_account.address}")
        
        # Initialize chain connections and contracts
        await self._initialize_connections()
        
        print("✅ Official LayerZero OFT Bridge Service initialized")
        print("🌉 Using @layerzerolabs/oft-evm official interface")
        print("✨ NEW: Contracts include deposit/withdraw functionality!")
        
    async def _initialize_connections(self):
        """Initialize Web3 connections and official OFT contract instances"""
        
        for chain_name, config in self.oft_contracts.items():
            try:
                # Initialize Web3 connection
                web3 = Web3(Web3.HTTPProvider(config['rpc']))
                
                if web3.is_connected():
                    self.web3_connections[chain_name] = web3
                    
                    # Initialize OFT contract if address is configured
                    if config.get('address'):
                        oft_contract = web3.eth.contract(
                            address=config['address'],
                            abi=OFFICIAL_LAYERZERO_OFT_ABI
                        )
                        self.oft_instances[chain_name] = oft_contract
                        print(f"✅ Connected to {chain_name} - Official OFT contract ready at {config['address']}")
                        print(f"   ✨ NEW: Supports deposit() and withdraw() functions")
                    else:
                        print(f"⚠️ Connected to {chain_name} - Contract address not configured yet")
                        print(f"   Deploy contract first: npx hardhat run scripts/deploy-official-oft.js --network {chain_name.replace('_', '')}")
                    
                    print(f"🔗 LayerZero Endpoint: {config['layerzero_endpoint']}")
                    print(f"🆔 LayerZero EID: {config['layerzero_eid']}")
                    
                else:
                    print(f"❌ Failed to connect to {chain_name}")
                    
            except Exception as e:
                print(f"⚠️ Error initializing {chain_name}: {e}")

    async def deposit_eth_for_tokens(
        self,
        chain: str,
        user_address: str,
        amount_eth: float
    ) -> Dict[str, Any]:
        """
        NEW FUNCTION: Deposit ETH to get cfWETH tokens (1:1 ratio)
        """
        try:
            print(f"\n💰 === DEPOSITING ETH FOR cfWETH TOKENS ===")
            print(f"🌐 Chain: {chain}")
            print(f"👤 User: {user_address}")
            print(f"💸 Amount: {amount_eth} ETH")
            
            # Get Web3 and contract instances
            web3 = self.web3_connections.get(chain)
            oft_contract = self.oft_instances.get(chain)
            
            if not web3 or not oft_contract:
                return {"success": False, "error": f"Chain {chain} not available"}
            
            # Get user account for signing
            from app.services.multi_account_manager import address_key_manager
            user_account_info = address_key_manager.get_account_info_for_address(user_address)
            if not user_account_info:
                return {"success": False, "error": f"No private key available for user address {user_address}"}
            
            user_account = user_account_info['account']
            amount_wei = Web3.to_wei(amount_eth, 'ether')
            
            # Check user ETH balance
            eth_balance = web3.eth.get_balance(user_account.address)
            if eth_balance < amount_wei:
                return {"success": False, "error": f"Insufficient ETH balance. Have: {Web3.from_wei(eth_balance, 'ether')} ETH, Need: {amount_eth} ETH"}
            
            # Build deposit transaction
            nonce = web3.eth.get_transaction_count(user_account.address)
            
            transaction = oft_contract.functions.deposit().build_transaction({
                'from': user_account.address,
                'value': amount_wei,
                'gas': 100000,
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id
            })
            
            # Sign and send transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, user_account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"📤 Deposit transaction sent: {tx_hash.hex()}")
            
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                # Check new cfWETH balance
                new_balance = oft_contract.functions.balanceOf(user_account.address).call()
                new_balance_eth = float(Web3.from_wei(new_balance, 'ether'))
                
                print(f"✅ ETH deposit successful!")
                print(f"💳 New cfWETH balance: {new_balance_eth} cfWETH")
                
                return {
                    "success": True,
                    "transaction_hash": tx_hash.hex(),
                    "amount_deposited": amount_eth,
                    "new_cfweth_balance": new_balance_eth,
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber
                }
            else:
                return {"success": False, "error": "Deposit transaction failed"}
                
        except Exception as e:
            print(f"❌ ETH deposit error: {e}")
            return {"success": False, "error": str(e)}

    async def estimate_oft_transfer_fee(
        self, 
        from_chain: str, 
        to_chain: str, 
        amount_eth: float
    ) -> Dict[str, Any]:
        """
        Estimate LayerZero OFT transfer fee using official quoteSend function
        """
        try:
            # Check if OFT contracts are deployed
            source_config = self.oft_contracts[from_chain]
            target_config = self.oft_contracts[to_chain]
            
            if not source_config.get('address') or not target_config.get('address'):
                return {
                    "success": False, 
                    "error": "Official OFT contracts not yet deployed. Deploy contracts first.",
                    "deployment_needed": True,
                    "deploy_command": "npx hardhat run scripts/deploy-official-oft.js --network optimismSepolia"
                }
            
            # Use official LayerZero V2 quoteSend function
            source_web3 = self.web3_connections.get(from_chain)
            oft_contract = self.oft_instances[from_chain]
            
            if source_web3 and oft_contract:
                # Convert amount to Wei
                amount_wei = Web3.to_wei(amount_eth, 'ether')
                
                # Convert recipient address to bytes32 format
                recipient_addr = "0x28918ecf013F32fAf45e05d62B4D9b207FCae784"
                recipient_bytes32 = Web3.to_bytes(hexstr=recipient_addr.lower().replace('0x', '').zfill(64))
                
                print(f"💸 Calling official LayerZero V2 quoteSend on {from_chain} for {to_chain}")
                
                # Create official LayerZero V2 SendParam struct
                send_param = (
                    target_config['layerzero_eid'],  # dstEid
                    recipient_bytes32,               # to
                    amount_wei,                      # amountLD
                    amount_wei,                      # minAmountLD
                    b'',                            # extraOptions
                    b'',                            # composeMsg
                    b''                             # oftCmd
                )
                
                # Call the official quoteSend function with struct parameter
                quote_result = oft_contract.functions.quoteSend(
                    send_param,                     # _sendParam struct
                    False                           # _payInLzToken
                ).call()
                
                # Extract fees from the tuple result
                native_fee_wei = quote_result[0]  # nativeFee
                lz_token_fee = quote_result[1]    # lzTokenFee
                
                native_fee_eth = float(Web3.from_wei(native_fee_wei, 'ether'))
                
                print(f"✅ Official LayerZero V2 quoteSend fee: {native_fee_eth} ETH for {from_chain} → {to_chain}")
                
                return {
                    "success": True,
                    "native_fee_wei": native_fee_wei,
                    "native_fee_eth": native_fee_eth,
                    "lz_token_fee": lz_token_fee,
                    "total_cost_eth": amount_eth + native_fee_eth,
                    "bridge_type": "Official LayerZero V2 OFT with Deposit/Withdraw",
                    "from_chain": from_chain,
                    "to_chain": to_chain,
                    "amount_eth": amount_eth,
                    "fee_method": "official_v2_quoteSend"
                }
            
            return {"success": False, "error": "Web3 connection or contract not available"}
                
        except Exception as e:
            return {"success": False, "error": f"Fee estimation error: {str(e)}"}

    async def transfer_eth_layerzero_oft(
        self,
        from_chain: str,
        to_chain: str,
        from_address: str,
        to_address: str,
        amount_eth: float,
        escrow_id: str
    ) -> Dict[str, Any]:
        """
        Execute LayerZero OFT cross-chain ETH transfer using official interface
        NEW: Automatically handles ETH deposit to get cfWETH tokens
        """
        try:
            print(f"\n🌉 === OFFICIAL LAYERZERO OFT CROSS-CHAIN TRANSFER V2 ===")
            print(f"📤 From: {from_chain} ({from_address})")
            print(f"📥 To: {to_chain} ({to_address})")
            print(f"💰 Amount: {amount_eth} ETH")
            print(f"🔗 Escrow ID: {escrow_id}")
            print(f"✨ NEW: Auto deposit ETH → cfWETH if needed")
            
            # Get Web3 instances
            source_web3 = self.web3_connections.get(from_chain)
            target_web3 = self.web3_connections.get(to_chain)
            
            if not source_web3:
                return {"success": False, "error": f"Source chain {from_chain} not connected"}
            if not target_web3:
                return {"success": False, "error": f"Target chain {to_chain} not connected"}
            
            # Get configurations
            source_config = self.oft_contracts[from_chain]
            target_config = self.oft_contracts[to_chain]
            
            # Check if OFT contracts are deployed
            if not source_config.get('address') or not target_config.get('address'):
                return {
                    "success": False,
                    "error": "Official OFT contracts not deployed yet. Please deploy contracts first.",
                    "deployment_instructions": {
                        "step1": "Deploy official LayerZero OFT contracts on all chains",
                        "step2": "Set peer addresses between chains", 
                        "step3": "Update configuration with deployed addresses",
                        "deploy_command": "npx hardhat run scripts/deploy-official-oft.js --network optimismSepolia"
                    }
                }
            
            # Convert amount to Wei
            amount_wei = Web3.to_wei(amount_eth, 'ether')
            
            # Get user account for signing
            from app.services.multi_account_manager import address_key_manager
            user_account_info = address_key_manager.get_account_info_for_address(from_address)
            if not user_account_info:
                return {"success": False, "error": f"No private key available for user address {from_address}"}
            
            user_account = user_account_info['account']
            
            # STEP 1: Check token balance and deposit ETH if needed
            print(f"\n💰 === STEP 1: CHECK TOKEN BALANCE ===")
            oft_contract = self.oft_instances[from_chain]
            
            # Check current cfWETH balance
            oft_balance = oft_contract.functions.balanceOf(user_account.address).call()
            oft_balance_eth = float(Web3.from_wei(oft_balance, 'ether'))
            
            print(f"💳 User cfWETH balance: {oft_balance_eth} cfWETH")
            print(f"🎯 Required amount: {amount_eth} cfWETH")
            
            if oft_balance_eth < amount_eth:
                needed_amount = amount_eth - oft_balance_eth
                print(f"⚠️ Insufficient cfWETH balance. Need to deposit {needed_amount} ETH")
                
                # NEW: Use deposit function instead of mint
                deposit_result = await self.deposit_eth_for_tokens(
                    from_chain, from_address, needed_amount
                )
                
                if not deposit_result["success"]:
                    return {"success": False, "error": f"Failed to deposit ETH for cfWETH tokens: {deposit_result['error']}"}
                    
                print(f"✅ Successfully deposited {needed_amount} ETH for cfWETH tokens!")
            else:
                print(f"✅ Sufficient cfWETH tokens available for transfer")
            
            # STEP 2: Execute LayerZero OFT transfer
            print(f"\n🚀 === STEP 2: EXECUTE OFFICIAL LAYERZERO OFT TRANSFER ===")
            oft_result = await self._execute_official_oft_send(
                source_web3, from_chain, to_chain, user_account, to_address, amount_wei
            )
            
            if not oft_result["success"]:
                return {"success": False, "error": f"Failed to execute OFT transfer: {oft_result['error']}"}
            
            # STEP 3: Record transfer in database
            print(f"\n📊 === STEP 3: RECORD TRANSFER ===")
            transfer_record = {
                "transfer_id": escrow_id,
                "from_chain": from_chain,
                "to_chain": to_chain,
                "from_address": from_address,
                "to_address": to_address,
                "amount_eth": amount_eth,
                "bridge_type": "official_layerzero_oft_v2",
                "status": "completed",
                "oft_transaction_hash": oft_result.get("transaction_hash"),
                "layerzero_eid_source": source_config['layerzero_eid'],
                "layerzero_eid_target": target_config['layerzero_eid'],
                "native_fee_paid": oft_result.get("native_fee_paid"),
                "timestamp": time.time(),
                "block_number_source": oft_result.get("block_number"),
                "gas_used": oft_result.get("gas_used"),
                "interface_used": "official_layerzero_v2_oft_with_deposit_withdraw",
                "deposit_enabled": True
            }
            
            # Convert Decimal objects for MongoDB
            transfer_record = convert_decimals_to_float(transfer_record)
            
            # Save to database
            try:
                await self.database.transfers.insert_one(transfer_record)
                print(f"✅ Transfer recorded in database")
            except Exception as e:
                print(f"⚠️ Warning: Failed to record transfer in database: {e}")
            
            print(f"\n🎉 === OFFICIAL LAYERZERO OFT TRANSFER V2 COMPLETED ===")
            print(f"✅ Official interface transfer successful!")
            print(f"🔗 Source TX: {oft_result.get('transaction_hash')}")
            print(f"💰 Amount bridged: {amount_eth} ETH")
            print(f"🌉 Bridge type: Official LayerZero V2 OFT with Deposit/Withdraw")
            
            return {
                "success": True,
                "transfer_id": escrow_id,
                "bridge_type": "official_layerzero_oft_v2",
                "amount_transferred": amount_eth,
                "oft_transaction_hash": oft_result.get("transaction_hash"),
                "native_fee_paid": oft_result.get("native_fee_paid"),
                "layerzero_guid": oft_result.get("layerzero_guid"),
                "message": "Official LayerZero OFT V2 transfer completed successfully",
                "is_decentralized": True,
                "interface_used": "official_layerzero_v2_oft_with_deposit_withdraw",
                "deposit_enabled": True
            }
            
        except Exception as e:
            print(f"❌ Official LayerZero OFT transfer error: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_official_oft_send(
        self,
        web3: Web3,
        from_chain: str,
        to_chain: str,
        user_account,
        to_address: str,
        amount_wei: int
    ) -> Dict[str, Any]:
        """Execute LayerZero OFT send using official V2 interface"""
        try:
            source_config = self.oft_contracts[from_chain]
            target_config = self.oft_contracts[to_chain]
            
            print(f"🔗 Official OFT Send: {from_chain} → {to_chain}")
            print(f"📍 Contract: {source_config['address']}")
            
            oft_contract = web3.eth.contract(
                address=source_config['address'],
                abi=OFFICIAL_LAYERZERO_OFT_ABI
            )
            
            # Convert recipient address to bytes32 format
            recipient_bytes32 = Web3.to_bytes(hexstr=to_address.lower().replace('0x', '').zfill(64))
            print(f"🔧 Recipient bytes32: {recipient_bytes32.hex()}")
            
            # Get fee estimate using official quoteSend
            fee_estimate = await self.estimate_oft_transfer_fee(from_chain, to_chain, float(Web3.from_wei(amount_wei, 'ether')))
            if not fee_estimate["success"]:
                return {"success": False, "error": f"Fee estimation failed: {fee_estimate['error']}"}
            
            native_fee = fee_estimate["native_fee_wei"]
            print(f"💳 Using official LayerZero fee: {Web3.from_wei(native_fee, 'ether')} ETH")
            
            # Create official LayerZero V2 SendParam struct
            send_param = (
                target_config['layerzero_eid'],  # dstEid
                recipient_bytes32,               # to
                amount_wei,                      # amountLD
                amount_wei,                      # minAmountLD
                b'',                            # extraOptions
                b'',                            # composeMsg
                b''                             # oftCmd
            )
            
            messaging_fee = (native_fee, 0)  # (nativeFee, lzTokenFee)
            
            # Test call first to validate
            try:
                oft_contract.functions.send(
                    send_param,
                    messaging_fee,
                    user_account.address
                ).call({
                    'from': user_account.address,
                    'value': native_fee
                })
                print("✅ Official OFT send simulation successful")
            except Exception as sim_error:
                return {"success": False, "error": f"Official OFT send simulation failed: {sim_error}"}
            
            # Build transaction
            nonce = web3.eth.get_transaction_count(user_account.address)
            
            transaction = oft_contract.functions.send(
                send_param,
                messaging_fee,
                user_account.address
            ).build_transaction({
                'from': user_account.address,
                'value': native_fee,
                'gas': 500000,
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id
            })
            
            # Sign and send transaction
            print(f"✍️ Signing and sending official OFT transaction...")
            signed_txn = web3.eth.account.sign_transaction(transaction, user_account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"📤 Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            print(f"⏳ Waiting for transaction confirmation...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print(f"✅ Official OFT send successful!")
                
                # Extract LayerZero GUID from logs
                layerzero_guid = None
                try:
                    for log in receipt.logs:
                        if len(log.topics) > 0:
                            layerzero_guid = log.topics[0].hex()[:32]
                            break
                except:
                    pass
                
                return {
                    "success": True,
                    "transaction_hash": tx_hash.hex(),
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber,
                    "native_fee_paid": float(Web3.from_wei(native_fee, 'ether')),
                    "layerzero_guid": layerzero_guid,
                    "destination_eid": target_config['layerzero_eid'],
                    "interface_used": "official_layerzero_v2_oft_with_deposit_withdraw"
                }
            else:
                return {"success": False, "error": f"Transaction failed - Receipt status: {receipt.status}"}
                
        except Exception as e:
            print(f"❌ Official OFT send error: {e}")
            import traceback
            print(f"🔍 Full error traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

# Initialize service instance
layerzero_oft_bridge_service = LayerZeroOFTBridgeService()
