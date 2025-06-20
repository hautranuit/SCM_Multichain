"""
ChainFLIP Cross-Chain NFT Bridge Service
Implements cross-chain NFT transfers using LayerZero V2 messaging
Supports: Base Sepolia, OP Sepolia, Arbitrum Sepolia, Polygon Amoy
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from app.core.config import get_settings
from app.core.database import get_database
from app.services.blockchain_service import BlockchainService, get_private_key_for_address
import os

settings = get_settings()

# Network configurations for cross-chain NFT transfers
NETWORK_CONFIG = {
    "base_sepolia": {
        "name": "Base Sepolia",
        "chain_id": 84532,
        "rpc_url": settings.base_sepolia_rpc,
        "nft_contract": None,  # Will be updated after deployment
        "messenger_contract": settings.direct_messenger_base_sepolia,
        "layer_zero_eid": 40245  # Base Sepolia Endpoint ID
    },
    "optimism_sepolia": {
        "name": "OP Sepolia", 
        "chain_id": 11155420,
        "rpc_url": settings.optimism_sepolia_rpc,
        "nft_contract": None,  # Will be updated after deployment
        "messenger_contract": settings.direct_messenger_op_sepolia,
        "layer_zero_eid": 40232  # OP Sepolia Endpoint ID
    },
    "arbitrum_sepolia": {
        "name": "Arbitrum Sepolia",
        "chain_id": 421614,
        "rpc_url": settings.arbitrum_sepolia_rpc, 
        "nft_contract": None,  # Will be updated after deployment
        "messenger_contract": settings.direct_messenger_arbitrum_sepolia,
        "layer_zero_eid": 40231  # Arbitrum Sepolia Endpoint ID
    },
    "polygon_amoy": {
        "name": "Polygon Amoy",
        "chain_id": 80002,
        "rpc_url": settings.polygon_pos_rpc,
        "nft_contract": None,  # Will be updated after deployment  
        "messenger_contract": settings.direct_messenger_polygon_amoy,
        "layer_zero_eid": 40267  # Polygon Amoy Endpoint ID
    }
}

class NFTBridgeService:
    def __init__(self):
        self.database = None
        self.blockchain_service: Optional[BlockchainService] = None
        self.web3_connections: Dict[str, Web3] = {}
        self.nft_contracts: Dict[str, Any] = {}
        
        # Enhanced NFT ABI with cross-chain functions
        self.cross_chain_nft_abi = [
            {
                "inputs": [
                    {"name": "to", "type": "address"},
                    {"name": "tokenId", "type": "uint256"},
                    {"name": "uri", "type": "string"}
                ],
                "name": "safeMint",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "tokenId", "type": "uint256"}
                ],
                "name": "burnForBridge",
                "outputs": [{"name": "tokenURIData", "type": "string"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "tokenId", "type": "uint256"}
                ],
                "name": "ownerOf",
                "outputs": [{"name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "tokenId", "type": "uint256"}
                ],
                "name": "tokenURI",
                "outputs": [{"name": "", "type": "string"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "tokenId", "type": "uint256"}
                ],
                "name": "exists",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "tokenId", "type": "uint256"},
                    {"indexed": False, "name": "tokenURI", "type": "string"},
                    {"indexed": True, "name": "timestamp", "type": "uint256"}
                ],
                "name": "TokenBurned",
                "type": "event"
            }
        ]
        
        # LayerZero Messenger ABI (simplified for NFT bridge)
        self.messenger_abi = [
            {
                "inputs": [
                    {"name": "_dstEid", "type": "uint32"},
                    {"name": "_to", "type": "bytes"},
                    {"name": "_message", "type": "bytes"},
                    {"name": "_options", "type": "bytes"},
                    {"name": "_fee", "type": "tuple", "components": [
                        {"name": "nativeFee", "type": "uint256"},
                        {"name": "lzTokenFee", "type": "uint256"}
                    ]}
                ],
                "name": "send",
                "outputs": [
                    {"name": "msgReceipt", "type": "tuple", "components": [
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
                    {"name": "_to", "type": "bytes"},
                    {"name": "_message", "type": "bytes"},
                    {"name": "_options", "type": "bytes"},
                    {"name": "_payInLzToken", "type": "bool"}
                ],
                "name": "quote",
                "outputs": [
                    {"name": "fee", "type": "tuple", "components": [
                        {"name": "nativeFee", "type": "uint256"},
                        {"name": "lzTokenFee", "type": "uint256"}
                    ]}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
    async def initialize(self):
        """Initialize NFT Bridge Service"""
        print("🌉 Initializing ChainFLIP Cross-Chain NFT Bridge Service...")
        
        # Initialize database connection
        self.database = await get_database()
        
        # Initialize blockchain service
        self.blockchain_service = BlockchainService()
        await self.blockchain_service.initialize()
        
        # Initialize Web3 connections for all networks
        await self.initialize_network_connections()
        
        # Load NFT contract addresses from environment
        await self.load_nft_contract_addresses()
        
        print("✅ NFT Bridge Service initialized successfully")
        
    async def initialize_network_connections(self):
        """Initialize Web3 connections for all supported networks"""
        print("🔗 Initializing network connections...")
        
        for network_key, config in NETWORK_CONFIG.items():
            try:
                web3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
                web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                
                if web3.is_connected():
                    latest_block = web3.eth.block_number
                    self.web3_connections[network_key] = web3
                    print(f"✅ Connected to {config['name']} (Chain ID: {config['chain_id']}, Block: {latest_block})")
                else:
                    print(f"❌ Failed to connect to {config['name']}")
                    
            except Exception as e:
                print(f"❌ Connection error for {config['name']}: {e}")
                
    async def load_nft_contract_addresses(self):
        """Load NFT contract addresses from environment variables"""
        print("📋 Loading NFT contract addresses...")
        
        # Update network config with contract addresses from environment
        NETWORK_CONFIG["base_sepolia"]["nft_contract"] = os.environ.get("NFT_CONTRACT_BASE_SEPOLIA")
        NETWORK_CONFIG["optimism_sepolia"]["nft_contract"] = os.environ.get("NFT_CONTRACT_OP_SEPOLIA") 
        NETWORK_CONFIG["arbitrum_sepolia"]["nft_contract"] = os.environ.get("NFT_CONTRACT_ARBITRUM_SEPOLIA")
        NETWORK_CONFIG["polygon_amoy"]["nft_contract"] = os.environ.get("NFT_CONTRACT_POLYGON_AMOY")
        
        # Initialize contract instances
        for network_key, config in NETWORK_CONFIG.items():
            if config["nft_contract"] and network_key in self.web3_connections:
                try:
                    web3 = self.web3_connections[network_key]
                    contract = web3.eth.contract(
                        address=config["nft_contract"],
                        abi=self.cross_chain_nft_abi
                    )
                    self.nft_contracts[network_key] = contract
                    print(f"✅ Loaded NFT contract for {config['name']}: {config['nft_contract']}")
                except Exception as e:
                    print(f"⚠️ Failed to load NFT contract for {config['name']}: {e}")
            else:
                print(f"⚠️ No NFT contract address configured for {config['name']}")
                
    async def transfer_nft_cross_chain(
        self,
        token_id: int,
        from_chain: str,
        to_chain: str, 
        from_address: str,
        to_address: str,
        caller_private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main function: Transfer NFT from one chain to another
        
        Flow:
        1. Verify NFT ownership on source chain
        2. Get tokenURI from source chain 
        3. Burn NFT on source chain (using burnForBridge)
        4. Send cross-chain message via LayerZero
        5. Mint NFT on destination chain with same tokenURI
        
        Args:
            token_id: The NFT token ID to transfer
            from_chain: Source chain ("base_sepolia", "optimism_sepolia", etc.)
            to_chain: Destination chain 
            from_address: Current owner address on source chain
            to_address: Recipient address on destination chain
            caller_private_key: Private key for signing transactions (optional)
            
        Returns:
            Dictionary with transfer status and transaction details
        """
        try:
            print(f"🌉 Starting cross-chain NFT transfer:")
            print(f"   Token ID: {token_id}")
            print(f"   From: {from_chain} ({from_address})")
            print(f"   To: {to_chain} ({to_address})")
            
            # Validate input parameters
            if from_chain not in NETWORK_CONFIG:
                raise ValueError(f"Unsupported source chain: {from_chain}")
            if to_chain not in NETWORK_CONFIG:
                raise ValueError(f"Unsupported destination chain: {to_chain}")
            if from_chain == to_chain:
                raise ValueError("Source and destination chains cannot be the same")
                
            # Get network configurations
            from_config = NETWORK_CONFIG[from_chain]
            to_config = NETWORK_CONFIG[to_chain]
            
            # Get Web3 connections
            from_web3 = self.web3_connections.get(from_chain)
            to_web3 = self.web3_connections.get(to_chain)
            
            if not from_web3 or not to_web3:
                raise Exception("Missing Web3 connections for source or destination chain")
                
            # Get NFT contracts
            from_nft_contract = self.nft_contracts.get(from_chain)
            to_nft_contract = self.nft_contracts.get(to_chain)
            
            if not from_nft_contract or not to_nft_contract:
                raise Exception("Missing NFT contracts for source or destination chain")
                
            # Step 1: Verify NFT ownership on source chain
            print(f"🔍 Step 1: Verifying NFT ownership on {from_config['name']}...")
            owner = from_nft_contract.functions.ownerOf(token_id).call()
            if owner.lower() != from_address.lower():
                raise Exception(f"NFT not owned by specified address. Owner: {owner}, Specified: {from_address}")
            print(f"✅ NFT ownership verified")
            
            # Step 2: Get tokenURI from source chain
            print(f"📄 Step 2: Getting tokenURI from source chain...")
            token_uri = from_nft_contract.functions.tokenURI(token_id).call()
            print(f"✅ TokenURI retrieved: {token_uri}")
            
            # Step 3: Burn NFT on source chain
            print(f"🔥 Step 3: Burning NFT on source chain...")
            burn_result = await self.burn_nft_on_source_chain(
                from_chain, token_id, from_address, caller_private_key
            )
            print(f"✅ NFT burned successfully. TX: {burn_result['transaction_hash']}")
            
            # Step 4: Send cross-chain message via LayerZero
            print(f"📡 Step 4: Sending cross-chain message...")
            message_result = await self.send_cross_chain_message(
                from_chain, to_chain, token_id, token_uri, to_address, from_address, caller_private_key
            )
            print(f"✅ Cross-chain message sent. TX: {message_result['transaction_hash']}")
            
            # Step 5: Record transfer in database
            transfer_record = {
                "transfer_id": f"{from_chain}-{to_chain}-{token_id}-{int(time.time())}",
                "token_id": str(token_id),
                "from_chain": from_chain,
                "to_chain": to_chain,
                "from_address": from_address,
                "to_address": to_address,
                "token_uri": token_uri,
                "burn_tx_hash": burn_result['transaction_hash'],
                "message_tx_hash": message_result['transaction_hash'],
                "status": "message_sent",
                "timestamp": datetime.utcnow(),
                "layer_zero_guid": message_result.get('layer_zero_guid'),
                "layer_zero_nonce": message_result.get('layer_zero_nonce')
            }
            
            await self.database.nft_transfers.insert_one(transfer_record)
            print(f"✅ Transfer recorded in database")
            
            return {
                "success": True,
                "transfer_id": transfer_record["transfer_id"],
                "burn_transaction": burn_result,
                "message_transaction": message_result,
                "status": "cross_chain_transfer_initiated",
                "estimated_completion": "5-10 minutes (LayerZero delivery time)"
            }
            
        except Exception as e:
            print(f"❌ Cross-chain transfer failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "transfer_failed"
            }
            
    async def burn_nft_on_source_chain(
        self,
        chain: str,
        token_id: int,
        owner_address: str,
        caller_private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Burn NFT on source chain using burnForBridge function"""
        try:
            web3 = self.web3_connections[chain]
            nft_contract = self.nft_contracts[chain]
            config = NETWORK_CONFIG[chain]
            
            # Get private key
            if caller_private_key:
                account = Account.from_key(caller_private_key)
            else:
                private_key = get_private_key_for_address(owner_address)
                account = Account.from_key(private_key)
                
            # Build burn transaction
            burn_function = nft_contract.functions.burnForBridge(token_id)
            
            # Estimate gas
            gas_estimate = burn_function.estimate_gas({'from': account.address})
            gas_price = web3.eth.gas_price
            
            # Build transaction
            transaction = burn_function.build_transaction({
                'from': account.address,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': gas_price,
                'nonce': web3.eth.get_transaction_count(account.address),
                'chainId': config['chain_id']
            })
            
            # Sign and send transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                print(f"✅ NFT burned successfully on {config['name']}")
                return {
                    "success": True,
                    "transaction_hash": receipt.transactionHash.hex(),
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "chain": chain
                }
            else:
                raise Exception("Burn transaction failed")
                
        except Exception as e:
            print(f"❌ Failed to burn NFT on {chain}: {e}")
            raise e
            
    async def send_cross_chain_message(
        self,
        from_chain: str,
        to_chain: str,
        token_id: int,
        token_uri: str,
        to_address: str,
        from_address: str,
        caller_private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send cross-chain message via LayerZero to mint NFT on destination"""
        try:
            from_web3 = self.web3_connections[from_chain]
            from_config = NETWORK_CONFIG[from_chain]
            to_config = NETWORK_CONFIG[to_chain]
            
            # Get private key
            if caller_private_key:
                account = Account.from_key(caller_private_key)
            else:
                private_key = get_private_key_for_address(from_address)
                account = Account.from_key(private_key)
                
            # Create LayerZero message payload
            message_payload = {
                "action": "mint_nft",
                "token_id": token_id,
                "token_uri": token_uri,
                "to_address": to_address,
                "from_address": from_address,
                "original_chain": from_chain
            }
            
            # Encode message for LayerZero
            encoded_message = json.dumps(message_payload).encode('utf-8')
            
            # Get messenger contract
            messenger_contract = from_web3.eth.contract(
                address=from_config["messenger_contract"],
                abi=self.messenger_abi
            )
            
            # Quote the fee for cross-chain message
            dst_eid = to_config["layer_zero_eid"]
            to_bytes = Web3.to_bytes(hexstr=to_address)
            options = b''  # Default options
            
            fee_quote = messenger_contract.functions.quote(
                dst_eid,
                to_bytes,
                encoded_message,
                options,
                False  # payInLzToken = false
            ).call()
            
            native_fee = fee_quote[0]  # fee.nativeFee
            print(f"💰 LayerZero fee quote: {Web3.from_wei(native_fee, 'ether')} ETH")
            
            # Send cross-chain message
            send_function = messenger_contract.functions.send(
                dst_eid,
                to_bytes,
                encoded_message,
                options,
                (native_fee, 0)  # fee tuple (nativeFee, lzTokenFee)
            )
            
            # Estimate gas
            gas_estimate = send_function.estimate_gas({
                'from': account.address,
                'value': native_fee
            })
            gas_price = from_web3.eth.gas_price
            
            # Build transaction
            transaction = send_function.build_transaction({
                'from': account.address,
                'value': native_fee,
                'gas': int(gas_estimate * 1.2),
                'gasPrice': gas_price,
                'nonce': from_web3.eth.get_transaction_count(account.address),
                'chainId': from_config['chain_id']
            })
            
            # Sign and send transaction
            signed_txn = from_web3.eth.account.sign_transaction(transaction, private_key=account.key)
            tx_hash = from_web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = from_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                print(f"✅ Cross-chain message sent successfully")
                return {
                    "success": True,
                    "transaction_hash": receipt.transactionHash.hex(),
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "native_fee_paid": native_fee,
                    "from_chain": from_chain,
                    "to_chain": to_chain,
                    "message_payload": message_payload
                }
            else:
                raise Exception("Cross-chain message transaction failed")
                
        except Exception as e:
            print(f"❌ Failed to send cross-chain message: {e}")
            raise e
            
    async def get_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Get the status of a cross-chain NFT transfer"""
        try:
            transfer = await self.database.nft_transfers.find_one({"transfer_id": transfer_id})
            if not transfer:
                return {"error": "Transfer not found"}
                
            # Convert ObjectId to string for JSON serialization
            transfer["_id"] = str(transfer["_id"])
            
            # Check if NFT has been minted on destination chain
            if transfer["status"] == "message_sent":
                # Try to verify if NFT exists on destination chain
                to_chain = transfer["to_chain"]
                token_id = int(transfer["token_id"])
                to_address = transfer["to_address"]
                
                if to_chain in self.nft_contracts:
                    try:
                        to_nft_contract = self.nft_contracts[to_chain]
                        owner = to_nft_contract.functions.ownerOf(token_id).call()
                        if owner.lower() == to_address.lower():
                            # Update status to completed
                            await self.database.nft_transfers.update_one(
                                {"transfer_id": transfer_id},
                                {"$set": {"status": "completed", "completed_at": datetime.utcnow()}}
                            )
                            transfer["status"] = "completed"
                            transfer["completed_at"] = datetime.utcnow()
                    except Exception:
                        # NFT not yet minted on destination, keep status as message_sent
                        pass
                        
            return transfer
            
        except Exception as e:
            print(f"❌ Error getting transfer status: {e}")
            return {"error": str(e)}
            
    async def get_all_transfers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all NFT transfers with optional limit"""
        try:
            cursor = self.database.nft_transfers.find().sort("timestamp", -1).limit(limit)
            transfers = []
            async for transfer in cursor:
                transfer["_id"] = str(transfer["_id"])
                transfers.append(transfer)
            return transfers
        except Exception as e:
            print(f"❌ Error getting transfers: {e}")
            return []
            
    async def mint_nft_on_destination_chain(
        self,
        to_chain: str,
        token_id: int,
        to_address: str,
        token_uri: str,
        use_admin_account: bool = True
    ) -> Dict[str, Any]:
        """
        Mint NFT on destination chain (typically called by admin for cross-chain transfers)
        
        Args:
            to_chain: Destination chain identifier
            token_id: Token ID to mint
            to_address: Address to mint NFT to
            token_uri: Metadata URI for the NFT
            use_admin_account: Whether to use admin account for minting (default: True)
        """
        try:
            print(f"🏭 Minting NFT on destination chain: {to_chain}")
            print(f"   Token ID: {token_id}")
            print(f"   To Address: {to_address}")
            print(f"   Token URI: {token_uri}")
            print(f"   Using Admin Account: {use_admin_account}")
            
            if to_chain not in self.web3_connections:
                raise Exception(f"No connection to destination chain: {to_chain}")
                
            if to_chain not in self.nft_contracts:
                raise Exception(f"No NFT contract configured for chain: {to_chain}")
                
            web3 = self.web3_connections[to_chain]
            nft_contract = self.nft_contracts[to_chain]
            config = NETWORK_CONFIG[to_chain]
            
            # Determine which account to use for minting
            if use_admin_account:
                # Use admin account (has MINTER_ROLE)
                from app.core.config import get_settings
                settings = get_settings()
                admin_private_key = settings.deployer_private_key
                if not admin_private_key:
                    raise Exception("Admin private key not configured")
                account = Account.from_key(admin_private_key)
                print(f"🔐 Using admin account for minting: {account.address}")
            else:
                # Use recipient's account (must have MINTER_ROLE)
                private_key = get_private_key_for_address(to_address)
                if not private_key:
                    raise Exception(f"No private key found for address: {to_address}")
                account = Account.from_key(private_key)
                print(f"🔐 Using recipient account for minting: {account.address}")
            
            # Check if token already exists
            try:
                existing_owner = nft_contract.functions.ownerOf(token_id).call()
                print(f"⚠️ Token {token_id} already exists on {to_chain}, owned by: {existing_owner}")
                if existing_owner.lower() == to_address.lower():
                    return {
                        "success": True,
                        "already_exists": True,
                        "message": f"Token {token_id} already minted to correct address on {to_chain}",
                        "owner": existing_owner
                    }
                else:
                    raise Exception(f"Token {token_id} already exists but owned by different address: {existing_owner}")
            except Exception as e:
                if "nonexistent token" in str(e).lower() or "invalid token" in str(e).lower():
                    # Token doesn't exist, proceed with minting
                    print(f"✅ Token {token_id} doesn't exist on {to_chain}, proceeding with mint")
                else:
                    # Some other error occurred
                    raise e
            
            # Build mint transaction using safeMint(to, tokenId, uri)
            mint_function = nft_contract.functions.safeMint(to_address, token_id, token_uri)
            
            # Estimate gas
            gas_estimate = mint_function.estimate_gas({'from': account.address})
            gas_price = web3.eth.gas_price
            
            # Build transaction
            transaction = mint_function.build_transaction({
                'from': account.address,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': gas_price,
                'nonce': web3.eth.get_transaction_count(account.address),
                'chainId': config['chain_id']
            })
            
            print(f"📤 Sending mint transaction on {to_chain}...")
            print(f"   Gas estimate: {gas_estimate}")
            print(f"   Gas price: {gas_price}")
            print(f"   Nonce: {transaction['nonce']}")
            
            # Sign and send transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Mint transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                print(f"✅ NFT minted successfully on {to_chain}")
                print(f"   Block: {receipt.blockNumber}")
                print(f"   Gas used: {receipt.gasUsed}")
                
                # Verify minting
                try:
                    owner = nft_contract.functions.ownerOf(token_id).call()
                    token_uri_stored = nft_contract.functions.tokenURI(token_id).call()
                    print(f"✅ Verification:")
                    print(f"   Owner: {owner}")
                    print(f"   Expected: {to_address}")
                    print(f"   Owner match: {owner.lower() == to_address.lower()}")
                    print(f"   Token URI: {token_uri_stored}")
                except Exception as verify_error:
                    print(f"⚠️ Verification failed: {verify_error}")
                
                return {
                    "success": True,
                    "transaction_hash": receipt.transactionHash.hex(),
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "chain": to_chain,
                    "token_id": token_id,
                    "to_address": to_address,
                    "token_uri": token_uri,
                    "minter_account": account.address
                }
            else:
                raise Exception(f"Mint transaction failed with status: {receipt.status}")
                
        except Exception as e:
            print(f"❌ Failed to mint NFT on destination chain: {e}")
            return {
                "success": False,
                "error": str(e),
                "chain": to_chain,
                "token_id": token_id
            }

# Global instance
nft_bridge_service = NFTBridgeService()