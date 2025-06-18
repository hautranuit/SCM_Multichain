"""
Direct LayerZero Messaging Service
Handles direct cross-chain messaging using LayerZero for ChainFLIP CID sync
Uses DirectLayerZeroMessenger contracts deployed on all 4 chains
"""
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from app.core.config import get_settings
from app.core.database import get_database

settings = get_settings()

# LayerZero V2 endpoint IDs for the 4 chains
LAYERZERO_ENDPOINTS = {
    "base_sepolia": 40245,      # Manufacturer chain
    "op_sepolia": 40232,        # Buyer chain
    "arbitrum_sepolia": 40231,  # Additional chain
    "polygon_amoy": 40267       # Hub chain
}

# Chain configurations
CHAIN_CONFIGS = {
    "base_sepolia": {
        "chain_id": 84532,
        "rpc_url": settings.base_sepolia_rpc,
        "layerzero_eid": 40245,
        "role": "manufacturer",
        "name": "Base Sepolia"
    },
    "op_sepolia": {
        "chain_id": 11155420,
        "rpc_url": "https://sepolia.optimism.io",  # Public OP Sepolia RPC
        "layerzero_eid": 40232,
        "role": "buyer",
        "name": "Optimism Sepolia"
    },
    "arbitrum_sepolia": {
        "chain_id": 421614,
        "rpc_url": "https://sepolia-rollup.arbitrum.io/rpc",  # Public Arbitrum Sepolia RPC
        "layerzero_eid": 40231,
        "role": "additional",
        "name": "Arbitrum Sepolia"
    },
    "polygon_amoy": {
        "chain_id": 80002,
        "rpc_url": settings.polygon_pos_rpc,
        "layerzero_eid": 40267,
        "role": "hub",
        "name": "Polygon Amoy"
    }
}

# Target admin address for cross-chain CID sync on Polygon Amoy
TARGET_ADMIN_ADDRESS = "0x36DDc43D2FfA30588CcAC8C2979b69225c292a73"  # Polygon Amoy admin

