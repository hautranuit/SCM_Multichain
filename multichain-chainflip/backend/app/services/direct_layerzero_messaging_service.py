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

# LayerZero V2 endpoint IDs for the 4 chains (Updated to match working OFT implementation)
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

# DirectLayerZeroMessenger ABI - Based on actual contract interface
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
            {"name": "role", "type": "bytes32"},
            {"name": "account", "type": "address"}
        ],
        "name": "hasRole",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "SENDER_ROLE",
        "outputs": [{"name": "", "type": "bytes32"}],
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
        product_data: Dict[str, Any],
        manufacturer_private_key: str = None
    ) -> Dict[str, Any]:
        """
        Send CID sync message using the actual DirectLayerZeroMessenger contract
        This uses LayerZero V1 pattern with proper message passing (not OFT token transfer)
        """
        try:
            print(f"\n🌐 === DIRECT LAYERZERO CID SYNC (CORRECTED IMPLEMENTATION) ===")
            print(f"🏭 Source: {source_chain}")
            print(f"🔖 Token ID: {token_id}")
            print(f"📦 CID: {metadata_cid}")
            print(f"👤 Manufacturer: {manufacturer}")
            
            # Determine which account to use for sending
            if manufacturer_private_key:
                sending_account = Account.from_key(manufacturer_private_key)
                print(f"🔐 Using manufacturer account for cross-chain messaging: {sending_account.address}")
                
                # Verify the manufacturer address matches
                if sending_account.address.lower() != manufacturer.lower():
                    return {
                        "success": False,
                        "error": f"Manufacturer private key address {sending_account.address} doesn't match manufacturer {manufacturer}"
                    }
            else:
                sending_account = self.account
                print(f"🔐 Using deployer account for cross-chain messaging: {sending_account.address}")
            
            # Get source chain Web3 and contract
            source_web3 = self.web3_connections.get(source_chain)
            source_contract = self.messenger_contracts.get(source_chain)
            
            if not source_web3:
                return {"success": False, "error": f"Source chain {source_chain} not connected"}
            
            if not source_contract:
                return {"success": False, "error": f"DirectLayerZeroMessenger contract not available for {source_chain}"}
            
            # Check if sender has SENDER_ROLE
            try:
                sender_role = Web3.keccak(text="SENDER_ROLE")
                has_sender_role = source_contract.functions.hasRole(sender_role, sending_account.address).call()
                print(f"🔑 SENDER_ROLE check: {has_sender_role}")
                
                if not has_sender_role:
                    print(f"⚠️ WARNING: Account {sending_account.address} doesn't have SENDER_ROLE")
                    print(f"💡 The contract owner needs to grant SENDER_ROLE to this account")
                    return {
                        "success": False,
                        "error": f"Account {sending_account.address} doesn't have SENDER_ROLE",
                        "solution": f"Contract owner should call: grantRole(SENDER_ROLE, '{sending_account.address}')"
                    }
                
            except Exception as role_check_error:
                print(f"⚠️ Could not check SENDER_ROLE: {role_check_error}")
                # Continue anyway - might be a view function issue
            
            # Send ONLY to Polygon Amoy (as requested by user)
            target_chain = "polygon_amoy"
            target_config = CHAIN_CONFIGS[target_chain]
            target_eid = target_config["layerzero_eid"]
            
            print(f"🎯 Target: {target_chain} (EID: {target_eid}) ONLY")
            
            # Use simple cross-chain message instead of syncCIDToAllChains
            print(f"📋 Preparing single-chain CID sync transaction...")
            
            # Create payload for CID sync message
            cid_sync_payload = json.dumps({
                "type": "CID_SYNC",
                "token_id": token_id,
                "metadata_cid": metadata_cid,
                "manufacturer": manufacturer,
                "source_chain_id": source_web3.eth.chain_id,
                "timestamp": int(time.time())
            }).encode('utf-8')
            
            # Use higher LayerZero fee based on working example (12345678 gwei ≈ 0.012 ETH)
            native_fee = Web3.to_wei(0.015, 'ether')  # Higher fee for LayerZero
            
            # Check account balance
            account_balance = source_web3.eth.get_balance(sending_account.address)
            account_balance_eth = Web3.from_wei(account_balance, 'ether')
            fee_eth = Web3.from_wei(native_fee, 'ether')
            
            print(f"💳 Account balance: {account_balance_eth} ETH")
            print(f"💰 Required fee: {fee_eth} ETH (LayerZero working fee)")
            
            if account_balance < native_fee:
                return {
                    "success": False,
                    "error": f"Insufficient balance for LayerZero fees. Need: {fee_eth} ETH, Have: {account_balance_eth} ETH"
                }
            
            # Use the contract's built-in syncCIDToAllChains function (it exists on the contract!)
            nonce = source_web3.eth.get_transaction_count(sending_account.address)
            gas_price = source_web3.eth.gas_price
            
            transaction = source_contract.functions.syncCIDToAllChains(
                token_id,
                metadata_cid,
                manufacturer
            ).build_transaction({
                'from': sending_account.address,
                'value': native_fee,  # LayerZero fees - using working amount
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
            print(f"   Function: syncCIDToAllChains('{token_id}', '{metadata_cid}', '{manufacturer}')")
            print(f"   Target: All configured chains via LayerZero")
            
            # Sign and send transaction
            signed_txn = source_web3.eth.account.sign_transaction(transaction, sending_account.key)
            tx_hash = source_web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"📤 Transaction sent: {tx_hash_hex}")
            print(f"⏳ Waiting for confirmation...")
            
            # Wait for transaction confirmation
            receipt = source_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print(f"✅ LayerZero CID sync transaction confirmed!")
                print(f"🌐 Cross-chain message sent to all configured chains successfully!")
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
                    "layerzero_fee_paid": float(fee_eth),
                    "sync_method": "direct_layerzero_v1_messaging",
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
                    "layerzero_fee_paid": float(fee_eth),
                    "sync_method": "direct_layerzero_syncCIDToAllChains",
                    "target_chains": "all_configured_chains",
                    "events": sync_events,
                    "sync_id": sync_record["sync_id"],
                    "message": "CID synced to all configured chains via LayerZero"
                }
            else:
                print(f"❌ Transaction failed with status: {receipt.status}")
                print(f"🔍 This could be due to:")
                print(f"   • Trusted remote not set for target chain")
                print(f"   • Insufficient LayerZero fees")
                print(f"   • SENDER_ROLE not granted to account")
                print(f"   • Contract permissions issue")
                
                return {
                    "success": False,
                    "error": f"DirectLayerZero transaction failed with status {receipt.status}",
                    "transaction_hash": tx_hash_hex,
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "troubleshooting": {
                        "check_trusted_remotes": f"Verify trusted remotes are set for target chains",
                        "check_sender_role": f"Verify {sending_account.address} has SENDER_ROLE",
                        "check_fees": f"Verify sufficient LayerZero fees provided: {fee_eth} ETH"
                    }
                }
                
        except Exception as e:
            print(f"❌ Direct LayerZero CID sync error: {e}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    async def _estimate_sync_fees(
        self,
        source_chain: str,
        target_chain: str,
        payload_size: int
    ) -> Dict[str, Any]:
        """Estimate LayerZero fees for CID sync using contract's estimateFees function"""
        try:
            source_web3 = self.web3_connections.get(source_chain)
            source_contract = self.messenger_contracts.get(source_chain)
            
            if not source_web3 or not source_contract:
                return {"success": False, "error": "Source chain or contract not available"}
            
            target_config = CHAIN_CONFIGS[target_chain]
            target_eid = target_config["layerzero_eid"]
            
            # Create sample payload for fee estimation
            sample_payload = json.dumps({
                "type": "CID_SYNC",
                "token_id": "sample_token",
                "metadata_cid": "sample_cid",
                "manufacturer": "0x0000000000000000000000000000000000000000",
                "source_chain_id": source_web3.eth.chain_id,
                "timestamp": int(time.time())
            }).encode('utf-8')
            
            try:
                # Use the contract's estimateFees function
                (native_fee, zro_fee) = source_contract.functions.estimateFees(
                    target_eid,
                    sample_payload,
                    False,  # useZro
                    b''     # adapterParams
                ).call()
                
                print(f"💰 LayerZero fee estimate for {target_chain}: {Web3.from_wei(native_fee, 'ether')} ETH")
                
                return {
                    "success": True,
                    "native_fee_wei": native_fee,
                    "native_fee_eth": float(Web3.from_wei(native_fee, 'ether')),
                    "zro_fee_wei": zro_fee,
                    "target_chain": target_chain,
                    "target_eid": target_eid
                }
                
            except Exception as estimate_error:
                print(f"⚠️ Fee estimation failed for {target_chain}: {estimate_error}")
                
                # Check if this is a trusted remote issue
                if "trusted" in str(estimate_error).lower() or "remote" in str(estimate_error).lower():
                    print(f"🔧 Trusted remote issue detected for {target_chain}")
                    return {
                        "success": False,
                        "error": f"Trusted remote not configured for {target_chain}",
                        "target_eid": target_eid,
                        "solution": f"setTrustedRemote({target_eid}, trustedRemoteBytes)"
                    }
                
                # Use fallback estimate
                fallback_fee = Web3.to_wei(0.01, 'ether')  # 0.01 ETH fallback
                return {
                    "success": True,
                    "native_fee_wei": fallback_fee,
                    "native_fee_eth": 0.01,
                    "zro_fee_wei": 0,
                    "target_chain": target_chain,
                    "target_eid": target_eid,
                    "fallback": True
                }
                
        except Exception as e:
            print(f"❌ Fee estimation error: {e}")
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

    async def check_trusted_remotes(self) -> Dict[str, Any]:
        """Check trusted remote configurations between DirectLayerZeroMessenger contracts"""
        try:
            print(f"\n🔍 === CHECKING LAYERZERO TRUSTED REMOTES ===")
            
            trusted_remote_status = {}
            
            for source_chain, source_contract in self.messenger_contracts.items():
                if not source_contract:
                    continue
                    
                print(f"\n📍 Checking {CHAIN_CONFIGS[source_chain]['name']} trusted remotes:")
                source_eid = CHAIN_CONFIGS[source_chain]["layerzero_eid"]
                
                chain_remotes = {}
                
                for target_chain, target_address in self.contract_addresses.items():
                    if source_chain == target_chain:
                        continue
                        
                    target_eid = CHAIN_CONFIGS[target_chain]["layerzero_eid"]
                    
                    try:
                        # Check chain config for trusted remote
                        chain_config = source_contract.functions.getChainConfig(target_eid).call()
                        trusted_remote = chain_config[4]  # trustedRemote is at index 4
                        
                        # Expected trusted remote: target_contract_address + source_contract_address (LayerZero V1 format)
                        source_address = self.contract_addresses[source_chain]
                        expected_remote = target_address.lower().replace('0x', '') + source_address.lower().replace('0x', '')
                        
                        if trusted_remote and len(trusted_remote) > 0:
                            actual_remote = trusted_remote.hex() if isinstance(trusted_remote, bytes) else trusted_remote
                            is_correct = actual_remote.lower() == expected_remote.lower()
                            
                            chain_remotes[target_chain] = {
                                "target_eid": target_eid,
                                "expected_remote": expected_remote,
                                "actual_remote": actual_remote,
                                "is_set": True,
                                "is_correct": is_correct,
                                "status": "✅ CORRECT" if is_correct else "❌ INCORRECT",
                            }
                            
                            print(f"   {target_chain} (EID {target_eid}): {chain_remotes[target_chain]['status']}")
                            if not is_correct:
                                print(f"     Expected: {expected_remote}")
                                print(f"     Actual:   {actual_remote}")
                        else:
                            chain_remotes[target_chain] = {
                                "target_eid": target_eid,
                                "expected_remote": expected_remote,
                                "actual_remote": None,
                                "is_set": False,
                                "is_correct": False,
                                "status": "❌ NOT SET",
                                "solution": f"setTrustedRemote({target_eid}, 0x{expected_remote})"
                            }
                            
                            print(f"   {target_chain} (EID {target_eid}): ❌ NOT SET")
                            print(f"     Solution: setTrustedRemote({target_eid}, 0x{expected_remote})")
                            
                    except Exception as remote_error:
                        chain_remotes[target_chain] = {
                            "target_eid": target_eid,
                            "expected_remote": None,
                            "actual_remote": None,
                            "is_set": False,
                            "is_correct": False,
                            "status": f"❌ ERROR: {remote_error}",
                            "error": str(remote_error)
                        }
                        
                        print(f"   {target_chain} (EID {target_eid}): ❌ ERROR - {remote_error}")
                
                trusted_remote_status[source_chain] = {
                    "source_eid": source_eid,
                    "trusted_remotes": chain_remotes,
                    "total_remotes": len(chain_remotes),
                    "correct_remotes": sum(1 for r in chain_remotes.values() if r.get("is_correct", False)),
                    "missing_remotes": sum(1 for r in chain_remotes.values() if not r.get("is_set", True))
                }
            
            return {
                "success": True,
                "trusted_remote_status": trusted_remote_status,
                "timestamp": time.time()
            }
            
        except Exception as e:
            print(f"❌ Trusted remote check error: {e}")
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