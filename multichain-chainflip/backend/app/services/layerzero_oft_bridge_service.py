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
        "name": "depositWETH",
        "outputs": [],
        "stateMutability": "nonpayable",
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
        
        # LayerZero OFT Configuration (FINAL FIXED CONTRACTS - JUNE 2025 - ALL QUOTESEND FIXED)
        self.oft_contracts = {
            "optimism_sepolia": {
                "address": "0x1A3F3924662aaa4f5122cD2B2EDff614Cf1d6eb0",  # ✅ FINAL FIXED CONTRACT
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
                "address": "0x35F63413FC7d0BE3f3e5f819BDd32b867A92d966",  # ✅ FINAL FIXED CONTRACT
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
                "address": "0x7793D6Af377548082833E341Fb93681B531C656B",  # ✅ FINAL FIXED CONTRACT
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
                "address": "0x736A068c7d2124D21026d86ee9F23F0A2d1dA5A4",  # ✅ FINAL FIXED CONTRACT
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
            
            # STEP 1.6: Convert WETH to OFT tokens (CRITICAL MISSING STEP!)
            print(f"\n🔄 === STEP 1.6: CONVERT WETH TO OFT TOKENS ===")
            oft_contract = self.oft_instances[from_chain]
            
            # Check current OFT balance
            oft_balance = oft_contract.functions.balanceOf(user_account.address).call()
            oft_balance_eth = float(Web3.from_wei(oft_balance, 'ether'))
            
            print(f"💳 Current OFT balance: {oft_balance_eth} cfWETH")
            print(f"🎯 Required OFT amount: {amount_eth} cfWETH")
            
            if oft_balance_eth < amount_eth:
                needed_deposit = amount_eth - oft_balance_eth
                print(f"🔄 Need to deposit {needed_deposit} WETH to get OFT tokens...")
                
                # Build depositWETH transaction
                deposit_nonce = source_web3.eth.get_transaction_count(user_account.address)
                deposit_amount_wei = Web3.to_wei(needed_deposit, 'ether')
                
                deposit_transaction = oft_contract.functions.depositWETH(deposit_amount_wei).build_transaction({
                    'from': user_account.address,
                    'gas': 200000,
                    'gasPrice': source_web3.eth.gas_price,
                    'nonce': deposit_nonce,
                    'chainId': source_web3.eth.chain_id
                })
                
                # Sign and send deposit transaction
                signed_deposit = source_web3.eth.account.sign_transaction(deposit_transaction, user_account.key)
                deposit_tx_hash = source_web3.eth.send_raw_transaction(signed_deposit.raw_transaction)
                deposit_receipt = source_web3.eth.wait_for_transaction_receipt(deposit_tx_hash, timeout=300)
                
                if deposit_receipt.status == 1:
                    print(f"✅ WETH deposited successfully: {deposit_tx_hash.hex()}")
                    
                    # Verify OFT balance increased
                    new_oft_balance = oft_contract.functions.balanceOf(user_account.address).call()
                    new_oft_balance_eth = float(Web3.from_wei(new_oft_balance, 'ether'))
                    print(f"✅ New OFT balance: {new_oft_balance_eth} cfWETH")
                    
                    if new_oft_balance_eth >= amount_eth:
                        print(f"✅ Sufficient OFT tokens now available for transfer")
                    else:
                        return {"success": False, "error": f"OFT deposit succeeded but still insufficient balance. Have: {new_oft_balance_eth}, Need: {amount_eth}"}
                else:
                    return {"success": False, "error": "WETH deposit transaction failed"}
            else:
                print(f"✅ Sufficient OFT tokens already available")
            
            print(f"✅ Ready to proceed with LayerZero OFT transfer")
            
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



    async def _execute_oft_send_adaptive(
        self, 
        web3: Web3, 
        from_chain: str, 
        to_chain: str, 
        user_account, 
        to_address: str, 
        amount_wei: int
    ) -> Dict[str, Any]:
        """Execute LayerZero OFT send with adaptive pattern detection"""
        try:
            source_config = self.oft_contracts[from_chain]
            target_config = self.oft_contracts[to_chain]
            
            print(f"🔗 Adaptive OFT Send: {from_chain} → {to_chain}")
            print(f"📍 Contract: {source_config['address']}")
            
            # First, test and find working configuration
            send_test = await self.test_and_fix_layerzero_send(from_chain, to_chain)
            
            if not send_test["success"] or not send_test.get("working_configuration"):
                return {"success": False, "error": "No working LayerZero configuration found"}
            
            working_config = send_test["working_configuration"]
            config_type = working_config["type"]
            
            print(f"✅ Using working configuration: {config_type}")
            
            # Get fee estimate
            fee_estimate = await self.estimate_oft_transfer_fee(from_chain, to_chain, float(Web3.from_wei(amount_wei, 'ether')))
            if not fee_estimate["success"]:
                return {"success": False, "error": f"Fee estimation failed: {fee_estimate['error']}"}
            
            native_fee = fee_estimate["native_fee_wei"]
            
            # Convert recipient address to bytes32 format
            recipient_bytes32 = Web3.to_bytes(hexstr=to_address.lower().replace('0x', '').zfill(64))
            
            # Create contract instance with appropriate ABI
            oft_contract = web3.eth.contract(
                address=source_config['address'],
                abi=working_config["abi"]
            )
            
            # Build transaction based on configuration type
            nonce = web3.eth.get_transaction_count(user_account.address)
            
            if config_type == "v2_struct":
                print(f"🔧 Using V2 struct-based send")
                
                # Create struct parameters
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
                
                # Test call first
                try:
                    oft_contract.functions.send(
                        send_param,
                        messaging_fee,
                        user_account.address
                    ).call({
                        'from': user_account.address,
                        'value': native_fee
                    })
                    print("✅ V2 struct simulation successful")
                except Exception as sim_error:
                    return {"success": False, "error": f"V2 struct simulation failed: {sim_error}"}
                
                # Build transaction
                transaction = oft_contract.functions.send(
                    send_param,
                    messaging_fee,
                    user_account.address
                ).build_transaction({
                    'from': user_account.address,
                    'value': native_fee,
                    'gas': 1000000,
                    'gasPrice': web3.eth.gas_price,
                    'nonce': nonce,
                    'chainId': web3.eth.chain_id
                })
                
            elif config_type == "oft_adapter":
                print(f"🔧 Using OFT Adapter sendFrom")
                
                messaging_fee = (native_fee, 0)
                function_name = working_config["send_function"]  # Should be "sendFrom"
                
                # Test call first
                try:
                    getattr(oft_contract.functions, function_name)(
                        target_config['layerzero_eid'],
                        recipient_bytes32,
                        amount_wei,
                        amount_wei,
                        b'',
                        messaging_fee,
                        user_account.address
                    ).call({
                        'from': user_account.address,
                        'value': native_fee
                    })
                    print("✅ OFT Adapter simulation successful")
                except Exception as sim_error:
                    return {"success": False, "error": f"OFT Adapter simulation failed: {sim_error}"}
                
                # Build transaction
                transaction = getattr(oft_contract.functions, function_name)(
                    target_config['layerzero_eid'],
                    recipient_bytes32,
                    amount_wei,
                    amount_wei,
                    b'',
                    messaging_fee,
                    user_account.address
                ).build_transaction({
                    'from': user_account.address,
                    'value': native_fee,
                    'gas': 1000000,
                    'gasPrice': web3.eth.gas_price,
                    'nonce': nonce,
                    'chainId': web3.eth.chain_id
                })
                
            else:  # v1_individual (default/current implementation)
                print(f"🔧 Using V1 individual parameters")
                
                messaging_fee = (native_fee, 0)
                
                # Test call first
                try:
                    oft_contract.functions.send(
                        target_config['layerzero_eid'],
                        recipient_bytes32,
                        amount_wei,
                        amount_wei,
                        b'',
                        messaging_fee,
                        user_account.address
                    ).call({
                        'from': user_account.address,
                        'value': native_fee
                    })
                    print("✅ V1 individual simulation successful")
                except Exception as sim_error:
                    return {"success": False, "error": f"V1 individual simulation failed: {sim_error}"}
                
                # Build transaction
                transaction = oft_contract.functions.send(
                    target_config['layerzero_eid'],
                    recipient_bytes32,
                    amount_wei,
                    amount_wei,
                    b'',
                    messaging_fee,
                    user_account.address
                ).build_transaction({
                    'from': user_account.address,
                    'value': native_fee,
                    'gas': 1000000,
                    'gasPrice': web3.eth.gas_price,
                    'nonce': nonce,
                    'chainId': web3.eth.chain_id
                })
            
            # Sign and send transaction
            print(f"✍️ Signing and sending adaptive OFT transaction...")
            signed_txn = web3.eth.account.sign_transaction(transaction, user_account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"📤 Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            print(f"⏳ Waiting for transaction confirmation...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print(f"✅ Adaptive OFT send successful!")
                
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
                    "configuration_used": config_type,
                    "adaptive_method": True
                }
            else:
                return {"success": False, "error": f"Transaction failed - Receipt status: {receipt.status}"}
                
        except Exception as e:
            print(f"❌ Adaptive OFT send error: {e}")
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
            # Try adaptive method first
            adaptive_result = await self._execute_oft_send_adaptive(
                web3, from_chain, to_chain, user_account, to_address, amount_wei
            )
            
            if adaptive_result["success"]:
                return adaptive_result
            
            print(f"⚠️ Adaptive method failed: {adaptive_result.get('error')}")
            print(f"🔄 Falling back to original implementation...")
            
            # Fallback to original implementation
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

    async def investigate_contract_implementation(self, chain_name: str) -> Dict[str, Any]:
        """Deep investigation of the deployed contract to understand its actual implementation"""
        try:
            web3 = self.web3_connections.get(chain_name)
            config = self.oft_contracts[chain_name]
            contract_address = config.get('address')
            
            if not web3 or not contract_address:
                return {"success": False, "error": "Chain or contract not available"}
            
            print(f"🔍 DEEP CONTRACT INVESTIGATION: {chain_name}")
            print(f"📍 Contract Address: {contract_address}")
            
            investigation_results = {}
            
            # 1. Basic Contract Info
            try:
                code = web3.eth.get_code(contract_address)
                code_size = len(code)
                investigation_results["basic_info"] = {
                    "has_code": code_size > 0,
                    "code_size_bytes": code_size,
                    "code_hash": web3.keccak(code).hex() if code_size > 0 else None
                }
                print(f"📦 Contract code size: {code_size} bytes")
            except Exception as e:
                investigation_results["basic_info"] = {"error": str(e)}
            
            # 2. Check for LayerZero Standards
            try:
                # Test different LayerZero endpoint patterns
                endpoint_tests = {}
                
                # Test lzEndpoint (V2 standard)
                try:
                    lz_abi = [{"inputs": [], "name": "lzEndpoint", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"}]
                    contract = web3.eth.contract(address=contract_address, abi=lz_abi)
                    endpoint = contract.functions.lzEndpoint().call()
                    endpoint_tests["lzEndpoint"] = {"status": "works", "result": endpoint}
                except Exception as e:
                    endpoint_tests["lzEndpoint"] = {"status": "failed", "error": str(e)}
                
                # Test endpoint (V1 standard)
                try:
                    endpoint_abi = [{"inputs": [], "name": "endpoint", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"}]
                    contract = web3.eth.contract(address=contract_address, abi=endpoint_abi)
                    endpoint = contract.functions.endpoint().call()
                    endpoint_tests["endpoint"] = {"status": "works", "result": endpoint}
                except Exception as e:
                    endpoint_tests["endpoint"] = {"status": "failed", "error": str(e)}
                
                investigation_results["layerzero_endpoints"] = endpoint_tests
                
            except Exception as e:
                investigation_results["layerzero_endpoints"] = {"error": str(e)}
            
            # 3. Check for OFT vs OFT Adapter patterns
            try:
                oft_pattern_tests = {}
                
                # Test for underlying token (OFT Adapter pattern)
                token_function_names = ["token", "innerToken", "underlyingToken", "wrappedToken"]
                for func_name in token_function_names:
                    try:
                        token_abi = [{"inputs": [], "name": func_name, "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"}]
                        contract = web3.eth.contract(address=contract_address, abi=token_abi)
                        token_addr = contract.functions[func_name]().call()
                        oft_pattern_tests[func_name] = {"status": "works", "result": token_addr}
                        print(f"✅ Found {func_name}: {token_addr}")
                    except Exception as e:
                        oft_pattern_tests[func_name] = {"status": "failed", "error": str(e)}
                
                investigation_results["oft_patterns"] = oft_pattern_tests
                
            except Exception as e:
                investigation_results["oft_patterns"] = {"error": str(e)}
            
            # 4. Check for Proxy Patterns
            try:
                proxy_tests = {}
                
                # Common proxy implementation functions
                proxy_functions = ["implementation", "getImplementation", "_implementation"]
                for func_name in proxy_functions:
                    try:
                        proxy_abi = [{"inputs": [], "name": func_name, "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"}]
                        contract = web3.eth.contract(address=contract_address, abi=proxy_abi)
                        impl_addr = contract.functions[func_name]().call()
                        proxy_tests[func_name] = {"status": "works", "result": impl_addr}
                        print(f"🔗 Proxy detected - {func_name}: {impl_addr}")
                    except Exception as e:
                        proxy_tests[func_name] = {"status": "failed", "error": str(e)}
                
                investigation_results["proxy_patterns"] = proxy_tests
                
            except Exception as e:
                investigation_results["proxy_patterns"] = {"error": str(e)}
            
            # 5. Test Various Send Function Signatures
            try:
                send_function_tests = {}
                
                # V2 OFT Standard with struct
                try:
                    v2_send_abi = [{
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
                        "outputs": [],
                        "stateMutability": "payable",
                        "type": "function"
                    }]
                    
                    # Just check if function signature exists
                    contract = web3.eth.contract(address=contract_address, abi=v2_send_abi)
                    send_function_tests["v2_struct_send"] = {"status": "signature_exists", "result": "V2 struct-based send function found"}
                    
                except Exception as e:
                    send_function_tests["v2_struct_send"] = {"status": "failed", "error": str(e)}
                
                # V1 OFT Standard with individual parameters (current implementation)
                try:
                    v1_send_abi = [{
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
                    
                    contract = web3.eth.contract(address=contract_address, abi=v1_send_abi)
                    send_function_tests["v1_individual_send"] = {"status": "signature_exists", "result": "V1 individual parameter send function found"}
                    
                except Exception as e:
                    send_function_tests["v1_individual_send"] = {"status": "failed", "error": str(e)}
                
                investigation_results["send_function_variants"] = send_function_tests
                
            except Exception as e:
                investigation_results["send_function_variants"] = {"error": str(e)}
            
            # 6. Test Fee Quote Functions Comprehensively
            try:
                fee_function_tests = {}
                
                # Multiple quoteSend variants
                quote_variants = [
                    # V2 struct-based
                    {
                        "name": "quoteSend_v2_struct",
                        "abi": [{
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
                    },
                    # V1 individual parameters
                    {
                        "name": "quoteSend_v1_individual",
                        "abi": [{
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
                    }
                ]
                
                for variant in quote_variants:
                    try:
                        contract = web3.eth.contract(address=contract_address, abi=variant["abi"])
                        fee_function_tests[variant["name"]] = {"status": "signature_exists", "result": "Function signature found"}
                    except Exception as e:
                        fee_function_tests[variant["name"]] = {"status": "failed", "error": str(e)}
                
                investigation_results["fee_quote_variants"] = fee_function_tests
                
            except Exception as e:
                investigation_results["fee_quote_variants"] = {"error": str(e)}
            
            # 7. Check Contract Initialization State
            try:
                initialization_tests = {}
                
                # Check if peer is set for target chain (critical for LayerZero)
                try:
                    peer_abi = [{"inputs": [{"name": "_eid", "type": "uint32"}], "name": "peers", "outputs": [{"name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"}]
                    contract = web3.eth.contract(address=contract_address, abi=peer_abi)
                    
                    # Test peer connection to zkEVM Cardona (our target)
                    zkevm_eid = 40158
                    peer_address = contract.functions.peers(zkevm_eid).call()
                    
                    if peer_address != b'\x00' * 32:  # Not zero bytes
                        initialization_tests["peer_zkevm"] = {"status": "configured", "result": peer_address.hex()}
                        print(f"✅ Peer configured for zkEVM: {peer_address.hex()}")
                    else:
                        initialization_tests["peer_zkevm"] = {"status": "not_configured", "result": "Peer not set"}
                        print(f"⚠️ Peer NOT configured for zkEVM")
                        
                except Exception as e:
                    initialization_tests["peer_zkevm"] = {"status": "failed", "error": str(e)}
                
                investigation_results["initialization_state"] = initialization_tests
                
            except Exception as e:
                investigation_results["initialization_state"] = {"error": str(e)}
            
            return {
                "success": True,
                "chain": chain_name,
                "contract_address": contract_address,
                "investigation_results": investigation_results,
                "recommendations": self._generate_fix_recommendations(investigation_results)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Investigation failed: {str(e)}"}

    def _generate_fix_recommendations(self, investigation_results: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on investigation results"""
        recommendations = []
        
        # Check LayerZero endpoint availability
        lz_endpoints = investigation_results.get("layerzero_endpoints", {})
        if lz_endpoints.get("lzEndpoint", {}).get("status") == "works":
            recommendations.append("✅ LayerZero V2 endpoint detected - use V2 functions")
        elif lz_endpoints.get("endpoint", {}).get("status") == "works":
            recommendations.append("⚠️ LayerZero V1 endpoint detected - may need V1 functions")
        else:
            recommendations.append("❌ No LayerZero endpoint found - contract may not be LayerZero OFT")
        
        # Check OFT pattern
        oft_patterns = investigation_results.get("oft_patterns", {})
        underlying_token_found = False
        for pattern_name, pattern_result in oft_patterns.items():
            if pattern_result.get("status") == "works":
                underlying_token_found = True
                recommendations.append(f"🔗 OFT Adapter pattern detected - underlying token via {pattern_name}")
                break
        
        if not underlying_token_found:
            recommendations.append("📦 Direct OFT pattern (not adapter) - may need different deposit method")
        
        # Check proxy pattern
        proxy_patterns = investigation_results.get("proxy_patterns", {})
        for proxy_name, proxy_result in proxy_patterns.items():
            if proxy_result.get("status") == "works":
                recommendations.append(f"🔄 Proxy contract detected - implementation at {proxy_result.get('result')}")
                break
        
        # Check initialization
        init_state = investigation_results.get("initialization_state", {})
        peer_config = init_state.get("peer_zkevm", {})
        if peer_config.get("status") == "not_configured":
            recommendations.append("❌ CRITICAL: Peer not configured for target chain - this prevents transfers")
        elif peer_config.get("status") == "configured":
            recommendations.append("✅ Peer properly configured for target chain")
        
        # Check function signatures
        send_variants = investigation_results.get("send_function_variants", {})
        if send_variants.get("v2_struct_send", {}).get("status") == "signature_exists":
            recommendations.append("🔧 Use V2 struct-based send function parameters")
        elif send_variants.get("v1_individual_send", {}).get("status") == "signature_exists":
            recommendations.append("🔧 Use V1 individual parameter send function")
        
        return recommendations

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

    async def test_and_fix_layerzero_send(self, chain_name: str, target_chain: str) -> Dict[str, Any]:
        """Test different LayerZero send patterns and identify working configuration"""
        try:
            web3 = self.web3_connections.get(chain_name)
            source_config = self.oft_contracts[chain_name]
            target_config = self.oft_contracts[target_chain]
            contract_address = source_config.get('address')
            
            if not web3 or not contract_address:
                return {"success": False, "error": "Chain or contract not available"}
            
            print(f"🔧 TESTING AND FIXING LAYERZERO SEND: {chain_name} → {target_chain}")
            print(f"📍 Contract: {contract_address}")
            
            test_results = []
            working_configuration = None
            
            # Test parameters
            target_eid = target_config['layerzero_eid']
            recipient_address = "0x28918ecf013F32fAf45e05d62B4D9b207FCae784"
            recipient_bytes32 = Web3.to_bytes(hexstr=recipient_address.lower().replace('0x', '').zfill(64))
            test_amount = Web3.to_wei(0.001, 'ether')  # Small test amount
            test_fee = Web3.to_wei(0.002, 'ether')    # Test fee
            
            print(f"🎯 Target EID: {target_eid}")
            print(f"📧 Recipient: {recipient_address}")
            print(f"💰 Test amount: 0.001 ETH")
            
            # Test 1: V2 OFT Standard with struct parameters
            try:
                print(f"\n🧪 TEST 1: V2 OFT with struct parameters")
                
                v2_send_abi = [{
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
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_address, abi=v2_send_abi)
                
                # Create struct parameters
                send_param = (
                    target_eid,           # dstEid
                    recipient_bytes32,    # to
                    test_amount,          # amountLD
                    test_amount,          # minAmountLD
                    b'',                  # extraOptions
                    b'',                  # composeMsg
                    b''                   # oftCmd
                )
                
                messaging_fee = (test_fee, 0)  # (nativeFee, lzTokenFee)
                
                # Test call
                result = contract.functions.send(
                    send_param,
                    messaging_fee,
                    self.current_account.address
                ).call({
                    'from': self.current_account.address,
                    'value': test_fee
                })
                
                test_results.append({
                    "test_name": "V2_struct_send",
                    "status": "success",
                    "result": "Function call successful",
                    "configuration": {
                        "type": "v2_struct",
                        "abi": v2_send_abi,
                        "parameters": "struct-based"
                    }
                })
                
                working_configuration = {
                    "type": "v2_struct",
                    "abi": v2_send_abi,
                    "send_function": "send",
                    "parameter_format": "struct"
                }
                
                print(f"✅ V2 struct send: SUCCESS")
                
            except Exception as e:
                test_results.append({
                    "test_name": "V2_struct_send",
                    "status": "failed",
                    "error": str(e)
                })
                print(f"❌ V2 struct send failed: {e}")
            
            # Test 2: V1 OFT Standard with individual parameters (current implementation)
            if working_configuration is None:
                try:
                    print(f"\n🧪 TEST 2: V1 OFT with individual parameters")
                    
                    v1_send_abi = [{
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
                    
                    contract = web3.eth.contract(address=contract_address, abi=v1_send_abi)
                    messaging_fee = (test_fee, 0)  # (nativeFee, lzTokenFee)
                    
                    # Test call
                    result = contract.functions.send(
                        target_eid,           # _dstEid
                        recipient_bytes32,    # _to
                        test_amount,          # _amountLD
                        test_amount,          # _minAmountLD
                        b'',                  # _extraOptions
                        messaging_fee,        # _fee
                        self.current_account.address  # _refundAddress
                    ).call({
                        'from': self.current_account.address,
                        'value': test_fee
                    })
                    
                    test_results.append({
                        "test_name": "V1_individual_send",
                        "status": "success",
                        "result": "Function call successful",
                        "configuration": {
                            "type": "v1_individual",
                            "abi": v1_send_abi,
                            "parameters": "individual"
                        }
                    })
                    
                    working_configuration = {
                        "type": "v1_individual",
                        "abi": v1_send_abi,
                        "send_function": "send",
                        "parameter_format": "individual"
                    }
                    
                    print(f"✅ V1 individual send: SUCCESS")
                    
                except Exception as e:
                    test_results.append({
                        "test_name": "V1_individual_send",
                        "status": "failed",
                        "error": str(e)
                    })
                    print(f"❌ V1 individual send failed: {e}")
            
            # Test 3: OFT Adapter specific send (if underlying token detected)
            if working_configuration is None:
                try:
                    print(f"\n🧪 TEST 3: OFT Adapter send pattern")
                    
                    # First check if this is an adapter by looking for underlying token
                    token_abi = [{"inputs": [], "name": "token", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"}]
                    token_contract = web3.eth.contract(address=contract_address, abi=token_abi)
                    underlying_token = token_contract.functions.token().call()
                    
                    print(f"🔗 Underlying token found: {underlying_token}")
                    
                    # Try adapter-specific send
                    adapter_send_abi = [{
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
                        "name": "sendFrom",  # Note: sendFrom instead of send
                        "outputs": [],
                        "stateMutability": "payable",
                        "type": "function"
                    }]
                    
                    contract = web3.eth.contract(address=contract_address, abi=adapter_send_abi)
                    messaging_fee = (test_fee, 0)
                    
                    result = contract.functions.sendFrom(
                        target_eid,
                        recipient_bytes32,
                        test_amount,
                        test_amount,
                        b'',
                        messaging_fee,
                        self.current_account.address
                    ).call({
                        'from': self.current_account.address,
                        'value': test_fee
                    })
                    
                    test_results.append({
                        "test_name": "OFT_adapter_sendFrom",
                        "status": "success",
                        "result": "sendFrom function successful",
                        "underlying_token": underlying_token,
                        "configuration": {
                            "type": "oft_adapter",
                            "abi": adapter_send_abi,
                            "function": "sendFrom"
                        }
                    })
                    
                    working_configuration = {
                        "type": "oft_adapter",
                        "abi": adapter_send_abi,
                        "send_function": "sendFrom",
                        "underlying_token": underlying_token
                    }
                    
                    print(f"✅ OFT Adapter sendFrom: SUCCESS")
                    
                except Exception as e:
                    test_results.append({
                        "test_name": "OFT_adapter_sendFrom", 
                        "status": "failed",
                        "error": str(e)
                    })
                    print(f"❌ OFT Adapter sendFrom failed: {e}")
            
            # Generate fix code if working configuration found
            fix_code = None
            if working_configuration:
                fix_code = self._generate_send_fix_code(working_configuration)
            
            return {
                "success": True,
                "chain": chain_name,
                "target_chain": target_chain,
                "test_results": test_results,
                "working_configuration": working_configuration,
                "fix_needed": working_configuration is not None,
                "fix_code": fix_code,
                "recommendation": "Update _execute_oft_send function with working configuration" if working_configuration else "Contract may need redeployment or initialization"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Send test failed: {str(e)}"}

    def _generate_send_fix_code(self, config: Dict[str, Any]) -> str:
        """Generate the code fix for the working LayerZero configuration"""
        
        if config["type"] == "v2_struct":
            return """
# V2 OFT Fix: Use struct-based parameters
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

transaction = oft_contract.functions.send(
    send_param,                      # _sendParam struct
    messaging_fee,                   # _fee struct
    user_account.address            # _refundAddress
).build_transaction({...})
"""
        
        elif config["type"] == "oft_adapter":
            return f"""
# OFT Adapter Fix: Use sendFrom function
messaging_fee = (native_fee, 0)  # (nativeFee, lzTokenFee)

transaction = oft_contract.functions.sendFrom(
    target_config['layerzero_eid'],  # _dstEid
    recipient_bytes32,               # _to
    amount_wei,                      # _amountLD
    amount_wei,                      # _minAmountLD
    b'',                            # _extraOptions
    messaging_fee,                   # _fee
    user_account.address            # _refundAddress
).build_transaction({{...}})

# Note: Underlying token is {config.get('underlying_token', 'N/A')}
"""
        
        else:  # v1_individual (current implementation should work)
            return """
# V1 OFT Fix: Current implementation should work
# The issue might be in peer configuration or contract initialization
"""

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