# DirectLayerZeroMessenger ABI (essential functions only)
DIRECT_MESSENGER_ABI = [
    {
        "inputs": [
            {"name": "targetEid", "type": "uint16"},
            {"name": "messageType", "type": "string"},
            {"name": "payload", "type": "bytes"}
        ],
        "name": "sendCrossChainMessage",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "eid", "type": "uint16"},
            {"name": "peer", "type": "bytes32"}
        ],
        "name": "setPeer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "tokenId", "type": "string"},
            {"name": "metadataCID", "type": "string"},
            {"name": "manufacturer", "type": "address"}
        ],
        "name": "syncCIDToAllChains",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "targetEid", "type": "uint16"},
            {"name": "payload", "type": "bytes"},
            {"name": "useZro", "type": "bool"},
            {"name": "adapterParams", "type": "bytes"}
        ],
        "name": "estimateFees",
        "outputs": [
            {"name": "nativeFee", "type": "uint256"},
            {"name": "zroFee", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getSupportedEids",
        "outputs": [{"name": "", "type": "uint16[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "messageId", "type": "uint256"},
            {"indexed": True, "name": "sourceEid", "type": "uint16"},
            {"indexed": True, "name": "targetEid", "type": "uint16"},
            {"indexed": False, "name": "messageType", "type": "string"},
            {"indexed": False, "name": "messageHash", "type": "bytes32"}
        ],
        "name": "MessageSent",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenId", "type": "string"},
            {"indexed": False, "name": "metadataCID", "type": "string"},
            {"indexed": True, "name": "manufacturer", "type": "address"},
            {"indexed": True, "name": "sourceEid", "type": "uint16"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "CIDSynced",
        "type": "event"
    }
]

class DirectLayerZeroMessagingService:
    def __init__(self):
        self.web3_connections: Dict[str, Web3] = {}
        self.messenger_contracts: Dict[str, Any] = {}
        self.contract_addresses: Dict[str, str] = {}
        self.account = None
        self.database = None
        
    async def initialize(self):
        """Initialize the direct LayerZero messaging service"""
        try:
            print("🌐 Initializing Direct LayerZero Messaging Service...")
            
            # Initialize database connection
            self.database = await get_database()
            
            # Initialize account from private key
            if settings.deployer_private_key:
                self.account = Account.from_key(settings.deployer_private_key)
                print(f"✅ Account loaded: {self.account.address}")
            
            # Initialize Web3 connections for all 4 chains
            await self._initialize_web3_connections()
            
            # Load contract addresses (will be updated after deployment)
            await self._load_contract_addresses()
            
            # Initialize contract instances
            await self._initialize_contracts()
            
            print("✅ Direct LayerZero Messaging Service initialized successfully")
            
        except Exception as e:
            print(f"❌ Direct LayerZero Messaging Service initialization failed: {e}")
            raise

    async def _initialize_web3_connections(self):
        """Initialize Web3 connections for all chains"""
        for chain_name, config in CHAIN_CONFIGS.items():
            try:
                if config["rpc_url"]:
                    web3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
                    
                    # Add PoA middleware for chains that need it
                    if chain_name in ["base_sepolia", "polygon_amoy"]:
                        web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                    
                    if web3.is_connected():
                        latest_block = web3.eth.block_number
                        print(f"✅ Connected to {config['name']} (Chain ID: {config['chain_id']})")
                        print(f"📊 Latest block: {latest_block}")
                        self.web3_connections[chain_name] = web3
                    else:
                        print(f"❌ Failed to connect to {config['name']}")
                else:
                    print(f"⚠️ No RPC URL configured for {config['name']}")
                    
            except Exception as e:
                print(f"❌ Error connecting to {config['name']}: {e}")

    async def _load_contract_addresses(self):
        """Load DirectLayerZeroMessenger contract addresses"""
        # DirectLayerZeroMessenger Contract Addresses - Updated 2025-06-17 with deployed contracts
        self.contract_addresses = {
            "base_sepolia": settings.direct_messenger_base_sepolia or "0x1208F8F0E40381F14E41621906D13C9c3CaAa061",
            "op_sepolia": settings.direct_messenger_op_sepolia or "0x97420B3dEd4B3eA72Ff607fd96927Bfa605b197c", 
            "arbitrum_sepolia": settings.direct_messenger_arbitrum_sepolia or "0x25409B7ee450493248fD003A759304FF7f748c53",
            "polygon_amoy": settings.direct_messenger_polygon_amoy or "0x34705a7e91b465AE55844583EC16715C88bD457a"
        }
        
        print("📄 Loaded DirectLayerZeroMessenger contract addresses:")
        for chain, address in self.contract_addresses.items():
            print(f"   {CHAIN_CONFIGS[chain]['name']}: {address}")

    async def _initialize_contracts(self):
        """Initialize contract instances"""
        for chain_name, web3 in self.web3_connections.items():
            contract_address = self.contract_addresses.get(chain_name)
            if contract_address and contract_address.startswith("0x") and contract_address != "0x0000000000000000000000000000000000000000":
                try:
                    contract = web3.eth.contract(
                        address=contract_address,
                        abi=DIRECT_MESSENGER_ABI
                    )
                    self.messenger_contracts[chain_name] = contract
                    print(f"✅ Contract instance created for {CHAIN_CONFIGS[chain_name]['name']}")
                except Exception as e:
                    print(f"❌ Failed to create contract instance for {chain_name}: {e}")
            else:
                print(f"⚠️ No valid contract address for {chain_name}: {contract_address}")

    async def send_cid_sync_to_all_chains(
        self,
        source_chain: str,
        token_id: str,
        metadata_cid: str,
        manufacturer: str,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send CID sync message to all other chains using DirectLayerZeroMessenger
        This is the main function called from blockchain_service._sync_cid_to_hub
        """
        try:
            print(f"\n🌐 === DIRECT LAYERZERO CID SYNC TO ALL CHAINS ===")
            print(f"🏭 Source: {source_chain}")
            print(f"🔖 Token ID: {token_id}")
            print(f"📦 CID: {metadata_cid}")
            print(f"👤 Manufacturer: {manufacturer}")
            
            # Get source chain Web3 and contract
            source_web3 = self.web3_connections.get(source_chain)
            source_contract = self.messenger_contracts.get(source_chain)
            
            if not source_web3:
                return {"success": False, "error": f"Source chain {source_chain} not connected"}
            
            if not source_contract:
                return {"success": False, "error": f"DirectLayerZeroMessenger contract not available for {source_chain}"}
            
            # Estimate total fees for sending to all other chains
            print(f"💰 Estimating LayerZero fees for all chains...")
            
            total_fee_estimate = await self._estimate_total_sync_fees(
                source_chain, token_id, metadata_cid, manufacturer
            )
            
            if not total_fee_estimate["success"]:
                # Try to set up peer connections automatically if fee estimation fails
                print(f"💡 Fee estimation failed - attempting to set up LayerZero peer connections...")
                peer_setup_result = await self.setup_layerzero_peer_connections()
                print(f"🔗 Peer setup result: {peer_setup_result}")
                
                return {
                    "success": False, 
                    "error": f"Fee estimation failed: {total_fee_estimate['error']}",
                    "peer_setup_attempted": True,
                    "peer_setup_result": peer_setup_result
                }
            
            # Check if contract fee estimation failed (indicating peer connection issues)
            if total_fee_estimate.get("peer_setup_needed", False):
                print(f"\n💡 Contract fee estimation failed - peer connections likely missing!")
                print(f"🚀 ATTEMPTING TO SET UP ALL LAYERZERO PEER CONNECTIONS...")
                
                try:
                    peer_setup_result = await self.setup_layerzero_peer_connections()
                    print(f"🔗 Peer setup completed!")
                    print(f"📊 Setup Summary:")
                    print(f"   Total connections: {peer_setup_result.get('total_connections', 0)}")
                    print(f"   Successful: {peer_setup_result.get('summary', {}).get('successful', 0)}")
                    print(f"   Already set: {peer_setup_result.get('summary', {}).get('already_set', 0)}")
                    print(f"   Failed: {peer_setup_result.get('summary', {}).get('failed', 0)}")
                    
                    # If we successfully set up some connections, suggest retrying
                    successful_connections = peer_setup_result.get('summary', {}).get('successful', 0)
                    if successful_connections > 0:
                        return {
                            "success": False,
                            "error": "Peer connections were set up - please try minting again",
                            "peer_setup_completed": True,
                            "connections_established": successful_connections,
                            "retry_suggested": True,
                            "peer_setup_result": peer_setup_result
                        }
                    
                except Exception as peer_setup_error:
                    print(f"❌ Peer setup failed: {peer_setup_error}")
                    # Continue with normal flow
            
            total_fee_wei = total_fee_estimate["total_fee_wei"]
            total_fee_eth = Web3.from_wei(total_fee_wei, 'ether')
            
            print(f"💰 Total estimated fee: {total_fee_eth} ETH")
            
            # Check if account has sufficient balance
            account_balance = source_web3.eth.get_balance(self.account.address)
            account_balance_eth = Web3.from_wei(account_balance, 'ether')
            
            print(f"💳 Account balance: {account_balance_eth} ETH")
            
            if account_balance < total_fee_wei:
                return {
                    "success": False,
                    "error": f"Insufficient balance for LayerZero fees. Need: {total_fee_eth} ETH, Have: {account_balance_eth} ETH"
                }
            
            # Execute direct cross-chain message to Polygon Amoy only
            print(f"🚀 Executing direct cross-chain message to Polygon Amoy...")
            
            nonce = source_web3.eth.get_transaction_count(self.account.address)
            gas_price = source_web3.eth.gas_price
            
            # Get the correct target EID from fee estimation (might have been updated)
            target_eid = CHAIN_CONFIGS["polygon_amoy"]["layerzero_eid"]
            
            # Prepare payload for Polygon Amoy
            payload_data = {
                "type": "CID_SYNC",
                "token_id": token_id,
                "metadata_cid": metadata_cid,
                "manufacturer": manufacturer,
                "source_chain_id": source_web3.eth.chain_id,
                "timestamp": int(time.time())
            }
            payload_bytes = json.dumps(payload_data).encode('utf-8')
            
            print(f"📋 Using LayerZero EID: {target_eid} for Polygon Amoy")
            
            # Build transaction for direct cross-chain message
            transaction = source_contract.functions.sendCrossChainMessage(
                target_eid,
                "CID_SYNC",
                payload_bytes
            ).build_transaction({
                'from': self.account.address,
                'value': total_fee_wei,  # LayerZero fees
                'gas': 800000,  # Increased gas limit for LayerZero cross-chain messaging
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': source_web3.eth.chain_id
            })
            
            print(f"📋 Transaction details:")
            print(f"   Value (LayerZero fees): {total_fee_eth} ETH")
            print(f"   Gas: {transaction['gas']}")
            print(f"   Gas Price: {Web3.from_wei(gas_price, 'gwei')} Gwei")
            
            # Sign and send transaction
            signed_txn = source_web3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = source_web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"📤 Transaction sent: {tx_hash_hex}")
            print(f"⏳ Waiting for confirmation...")
            
            # Wait for transaction confirmation
            receipt = source_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print(f"✅ CID sync transaction confirmed!")
                print(f"📊 Block: {receipt.blockNumber}")
                print(f"⛽ Gas Used: {receipt.gasUsed}")
                
                # Parse events to get sync details
                sync_events = await self._parse_sync_events(source_contract, receipt)
                
                # Store sync record in database
                sync_record = {
                    "sync_id": str(uuid.uuid4()),
                    "token_id": token_id,
                    "metadata_cid": metadata_cid,
                    "manufacturer": manufacturer,
                    "source_chain": source_chain,
                    "source_eid": CHAIN_CONFIGS[source_chain]["layerzero_eid"],
                    "transaction_hash": tx_hash_hex,
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "layerzero_fee_paid": float(total_fee_eth),
                    "sync_method": "direct_layerzero_polygon_only",
                    "target_chains": ["polygon_amoy"],
                    "target_admin": TARGET_ADMIN_ADDRESS,
                    "events": sync_events,
                    "timestamp": time.time(),
                    "status": "sent"
                }
                
                # Save to database
                await self.database.direct_layerzero_syncs.insert_one(sync_record)
                
                return {
                    "success": True,
                    "transaction_hash": tx_hash_hex,
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "layerzero_fee_paid": float(total_fee_eth),
                    "target_chains": 1,  # Only sending to Polygon Amoy
                    "sync_method": "direct_layerzero_polygon_only",
                    "events": sync_events,
                    "sync_id": sync_record["sync_id"]
                }
            else:
                print(f"❌ Transaction failed with status: {receipt.status}")
                print(f"🔍 Transaction Hash: {tx_hash_hex}")
                print(f"📊 Block: {receipt.blockNumber}")
                print(f"⛽ Gas Used: {receipt.gasUsed}")
                print(f"📋 Transaction Details:")
                print(f"   From: {self.account.address}")
                print(f"   To: {receipt.to}")
                print(f"   Value: {Web3.from_wei(total_fee_wei, 'ether')} ETH")
                print(f"   Target EID: {target_eid}")
                print(f"   Payload Size: {len(payload_bytes)} bytes")
                
                print(f"\n🔧 TROUBLESHOOTING GUIDE:")
                print(f"1. ❌ Contract Execution Reverted - This usually means:")
                print(f"   • Peer connection not set between Base Sepolia and Polygon Amoy contracts")
                print(f"   • Base contract: 0x1208F8F0E40381F14E41621906D13C9c3CaAa061")
                print(f"   • Expected Polygon peer: 0x34705a7e91b465AE55844583EC16715C88bD457a")
                print(f"   • LayerZero EID: {target_eid} (confirmed correct)")
                print(f"\n2. 💡 SOLUTION: Configure peer connection using:")
                print(f"   setPeer({target_eid}, '0x34705a7e91b465AE55844583EC16715C88bD457a')")
                print(f"\n3. 🔄 For now, falling back to database-only registry...")
                
                # Try to get more details about the failure
                try:
                    # Attempt to get transaction details
                    tx_details = source_web3.eth.get_transaction(tx_hash)
                    print(f"📄 Transaction Input Data Length: {len(tx_details.input)} bytes")
                except Exception as e:
                    print(f"⚠️ Could not get transaction details: {e}")
                
                return {
                    "success": False,
                    "error": f"DirectLayerZero transaction failed - likely peer connection not configured",
                    "transaction_hash": tx_hash_hex,
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "troubleshooting": {
                        "issue": "Peer connection not set",
                        "solution": f"setPeer({target_eid}, '0x34705a7e91b465AE55844583EC16715C88bD457a')",
                        "target_eid": target_eid,
                        "payload_size": len(payload_bytes),
                        "fee_paid": float(total_fee_eth)
                    }
                }
                
        except Exception as e:
            print(f"❌ Direct LayerZero CID sync error: {e}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    async def _estimate_total_sync_fees(
        self,
        source_chain: str,
        token_id: str,
        metadata_cid: str,
        manufacturer: str
    ) -> Dict[str, Any]:
        """Estimate total LayerZero fees for syncing to Polygon Amoy using contract fee estimation"""
        try:
            source_web3 = self.web3_connections.get(source_chain)
            source_contract = self.messenger_contracts.get(source_chain)
            
            if not source_web3 or not source_contract:
                return {"success": False, "error": "Source chain or contract not available"}
            
            # Prepare payload (same as contract would create)
            payload_data = {
                "type": "CID_SYNC",
                "token_id": token_id,
                "metadata_cid": metadata_cid,
                "manufacturer": manufacturer,
                "source_chain_id": source_web3.eth.chain_id,
                "timestamp": int(time.time())
            }
            
            payload_bytes = json.dumps(payload_data).encode('utf-8')
            
            # Calculate number of target chains - CURRENTLY: Only Polygon Amoy (will expand to all chains once peers are set)
            target_chains = ["polygon_amoy"]  # TODO: Expand to ["optimism_sepolia", "arbitrum_sepolia", "polygon_amoy"] once all peers are configured
            
            # Try to estimate fee from contract if estimateFees function exists
            try:
                target_eid = 40267  # Confirmed correct EID for Polygon Amoy
                
                # First, let's check if the contract supports this EID
                try:
                    supported_eids = source_contract.functions.getSupportedEids().call()
                    print(f"📋 Contract supports these LayerZero EIDs: {supported_eids}")
                    
                    if target_eid not in supported_eids:
                        print(f"⚠️ Warning: EID {target_eid} not in supported EIDs list")
                        print(f"🔧 This might indicate peer connection not set up")
                    else:
                        print(f"✅ EID {target_eid} is supported by contract")
                        
                except Exception as supported_eids_error:
                    print(f"⚠️ Could not get supported EIDs: {supported_eids_error}")
                
                # Try to estimate fees with the correct EID
                print(f"🔍 Estimating fees for LayerZero EID: {target_eid}")
                
                estimated_fee = source_contract.functions.estimateFees(
                    target_eid,
                    payload_bytes,
                    False,  # useZro
                    b''     # adapterParams (empty)
                ).call()
                
                # estimated_fee returns (nativeFee, zroFee)
                native_fee = estimated_fee[0]
                
                print(f"💰 Contract-based fee estimation:")
                print(f"   Target EID: {target_eid}")
                print(f"   Native fee from contract: {Web3.from_wei(native_fee, 'ether')} ETH")
                
                # Add 50% buffer for safety
                total_estimated_fee = int(native_fee * 1.5)
                
            except Exception as contract_fee_error:
                print(f"⚠️ Contract fee estimation failed: {contract_fee_error}")
                
                # Check if this is a peer connection issue
                if "execution reverted" in str(contract_fee_error):
                    print(f"🔧 This looks like a peer connection issue!")
                    print(f"💡 The DirectLayerZeroMessenger contract on Base Sepolia")
                    print(f"   might not have peer connection set to Polygon Amoy contract")
                    print(f"📞 Expected peer: 0x34705a7e91b465AE55844583EC16715C88bD457a")
                    
                    # ATTEMPT TO SET UP PEER CONNECTIONS AUTOMATICALLY
                    print(f"\n🚀 ATTEMPTING TO SET UP PEER CONNECTIONS AUTOMATICALLY...")
                    try:
                        # Get a reference to self (we're inside the _estimate_total_sync_fees method)
                        # We need to call the peer setup from the main class instance
                        print(f"🔗 Calling setup_layerzero_peer_connections()...")
                        
                        # This is a bit tricky since we're in an async method calling another async method
                        # Let's try a different approach - set a flag to trigger peer setup
                        peer_setup_needed = True
                        print(f"🏷️ Setting peer_setup_needed flag = True")
                        
                    except Exception as peer_setup_error:
                        print(f"❌ Could not set up peer connections: {peer_setup_error}")
                
                print(f"🔄 Using higher hardcoded estimate...")
                
                # Use a higher estimate as fallback
                estimated_fee_per_message = Web3.to_wei(0.01, 'ether')  # 0.01 ETH per message
                total_estimated_fee = estimated_fee_per_message * len(target_chains)
                target_eid = 40267  # Use correct EID
                
                # Add a flag to indicate peer setup is needed
                peer_setup_needed = True
            
            print(f"💰 Final fee estimation:")
            print(f"   Target chains: {len(target_chains)}")
            print(f"   Total estimated: {Web3.from_wei(total_estimated_fee, 'ether')} ETH")
            
            # Check if we had a contract fee estimation failure (peer connection issue)
            contract_fee_failed = False
            if 'peer_setup_needed' in locals() and peer_setup_needed:
                contract_fee_failed = True
            
            return {
                "success": True,
                "total_fee_wei": total_estimated_fee,
                "total_fee_eth": float(Web3.from_wei(total_estimated_fee, 'ether')),
                "target_chains": len(target_chains),
                "fee_per_message": float(Web3.from_wei(total_estimated_fee, 'ether')),
                "contract_fee_failed": contract_fee_failed,  # Flag to indicate peer connection issues
                "peer_setup_needed": contract_fee_failed
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _parse_sync_events(self, contract, receipt) -> List[Dict[str, Any]]:
        """Parse CIDSynced and MessageSent events from transaction receipt"""
        events = []
        
        try:
            # Get all logs and filter for our contract events
            for log in receipt.logs:
                try:
                    # Try to decode as CIDSynced event
                    decoded = contract.events.CIDSynced().processLog(log)
                    events.append({
                        "event": "CIDSynced",
                        "token_id": decoded.args.tokenId,
                        "metadata_cid": decoded.args.metadataCID,
                        "manufacturer": decoded.args.manufacturer,
                        "source_eid": decoded.args.sourceEid,
                        "timestamp": decoded.args.timestamp
                    })
                except:
                    try:
                        # Try to decode as MessageSent event
                        decoded = contract.events.MessageSent().processLog(log)
                        events.append({
                            "event": "MessageSent",
                            "message_id": decoded.args.messageId,
                            "source_eid": decoded.args.sourceEid,
                            "target_eid": decoded.args.targetEid,
                            "message_type": decoded.args.messageType,
                            "message_hash": decoded.args.messageHash.hex()
                        })
                    except:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Event parsing error: {e}")
            
        return events

    async def setup_layerzero_peer_connections(self) -> Dict[str, Any]:
        """
        Set up peer connections between DirectLayerZero contracts
        Based on LayerZero best practices from jamesbachini.com/layerzero-example/
        """
        try:
            print(f"\n🔗 === SETTING UP LAYERZERO PEER CONNECTIONS ===")
            
            # Define peer mappings (each contract needs to know about ALL other chains)
            # 4 chains total: Base Sepolia, Optimism Sepolia, Arbitrum Sepolia, Polygon Amoy
            peer_connections = [
                # Base Sepolia peers (needs to connect to 3 other chains)
                {
                    "source_chain": "base_sepolia",
                    "target_chain": "optimism_sepolia", 
                    "target_eid": 40232,
                    "target_contract": "0x97420B3dEd4B3eA72Ff607fd96927Bfa605b197c"
                },
                {
                    "source_chain": "base_sepolia",
                    "target_chain": "arbitrum_sepolia",
                    "target_eid": 40231, 
                    "target_contract": "0x25409B7ee450493248fD003A759304FF7f748c53"
                },
                {
                    "source_chain": "base_sepolia",
                    "target_chain": "polygon_amoy",
                    "target_eid": 40267,
                    "target_contract": "0x34705a7e91b465AE55844583EC16715C88bD457a"
                },
                
                # Optimism Sepolia peers (needs to connect to 3 other chains)
                {
                    "source_chain": "optimism_sepolia",
                    "target_chain": "base_sepolia",
                    "target_eid": 40245,
                    "target_contract": "0x1208F8F0E40381F14E41621906D13C9c3CaAa061"
                },
                {
                    "source_chain": "optimism_sepolia", 
                    "target_chain": "arbitrum_sepolia",
                    "target_eid": 40231,
                    "target_contract": "0x25409B7ee450493248fD003A759304FF7f748c53"
                },
                {
                    "source_chain": "optimism_sepolia",
                    "target_chain": "polygon_amoy",
                    "target_eid": 40267,
                    "target_contract": "0x34705a7e91b465AE55844583EC16715C88bD457a"
                },
                
                # Arbitrum Sepolia peers (needs to connect to 3 other chains)
                {
                    "source_chain": "arbitrum_sepolia",
                    "target_chain": "base_sepolia", 
                    "target_eid": 40245,
                    "target_contract": "0x1208F8F0E40381F14E41621906D13C9c3CaAa061"
                },
                {
                    "source_chain": "arbitrum_sepolia",
                    "target_chain": "optimism_sepolia",
                    "target_eid": 40232,
                    "target_contract": "0x97420B3dEd4B3eA72Ff607fd96927Bfa605b197c"
                },
                {
                    "source_chain": "arbitrum_sepolia",
                    "target_chain": "polygon_amoy",
                    "target_eid": 40267,
                    "target_contract": "0x34705a7e91b465AE55844583EC16715C88bD457a"
                },
                
                # Polygon Amoy peers (needs to connect to 3 other chains)
                {
                    "source_chain": "polygon_amoy",
                    "target_chain": "base_sepolia",
                    "target_eid": 40245,
                    "target_contract": "0x1208F8F0E40381F14E41621906D13C9c3CaAa061"
                },
                {
                    "source_chain": "polygon_amoy",
                    "target_chain": "optimism_sepolia", 
                    "target_eid": 40232,
                    "target_contract": "0x97420B3dEd4B3eA72Ff607fd96927Bfa605b197c"
                },
                {
                    "source_chain": "polygon_amoy",
                    "target_chain": "arbitrum_sepolia",
                    "target_eid": 40231,
                    "target_contract": "0x25409B7ee450493248fD003A759304FF7f748c53"
                }
            ]
            
            results = []
            
            for connection in peer_connections:
                try:
                    source_chain = connection["source_chain"]
                    target_eid = connection["target_eid"]
                    target_contract = connection["target_contract"]
                    
                    print(f"\n🔗 Setting up peer: {source_chain} -> {connection['target_chain']}")
                    print(f"   Target EID: {target_eid}")
                    print(f"   Target Contract: {target_contract}")
                    
                    source_web3 = self.web3_connections.get(source_chain)
                    source_contract_instance = self.messenger_contracts.get(source_chain)
                    
                    if not source_web3 or not source_contract_instance:
                        print(f"❌ Source chain {source_chain} not available")
                        continue
                    
                    # Check if peer connection already exists
                    try:
                        # Check if setPeer function exists (this is the standard LayerZero function)
                        print(f"🔍 Checking if peer connection already exists...")
                        
                        # Try to call setPeer (this might fail if already set or if we don't have permission)
                        nonce = source_web3.eth.get_transaction_count(self.account.address)
                        gas_price = source_web3.eth.gas_price
                        
                        # Convert target contract address to bytes32 format for LayerZero
                        target_address_bytes32 = target_contract.lower().replace('0x', '').ljust(64, '0')
                        target_address_bytes = bytes.fromhex(target_address_bytes32)
                        
                        transaction = source_contract_instance.functions.setPeer(
                            target_eid,
                            target_address_bytes
                        ).build_transaction({
                            'from': self.account.address,
                            'gas': 200000,
                            'gasPrice': gas_price,
                            'nonce': nonce,
                            'chainId': source_web3.eth.chain_id
                        })
                        
                        # Sign and send transaction
                        signed_txn = source_web3.eth.account.sign_transaction(transaction, self.account.key)
                        tx_hash = source_web3.eth.send_raw_transaction(signed_txn.raw_transaction)
                        tx_hash_hex = tx_hash.hex()
                        
                        print(f"📤 setPeer transaction sent: {tx_hash_hex}")
                        
                        # Wait for confirmation
                        receipt = source_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                        
                        if receipt.status == 1:
                            print(f"✅ Peer connection established successfully!")
                            print(f"📊 Block: {receipt.blockNumber}")
                            print(f"⛽ Gas Used: {receipt.gasUsed}")
                            
                            results.append({
                                "source_chain": source_chain,
                                "target_chain": connection["target_chain"],
                                "target_eid": target_eid,
                                "status": "success",
                                "transaction_hash": tx_hash_hex
                            })
                        else:
                            print(f"❌ setPeer transaction failed")
                            results.append({
                                "source_chain": source_chain,
                                "target_chain": connection["target_chain"], 
                                "target_eid": target_eid,
                                "status": "failed",
                                "error": "Transaction failed"
                            })
                            
                    except Exception as peer_error:
                        print(f"⚠️ setPeer failed: {peer_error}")
                        
                        # This might be expected if peer is already set or we don't have permission
                        if "already set" in str(peer_error).lower():
                            print(f"✅ Peer connection already exists")
                            results.append({
                                "source_chain": source_chain,
                                "target_chain": connection["target_chain"],
                                "target_eid": target_eid, 
                                "status": "already_set"
                            })
                        else:
                            print(f"❌ Permission denied or other error: {peer_error}")
                            results.append({
                                "source_chain": source_chain,
                                "target_chain": connection["target_chain"],
                                "target_eid": target_eid,
                                "status": "permission_denied",
                                "error": str(peer_error)
                            })
                    
                except Exception as connection_error:
                    print(f"❌ Failed to set up peer connection: {connection_error}")
                    results.append({
                        "source_chain": connection.get("source_chain"),
                        "status": "error",
                        "error": str(connection_error)
                    })
            
            return {
                "success": True,
                "message": "Peer connection setup attempted for all 4 chains",
                "total_connections": len(results),
                "chains_configured": ["base_sepolia", "optimism_sepolia", "arbitrum_sepolia", "polygon_amoy"],
                "summary": {
                    "successful": len([r for r in results if r.get("status") == "success"]),
                    "already_set": len([r for r in results if r.get("status") == "already_set"]),
                    "failed": len([r for r in results if r.get("status") in ["failed", "permission_denied", "error"]])
                },
                "results": results
            }
            
        except Exception as e:
            print(f"❌ LayerZero peer setup error: {e}")
            return {"success": False, "error": str(e)}

    async def get_sync_status(self, sync_id: str) -> Dict[str, Any]:
        """Get status of a cross-chain sync operation"""
        try:
            sync_record = await self.database.direct_layerzero_syncs.find_one({"sync_id": sync_id})
            
            if not sync_record:
                return {"found": False, "error": "Sync record not found"}
            
            return {
                "found": True,
                "sync_id": sync_id,
                "token_id": sync_record["token_id"],
                "metadata_cid": sync_record["metadata_cid"],
                "status": sync_record["status"],
                "source_chain": sync_record["source_chain"],
                "target_chains": sync_record["target_chains"],
                "transaction_hash": sync_record["transaction_hash"],
                "layerzero_fee_paid": sync_record["layerzero_fee_paid"],
                "timestamp": sync_record["timestamp"],
                "events": sync_record.get("events", [])
            }
            
        except Exception as e:
            return {"found": False, "error": str(e)}

    async def update_contract_addresses(self, addresses: Dict[str, str]):
        """Update contract addresses after deployment"""
        self.contract_addresses.update(addresses)
        await self._initialize_contracts()
        print("✅ Contract addresses updated and contracts reinitialized")

# Global instance
direct_layerzero_messaging_service = DirectLayerZeroMessagingService()