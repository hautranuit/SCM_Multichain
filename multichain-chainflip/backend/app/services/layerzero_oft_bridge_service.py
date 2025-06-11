"""
LayerZero OFT (Omnichain Fungible Token) Bridge Service
Replaces custodial relay model with true cross-chain ETH bridging using LayerZero V2

Key Features:
- Lock/mint mechanism instead of custodial transfers
- Uses existing LayerZero infrastructure 
- True decentralized cross-chain bridging
- Integrates with deployed LayerZero contracts
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

# LayerZero OFT Contract ABI (Simplified for ETH bridging)
LAYERZERO_OFT_ABI = [
    {
        "inputs": [
            {"name": "_dstEid", "type": "uint32"},
            {"name": "_to", "type": "bytes32"},
            {"name": "_amountLD", "type": "uint256"},
            {"name": "_minAmountLD", "type": "uint256"},
            {"name": "_extraOptions", "type": "bytes"}
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
    {
        "inputs": [
            {"name": "_dstEid", "type": "uint32"},
            {"name": "_to", "type": "bytes32"},
            {"name": "_amountLD", "type": "uint256"},
            {"name": "_minAmountLD", "type": "uint256"},
            {"name": "_extraOptions", "type": "bytes"},
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
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# WETH ABI for wrapping/unwrapping
WETH_ABI = [
    {
        "constant": False,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

class LayerZeroOFTBridgeService:
    def __init__(self):
        self.database = None
        
        # Multi-chain Web3 connections
        self.web3_connections = {}
        
        # LayerZero OFT Configuration (to be deployed)
        self.oft_contracts = {
            "optimism_sepolia": {
                "address": None,  # Will be set after OFT deployment
                "weth_address": "0x4200000000000000000000000000000000000006",
                "rpc": settings.optimism_sepolia_rpc,
                "chain_id": 11155420,
                "layerzero_eid": 40232,  # LayerZero V2 Endpoint ID
                "layerzero_config": "0xA4f7a7A48cC8C16D35c7F6944E7610694F5BEB26",  # Your existing LZ contract
                "alternative_rpcs": [
                    "https://opt-sepolia.g.alchemy.com/v2/demo",
                    "https://sepolia.optimism.io/rpc"
                ]
            },
            "arbitrum_sepolia": {
                "address": None,  # Will be set after OFT deployment
                "weth_address": "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73",
                "rpc": settings.arbitrum_sepolia_rpc,
                "chain_id": 421614,
                "layerzero_eid": 40231,  # LayerZero V2 Endpoint ID
                "layerzero_config": "0x217e72E43e9375c1121ca36dcAc3fe878901836D",  # Your existing LZ contract
                "alternative_rpcs": [
                    "https://arbitrum-sepolia.drpc.org",
                    "https://arb-sepolia.g.alchemy.com/v2/demo"
                ]
            },
            "polygon_pos": {
                "address": None,  # Will be set after OFT deployment
                "weth_address": "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889",
                "rpc": settings.polygon_pos_rpc,
                "chain_id": 80002,
                "layerzero_eid": 40267,  # LayerZero V2 Endpoint ID
                "layerzero_config": "0x72a336eAAC8186906F1Ee85dDF00C7d6b91257A43",  # Your existing LZ contract
                "alternative_rpcs": [
                    "https://polygon-amoy.g.alchemy.com/v2/demo",
                    "https://polygon-amoy.drpc.org"
                ]
            },
            "zkevm_cardona": {
                "address": None,  # Will be set after OFT deployment
                "weth_address": "0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9",
                "rpc": settings.zkevm_cardona_rpc,
                "chain_id": 2442,
                "layerzero_eid": 40158,  # LayerZero V2 Endpoint ID (estimated)
                "layerzero_config": "0xd3c6396D0212Edd8424bd6544E7DF8BA74c16476",  # Your existing FxPortal contract
                "alternative_rpcs": [
                    "https://polygon-zkevm-cardona.drpc.org"
                ]
            }
        }
        
        # Contract instances
        self.oft_instances = {}
        self.weth_instances = {}
        
        # Account for signing transactions
        self.current_account = None
        
    async def initialize(self):
        """Initialize LayerZero OFT bridge service"""
        self.database = await get_database()
        
        # Initialize account
        from app.services.multi_account_manager import address_key_manager
        deployer_account_info = address_key_manager.get_account_info_for_address('0x032041b4b356fEE1496805DD4749f181bC736FFA')
        if deployer_account_info:
            self.current_account = deployer_account_info['account']
            print(f"🔑 LayerZero OFT Bridge using account: {self.current_account.address}")
        
        # Initialize chain connections and contracts
        await self._initialize_connections()
        
        print("✅ LayerZero OFT Bridge Service initialized")
        print("🌉 True cross-chain bridging enabled with LayerZero OFT")
        
    async def _initialize_connections(self):
        """Initialize Web3 connections and contract instances"""
        
        for chain_name, config in self.oft_contracts.items():
            try:
                # Try primary RPC first
                web3 = await self._try_rpc_connection(config['rpc'], chain_name)
                
                # If primary fails, try alternatives
                if not web3 or not web3.is_connected():
                    print(f"⚠️ Primary RPC failed for {chain_name}, trying alternatives...")
                    for alt_rpc in config.get('alternative_rpcs', []):
                        web3 = await self._try_rpc_connection(alt_rpc, chain_name)
                        if web3 and web3.is_connected():
                            print(f"✅ Connected to {chain_name} using alternative RPC: {alt_rpc}")
                            break
                
                if web3 and web3.is_connected():
                    self.web3_connections[chain_name] = web3
                    
                    # Initialize WETH contract (for wrapping/unwrapping)
                    weth_contract = web3.eth.contract(
                        address=config['weth_address'],
                        abi=WETH_ABI
                    )
                    self.weth_instances[chain_name] = weth_contract
                    
                    # OFT contract will be initialized after deployment
                    print(f"✅ Connected to {chain_name} - WETH contract ready")
                    print(f"🔗 LayerZero Config: {config['layerzero_config']}")
                    print(f"🆔 LayerZero EID: {config['layerzero_eid']}")
                    
                else:
                    print(f"❌ Failed to connect to {chain_name} with all available RPCs")
                    
            except Exception as e:
                print(f"⚠️ Error initializing {chain_name}: {e}")

    async def _try_rpc_connection(self, rpc_url: str, chain_name: str) -> Optional[Web3]:
        """Try to connect to a specific RPC with comprehensive testing"""
        try:
            print(f"🔍 Testing RPC connection: {rpc_url}")
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if web3.is_connected():
                # Test basic functionality
                try:
                    chain_id = web3.eth.chain_id
                    latest_block = web3.eth.block_number
                    
                    print(f"✅ RPC working - Chain ID: {chain_id}, Block: {latest_block}")
                    
                    # Test transaction capabilities
                    test_nonce = web3.eth.get_transaction_count(self.current_account.address)
                    print(f"✅ RPC can read account state - Nonce: {test_nonce}")
                    
                    return web3
                except Exception as e:
                    print(f"❌ RPC connected but has issues: {e}")
                    return None
            else:
                print(f"❌ RPC connection failed")
                return None
                
        except Exception as e:
            print(f"❌ RPC connection error: {e}")
            return None

    async def estimate_oft_transfer_fee(
        self, 
        from_chain: str, 
        to_chain: str, 
        amount_eth: float
    ) -> Dict[str, Any]:
        """
        Estimate LayerZero OFT transfer fee
        """
        try:
            # Get source chain Web3 and OFT contract
            source_web3 = self.web3_connections.get(from_chain)
            if not source_web3:
                return {"success": False, "error": f"Source chain {from_chain} not connected"}
            
            # Check if OFT contracts are deployed
            source_config = self.oft_contracts[from_chain]
            target_config = self.oft_contracts[to_chain]
            
            if not source_config.get('address') or not target_config.get('address'):
                return {
                    "success": False, 
                    "error": "OFT contracts not yet deployed. Deploy OFT contracts first.",
                    "deployment_needed": True,
                    "deploy_command": "npx hardhat run scripts/deploy-oft.js --network optimismSepolia"
                }
            
            # Get OFT contract instance
            oft_contract = source_web3.eth.contract(
                address=source_config['address'],
                abi=LAYERZERO_OFT_ABI
            )
            
            # Convert amount to Wei
            amount_wei = Web3.to_wei(amount_eth, 'ether')
            
            # Prepare recipient address (32 bytes format for LayerZero)
            recipient_bytes32 = bytes(32)  # Placeholder - will be actual recipient
            
            # Quote the send fee
            try:
                fee_quote = oft_contract.functions.quoteSend(
                    target_config['layerzero_eid'],  # Destination endpoint ID
                    recipient_bytes32,              # Recipient address
                    amount_wei,                     # Amount to transfer
                    amount_wei,                     # Minimum amount (no slippage for now)
                    b'',                           # Extra options
                    False                          # Pay in LZ token (false = pay in native)
                ).call()
                
                # Extract fee information
                native_fee = fee_quote[0]  # Native fee in Wei
                lz_token_fee = fee_quote[1]  # LZ token fee (should be 0 since payInLzToken=false)
                
                return {
                    "success": True,
                    "native_fee_wei": native_fee,
                    "native_fee_eth": Web3.from_wei(native_fee, 'ether'),
                    "lz_token_fee": lz_token_fee,
                    "total_cost_eth": amount_eth + Web3.from_wei(native_fee, 'ether'),
                    "bridge_type": "LayerZero OFT",
                    "from_chain": from_chain,
                    "to_chain": to_chain,
                    "amount_eth": amount_eth
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Fee estimation failed: {str(e)}",
                    "oft_address": source_config['address'],
                    "target_eid": target_config['layerzero_eid']
                }
                
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
        Execute LayerZero OFT cross-chain ETH transfer
        Replaces the custodial relay model with true cross-chain bridging
        """
        try:
            print(f"\n🌉 === LAYERZERO OFT CROSS-CHAIN TRANSFER ===")
            print(f"📤 From: {from_chain} ({from_address})")
            print(f"📥 To: {to_chain} ({to_address})")
            print(f"💰 Amount: {amount_eth} ETH")
            print(f"🔗 Escrow ID: {escrow_id}")
            
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
                    "error": "OFT contracts not deployed yet. Please deploy OFT contracts first.",
                    "deployment_instructions": {
                        "step1": "Deploy LayerZero OFT contracts on all chains",
                        "step2": "Set peer addresses between chains",
                        "step3": "Update configuration with deployed addresses",
                        "deploy_command": "npx create-lz-oapp@latest --template oft"
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
            
            # STEP 1: Wrap ETH to WETH (if needed)
            print(f"\n💱 === STEP 1: WRAP ETH TO WETH ===")
            weth_contract = self.weth_instances[from_chain]
            
            # Check current WETH balance
            weth_balance = weth_contract.functions.balanceOf(user_account.address).call()
            weth_balance_eth = Web3.from_wei(weth_balance, 'ether')
            
            if weth_balance_eth < amount_eth:
                # Need to wrap more ETH
                wrap_amount = amount_eth - weth_balance_eth
                wrap_result = await self._wrap_eth_to_weth(
                    source_web3, from_chain, user_account, wrap_amount
                )
                if not wrap_result["success"]:
                    return {"success": False, "error": f"Failed to wrap ETH: {wrap_result['error']}"}
                print(f"✅ Wrapped {wrap_amount} ETH to WETH")
            else:
                print(f"✅ Sufficient WETH balance: {weth_balance_eth} ETH")
            
            # STEP 2: Approve OFT contract to spend WETH
            print(f"\n🔓 === STEP 2: APPROVE OFT CONTRACT ===")
            approval_result = await self._approve_weth_for_oft(
                source_web3, from_chain, user_account, amount_wei
            )
            if not approval_result["success"]:
                return {"success": False, "error": f"Failed to approve WETH: {approval_result['error']}"}
            
            # STEP 3: Execute LayerZero OFT transfer
            print(f"\n🚀 === STEP 3: EXECUTE LAYERZERO OFT TRANSFER ===")
            oft_result = await self._execute_oft_send(
                source_web3, from_chain, to_chain, user_account, to_address, amount_wei
            )
            if not oft_result["success"]:
                return {"success": False, "error": f"Failed to execute OFT transfer: {oft_result['error']}"}
            
            # STEP 4: Record transfer in database
            print(f"\n📊 === STEP 4: RECORD TRANSFER ===")
            transfer_record = {
                "transfer_id": escrow_id,
                "from_chain": from_chain,
                "to_chain": to_chain,
                "from_address": from_address,
                "to_address": to_address,
                "amount_eth": amount_eth,
                "bridge_type": "layerzero_oft",
                "status": "completed",
                "wrap_transaction_hash": wrap_result.get("transaction_hash") if 'wrap_result' in locals() else None,
                "approve_transaction_hash": approval_result.get("transaction_hash"),
                "oft_transaction_hash": oft_result.get("transaction_hash"),
                "layerzero_eid_source": source_config['layerzero_eid'],
                "layerzero_eid_target": target_config['layerzero_eid'],
                "native_fee_paid": oft_result.get("native_fee_paid"),
                "timestamp": time.time(),
                "block_number_source": oft_result.get("block_number"),
                "gas_used": oft_result.get("gas_used")
            }
            
            # Convert Decimal objects for MongoDB
            transfer_record = convert_decimals_to_float(transfer_record)
            
            # Save to database
            try:
                await self.database.transfers.insert_one(transfer_record)
                print(f"✅ Transfer recorded in database")
            except Exception as e:
                print(f"⚠️ Warning: Failed to record transfer in database: {e}")
            
            print(f"\n🎉 === LAYERZERO OFT TRANSFER COMPLETED ===")
            print(f"✅ True cross-chain bridging successful!")
            print(f"🔗 Source TX: {oft_result.get('transaction_hash')}")
            print(f"💰 Amount bridged: {amount_eth} ETH")
            print(f"🌉 Bridge type: LayerZero OFT (decentralized)")
            
            return {
                "success": True,
                "transfer_id": escrow_id,
                "bridge_type": "layerzero_oft",
                "amount_transferred": amount_eth,
                "wrap_transaction_hash": wrap_result.get("transaction_hash") if 'wrap_result' in locals() else None,
                "approve_transaction_hash": approval_result.get("transaction_hash"),
                "oft_transaction_hash": oft_result.get("transaction_hash"),
                "native_fee_paid": oft_result.get("native_fee_paid"),
                "layerzero_guid": oft_result.get("layerzero_guid"),
                "message": "LayerZero OFT transfer completed successfully",
                "is_decentralized": True
            }
            
        except Exception as e:
            print(f"❌ LayerZero OFT transfer error: {e}")
            return {"success": False, "error": str(e)}

    async def _wrap_eth_to_weth(
        self, 
        web3: Web3, 
        chain_name: str, 
        user_account, 
        amount_eth: float
    ) -> Dict[str, Any]:
        """Wrap ETH to WETH for OFT transfer"""
        try:
            weth_contract = self.weth_instances[chain_name]
            amount_wei = Web3.to_wei(amount_eth, 'ether')
            
            # Build wrap transaction
            nonce = web3.eth.get_transaction_count(user_account.address)
            
            transaction = weth_contract.functions.deposit().build_transaction({
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
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                return {
                    "success": True,
                    "transaction_hash": tx_hash.hex(),
                    "amount_wrapped": amount_eth,
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber
                }
            else:
                return {"success": False, "error": "Wrap transaction failed"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _approve_weth_for_oft(
        self, 
        web3: Web3, 
        chain_name: str, 
        user_account, 
        amount_wei: int
    ) -> Dict[str, Any]:
        """Approve OFT contract to spend WETH"""
        try:
            weth_contract = self.weth_instances[chain_name]
            oft_address = self.oft_contracts[chain_name]['address']
            
            # Check current allowance
            current_allowance = weth_contract.functions.allowance(
                user_account.address, oft_address
            ).call()
            
            if current_allowance >= amount_wei:
                return {"success": True, "message": "Sufficient allowance already exists"}
            
            # Build approval transaction
            nonce = web3.eth.get_transaction_count(user_account.address)
            
            transaction = weth_contract.functions.approve(
                oft_address, amount_wei
            ).build_transaction({
                'from': user_account.address,
                'gas': 100000,
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id
            })
            
            # Sign and send transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, user_account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                return {
                    "success": True,
                    "transaction_hash": tx_hash.hex(),
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber
                }
            else:
                return {"success": False, "error": "Approval transaction failed"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_oft_send(
        self, 
        web3: Web3, 
        from_chain: str, 
        to_chain: str, 
        user_account, 
        to_address: str, 
        amount_wei: int
    ) -> Dict[str, Any]:
        """Execute LayerZero OFT send transaction"""
        try:
            source_config = self.oft_contracts[from_chain]
            target_config = self.oft_contracts[to_chain]
            
            oft_contract = web3.eth.contract(
                address=source_config['address'],
                abi=LAYERZERO_OFT_ABI
            )
            
            # Convert recipient address to bytes32 format
            recipient_bytes32 = Web3.to_bytes(hexstr=to_address.lower().replace('0x', '').ljust(64, '0'))
            
            # Get fee quote first
            fee_quote = oft_contract.functions.quoteSend(
                target_config['layerzero_eid'],
                recipient_bytes32,
                amount_wei,
                amount_wei,  # Min amount (no slippage)
                b'',         # Extra options
                False        # Pay in native token
            ).call()
            
            native_fee = fee_quote[0]
            
            # Build OFT send transaction
            nonce = web3.eth.get_transaction_count(user_account.address)
            
            transaction = oft_contract.functions.send(
                target_config['layerzero_eid'],  # Destination endpoint ID
                recipient_bytes32,              # Recipient address (bytes32)
                amount_wei,                     # Amount to transfer
                amount_wei,                     # Min amount (no slippage)
                b''                            # Extra options
            ).build_transaction({
                'from': user_account.address,
                'value': native_fee,           # Pay LayerZero fee
                'gas': 500000,                 # Higher gas for cross-chain
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id
            })
            
            # Sign and send transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, user_account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                # Extract LayerZero GUID from logs (for tracking)
                layerzero_guid = None
                try:
                    for log in receipt.logs:
                        if len(log.topics) > 0:
                            # Look for LayerZero packet sent event
                            layerzero_guid = log.topics[0].hex()[:32]  # Simplified GUID extraction
                            break
                except:
                    pass
                
                return {
                    "success": True,
                    "transaction_hash": tx_hash.hex(),
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber,
                    "native_fee_paid": Web3.from_wei(native_fee, 'ether'),
                    "layerzero_guid": layerzero_guid,
                    "destination_eid": target_config['layerzero_eid']
                }
            else:
                return {"success": False, "error": "OFT send transaction failed"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_oft_balance(self, chain_name: str, address: str) -> Dict[str, Any]:
        """Get OFT and WETH balances for an address"""
        try:
            web3 = self.web3_connections.get(chain_name)
            if not web3:
                return {"success": False, "error": f"Chain {chain_name} not connected"}
            
            # Get ETH balance
            eth_balance_wei = web3.eth.get_balance(address)
            eth_balance = Web3.from_wei(eth_balance_wei, 'ether')
            
            # Get WETH balance
            weth_contract = self.weth_instances[chain_name]
            weth_balance_wei = weth_contract.functions.balanceOf(address).call()
            weth_balance = Web3.from_wei(weth_balance_wei, 'ether')
            
            # Get OFT balance (if deployed)
            oft_balance = 0
            config = self.oft_contracts[chain_name]
            if config.get('address'):
                try:
                    oft_contract = web3.eth.contract(
                        address=config['address'],
                        abi=LAYERZERO_OFT_ABI
                    )
                    oft_balance_wei = oft_contract.functions.balanceOf(address).call()
                    oft_balance = Web3.from_wei(oft_balance_wei, 'ether')
                except:
                    pass
            
            return {
                "success": True,
                "chain_name": chain_name,
                "address": address,
                "eth_balance": eth_balance,
                "weth_balance": weth_balance,
                "oft_balance": oft_balance,
                "total_balance": eth_balance + weth_balance + oft_balance
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def update_oft_addresses(self, oft_addresses: Dict[str, str]):
        """Update OFT contract addresses after deployment"""
        for chain_name, address in oft_addresses.items():
            if chain_name in self.oft_contracts:
                self.oft_contracts[chain_name]['address'] = address
                print(f"✅ Updated OFT address for {chain_name}: {address}")
                
        # Initialize OFT contract instances
        for chain_name, config in self.oft_contracts.items():
            if config.get('address') and chain_name in self.web3_connections:
                web3 = self.web3_connections[chain_name]
                oft_contract = web3.eth.contract(
                    address=config['address'],
                    abi=LAYERZERO_OFT_ABI
                )
                self.oft_instances[chain_name] = oft_contract
                print(f"🔗 OFT contract instance created for {chain_name}")

# Global instance
layerzero_oft_bridge_service = LayerZeroOFTBridgeService()
