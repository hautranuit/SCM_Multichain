"""
Multi-Chain Blockchain Service
Handles interactions with Polygon PoS Hub and L2 CDK Participants
"""
import asyncio
import json
from typing import Dict, List, Optional, Any
from web3 import Web3
# from web3.middleware import geth_poa_middleware
import httpx
from app.core.config import get_settings
from app.core.database import get_database

settings = get_settings()

class BlockchainService:
    def __init__(self):
        self.pos_web3: Optional[Web3] = None
        self.l2_web3: Optional[Web3] = None
        self.contracts: Dict[str, Any] = {}
        self.database = None
        
    async def initialize(self):
        """Initialize blockchain connections and contracts"""
        print("🔗 Initializing Multi-Chain Blockchain Service...")
        
        # Initialize database connection using async method
        self.database = await get_database()
        
        # Initialize Polygon PoS connection
        if settings.polygon_pos_rpc:
            self.pos_web3 = Web3(Web3.HTTPProvider(settings.polygon_pos_rpc))
            # For PoS networks like Polygon
            # self.pos_web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if self.pos_web3.is_connected():
                print(f"✅ Connected to Polygon PoS (Chain ID: {settings.polygon_pos_chain_id})")
            else:
                print("❌ Failed to connect to Polygon PoS")
        
        # Initialize L2 CDK connection (if configured)
        if settings.l2_cdk_rpc:
            self.l2_web3 = Web3(Web3.HTTPProvider(settings.l2_cdk_rpc))
            # For L2 CDK networks
            # self.l2_web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if self.l2_web3.is_connected():
                print(f"✅ Connected to L2 CDK (Chain ID: {settings.l2_cdk_chain_id})")
            else:
                print("❌ Failed to connect to L2 CDK")
        
        # Load contract ABIs and initialize contracts
        await self.load_contracts()
        
    async def load_contracts(self):
        """Load contract ABIs and create contract instances"""
        try:
            # Load contract ABIs (these will be generated when we deploy)
            contract_configs = {
                "pos_hub": {
                    "address": settings.pos_hub_contract,
                    "abi_path": "/app/multichain-chainflip/contracts/polygon-pos-hub/artifacts/PolygonPoSHub.sol/PolygonPoSHub.json"
                },
                "l2_participant": {
                    "address": settings.l2_participant_contract,
                    "abi_path": "/app/multichain-chainflip/contracts/l2-cdk-participants/artifacts/L2Participant.sol/L2Participant.json"
                }
            }
            
            for contract_name, config in contract_configs.items():
                if config["address"] and self.pos_web3:
                    try:
                        # For now, we'll use a placeholder ABI
                        # This will be replaced when contracts are deployed
                        abi = []  # Load from file when available
                        contract = self.pos_web3.eth.contract(
                            address=config["address"],
                            abi=abi
                        )
                        self.contracts[contract_name] = contract
                        print(f"✅ Loaded {contract_name} contract")
                    except Exception as e:
                        print(f"⚠️ Failed to load {contract_name} contract: {e}")
                        
        except Exception as e:
            print(f"⚠️ Contract loading error: {e}")
    
    async def deploy_pos_hub_contract(self, deployer_private_key: str) -> str:
        """Deploy Polygon PoS Hub contract"""
        if not self.pos_web3:
            raise Exception("Polygon PoS connection not initialized")
            
        # This will be implemented when we create the contract
        # For now, return placeholder
        return "0x0000000000000000000000000000000000000000"
    
    async def deploy_l2_participant_contract(self, deployer_private_key: str, participant_id: str) -> str:
        """Deploy L2 CDK Participant contract"""
        if not self.l2_web3:
            raise Exception("L2 CDK connection not initialized")
            
        # This will be implemented when we create the contract
        return "0x0000000000000000000000000000000000000000"
    
    async def register_participant(self, participant_address: str, participant_type: str, chain_id: int) -> Dict[str, Any]:
        """Register a new participant in the multi-chain system"""
        
        participant_data = {
            "address": participant_address,
            "participant_type": participant_type,  # manufacturer, distributor, retailer, etc.
            "chain_id": chain_id,
            "registered_at": asyncio.get_event_loop().time(),
            "status": "active",
            "reputation_score": 100,  # Starting score
            "l2_contract_address": None
        }
        
        # Deploy L2 contract for this participant if on L2
        if chain_id != settings.polygon_pos_chain_id:
            try:
                l2_contract = await self.deploy_l2_participant_contract(
                    settings.deployer_private_key,
                    participant_address
                )
                participant_data["l2_contract_address"] = l2_contract
            except Exception as e:
                print(f"Failed to deploy L2 contract for participant: {e}")
        
        # Store in database
        result = await self.database.participants.insert_one(participant_data)
        participant_data["_id"] = str(result.inserted_id)
        
        return participant_data
    
    async def mint_product_nft(self, manufacturer: str, metadata_cid: str, initial_qr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mint a new product NFT on Polygon PoS Hub"""
        
        try:
            # Generate unique token ID
            token_id = await self.generate_token_id()
            
            # Create product data
            product_data = {
                "token_id": token_id,
                "manufacturer": manufacturer,
                "metadata_cid": metadata_cid,
                "chain_id": settings.polygon_pos_chain_id,
                "current_owner": manufacturer,
                "status": "manufactured",
                "created_at": asyncio.get_event_loop().time(),
                "qr_data": initial_qr_data,
                "transport_history": [],
                "anomaly_flags": [],
                "authenticity_score": 1.0
            }
            
            # Store in database
            result = await self.database.products.insert_one(product_data)
            product_data["_id"] = str(result.inserted_id)
            
            # TODO: Call smart contract to mint NFT
            # tx_hash = await self.call_contract_method("pos_hub", "mintProduct", ...)
            
            return product_data
            
        except Exception as e:
            raise Exception(f"Failed to mint product NFT: {e}")
    
    async def transfer_product(self, token_id: str, from_address: str, to_address: str, transport_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transfer product between participants and log transport data"""
        
        try:
            # Update product ownership
            update_result = await self.database.products.update_one(
                {"token_id": token_id},
                {
                    "$set": {
                        "current_owner": to_address,
                        "last_updated": asyncio.get_event_loop().time()
                    },
                    "$push": {
                        "transport_history": {
                            "from": from_address,
                            "to": to_address,
                            "timestamp": asyncio.get_event_loop().time(),
                            "transport_data": transport_data
                        }
                    }
                }
            )
            
            if update_result.modified_count == 0:
                raise Exception("Product not found or transfer failed")
            
            # Log transaction
            transaction_data = {
                "type": "transfer",
                "token_id": token_id,
                "from_address": from_address,
                "to_address": to_address,
                "chain_id": settings.polygon_pos_chain_id,
                "timestamp": asyncio.get_event_loop().time(),
                "transport_data": transport_data,
                "tx_hash": None  # Will be filled when blockchain transaction is made
            }
            
            await self.database.transactions.insert_one(transaction_data)
            
            return {"success": True, "message": "Product transferred successfully"}
            
        except Exception as e:
            raise Exception(f"Failed to transfer product: {e}")
    
    async def generate_token_id(self) -> str:
        """Generate unique token ID"""
        import time
        import random
        
        timestamp = int(time.time())
        random_part = random.randint(1000, 9999)
        return f"{timestamp}{random_part}"
    
    async def get_product_by_token_id(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get product information by token ID"""
        
        product = await self.database.products.find_one({"token_id": token_id})
        if product:
            product["_id"] = str(product["_id"])
        return product
    
    async def get_participant_products(self, participant_address: str) -> List[Dict[str, Any]]:
        """Get all products owned by a participant"""
        
        cursor = self.database.products.find({"current_owner": participant_address})
        products = []
        async for product in cursor:
            product["_id"] = str(product["_id"])
            products.append(product)
        
        return products
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """Get multi-chain network statistics"""
        
        try:
            # Count products by chain
            products_count = await self.database.products.count_documents({})
            participants_count = await self.database.participants.count_documents({})
            transactions_count = await self.database.transactions.count_documents({})
            
            # Network status
            pos_status = self.pos_web3.is_connected() if self.pos_web3 else False
            l2_status = self.l2_web3.is_connected() if self.l2_web3 else False
            
            return {
                "polygon_pos": {
                    "connected": pos_status,
                    "chain_id": settings.polygon_pos_chain_id,
                    "latest_block": self.pos_web3.eth.block_number if pos_status else 0
                },
                "l2_cdk": {
                    "connected": l2_status,
                    "chain_id": settings.l2_cdk_chain_id,
                    "latest_block": self.l2_web3.eth.block_number if l2_status else 0
                },
                "statistics": {
                    "total_products": products_count,
                    "total_participants": participants_count,
                    "total_transactions": transactions_count
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get network stats: {e}"}
    
    async def cross_chain_message(self, source_chain: int, target_chain: int, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send cross-chain message using FxPortal bridge"""
        
        try:
            # This will implement FxPortal bridge communication
            # For now, we'll simulate the cross-chain message
            
            message = {
                "id": await self.generate_token_id(),
                "source_chain": source_chain,
                "target_chain": target_chain,
                "data": message_data,
                "timestamp": asyncio.get_event_loop().time(),
                "status": "pending"
            }
            
            # Store cross-chain message
            await self.database.cross_chain_messages.insert_one(message)
            
            # TODO: Implement actual FxPortal bridge call
            
            return {"success": True, "message_id": message["id"]}
            
        except Exception as e:
            raise Exception(f"Cross-chain message failed: {e}")
