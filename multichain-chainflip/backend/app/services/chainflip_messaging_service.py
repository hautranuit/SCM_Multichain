"""
ChainFLIP Messaging Service
Simple LayerZero-based cross-chain CID sync using ChainFLIPMessenger contracts
Based on proven LayerZero NonblockingLzApp pattern
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

# LayerZero V2 endpoint IDs for testnets (uint32)
LAYERZERO_ENDPOINTS = {
    "base_sepolia": 40245,
    "polygon_amoy": 40267,     
    "optimism_sepolia": 40232,
    "arbitrum_sepolia": 40231
}

# Chain configurations
CHAIN_CONFIGS = {
    "base_sepolia": {
        "chain_id": 84532,
        "rpc_url": settings.base_sepolia_rpc,
        "layerzero_eid": 40245,
        "name": "Base Sepolia"
    },
    "polygon_amoy": {
        "chain_id": 80002,
        "rpc_url": settings.polygon_pos_rpc,
        "layerzero_eid": 40267,
        "name": "Polygon Amoy"
    },
    "optimism_sepolia": {
        "chain_id": 11155420,
        "rpc_url": "https://sepolia.optimism.io",
        "layerzero_eid": 40232,
        "name": "Optimism Sepolia"
    },
    "arbitrum_sepolia": {
        "chain_id": 421614,
        "rpc_url": "https://sepolia-rollup.arbitrum.io/rpc",
        "layerzero_eid": 40231,
        "name": "Arbitrum Sepolia"
    }
}

# ChainFLIPMessenger ABI - LayerZero V2 compatible
CHAINFLIP_MESSENGER_ABI = [
    {
        "inputs": [
            {"name": "_destEid", "type": "uint32"},
            {"name": "_tokenId", "type": "string"},
            {"name": "_metadataCID", "type": "string"},
            {"name": "_manufacturer", "type": "address"}
        ],
        "name": "sendCIDToChain",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "_tokenId", "type": "string"},
            {"name": "_metadataCID", "type": "string"},
            {"name": "_manufacturer", "type": "address"}
        ],
        "name": "syncCIDToAllChains",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "_destEid", "type": "uint32"},
            {"name": "_tokenId", "type": "string"},
            {"name": "_metadataCID", "type": "string"},
            {"name": "_manufacturer", "type": "address"},
            {"name": "_options", "type": "bytes"},
            {"name": "_payInLzToken", "type": "bool"}
        ],
        "name": "quote",
        "outputs": [
            {
                "components": [
                    {"name": "nativeFee", "type": "uint256"},
                    {"name": "lzTokenFee", "type": "uint256"}
                ],
                "name": "fee",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "_tokenId", "type": "string"}
        ],
        "name": "getCIDData",
        "outputs": [
            {
                "components": [
                    {"name": "tokenId", "type": "string"},
                    {"name": "metadataCID", "type": "string"},
                    {"name": "manufacturer", "type": "address"},
                    {"name": "timestamp", "type": "uint256"},
                    {"name": "sourceEid", "type": "uint32"}
                ],
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getAllCIDs",
        "outputs": [{"name": "", "type": "string[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getCIDCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "_tokenId", "type": "string"}
        ],
        "name": "hasCID",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getSupportedChains",
        "outputs": [{"name": "", "type": "uint32[]"}],
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
    {
        "inputs": [],
        "name": "endpoint",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenId", "type": "string"},
            {"indexed": False, "name": "metadataCID", "type": "string"},
            {"indexed": True, "name": "manufacturer", "type": "address"},
            {"indexed": True, "name": "destEid", "type": "uint32"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "CIDSynced",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenId", "type": "string"},
            {"indexed": False, "name": "metadataCID", "type": "string"},
            {"indexed": True, "name": "manufacturer", "type": "address"},
            {"indexed": True, "name": "sourceEid", "type": "uint32"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "CIDReceived",
        "type": "event"
    }
]

class ChainFLIPMessagingService:
    def __init__(self):
        self.web3_connections: Dict[str, Web3] = {}
        self.messenger_contracts: Dict[str, Any] = {}
        self.contract_addresses: Dict[str, str] = {}
        self.database = None
        
    async def initialize(self):
        """Initialize the ChainFLIP messaging service"""
        try:
            print("🌐 Initializing ChainFLIP Messaging Service...")
            
            # Initialize database connection
            self.database = await get_database()
            
            # Initialize Web3 connections for all chains
            await self._initialize_web3_connections()
            
            # Load contract addresses (to be updated after deployment)
            await self._load_contract_addresses()
            
            # Initialize contract instances
            await self._initialize_contracts()
            
            print("✅ ChainFLIP Messaging Service initialized successfully")
            
        except Exception as e:
            print(f"❌ ChainFLIP Messaging Service initialization failed: {e}")
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
        """Load ChainFLIPMessenger contract addresses - UPDATED WITH DEPLOYED ADDRESSES"""
        self.contract_addresses = {
            "base_sepolia": "0xDbc80005e688df0b2E1486D6619A7Cdf3b10C714",    # ✅ DEPLOYED
            "polygon_amoy": "0x225FD1670d94304b737A05412fbCE7a39224D1B1",    # ✅ DEPLOYED
            "optimism_sepolia": "0x69b862c5091fE37e6f1dD47CDC40c69916586e61",  # ✅ DEPLOYED
            "arbitrum_sepolia": "0xf42BB61B03697608104F12D8C009ad387b4750cB"   # ✅ DEPLOYED
        }
        
        print("📄 ChainFLIPMessenger contract addresses (✅ DEPLOYED):")
        for chain, address in self.contract_addresses.items():
            print(f"   {CHAIN_CONFIGS[chain]['name']}: {address}")

    async def _initialize_contracts(self):
        """Initialize contract instances"""
        for chain_name, web3 in self.web3_connections.items():
            contract_address = self.contract_addresses.get(chain_name)
            if contract_address and contract_address != "0x0000000000000000000000000000000000000000":
                try:
                    contract = web3.eth.contract(
                        address=contract_address,
                        abi=CHAINFLIP_MESSENGER_ABI
                    )
                    self.messenger_contracts[chain_name] = contract
                    print(f"✅ Contract instance created for {CHAIN_CONFIGS[chain_name]['name']}")
                except Exception as e:
                    print(f"❌ Failed to create contract instance for {chain_name}: {e}")
            else:
                print(f"⚠️ Contract address not set for {chain_name}")

    async def send_cid_sync_to_all_chains(
        self,
        source_chain: str,
        token_id: str,
        metadata_cid: str,
        manufacturer: str,
        product_data: Dict[str, Any],
        manufacturer_private_key: str = None
    ) -> Dict[str, Any]:
        """
        Send CID sync message using ChainFLIPMessenger contract
        Uses the simple LayerZero NonblockingLzApp pattern
        """
        try:
            print(f"\n🌐 === CHAINFLIP MESSENGER CID SYNC ===")
            print(f"🏭 Source: {source_chain}")
            print(f"🔖 Token ID: {token_id}")
            print(f"📦 CID: {metadata_cid}")
            print(f"👤 Manufacturer: {manufacturer}")
            
            # Determine which account to use for sending
            if manufacturer_private_key:
                sending_account = Account.from_key(manufacturer_private_key)
                print(f"🔐 Using manufacturer account: {sending_account.address}")
                
                # Verify the manufacturer address matches
                if sending_account.address.lower() != manufacturer.lower():
                    return {
                        "success": False,
                        "error": f"Manufacturer private key address {sending_account.address} doesn't match manufacturer {manufacturer}"
                    }
            else:
                return {
                    "success": False,
                    "error": "Manufacturer private key is required for cross-chain messaging"
                }
            
            # Get source chain Web3 and contract
            source_web3 = self.web3_connections.get(source_chain)
            source_contract = self.messenger_contracts.get(source_chain)
            
            if not source_web3:
                return {"success": False, "error": f"Source chain {source_chain} not connected"}
            
            if not source_contract:
                return {"success": False, "error": f"ChainFLIPMessenger contract not available for {source_chain}"}
            
            # Check contract owner (for debugging)
            try:
                contract_owner = source_contract.functions.owner().call()
                print(f"📋 Contract owner: {contract_owner}")
            except Exception as owner_error:
                print(f"⚠️ Could not check contract owner: {owner_error}")
            
            # Use LayerZero fee similar to the working example (12345678 gwei)
            native_fee = Web3.to_wei(12345678, 'gwei')  # ≈ 0.012 ETH
            
            # Check account balance
            account_balance = source_web3.eth.get_balance(sending_account.address)
            account_balance_eth = Web3.from_wei(account_balance, 'ether')
            fee_eth = Web3.from_wei(native_fee, 'ether')
            
            print(f"💳 Account balance: {account_balance_eth} ETH")
            print(f"💰 LayerZero fee: {fee_eth} ETH")
            
            if account_balance < native_fee:
                return {
                    "success": False,
                    "error": f"Insufficient balance for LayerZero fees. Need: {fee_eth} ETH, Have: {account_balance_eth} ETH"
                }
            
            # Build transaction
            nonce = source_web3.eth.get_transaction_count(sending_account.address)
            gas_price = source_web3.eth.gas_price
            
            transaction = source_contract.functions.syncCIDToAllChains(
                token_id,
                metadata_cid,
                manufacturer
            ).build_transaction({
                'from': sending_account.address,
                'value': native_fee,  # LayerZero fees
                'gas': 500000,       # Higher gas for cross-chain messaging
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': source_web3.eth.chain_id
            })
            
            print(f"📋 Transaction details:")
            print(f"   From: {sending_account.address}")
            print(f"   Value (LayerZero fee): {fee_eth} ETH")
            print(f"   Gas limit: {transaction['gas']}")
            print(f"   Gas price: {Web3.from_wei(gas_price, 'gwei')} Gwei")
            
            # Sign and send transaction
            signed_txn = source_web3.eth.account.sign_transaction(transaction, sending_account.key)
            tx_hash = source_web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"📤 Transaction sent: {tx_hash_hex}")
            print(f"⏳ Waiting for confirmation...")
            
            # Wait for transaction confirmation
            receipt = source_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print(f"✅ ChainFLIP CID sync transaction confirmed!")
                print(f"📊 Block: {receipt.blockNumber}")
                print(f"⛽ Gas Used: {receipt.gasUsed}")
                
                # Parse events
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
                    "layerzero_fee_paid": float(fee_eth),
                    "sync_method": "chainflip_messenger",
                    "events": sync_events,
                    "timestamp": time.time(),
                    "status": "sent"
                }
                
                # Save to database
                await self.database.chainflip_syncs.insert_one(sync_record)
                
                return {
                    "success": True,
                    "transaction_hash": tx_hash_hex,
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "layerzero_fee_paid": float(fee_eth),
                    "sync_method": "chainflip_messenger",
                    "events": sync_events,
                    "sync_id": sync_record["sync_id"],
                    "message": "CID synced to all chains via ChainFLIP Messenger"
                }
            else:
                print(f"❌ Transaction failed with status: {receipt.status}")
                
                return {
                    "success": False,
                    "error": f"ChainFLIP transaction failed with status {receipt.status}",
                    "transaction_hash": tx_hash_hex,
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed
                }
                
        except Exception as e:
            print(f"❌ ChainFLIP CID sync error: {e}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    async def _parse_sync_events(self, contract, receipt) -> List[Dict[str, Any]]:
        """Parse CIDSynced events from transaction receipt"""
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
                        "dest_chain": decoded.args.destChain,
                        "timestamp": decoded.args.timestamp
                    })
                except:
                    continue
                        
        except Exception as e:
            print(f"⚠️ Event parsing error: {e}")
            
        return events

    async def get_received_cids(self, chain_name: str) -> Dict[str, Any]:
        """Get all CIDs received on a specific chain"""
        try:
            contract = self.messenger_contracts.get(chain_name)
            if not contract:
                return {"success": False, "error": f"Contract not available for {chain_name}"}
            
            # Get all CIDs
            all_cids = contract.functions.getAllCIDs().call()
            cid_count = contract.functions.getCIDCount().call()
            
            # Get detailed data for each CID
            cid_data = []
            for cid in all_cids:
                try:
                    data = contract.functions.getCIDData(cid).call()
                    cid_data.append({
                        "token_id": data[0],
                        "metadata_cid": data[1],
                        "manufacturer": data[2],
                        "timestamp": data[3],
                        "source_chain": data[4]
                    })
                except Exception as e:
                    print(f"⚠️ Error getting CID data for {cid}: {e}")
            
            return {
                "success": True,
                "chain": chain_name,
                "cid_count": cid_count,
                "cids": cid_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def update_contract_addresses(self, addresses: Dict[str, str]):
        """Update contract addresses after deployment"""
        self.contract_addresses.update(addresses)
        await self._initialize_contracts()
        print("✅ Contract addresses updated and contracts reinitialized")

# Global instance
chainflip_messaging_service = ChainFLIPMessagingService()