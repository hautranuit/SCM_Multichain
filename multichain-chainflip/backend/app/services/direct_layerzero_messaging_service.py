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
        # For now, use placeholder addresses - these will be updated after deployment
        self.contract_addresses = {
            "base_sepolia": "0x0000000000000000000000000000000000000001",
            "op_sepolia": "0x0000000000000000000000000000000000000002", 
            "arbitrum_sepolia": "0x0000000000000000000000000000000000000003",
            "polygon_amoy": "0x0000000000000000000000000000000000000004"
        }
        
        print("📄 Loaded DirectLayerZeroMessenger contract addresses:")
        for chain, address in self.contract_addresses.items():
            print(f"   {CHAIN_CONFIGS[chain]['name']}: {address}")

    async def _initialize_contracts(self):
        """Initialize contract instances"""
        for chain_name, web3 in self.web3_connections.items():
            contract_address = self.contract_addresses.get(chain_name)
            if contract_address and contract_address != "0x0000000000000000000000000000000000000001":
                try:
                    contract = web3.eth.contract(
                        address=contract_address,
                        abi=DIRECT_MESSENGER_ABI
                    )
                    self.messenger_contracts[chain_name] = contract
                    print(f"✅ Contract instance created for {CHAIN_CONFIGS[chain_name]['name']}")
                except Exception as e:
                    print(f"❌ Failed to create contract instance for {chain_name}: {e}")

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
                return {
                    "success": False, 
                    "error": f"Fee estimation failed: {total_fee_estimate['error']}"
                }
            
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
            
            # Execute syncCIDToAllChains transaction
            print(f"🚀 Executing syncCIDToAllChains transaction...")
            
            nonce = source_web3.eth.get_transaction_count(self.account.address)
            gas_price = source_web3.eth.gas_price
            
            # Build transaction
            transaction = source_contract.functions.syncCIDToAllChains(
                token_id,
                metadata_cid,
                manufacturer
            ).build_transaction({
                'from': self.account.address,
                'value': total_fee_wei,  # LayerZero fees
                'gas': 2000000,  # High gas limit for complex operation
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
                    "sync_method": "direct_layerzero_all_chains",
                    "target_chains": [chain for chain in CHAIN_CONFIGS.keys() if chain != source_chain],
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
                    "target_chains": len([chain for chain in CHAIN_CONFIGS.keys() if chain != source_chain]),
                    "sync_method": "direct_layerzero_messenger",
                    "events": sync_events,
                    "sync_id": sync_record["sync_id"]
                }
            else:
                print(f"❌ Transaction failed with status: {receipt.status}")
                return {
                    "success": False,
                    "error": f"Transaction failed with status: {receipt.status}",
                    "transaction_hash": tx_hash_hex
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
        """Estimate total LayerZero fees for syncing to all other chains"""
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
            
            # Calculate number of target chains
            target_chains = [chain for chain in CHAIN_CONFIGS.keys() if chain != source_chain]
            
            # Estimate fee per message (use a reasonable estimate)
            estimated_fee_per_message = Web3.to_wei(0.0001, 'ether')  # 0.0001 ETH per message
            total_estimated_fee = estimated_fee_per_message * len(target_chains)
            
            print(f"💰 Fee estimation:")
            print(f"   Target chains: {len(target_chains)}")
            print(f"   Fee per message: {Web3.from_wei(estimated_fee_per_message, 'ether')} ETH")
            print(f"   Total estimated: {Web3.from_wei(total_estimated_fee, 'ether')} ETH")
            
            return {
                "success": True,
                "total_fee_wei": total_estimated_fee,
                "total_fee_eth": float(Web3.from_wei(total_estimated_fee, 'ether')),
                "target_chains": len(target_chains),
                "fee_per_message": float(Web3.from_wei(estimated_fee_per_message, 'ether'))
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