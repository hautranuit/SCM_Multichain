"""
Enhanced Multi-Chain Blockchain Service for ChainFLIP
Integrates with specialized L2 contracts: ManufacturerChain, TransporterChain, BuyerChain, and EnhancedPolygonPoSHub
"""
import asyncio
import json
import os
import time
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.contract import Contract
from app.core.config import get_settings
from app.core.database import get_database
from app.services.ipfs_service import ipfs_service
from app.services.encryption_service import encryption_service

settings = get_settings()

class MultiChainService:
    def __init__(self):
        self.hub_web3: Optional[Web3] = None
        self.manufacturer_web3: Optional[Web3] = None
        self.transporter_web3: Optional[Web3] = None
        self.buyer_web3: Optional[Web3] = None
        self.contracts: Dict[str, Contract] = {}
        self.database = None
        
        # Chain configurations - Updated with real deployed addresses
        self.chain_configs = {
            "hub": {
                "chain_id": 80002,  # Polygon Amoy
                "name": "Enhanced Polygon PoS Hub",
                "role": "Central coordination and FL aggregation",
                "contract_address": "0x45A2C5B59272dcC9b427926DCd6079B52D4335C8"
            },
            "manufacturer": {
                "chain_id": 2442,  # zkEVM Cardona
                "name": "Manufacturer zkEVM Chain", 
                "role": "Product creation and quality control",
                "contract_address": "0x4806bdE2D69Af285759e913DA9A4322F876ACE4d"
            },
            "transporter": {
                "chain_id": 421614,  # Arbitrum Sepolia
                "name": "Transporter Arbitrum Chain",
                "role": "Logistics and consensus",
                "contract_address": "0x5D9E723dC9f8A54a3904aaCF188893fb67d582a9"
            },
            "buyer": {
                "chain_id": 11155420,  # Optimism Sepolia
                "name": "Buyer Optimism Chain", 
                "role": "Marketplace and disputes",
                "contract_address": "0x4806bdE2D69Af285759e913DA9A4322F876ACE4d"
            }
        }
        
    async def initialize(self):
        """Initialize all blockchain connections and contracts"""
        print("🚀 Initializing ChainFLIP Multi-Chain Service...")
        
        # Initialize database
        self.database = await get_database()
        
        # Initialize Hub connection (Polygon PoS)
        if settings.polygon_pos_rpc:
            self.hub_web3 = Web3(Web3.HTTPProvider(settings.polygon_pos_rpc))
            if self.hub_web3.is_connected():
                print(f"✅ Connected to Hub Chain (Chain ID: {self.chain_configs['hub']['chain_id']})")
            else:
                print("❌ Failed to connect to Hub Chain")
        
        # Initialize L2 connections - Real multichain deployment
        # Manufacturer L2: zkEVM Cardona
        if settings.zkevm_cardona_rpc:
            self.manufacturer_web3 = Web3(Web3.HTTPProvider(settings.zkevm_cardona_rpc))
            if self.manufacturer_web3.is_connected():
                print(f"✅ Connected to Manufacturer Chain (zkEVM Cardona - Chain ID: {self.chain_configs['manufacturer']['chain_id']})")
            else:
                print("❌ Failed to connect to Manufacturer Chain")
        
        # Transporter L2: Arbitrum Sepolia  
        if settings.arbitrum_sepolia_rpc:
            self.transporter_web3 = Web3(Web3.HTTPProvider(settings.arbitrum_sepolia_rpc))
            if self.transporter_web3.is_connected():
                print(f"✅ Connected to Transporter Chain (Arbitrum Sepolia - Chain ID: {self.chain_configs['transporter']['chain_id']})")
            else:
                print("❌ Failed to connect to Transporter Chain")
        
        # Buyer L2: Optimism Sepolia
        if settings.optimism_sepolia_rpc:
            self.buyer_web3 = Web3(Web3.HTTPProvider(settings.optimism_sepolia_rpc))
            if self.buyer_web3.is_connected():
                print(f"✅ Connected to Buyer Chain (Optimism Sepolia - Chain ID: {self.chain_configs['buyer']['chain_id']})")
            else:
                print("❌ Failed to connect to Buyer Chain")
        
        # Load contract ABIs and addresses
        await self.load_contracts()
        
    async def load_contracts(self):
        """Load contract instances for all chains"""
        try:
            # Load contract addresses from environment or database
            contract_addresses = await self._get_contract_addresses()
            
            if not contract_addresses:
                print("⚠️ No contract addresses found. Please deploy contracts first.")
                return
            
            # Load ABIs (in production, these would be loaded from files)
            self.contract_abis = await self._load_contract_abis()
            
            # Initialize contract instances
            if self.hub_web3 and contract_addresses.get("hub"):
                self.contracts["hub"] = self.hub_web3.eth.contract(
                    address=contract_addresses["hub"],
                    abi=self.contract_abis.get("hub", [])
                )
                print("✅ Hub contract loaded")
            
            if self.manufacturer_web3 and contract_addresses.get("manufacturer"):
                self.contracts["manufacturer"] = self.manufacturer_web3.eth.contract(
                    address=contract_addresses["manufacturer"],
                    abi=self.contract_abis.get("manufacturer", [])
                )
                print("✅ Manufacturer contract loaded")
            
            if self.transporter_web3 and contract_addresses.get("transporter"):
                self.contracts["transporter"] = self.transporter_web3.eth.contract(
                    address=contract_addresses["transporter"],
                    abi=self.contract_abis.get("transporter", [])
                )
                print("✅ Transporter contract loaded")
            
            if self.buyer_web3 and contract_addresses.get("buyer"):
                self.contracts["buyer"] = self.buyer_web3.eth.contract(
                    address=contract_addresses["buyer"],
                    abi=self.contract_abis.get("buyer", [])
                )
                print("✅ Buyer contract loaded")
                
        except Exception as e:
            print(f"⚠️ Contract loading error: {e}")
    
    async def _get_contract_addresses(self) -> Dict[str, str]:
        """Get contract addresses from environment or database"""
        # Updated with real deployed addresses
        addresses = {
            "hub": settings.pos_hub_contract or "0x45A2C5B59272dcC9b427926DCd6079B52D4335C8",
            "manufacturer": settings.manufacturer_contract_address or "0x4806bdE2D69Af285759e913DA9A4322F876ACE4d",
            "transporter": settings.transporter_contract_address or "0x5D9E723dC9f8A54a3904aaCF188893fb67d582a9",
            "buyer": settings.buyer_contract_address or "0x4806bdE2D69Af285759e913DA9A4322F876ACE4d"
        }
        
        # If not in environment, check database
        if not any(addresses.values()):
            deployment_record = await self.database.deployments.find_one(
                {"status": "active"}, 
                sort=[("timestamp", -1)]
            )
            if deployment_record:
                addresses = deployment_record.get("contracts", {})
        
        return {k: v for k, v in addresses.items() if v}
    
    async def _load_contract_abis(self) -> Dict[str, List]:
        """Load contract ABIs (simplified for development)"""
        # In production, these would be loaded from compiled contract artifacts
        return {
            "hub": [],  # EnhancedPolygonPoSHub ABI
            "manufacturer": [],  # ManufacturerChain ABI  
            "transporter": [],  # TransporterChain ABI
            "buyer": []  # BuyerChain ABI
        }
    
    # ==========================================
    # MANUFACTURER CHAIN OPERATIONS (Algorithm 4 & 1)
    # ==========================================
    
    async def mint_product_on_manufacturer_chain(self, manufacturer: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Algorithm 4: Product Authenticity Verification - Mint product on manufacturer chain"""
        try:
            print(f"🏭 Minting product on Manufacturer Chain...")
            
            # Upload metadata to IPFS
            metadata_cid = await ipfs_service.upload_to_ipfs(product_data)
            
            # Generate unique product ID
            unique_product_id = f"PROD-{int(time.time())}-{len(product_data.get('uniqueProductID', ''))}"
            
            # Prepare mint parameters
            mint_params = {
                "uniqueProductID": unique_product_id,
                "batchNumber": product_data.get("batchNumber", f"BATCH-{int(time.time())}"),
                "manufacturingDate": product_data.get("manufacturingDate", time.strftime("%Y-%m-%d")),
                "expirationDate": product_data.get("expirationDate", ""),
                "productType": product_data.get("productType", "General"),
                "manufacturerID": manufacturer,
                "metadataCID": metadata_cid,
                "manufacturingCost": int(product_data.get("manufacturingCost", 100))
            }
            
            # Store in database (simulating blockchain transaction)
            token_id = await self._generate_token_id()
            
            product_record = {
                "token_id": token_id,
                "chain": "manufacturer",
                "chain_id": self.chain_configs["manufacturer"]["chain_id"],
                "manufacturer": manufacturer,
                "mint_params": mint_params,
                "metadata_cid": metadata_cid,
                "status": "manufactured",
                "quality_approved": False,
                "created_at": time.time(),
                "cross_chain_hash": await self._generate_cross_chain_hash(token_id, manufacturer)
            }
            
            result = await self.database.products.insert_one(product_record)
            
            print(f"✅ Product {token_id} minted on Manufacturer Chain")
            return {
                "success": True,
                "token_id": token_id,
                "chain": "manufacturer",
                "metadata_cid": metadata_cid,
                "cross_chain_hash": product_record["cross_chain_hash"]
            }
            
        except Exception as e:
            print(f"❌ Manufacturer chain minting error: {e}")
            return {"success": False, "error": str(e)}
    
    async def perform_quality_check(self, product_id: str, inspector: str, passed: bool, score: int, report_cid: str = "") -> Dict[str, Any]:
        """Algorithm 3: Supply Chain Consensus - Quality control on manufacturer chain"""
        try:
            print(f"🔍 Performing quality check for product {product_id}")
            
            # Verify product exists
            product = await self.database.products.find_one({"token_id": product_id})
            if not product:
                return {"success": False, "error": "Product not found"}
            
            if product.get("chain") != "manufacturer":
                return {"success": False, "error": "Product not on manufacturer chain"}
            
            # Record quality check
            quality_check = {
                "product_id": product_id,
                "inspector": inspector,
                "passed": passed,
                "score": score,
                "report_cid": report_cid,
                "timestamp": time.time()
            }
            
            await self.database.quality_checks.insert_one(quality_check)
            
            # Update product status if passed
            if passed and score >= 70:  # Minimum quality threshold
                await self.database.products.update_one(
                    {"token_id": product_id},
                    {
                        "$set": {
                            "quality_approved": True,
                            "quality_score": score,
                            "status": "quality_approved"
                        }
                    }
                )
                
                # Sync to hub for cross-chain coordination
                await self._sync_product_to_hub(product_id)
                
                print(f"✅ Product {product_id} approved for shipment")
                return {"success": True, "status": "approved", "score": score}
            else:
                print(f"❌ Product {product_id} failed quality check")
                return {"success": True, "status": "failed", "score": score}
                
        except Exception as e:
            print(f"❌ Quality check error: {e}")
            return {"success": False, "error": str(e)}
    
    async def claim_manufacturing_incentive(self, manufacturer: str) -> Dict[str, Any]:
        """Algorithm 1: Payment Release and Incentive Mechanism - Manufacturing incentives"""
        try:
            print(f"💰 Processing manufacturing incentive for {manufacturer}")
            
            # Calculate incentive based on production and quality
            incentive_data = await self._calculate_manufacturing_incentive(manufacturer)
            
            if incentive_data["amount"] > 0:
                # Record incentive payment
                payment_record = {
                    "recipient": manufacturer,
                    "type": "manufacturing_incentive",
                    "amount": incentive_data["amount"],
                    "quality_score": incentive_data["quality_score"],
                    "products_count": incentive_data["products_count"],
                    "timestamp": time.time(),
                    "chain": "manufacturer"
                }
                
                await self.database.incentive_payments.insert_one(payment_record)
                
                print(f"✅ Manufacturing incentive paid: ${incentive_data['amount']}")
                return {"success": True, "amount": incentive_data["amount"]}
            else:
                return {"success": False, "error": "No incentive available"}
                
        except Exception as e:
            print(f"❌ Manufacturing incentive error: {e}")
            return {"success": False, "error": str(e)}
    
    # ==========================================
    # TRANSPORTER CHAIN OPERATIONS (Algorithm 3 & 1 & 2)
    # ==========================================
    
    async def create_shipment(self, transporter: str, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Algorithm 3: Supply Chain Consensus - Create shipment on transporter chain"""
        try:
            print(f"🚛 Creating shipment on Transporter Chain...")
            
            shipment_id = await self._generate_shipment_id()
            
            shipment_record = {
                "shipment_id": shipment_id,
                "chain": "transporter",
                "product_token_id": shipment_data.get("product_token_id"),
                "transporter": transporter,
                "start_location": shipment_data.get("start_location"),
                "end_location": shipment_data.get("end_location"),
                "distance": shipment_data.get("distance", 0),
                "estimated_delivery_time": shipment_data.get("estimated_delivery_time"),
                "status": "created",
                "transport_fee": await self._calculate_transport_fee(shipment_data.get("distance", 0)),
                "created_at": time.time(),
                "consensus_votes": []
            }
            
            await self.database.shipments.insert_one(shipment_record)
            
            print(f"✅ Shipment {shipment_id} created on Transporter Chain")
            return {"success": True, "shipment_id": shipment_id}
            
        except Exception as e:
            print(f"❌ Shipment creation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def submit_consensus_vote(self, shipment_id: str, voter: str, approve: bool, reason: str) -> Dict[str, Any]:
        """Algorithm 3: Supply Chain Consensus - Vote on shipment approval"""
        try:
            print(f"🗳️ Submitting consensus vote for shipment {shipment_id}")
            
            vote_record = {
                "shipment_id": shipment_id,
                "voter": voter,
                "approve": approve,
                "reason": reason,
                "timestamp": time.time()
            }
            
            await self.database.consensus_votes.insert_one(vote_record)
            
            # Check if consensus reached
            consensus_result = await self._check_shipment_consensus(shipment_id)
            
            return {"success": True, "consensus_reached": consensus_result["reached"], "result": consensus_result.get("result")}
            
        except Exception as e:
            print(f"❌ Consensus voting error: {e}")
            return {"success": False, "error": str(e)}
    
    async def mark_delivered(self, shipment_id: str, transporter: str) -> Dict[str, Any]:
        """Mark shipment as delivered and calculate incentives"""
        try:
            print(f"📦 Marking shipment {shipment_id} as delivered")
            
            shipment = await self.database.shipments.find_one({"shipment_id": shipment_id})
            if not shipment:
                return {"success": False, "error": "Shipment not found"}
            
            if shipment.get("transporter") != transporter:
                return {"success": False, "error": "Not authorized transporter"}
            
            # Calculate delivery performance
            on_time = time.time() <= shipment.get("estimated_delivery_time", 0)
            
            # Update shipment status
            await self.database.shipments.update_one(
                {"shipment_id": shipment_id},
                {
                    "$set": {
                        "status": "delivered" if on_time else "delayed",
                        "actual_delivery_time": time.time(),
                        "on_time": on_time
                    }
                }
            )
            
            # Process transport incentive if on time
            if on_time:
                incentive_result = await self._award_transport_incentive(transporter, shipment)
                return {"success": True, "on_time": True, "incentive": incentive_result}
            else:
                return {"success": True, "on_time": False, "penalty": "Late delivery recorded"}
                
        except Exception as e:
            print(f"❌ Delivery marking error: {e}")
            return {"success": False, "error": str(e)}
    
    # ==========================================
    # BUYER CHAIN OPERATIONS (Algorithm 5 & 2 & 1)
    # ==========================================
    
    async def create_marketplace_listing(self, seller: str, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Algorithm 5: Post Supply Chain Management - Create marketplace listing"""
        try:
            print(f"🛒 Creating marketplace listing on Buyer Chain...")
            
            listing_id = await self._generate_listing_id()
            
            listing_record = {
                "listing_id": listing_id,
                "chain": "buyer",
                "product_token_id": listing_data.get("product_token_id"),
                "seller": seller,
                "price": listing_data.get("price"),
                "description": listing_data.get("description"),
                "category": listing_data.get("category", "Other"),
                "metadata_cid": listing_data.get("metadata_cid"),
                "is_active": True,
                "created_at": time.time()
            }
            
            await self.database.marketplace_listings.insert_one(listing_record)
            
            print(f"✅ Marketplace listing {listing_id} created")
            return {"success": True, "listing_id": listing_id}
            
        except Exception as e:
            print(f"❌ Marketplace listing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_purchase(self, buyer: str, listing_id: str, delivery_location: str, payment_amount: float) -> Dict[str, Any]:
        """Algorithm 5: Post Supply Chain Management - Create purchase order"""
        try:
            print(f"💳 Creating purchase order for listing {listing_id}")
            
            # Verify listing exists and is active
            listing = await self.database.marketplace_listings.find_one({"listing_id": listing_id})
            if not listing or not listing.get("is_active"):
                return {"success": False, "error": "Listing not found or inactive"}
            
            if listing.get("seller") == buyer:
                return {"success": False, "error": "Cannot buy your own product"}
            
            purchase_id = await self._generate_purchase_id()
            
            purchase_record = {
                "purchase_id": purchase_id,
                "listing_id": listing_id,
                "product_token_id": listing.get("product_token_id"),
                "buyer": buyer,
                "seller": listing.get("seller"),
                "price": listing.get("price"),
                "payment_amount": payment_amount,
                "collateral": payment_amount - listing.get("price", 0),
                "delivery_location": delivery_location,
                "status": "paid",
                "confirmation_deadline": time.time() + (7 * 24 * 3600),  # 7 days
                "created_at": time.time()
            }
            
            await self.database.purchases.insert_one(purchase_record)
            
            # Deactivate listing
            await self.database.marketplace_listings.update_one(
                {"listing_id": listing_id},
                {"$set": {"is_active": False}}
            )
            
            print(f"✅ Purchase {purchase_id} created")
            return {"success": True, "purchase_id": purchase_id}
            
        except Exception as e:
            print(f"❌ Purchase creation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def open_dispute(self, purchase_id: str, plaintiff: str, reason: str, evidence_cid: str = "") -> Dict[str, Any]:
        """Algorithm 2: Dispute Resolution and Voting Mechanism - Open purchase dispute"""
        try:
            print(f"⚖️ Opening dispute for purchase {purchase_id}")
            
            purchase = await self.database.purchases.find_one({"purchase_id": purchase_id})
            if not purchase:
                return {"success": False, "error": "Purchase not found"}
            
            if purchase.get("buyer") != plaintiff:
                return {"success": False, "error": "Not authorized to dispute"}
            
            dispute_id = await self._generate_dispute_id()
            
            dispute_record = {
                "dispute_id": dispute_id,
                "purchase_id": purchase_id,
                "plaintiff": plaintiff,
                "defendant": purchase.get("seller"),
                "reason": reason,
                "evidence_cid": evidence_cid,
                "status": "open",
                "chain": "buyer",
                "arbitrators": [],
                "votes": {},
                "created_at": time.time()
            }
            
            # Assign arbitrators
            arbitrators = await self._assign_arbitrators()
            dispute_record["arbitrators"] = arbitrators
            
            await self.database.disputes.insert_one(dispute_record)
            
            print(f"✅ Dispute {dispute_id} opened")
            return {"success": True, "dispute_id": dispute_id, "arbitrators": arbitrators}
            
        except Exception as e:
            print(f"❌ Dispute opening error: {e}")
            return {"success": False, "error": str(e)}
    
    async def confirm_delivery(self, purchase_id: str, buyer: str) -> Dict[str, Any]:
        """Algorithm 1: Payment Release - Confirm delivery and release payment"""
        try:
            print(f"✅ Confirming delivery for purchase {purchase_id}")
            
            purchase = await self.database.purchases.find_one({"purchase_id": purchase_id})
            if not purchase:
                return {"success": False, "error": "Purchase not found"}
            
            if purchase.get("buyer") != buyer:
                return {"success": False, "error": "Not authorized buyer"}
            
            if purchase.get("status") != "delivered":
                return {"success": False, "error": "Product not delivered yet"}
            
            # Release payment to seller
            payment_result = await self._release_purchase_payment(purchase_id)
            
            return {"success": True, "payment_released": payment_result["success"]}
            
        except Exception as e:
            print(f"❌ Delivery confirmation error: {e}")
            return {"success": False, "error": str(e)}
    
    # ==========================================
    # CROSS-CHAIN COORDINATION
    # ==========================================
    
    async def _sync_product_to_hub(self, product_id: str):
        """Sync product information to hub chain for cross-chain coordination"""
        try:
            product = await self.database.products.find_one({"token_id": product_id})
            if not product:
                return
            
            # Create cross-chain sync record
            sync_record = {
                "product_id": product_id,
                "source_chain": product.get("chain"),
                "target_chain": "hub",
                "sync_type": "product_approval",
                "data": {
                    "manufacturer": product.get("manufacturer"),
                    "metadata_cid": product.get("metadata_cid"),
                    "quality_approved": product.get("quality_approved")
                },
                "timestamp": time.time(),
                "status": "pending"
            }
            
            await self.database.cross_chain_syncs.insert_one(sync_record)
            print(f"🔗 Product {product_id} queued for hub sync")
            
        except Exception as e:
            print(f"⚠️ Hub sync error: {e}")
    
    # ==========================================
    # HELPER FUNCTIONS
    # ==========================================
    
    async def _generate_token_id(self) -> str:
        """Generate unique token ID"""
        return f"{int(time.time())}{await self._random_suffix()}"
    
    async def _generate_shipment_id(self) -> str:
        """Generate unique shipment ID"""
        return f"SHIP-{int(time.time())}-{await self._random_suffix()}"
    
    async def _generate_listing_id(self) -> str:
        """Generate unique listing ID"""
        return f"LIST-{int(time.time())}-{await self._random_suffix()}"
    
    async def _generate_purchase_id(self) -> str:
        """Generate unique purchase ID"""
        return f"PURCH-{int(time.time())}-{await self._random_suffix()}"
    
    async def _generate_dispute_id(self) -> str:
        """Generate unique dispute ID"""
        return f"DISP-{int(time.time())}-{await self._random_suffix()}"
    
    async def _random_suffix(self) -> str:
        """Generate random suffix"""
        import random
        return str(random.randint(1000, 9999))
    
    async def _generate_cross_chain_hash(self, token_id: str, manufacturer: str) -> str:
        """Generate cross-chain verification hash"""
        import hashlib
        data = f"{token_id}:{manufacturer}:{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def _calculate_manufacturing_incentive(self, manufacturer: str) -> Dict[str, Any]:
        """Calculate manufacturing incentive based on performance"""
        # Get manufacturer's products
        products_cursor = self.database.products.find({"manufacturer": manufacturer})
        products = await products_cursor.to_list(length=None)
        
        # Get quality checks
        quality_checks_cursor = self.database.quality_checks.find(
            {"product_id": {"$in": [p["token_id"] for p in products]}}
        )
        quality_checks = await quality_checks_cursor.to_list(length=None)
        
        if not quality_checks:
            return {"amount": 0, "quality_score": 0, "products_count": 0}
        
        # Calculate average quality score
        avg_quality = sum(qc["score"] for qc in quality_checks) / len(quality_checks)
        
        # Base incentive calculation
        base_incentive = len(products) * 50  # $50 per product
        quality_bonus = (avg_quality / 100) * base_incentive * 0.5  # Up to 50% bonus
        
        total_incentive = base_incentive + quality_bonus
        
        return {
            "amount": total_incentive,
            "quality_score": avg_quality,
            "products_count": len(products)
        }
    
    async def _calculate_transport_fee(self, distance: int) -> float:
        """Calculate transport fee based on distance"""
        base_fee = 10.0  # Base fee
        distance_fee = distance * 0.1  # $0.1 per km
        return base_fee + distance_fee
    
    async def _check_shipment_consensus(self, shipment_id: str) -> Dict[str, Any]:
        """Check if consensus reached for shipment approval"""
        votes_cursor = self.database.consensus_votes.find({"shipment_id": shipment_id})
        votes = await votes_cursor.to_list(length=None)
        
        if len(votes) < 3:  # Minimum votes required
            return {"reached": False}
        
        approve_count = sum(1 for vote in votes if vote["approve"])
        approval_rate = approve_count / len(votes)
        
        if approval_rate >= 0.66:  # 66% threshold
            # Update shipment status
            await self.database.shipments.update_one(
                {"shipment_id": shipment_id},
                {"$set": {"status": "approved", "consensus_reached_at": time.time()}}
            )
            return {"reached": True, "result": "approved"}
        elif len(votes) >= 5 and approval_rate < 0.34:  # Clear rejection
            await self.database.shipments.update_one(
                {"shipment_id": shipment_id},
                {"$set": {"status": "rejected", "consensus_reached_at": time.time()}}
            )
            return {"reached": True, "result": "rejected"}
        
        return {"reached": False}
    
    async def _award_transport_incentive(self, transporter: str, shipment: Dict[str, Any]) -> Dict[str, Any]:
        """Award transport incentive for on-time delivery"""
        try:
            base_incentive = shipment.get("transport_fee", 0) * 0.1  # 10% of transport fee
            
            payment_record = {
                "recipient": transporter,
                "type": "transport_incentive",
                "amount": base_incentive,
                "shipment_id": shipment.get("shipment_id"),
                "timestamp": time.time(),
                "chain": "transporter"
            }
            
            await self.database.incentive_payments.insert_one(payment_record)
            
            return {"success": True, "amount": base_incentive}
            
        except Exception as e:
            print(f"❌ Transport incentive error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _assign_arbitrators(self) -> List[str]:
        """Assign arbitrators for dispute resolution"""
        # Get available arbitrators
        arbitrators_cursor = self.database.participants.find(
            {"participant_type": "arbitrator", "status": "active"}
        ).limit(3)
        
        arbitrators = []
        async for arbitrator in arbitrators_cursor:
            arbitrators.append(arbitrator.get("address", ""))
        
        return arbitrators
    
    async def _release_purchase_payment(self, purchase_id: str) -> Dict[str, Any]:
        """Release payment to seller after delivery confirmation"""
        try:
            purchase = await self.database.purchases.find_one({"purchase_id": purchase_id})
            if not purchase:
                return {"success": False, "error": "Purchase not found"}
            
            # Update purchase status
            await self.database.purchases.update_one(
                {"purchase_id": purchase_id},
                {
                    "$set": {
                        "status": "completed",
                        "payment_released": True,
                        "payment_released_at": time.time()
                    }
                }
            )
            
            # Record payment transaction
            payment_record = {
                "purchase_id": purchase_id,
                "seller": purchase.get("seller"),
                "buyer": purchase.get("buyer"),
                "amount": purchase.get("price"),
                "type": "purchase_payment",
                "timestamp": time.time(),
                "chain": "buyer"
            }
            
            await self.database.payments.insert_one(payment_record)
            
            return {"success": True, "amount": purchase.get("price")}
            
        except Exception as e:
            print(f"❌ Payment release error: {e}")
            return {"success": False, "error": str(e)}
    
    # ==========================================
    # PUBLIC API METHODS
    # ==========================================
    
    async def get_chain_stats(self) -> Dict[str, Any]:
        """Get statistics for all chains"""
        try:
            stats = {}
            
            # Hub chain stats
            products_count = await self.database.products.count_documents({})
            participants_count = await self.database.participants.count_documents({})
            
            stats["hub"] = {
                "name": self.chain_configs["hub"]["name"],
                "products": products_count,
                "participants": participants_count,
                "connected": bool(self.hub_web3 and self.hub_web3.is_connected())
            }
            
            # Manufacturer chain stats
            manufacturer_products = await self.database.products.count_documents({"chain": "manufacturer"})
            quality_checks = await self.database.quality_checks.count_documents({})
            
            stats["manufacturer"] = {
                "name": self.chain_configs["manufacturer"]["name"],
                "products": manufacturer_products,
                "quality_checks": quality_checks,
                "connected": bool(self.manufacturer_web3)
            }
            
            # Transporter chain stats
            shipments = await self.database.shipments.count_documents({})
            consensus_votes = await self.database.consensus_votes.count_documents({})
            
            stats["transporter"] = {
                "name": self.chain_configs["transporter"]["name"],
                "shipments": shipments,
                "consensus_votes": consensus_votes,
                "connected": bool(self.transporter_web3)
            }
            
            # Buyer chain stats
            listings = await self.database.marketplace_listings.count_documents({})
            purchases = await self.database.purchases.count_documents({})
            disputes = await self.database.disputes.count_documents({})
            
            stats["buyer"] = {
                "name": self.chain_configs["buyer"]["name"],
                "marketplace_listings": listings,
                "purchases": purchases,
                "disputes": disputes,
                "connected": bool(self.buyer_web3)
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return {"error": str(e)}

# Global instance
multichain_service = MultiChainService()