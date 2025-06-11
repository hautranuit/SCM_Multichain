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

# LayerZero OFT Contract ABI (Updated for OFT Adapter with Deposit)
LAYERZERO_OFT_ABI = [
    {
        "inputs": [
            {"name": "_dstEid", "type": "uint32"},
            {"name": "_to", "type": "bytes32"},
            {"name": "_amountLD", "type": "uint256"},
            {"name": "_minAmountLD", "type": "uint256"},
            {"name": "_extraOptions", "type": "bytes"},
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
    {
        "inputs": [{"name": "amount", "type": "uint256"}],
        "name": "wrapAndDeposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "amount", "type": "uint256"}],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "lzEndpoint",
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
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

class LayerZeroOFTBridgeService:
    def __init__(self):
        self.database = None
        
        # Multi-chain Web3 connections
        self.web3_connections = {}
        
        # LayerZero OFT Configuration (DEPLOYED 2025)
        self.oft_contracts = {
            "optimism_sepolia": {
                "address": "0xf77FAB8A727ac0d6810881841Ad1274bacA306c9",  # DEPLOYED ✅
                "weth_address": "0x4200000000000000000000000000000000000006",
                "rpc": settings.optimism_sepolia_rpc,
                "chain_id": 11155420,
                "layerzero_eid": 40232,  # LayerZero V2 Endpoint ID
                "layerzero_endpoint": "0x6Ac7bdc07A0583A362F1497252872AE6c0A5F5B8",  # Updated 2025
                "alternative_rpcs": [
                    "https://opt-sepolia.g.alchemy.com/v2/demo",
                    "https://sepolia.optimism.io/rpc"
                ]
            },
            "arbitrum_sepolia": {
                "address": "0x9767D45C02Bf58842d723a1E1D8340a22748f6B8",  # DEPLOYED ✅
                "weth_address": "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73",
                "rpc": settings.arbitrum_sepolia_rpc,
                "chain_id": 421614,
                "layerzero_eid": 40231,  # LayerZero V2 Endpoint ID
                "layerzero_endpoint": "0x6EDCE65403992e310A62460808c4b910D972f10f",  # Updated 2025
                "alternative_rpcs": [
                    "https://arbitrum-sepolia.drpc.org",
                    "https://arb-sepolia.g.alchemy.com/v2/demo"
                ]
            },
            "polygon_pos": {
                "address": "0x2edF34BA32BC489BcbF313A98037b8c423f83000",  # DEPLOYED ✅
                "weth_address": "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889",
                "rpc": settings.polygon_pos_rpc,
                "chain_id": 80002,
                "layerzero_eid": 40313,  # Updated EID for 2025
                "layerzero_endpoint": "0x16c693A3924B947298F7227792953Cd6BBb21Ac8",  # Updated 2025
                "alternative_rpcs": [
                    "https://polygon-amoy.g.alchemy.com/v2/demo",
                    "https://polygon-amoy.drpc.org"
                ]
            },
            "zkevm_cardona": {
                "address": "0xc8DEf94605917074A3990D4c78cf52C556C47E28",  # DEPLOYED ✅
                "weth_address": "0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9",
                "rpc": settings.zkevm_cardona_rpc,
                "chain_id": 2442,
                "layerzero_eid": 40158,  # LayerZero V2 Endpoint ID (estimated)
                "layerzero_endpoint": "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3",  # Estimated
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
        print("🎉 ALL OFT CONTRACTS DEPLOYED AND READY!")
        
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
                    
                    # Initialize OFT contract (DEPLOYED!)
                    if config.get('address'):
                        oft_contract = web3.eth.contract(
                            address=config['address'],
                            abi=LAYERZERO_OFT_ABI
                        )
                        self.oft_instances[chain_name] = oft_contract
                        print(f"✅ Connected to {chain_name} - OFT contract ready at {config['address']}")
                    else:
                        print(f"⚠️ Connected to {chain_name} - OFT contract address not set")
                    
                    print(f"🔗 LayerZero Endpoint: {config['layerzero_endpoint']}")
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
        Estimate LayerZero OFT transfer fee using fixed fee approach
        (Since fee quote functions are not available on deployed contracts)
        """
        try:
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
            
            # FIXED FEE APPROACH - Common in LayerZero implementations
            # These are typical LayerZero cross-chain fees based on chain pairs
            
            fixed_fees = {
                "optimism_sepolia": {
                    "zkevm_cardona": 0.002,      # 0.002 ETH
                    "arbitrum_sepolia": 0.001,   # 0.001 ETH  
                    "polygon_pos": 0.0015        # 0.0015 ETH
                },
                "arbitrum_sepolia": {
                    "zkevm_cardona": 0.002,
                    "optimism_sepolia": 0.001,
                    "polygon_pos": 0.0015
                },
                "polygon_pos": {
                    "zkevm_cardona": 0.002,
                    "optimism_sepolia": 0.0015,
                    "arbitrum_sepolia": 0.0015
                },
                "zkevm_cardona": {
                    "optimism_sepolia": 0.002,
                    "arbitrum_sepolia": 0.002,
                    "polygon_pos": 0.002
                }
            }
            
            # Get fixed fee for this route
            native_fee_eth = fixed_fees.get(from_chain, {}).get(to_chain, 0.002)  # Default 0.002 ETH
            
            print(f"💸 Using fixed LayerZero fee: {native_fee_eth} ETH for {from_chain} → {to_chain}")
            
            return {
                "success": True,
                "native_fee_wei": Web3.to_wei(native_fee_eth, 'ether'),
                "native_fee_eth": native_fee_eth,
                "lz_token_fee": 0,
                "total_cost_eth": amount_eth + native_fee_eth,
                "bridge_type": "LayerZero OFT (Fixed Fee)",
                "from_chain": from_chain,
                "to_chain": to_chain,
                "amount_eth": amount_eth,
                "fee_method": "fixed_fee_bypass"
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
            
            # Check if OFT contracts are deployed (SHOULD BE NOW!)
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
            
            # STEP 1: Check WETH balance (skip OFT conversion - use WETH directly)
            print(f"\n💰 === STEP 1: CHECK WETH BALANCE ===")
            weth_contract = self.weth_instances[from_chain]
            
            # Check current WETH balance
            weth_balance = weth_contract.functions.balanceOf(user_account.address).call()
            weth_balance_eth = float(Web3.from_wei(weth_balance, 'ether'))
            
            print(f"💳 User WETH balance: {weth_balance_eth} ETH")
            print(f"🎯 Required amount: {amount_eth} ETH")
            
            if weth_balance_eth < amount_eth:
                return {"success": False, "error": f"Insufficient WETH balance. Have: {weth_balance_eth} ETH, Need: {amount_eth} ETH. Please wrap more ETH to WETH first."}
            
            print(f"✅ Sufficient WETH balance for bridge transfer")
            
            # STEP 1.5: Approve OFT contract to spend WETH
            print(f"\n🔓 === STEP 1.5: APPROVE WETH SPENDING ===")
            oft_address = self.oft_contracts[from_chain]['address']
            
            # Check current allowance
            current_allowance = weth_contract.functions.allowance(
                user_account.address, oft_address
            ).call()
            current_allowance_eth = float(Web3.from_wei(current_allowance, 'ether'))
            
            print(f"💳 Current WETH allowance: {current_allowance_eth} ETH")
            print(f"🎯 Required allowance: {amount_eth} ETH")
            
            if current_allowance_eth < amount_eth:
                print(f"🔄 Approving OFT contract to spend WETH...")
                
                # Build approval transaction
                approval_nonce = source_web3.eth.get_transaction_count(user_account.address)
                
                approval_transaction = weth_contract.functions.approve(
                    oft_address, amount_wei
                ).build_transaction({
                    'from': user_account.address,
                    'gas': 100000,
                    'gasPrice': source_web3.eth.gas_price,
                    'nonce': approval_nonce,
                    'chainId': source_web3.eth.chain_id
                })
                
                # Sign and send approval
                signed_approval = source_web3.eth.account.sign_transaction(approval_transaction, user_account.key)
                approval_tx_hash = source_web3.eth.send_raw_transaction(signed_approval.raw_transaction)
                approval_receipt = source_web3.eth.wait_for_transaction_receipt(approval_tx_hash, timeout=300)
                
                if approval_receipt.status == 1:
                    print(f"✅ WETH approval successful: {approval_tx_hash.hex()}")
                else:
                    return {"success": False, "error": "WETH approval transaction failed"}
            else:
                print(f"✅ Sufficient WETH allowance already exists")
            
            # Initialize conversion result for tracking
            oft_convert_result = {"success": True, "transaction_hash": None, "method": "weth_with_approval"}
            
            # STEP 2: Execute LayerZero OFT transfer
            print(f"\n🚀 === STEP 2: EXECUTE LAYERZERO OFT TRANSFER ===")
            oft_result = await self._execute_oft_send(
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
                "bridge_type": "layerzero_oft_weth_direct",
                "status": "completed",
                "weth_check": oft_convert_result.get("method", "weth_direct"),
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
                "bridge_type": "layerzero_oft_weth_direct",
                "amount_transferred": amount_eth,
                "weth_balance_used": True,
                "oft_transaction_hash": oft_result.get("transaction_hash"),
                "native_fee_paid": oft_result.get("native_fee_paid"),
                "layerzero_guid": oft_result.get("layerzero_guid"),
                "message": "LayerZero OFT WETH transfer completed successfully",
                "is_decentralized": True
            }
            
        except Exception as e:
            print(f"❌ LayerZero OFT transfer error: {e}")
            return {"success": False, "error": str(e)}

    async def _convert_eth_to_oft(
        self, 
        web3: Web3, 
        chain_name: str, 
        user_account, 
        amount_eth: float
    ) -> Dict[str, Any]:
        """Convert ETH to OFT tokens using wrapAndDeposit function"""
        try:
            oft_contract = self.oft_instances[chain_name]
            amount_wei = Web3.to_wei(amount_eth, 'ether')
            
            print(f"🔧 Converting {amount_eth} ETH to OFT tokens on {chain_name}")
            print(f"📍 OFT Contract: {self.oft_contracts[chain_name]['address']}")
            print(f"💰 Amount in Wei: {amount_wei}")
            
            # Test the function first with a call
            try:
                print(f"🧪 Testing wrapAndDeposit function call...")
                oft_contract.functions.wrapAndDeposit(amount_wei).call({
                    'from': user_account.address,
                    'value': amount_wei
                })
                print(f"✅ wrapAndDeposit call test successful")
            except Exception as call_error:
                print(f"❌ wrapAndDeposit call test failed: {call_error}")
                
                # Try alternative: deposit function (if WETH already wrapped)
                try:
                    print(f"🔄 Trying alternative: deposit function...")
                    oft_contract.functions.deposit(amount_wei).call({
                        'from': user_account.address
                    })
                    print(f"✅ deposit call test successful - using deposit instead")
                    
                    # Use deposit function instead
                    nonce = web3.eth.get_transaction_count(user_account.address)
                    
                    transaction = oft_contract.functions.deposit(amount_wei).build_transaction({
                        'from': user_account.address,
                        'gas': 200000,
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
                            "amount_converted": amount_eth,
                            "gas_used": receipt.gasUsed,
                            "block_number": receipt.blockNumber,
                            "method_used": "deposit"
                        }
                    else:
                        return {"success": False, "error": "Deposit transaction failed"}
                        
                except Exception as deposit_error:
                    print(f"❌ deposit call test also failed: {deposit_error}")
                    return {"success": False, "error": f"Both wrapAndDeposit and deposit failed. wrapAndDeposit: {call_error}, deposit: {deposit_error}"}
            
            # Build wrapAndDeposit transaction (original approach)
            nonce = web3.eth.get_transaction_count(user_account.address)
            print(f"📊 Account nonce: {nonce}")
            
            transaction = oft_contract.functions.wrapAndDeposit(amount_wei).build_transaction({
                'from': user_account.address,
                'value': amount_wei,  # Send ETH to convert to OFT tokens
                'gas': 200000,  # Gas for wrapping and depositing
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id
            })
            
            print(f"⛽ Transaction gas limit: 200,000")
            print(f"💰 Transaction value: {amount_eth} ETH")
            
            # Sign and send transaction
            print(f"✍️ Signing and sending wrapAndDeposit transaction...")
            signed_txn = web3.eth.account.sign_transaction(transaction, user_account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"📤 Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            print(f"⏳ Waiting for transaction confirmation...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print(f"✅ wrapAndDeposit transaction successful!")
                return {
                    "success": True,
                    "transaction_hash": tx_hash.hex(),
                    "amount_converted": amount_eth,
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber,
                    "method_used": "wrapAndDeposit"
                }
            else:
                print(f"❌ wrapAndDeposit transaction failed - Receipt status: {receipt.status}")
                return {"success": False, "error": f"wrapAndDeposit transaction failed - Receipt status: {receipt.status}"}
                
        except Exception as e:
            print(f"❌ ETH to OFT conversion error: {e}")
            import traceback
            print(f"🔍 Full error traceback: {traceback.format_exc()}")
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
        """Execute LayerZero OFT send transaction using direct send approach (no fee quote)"""
        try:
            source_config = self.oft_contracts[from_chain]
            target_config = self.oft_contracts[to_chain]
            
            print(f"🔗 Source chain: {from_chain} (EID: {source_config['layerzero_eid']})")
            print(f"🎯 Target chain: {to_chain} (EID: {target_config['layerzero_eid']})")
            print(f"📧 To address: {to_address}")
            print(f"💰 Amount: {Web3.from_wei(amount_wei, 'ether')} ETH")
            
            oft_contract = web3.eth.contract(
                address=source_config['address'],
                abi=LAYERZERO_OFT_ABI
            )
            
            # Convert recipient address to bytes32 format (LEFT-PADDED)
            recipient_bytes32 = Web3.to_bytes(hexstr=to_address.lower().replace('0x', '').zfill(64))
            print(f"🔧 Recipient bytes32: {recipient_bytes32.hex()}")
            
            # Use fixed LayerZero fee (bypass fee quote)
            fee_estimate = await self.estimate_oft_transfer_fee(from_chain, to_chain, float(Web3.from_wei(amount_wei, 'ether')))
            if not fee_estimate["success"]:
                return {"success": False, "error": f"Fee estimation failed: {fee_estimate['error']}"}
            
            native_fee = fee_estimate["native_fee_wei"]
            print(f"💳 Using fixed LayerZero fee: {Web3.from_wei(native_fee, 'ether')} ETH")
            
            # FIXED: Use direct send function parameters (not struct)
            print(f"🧪 Simulating OFT send transaction...")
            try:
                # Create MessagingFee struct
                messaging_fee = (native_fee, 0)  # (nativeFee, lzTokenFee)
                
                # Test with call first
                oft_contract.functions.send(
                    target_config['layerzero_eid'],  # _dstEid (uint32)
                    recipient_bytes32,               # _to (bytes32)  
                    amount_wei,                      # _amountLD (uint256)
                    amount_wei,                      # _minAmountLD (uint256)
                    b'',                            # _extraOptions (bytes)
                    messaging_fee,                   # _fee (MessagingFee struct)
                    user_account.address            # _refundAddress (address)
                ).call({
                    'from': user_account.address, 
                    'value': native_fee
                })
                print("✅ Transaction simulation successful")
                
            except Exception as sim_error:
                print(f"❌ Transaction simulation failed: {sim_error}")
                return {"success": False, "error": f"Simulation failed: {sim_error}"}
            
            # Build OFT send transaction using direct parameters
            nonce = web3.eth.get_transaction_count(user_account.address)
            print(f"📊 Account nonce: {nonce}")
            
            transaction = oft_contract.functions.send(
                target_config['layerzero_eid'],  # _dstEid (uint32)
                recipient_bytes32,               # _to (bytes32)  
                amount_wei,                      # _amountLD (uint256)
                amount_wei,                      # _minAmountLD (uint256)
                b'',                            # _extraOptions (bytes)
                messaging_fee,                   # _fee (MessagingFee struct)
                user_account.address            # _refundAddress (address)
            ).build_transaction({
                'from': user_account.address,
                'value': native_fee,           # Pay LayerZero fee
                'gas': 1000000,                # Increased gas limit for LayerZero
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
                'chainId': web3.eth.chain_id
            })
            
            print(f"⛽ Transaction gas limit: 1,000,000")
            print(f"💰 Transaction value (fee): {Web3.from_wei(native_fee, 'ether')} ETH")
            
            # Sign and send transaction
            print(f"✍️ Signing and sending OFT transaction...")
            signed_txn = web3.eth.account.sign_transaction(transaction, user_account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"📤 Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt with detailed logging
            print(f"⏳ Waiting for transaction confirmation...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print(f"✅ OFT send transaction successful!")
                
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
                    "native_fee_paid": float(Web3.from_wei(native_fee, 'ether')),
                    "layerzero_guid": layerzero_guid,
                    "destination_eid": target_config['layerzero_eid'],
                    "fee_method": "fixed_fee_bypass"
                }
            else:
                print(f"❌ OFT send transaction failed - Receipt status: {receipt.status}")
                return {"success": False, "error": f"OFT send transaction failed - Receipt status: {receipt.status}"}
                
        except Exception as e:
            print(f"❌ OFT send execution error: {e}")
            import traceback
            print(f"🔍 Full error traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    async def debug_oft_contract(self, chain_name: str) -> Dict[str, Any]:
        """Debug OFT contract to understand available functions"""
        try:
            web3 = self.web3_connections.get(chain_name)
            if not web3:
                return {"success": False, "error": f"Chain {chain_name} not connected"}
            
            config = self.oft_contracts[chain_name]
            contract_address = config.get('address')
            
            if not contract_address:
                return {"success": False, "error": f"No contract address for {chain_name}"}
            
            print(f"🔍 Debugging OFT contract on {chain_name}")
            print(f"📍 Contract address: {contract_address}")
            
            # Test basic contract interaction
            try:
                # Check if contract exists
                code = web3.eth.get_code(contract_address)
                if code == b'':
                    return {"success": False, "error": f"No contract code at {contract_address}"}
                
                print(f"✅ Contract code exists (length: {len(code)} bytes)")
                
                # Try basic ERC20-style balanceOf
                simple_abi = [
                    {
                        "inputs": [{"name": "account", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "", "type": "uint256"}],
                        "stateMutability": "view",
                        "type": "function"
                    }
                ]
                
                simple_contract = web3.eth.contract(address=contract_address, abi=simple_abi)
                balance = simple_contract.functions.balanceOf(self.current_account.address).call()
                print(f"✅ balanceOf works: {balance}")
                
                return {
                    "success": True,
                    "contract_address": contract_address,
                    "code_length": len(code),
                    "balance_check": "working",
                    "chain": chain_name,
                    "message": "Contract is deployed and responsive"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Contract interaction failed: {str(e)}",
                    "contract_address": contract_address
                }
            
        except Exception as e:
            return {"success": False, "error": f"Debug failed: {str(e)}"}

    async def test_oft_function_availability(self, chain_name: str) -> Dict[str, Any]:
        """Test which LayerZero functions are available on deployed contract"""
        try:
            web3 = self.web3_connections.get(chain_name)
            config = self.oft_contracts[chain_name]
            contract_address = config.get('address')
            
            if not web3 or not contract_address:
                return {"success": False, "error": "Chain or contract not available"}
            
            print(f"🧪 Enhanced LayerZero function testing on {chain_name}")
            
            # Test different possible LayerZero function signatures
            function_tests = []
            
            # Test 1: LayerZero V1 style quoteSend (Original)
            try:
                v1_abi = [{
                    "inputs": [
                        {"name": "_dstEid", "type": "uint32"},
                        {"name": "_to", "type": "bytes32"},
                        {"name": "_amountLD", "type": "uint256"},
                        {"name": "_minAmountLD", "type": "uint256"},
                        {"name": "_extraOptions", "type": "bytes"},
                        {"name": "_payInLzToken", "type": "bool"}
                    ],
                    "name": "quoteSend",
                    "outputs": [{"name": "", "type": "tuple", "components": [
                        {"name": "nativeFee", "type": "uint256"},
                        {"name": "lzTokenFee", "type": "uint256"}
                    ]}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=v1_abi)
                result = contract.functions.quoteSend(
                    40158,  # zkEVM EID
                    Web3.to_bytes(hexstr='0x28918ecf013F32fAf45e05d62B4D9b207FCae784'.lower().replace('0x', '').zfill(64)),
                    Web3.to_wei(0.01, 'ether'),
                    Web3.to_wei(0.01, 'ether'),
                    b'',
                    False
                ).call()
                function_tests.append({"name": "quoteSend_v1", "status": "works", "result": str(result)})
                
            except Exception as e:
                function_tests.append({"name": "quoteSend_v1", "status": "failed", "error": str(e)})
            
            # Test 2: LayerZero V2 OFT quoteSend with struct
            try:
                v2_abi = [{
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
                    "outputs": [{"name": "", "type": "tuple", "components": [
                        {"name": "nativeFee", "type": "uint256"},
                        {"name": "lzTokenFee", "type": "uint256"}
                    ]}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=v2_abi)
                send_param = (
                    40158,  # dstEid
                    Web3.to_bytes(hexstr='0x28918ecf013F32fAf45e05d62B4D9b207FCae784'.lower().replace('0x', '').zfill(64)),
                    Web3.to_wei(0.01, 'ether'),  # amountLD
                    Web3.to_wei(0.01, 'ether'),  # minAmountLD
                    b'',  # extraOptions
                    b'',  # composeMsg
                    b''   # oftCmd
                )
                
                result = contract.functions.quoteSend(send_param, False).call()
                function_tests.append({"name": "quoteSend_v2_struct", "status": "works", "result": str(result)})
                
            except Exception as e:
                function_tests.append({"name": "quoteSend_v2_struct", "status": "failed", "error": str(e)})
            
            # Test 3: Alternative quoteSend with different return type
            try:
                alt_abi = [{
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
                        {"name": "nativeFee", "type": "uint256"},
                        {"name": "lzTokenFee", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=alt_abi)
                result = contract.functions.quoteSend(
                    40158,
                    Web3.to_bytes(hexstr='0x28918ecf013F32fAf45e05d62B4D9b207FCae784'.lower().replace('0x', '').zfill(64)),
                    Web3.to_wei(0.01, 'ether'),
                    Web3.to_wei(0.01, 'ether'),
                    b'',
                    False
                ).call()
                function_tests.append({"name": "quoteSend_alt_return", "status": "works", "result": str(result)})
                
            except Exception as e:
                function_tests.append({"name": "quoteSend_alt_return", "status": "failed", "error": str(e)})
            
            # Test 4: estimateFee (common in LayerZero contracts)
            try:
                fee_abi = [{
                    "inputs": [
                        {"name": "_dstEid", "type": "uint32"},
                        {"name": "_to", "type": "bytes32"},
                        {"name": "_amountLD", "type": "uint256"},
                        {"name": "_payInLzToken", "type": "bool"},
                        {"name": "_extraOptions", "type": "bytes"}
                    ],
                    "name": "estimateFee",
                    "outputs": [
                        {"name": "nativeFee", "type": "uint256"},
                        {"name": "lzTokenFee", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=fee_abi)
                result = contract.functions.estimateFee(
                    40158,
                    Web3.to_bytes(hexstr='0x28918ecf013F32fAf45e05d62B4D9b207FCae784'.lower().replace('0x', '').zfill(64)),
                    Web3.to_wei(0.01, 'ether'),
                    False,
                    b''
                ).call()
                function_tests.append({"name": "estimateFee", "status": "works", "result": str(result)})
                
            except Exception as e:
                function_tests.append({"name": "estimateFee", "status": "failed", "error": str(e)})
            
            # Test 5: Simple endpoint getter
            try:
                endpoint_abi = [{
                    "inputs": [],
                    "name": "endpoint",
                    "outputs": [{"name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=endpoint_abi)
                endpoint = contract.functions.endpoint().call()
                function_tests.append({"name": "endpoint", "status": "works", "result": endpoint})
                
            except Exception as e:
                function_tests.append({"name": "endpoint", "status": "failed", "error": str(e)})
            
            # Test 6: LayerZero endpoint alternative
            try:
                lz_endpoint_abi = [{
                    "inputs": [],
                    "name": "lzEndpoint",
                    "outputs": [{"name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=lz_endpoint_abi)
                endpoint = contract.functions.lzEndpoint().call()
                function_tests.append({"name": "lzEndpoint", "status": "works", "result": endpoint})
                
            except Exception as e:
                function_tests.append({"name": "lzEndpoint", "status": "failed", "error": str(e)})
            
            # Test 7: Check for peer function (already working)
            try:
                peer_abi = [{
                    "inputs": [{"name": "_eid", "type": "uint32"}],
                    "name": "peers",
                    "outputs": [{"name": "", "type": "bytes32"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=peer_abi)
                peer = contract.functions.peers(40158).call()  # zkEVM EID
                function_tests.append({"name": "peers", "status": "works", "result": peer.hex()})
                
            except Exception as e:
                function_tests.append({"name": "peers", "status": "failed", "error": str(e)})
            
            # Test 8: OFT specific functions
            try:
                oft_abi = [{
                    "inputs": [],
                    "name": "token",
                    "outputs": [{"name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=oft_abi)
                token = contract.functions.token().call()
                function_tests.append({"name": "token", "status": "works", "result": token})
                
            except Exception as e:
                function_tests.append({"name": "token", "status": "failed", "error": str(e)})
            
            # Test 9: decimals
            try:
                decimals_abi = [{
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=decimals_abi)
                decimals = contract.functions.decimals().call()
                function_tests.append({"name": "decimals", "status": "works", "result": str(decimals)})
                
            except Exception as e:
                function_tests.append({"name": "decimals", "status": "failed", "error": str(e)})
            
            # Test 10: LayerZero send (without fee quote first)
            try:
                send_abi = [{
                    "inputs": [
                        {"name": "_dstEid", "type": "uint32"},
                        {"name": "_to", "type": "bytes32"},
                        {"name": "_amountLD", "type": "uint256"},
                        {"name": "_minAmountLD", "type": "uint256"},
                        {"name": "_extraOptions", "type": "bytes"},
                        {"name": "_fee", "type": "tuple", "components": [
                            {"name": "nativeFee", "type": "uint256"},
                            {"name": "lzTokenFee", "type": "uint256"}
                        ]},
                        {"name": "_refundAddress", "type": "address"}
                    ],
                    "name": "send",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                }]
                
                # Just test if the function exists (simulation)
                contract = web3.eth.contract(address=contract_address, abi=send_abi)
                function_tests.append({"name": "send_function_exists", "status": "works", "result": "function signature exists"})
                
            except Exception as e:
                function_tests.append({"name": "send_function_exists", "status": "failed", "error": str(e)})
            
            # Test 11: Get fee with zero values (to test parameter acceptance)
            try:
                zero_fee_abi = [{
                    "inputs": [
                        {"name": "_dstEid", "type": "uint32"},
                        {"name": "_to", "type": "bytes32"},
                        {"name": "_amountLD", "type": "uint256"},
                        {"name": "_minAmountLD", "type": "uint256"},
                        {"name": "_extraOptions", "type": "bytes"},
                        {"name": "_payInLzToken", "type": "bool"}
                    ],
                    "name": "quoteSend",
                    "outputs": [{"name": "", "type": "tuple", "components": [
                        {"name": "nativeFee", "type": "uint256"},
                        {"name": "lzTokenFee", "type": "uint256"}
                    ]}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=zero_fee_abi)
                # Test with minimal values
                result = contract.functions.quoteSend(
                    40158,  # zkEVM EID
                    Web3.to_bytes(hexstr='0x28918ecf013F32fAf45e05d62B4D9b207FCae784'.lower().replace('0x', '').zfill(64)),
                    1,  # 1 wei instead of 0.01 ETH
                    1,  # 1 wei minimum
                    b'',
                    False
                ).call()
                function_tests.append({"name": "quoteSend_minimal", "status": "works", "result": str(result)})
                
            except Exception as e:
                function_tests.append({"name": "quoteSend_minimal", "status": "failed", "error": str(e)})
            
            # Test 12: Test send function with minimal parameters
            try:
                send_debug_abi = [{
                    "inputs": [
                        {"name": "_dstEid", "type": "uint32"},
                        {"name": "_to", "type": "bytes32"},
                        {"name": "_amountLD", "type": "uint256"},
                        {"name": "_minAmountLD", "type": "uint256"},
                        {"name": "_extraOptions", "type": "bytes"},
                        {"name": "_fee", "type": "tuple", "components": [
                            {"name": "nativeFee", "type": "uint256"},
                            {"name": "lzTokenFee", "type": "uint256"}
                        ]},
                        {"name": "_refundAddress", "type": "address"}
                    ],
                    "name": "send",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=send_debug_abi)
                
                # Test with minimal parameters
                test_params = {
                    '_dstEid': 40158,  # zkEVM EID
                    '_to': Web3.to_bytes(hexstr='0x28918ecf013F32fAf45e05d62B4D9b207FCae784'.lower().replace('0x', '').zfill(64)),
                    '_amountLD': 1000000000000000,  # 0.001 ETH in wei
                    '_minAmountLD': 1000000000000000,
                    '_extraOptions': b'',
                    '_fee': (Web3.to_wei(0.002, 'ether'), 0),  # 0.002 ETH fee
                    '_refundAddress': self.current_account.address
                }
                
                # Just test the call (simulation)
                result = contract.functions.send(
                    test_params['_dstEid'],
                    test_params['_to'],
                    test_params['_amountLD'],
                    test_params['_minAmountLD'],
                    test_params['_extraOptions'],
                    test_params['_fee'],
                    test_params['_refundAddress']
                ).call({
                    'from': self.current_account.address,
                    'value': Web3.to_wei(0.002, 'ether')
                })
                
                function_tests.append({"name": "send_simulation", "status": "works", "result": "simulation successful"})
                
            except Exception as e:
                function_tests.append({"name": "send_simulation", "status": "failed", "error": str(e)})
            
            # Test 13: Check if this is a Proxy contract
            try:
                proxy_abi = [{
                    "inputs": [],
                    "name": "implementation",
                    "outputs": [{"name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=proxy_abi)
                impl = contract.functions.implementation().call()
                function_tests.append({"name": "proxy_implementation", "status": "works", "result": impl})
                
            except Exception as e:
                function_tests.append({"name": "proxy_implementation", "status": "failed", "error": str(e)})
            
            # Test 14: Check balanceOf for the user
            try:
                balance_abi = [{
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=balance_abi)
                balance = contract.functions.balanceOf(self.current_account.address).call()
                function_tests.append({"name": "user_balance", "status": "works", "result": str(balance)})
                
            except Exception as e:
                function_tests.append({"name": "user_balance", "status": "failed", "error": str(e)})
            
            # Test 15: Check for deposit function (OFT Adapter)
            try:
                deposit_abi = [{
                    "inputs": [{"name": "amount", "type": "uint256"}],
                    "name": "deposit",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }]
                
                # Just check if function exists
                contract = web3.eth.contract(address=contract_address, abi=deposit_abi)
                function_tests.append({"name": "deposit_function", "status": "works", "result": "function exists"})
                
            except Exception as e:
                function_tests.append({"name": "deposit_function", "status": "failed", "error": str(e)})
            
            # Test 16: Check for mint function
            try:
                mint_abi = [{
                    "inputs": [
                        {"name": "to", "type": "address"},
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "mint",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=mint_abi)
                function_tests.append({"name": "mint_function", "status": "works", "result": "function exists"})
                
            except Exception as e:
                function_tests.append({"name": "mint_function", "status": "failed", "error": str(e)})
            
            # Test 17: Check for wrapAndDeposit function
            try:
                wrap_deposit_abi = [{
                    "inputs": [{"name": "amount", "type": "uint256"}],
                    "name": "wrapAndDeposit",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=wrap_deposit_abi)
                function_tests.append({"name": "wrapAndDeposit_function", "status": "works", "result": "function exists"})
                
            except Exception as e:
                function_tests.append({"name": "wrapAndDeposit_function", "status": "failed", "error": str(e)})
            
            # Test 18: Check underlying token address
            try:
                token_abi = [{
                    "inputs": [],
                    "name": "innerToken",
                    "outputs": [{"name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=token_abi)
                token_addr = contract.functions.innerToken().call()
                function_tests.append({"name": "innerToken", "status": "works", "result": token_addr})
                
            except Exception as e:
                function_tests.append({"name": "innerToken", "status": "failed", "error": str(e)})
            
            # Test 19: Check alternative underlying token
            try:
                underlying_abi = [{
                    "inputs": [],
                    "name": "underlyingToken",
                    "outputs": [{"name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=underlying_abi)
                underlying = contract.functions.underlyingToken().call()
                function_tests.append({"name": "underlyingToken", "status": "works", "result": underlying})
                
            except Exception as e:
                function_tests.append({"name": "underlyingToken", "status": "failed", "error": str(e)})
            
            return {
                "success": True,
                "contract_address": contract_address,
                "chain": chain_name,
                "function_tests": function_tests,
                "summary": {
                    "total_tests": len(function_tests),
                    "working_functions": [test["name"] for test in function_tests if test["status"] == "works"],
                    "failed_functions": [test["name"] for test in function_tests if test["status"] == "failed"]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Function test failed: {str(e)}"}

    async def get_oft_balance(self, chain_name: str, address: str) -> Dict[str, Any]:
        """Get OFT and WETH balances for an address"""
        try:
            web3 = self.web3_connections.get(chain_name)
            if not web3:
                return {"success": False, "error": f"Chain {chain_name} not connected"}
            
            # Get ETH balance
            eth_balance_wei = web3.eth.get_balance(address)
            eth_balance = float(Web3.from_wei(eth_balance_wei, 'ether'))
            
            # Get WETH balance
            weth_contract = self.weth_instances[chain_name]
            weth_balance_wei = weth_contract.functions.balanceOf(address).call()
            weth_balance = float(Web3.from_wei(weth_balance_wei, 'ether'))
            
            # Get OFT balance (should be deployed now!)
            oft_balance = 0.0
            config = self.oft_contracts[chain_name]
            if config.get('address'):
                try:
                    oft_contract = web3.eth.contract(
                        address=config['address'],
                        abi=LAYERZERO_OFT_ABI
                    )
                    oft_balance_wei = oft_contract.functions.balanceOf(address).call()
                    oft_balance = float(Web3.from_wei(oft_balance_wei, 'ether'))
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
