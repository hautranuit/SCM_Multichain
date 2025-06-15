"""
Algorithm 5: Post Supply Chain Management Service
Implements secondary marketplace for delivered NFT products
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import uuid
import math
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorDatabase

from .blockchain_service import blockchain_service
from .ipfs_service import ipfs_service


@dataclass
class MarketplaceListing:
    listing_id: str
    product_id: str
    seller_address: str
    listing_price: float
    currency: str  # "ETH", "USDC", etc.
    condition: str  # "new", "like_new", "good", "fair", "poor"
    description: str
    images: List[str]  # IPFS CIDs for additional images
    created_at: datetime
    updated_at: datetime
    status: str  # "active", "sold", "cancelled", "expired"
    delivery_method: str  # "physical", "digital", "pickup"
    location: Optional[str]
    authenticity_verified: bool
    transfer_history: List[Dict]


@dataclass
class OwnershipTransfer:
    transfer_id: str
    product_id: str
    from_address: str
    to_address: str
    transaction_hash: str
    transfer_price: float
    transfer_fee: float
    escrow_used: bool
    completed_at: datetime
    verification_status: str


@dataclass
class ProductValuation:
    product_id: str
    current_estimated_value: float
    valuation_factors: Dict
    market_demand_score: float
    condition_score: float
    rarity_score: float
    historical_prices: List[Dict]
    last_updated: datetime


class PostSupplyChainService:
    """
    Algorithm 5: Post Supply Chain Management
    
    Features:
    1. Secondary marketplace for delivered NFT products
    2. Ownership transfer mechanisms with escrow
    3. Product history tracking for resales
    4. Value assessment algorithms
    5. Authenticity verification for resales
    6. Digital marketplace integration
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.database: Optional[AsyncIOMotorDatabase] = None
        
        # Marketplace configuration
        self.platform_fee_percentage = 0.025  # 2.5% platform fee on sales
        self.escrow_duration_days = 7  # Escrow period for transfers
        self.authenticity_verification_required = True
        
        # Valuation factors weights
        self.valuation_weights = {
            "condition": 0.3,
            "rarity": 0.25,
            "market_demand": 0.2,
            "brand_reputation": 0.15,
            "age": 0.1
        }
        
        # Transfer security settings
        self.require_identity_verification = True
        self.max_transfer_value_without_kyc = 1000.0  # USD equivalent
        
    async def initialize(self):
        """Initialize the post supply chain service"""
        try:
            self.database = await self.get_database()
            await self._ensure_collections()
            self.logger.info("✅ Post Supply Chain Management Service initialized")
        except Exception as e:
            self.logger.error(f"❌ Post supply chain service initialization failed: {e}")
            raise
    
    async def get_database(self):
        """Get database instance"""
        if blockchain_service.database is not None:
            return blockchain_service.database
        return None
    
    async def _ensure_collections(self):
        """Ensure required database collections exist"""
        collections = [
            "marketplace_listings",
            "ownership_transfers", 
            "product_valuations",
            "resale_history",
            "marketplace_transactions",
            "product_condition_reports"
        ]
        
        for collection in collections:
            await self.database[collection].create_index("timestamp")
            
        # Create specific indexes
        await self.database["marketplace_listings"].create_index("product_id")
        await self.database["marketplace_listings"].create_index("seller_address") 
        await self.database["marketplace_listings"].create_index("status")
        await self.database["ownership_transfers"].create_index("product_id")
        await self.database["product_valuations"].create_index("product_id")
    
    # === SECONDARY MARKETPLACE FUNCTIONALITY ===
    
    async def create_marketplace_listing(
        self,
        product_id: str,
        seller_address: str,
        listing_price: float,
        currency: str = "ETH",
        condition: str = "good",
        description: str = "",
        delivery_method: str = "physical",
        location: str = "",
        additional_images: List[str] = None
    ) -> Dict:
        """
        Create a new marketplace listing for a delivered product
        """
        try:
            self.logger.info(f"🛍️ Creating marketplace listing for product: {product_id}")
            
            # Verify product ownership and delivery status
            ownership_verification = await self._verify_listing_eligibility(product_id, seller_address)
            if not ownership_verification["eligible"]:
                return {
                    "success": False,
                    "error": ownership_verification["reason"],
                    "error_code": "LISTING_NOT_ELIGIBLE"
                }
            
            # Verify product authenticity before listing
            if self.authenticity_verification_required:
                authenticity_check = await self._verify_product_for_resale(product_id, seller_address)
                if not authenticity_check["authentic"]:
                    return {
                        "success": False,
                        "error": "Product authenticity verification failed",
                        "error_code": "AUTHENTICITY_FAILED",
                        "details": authenticity_check
                    }
            
            # Create listing
            listing = MarketplaceListing(
                listing_id=f"LISTING-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}",
                product_id=product_id,
                seller_address=seller_address,
                listing_price=listing_price,
                currency=currency,
                condition=condition,
                description=description,
                images=additional_images or [],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status="active",
                delivery_method=delivery_method,
                location=location,
                authenticity_verified=self.authenticity_verification_required,
                transfer_history=[]
            )
            
            # Store in database
            await self.database["marketplace_listings"].insert_one({
                **listing.__dict__,
                "ownership_verification": ownership_verification,
                "valuation_estimate": await self._calculate_product_valuation(product_id)
            })
            
            # Update product status to "listed_for_sale"
            await self._update_product_marketplace_status(product_id, "listed_for_sale", listing.listing_id)
            
            self.logger.info(f"✅ Marketplace listing created: {listing.listing_id}")
            
            return {
                "success": True,
                "listing_id": listing.listing_id,
                "listing_details": listing.__dict__,
                "estimated_fees": {
                    "platform_fee": listing_price * self.platform_fee_percentage,
                    "seller_receives": listing_price * (1 - self.platform_fee_percentage)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Marketplace listing creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _verify_listing_eligibility(self, product_id: str, seller_address: str) -> Dict:
        """Verify if a product can be listed for sale"""
        try:
            # Get product information
            product = await blockchain_service.get_product_by_token_id(product_id)
            if not product:
                return {"eligible": False, "reason": "Product not found"}
            
            # Check if product has been delivered
            delivery_status = product.get("delivery_status", "")
            if delivery_status != "delivered":
                return {"eligible": False, "reason": "Product has not been delivered yet"}
            
            # Check current ownership
            current_owner = product.get("current_owner", "")
            if current_owner.lower() != seller_address.lower():
                return {"eligible": False, "reason": "Seller is not the current owner"}
            
            # Check if already listed
            existing_listing = await self.database["marketplace_listings"].find_one({
                "product_id": product_id,
                "status": "active"
            })
            if existing_listing:
                return {"eligible": False, "reason": "Product is already listed for sale"}
            
            # Check for any pending transfers
            pending_transfer = await self.database["ownership_transfers"].find_one({
                "product_id": product_id,
                "status": "pending"
            })
            if pending_transfer:
                return {"eligible": False, "reason": "Product has a pending ownership transfer"}
            
            return {
                "eligible": True,
                "product_details": {
                    "name": product.get("name", ""),
                    "manufacturer": product.get("manufacturer", ""),
                    "delivery_date": product.get("delivery_confirmation_date", ""),
                    "current_condition": product.get("condition", "unknown")
                }
            }
            
        except Exception as e:
            return {"eligible": False, "reason": f"Verification error: {str(e)}"}
    
    async def _verify_product_for_resale(self, product_id: str, seller_address: str) -> Dict:
        """Verify product authenticity for resale"""
        try:
            # Get latest product data for QR verification
            product = await blockchain_service.get_product_by_token_id(product_id)
            if not product:
                return {"authentic": False, "reason": "Product not found"}
            
            # Simulate QR data retrieval (in real implementation, this would come from the seller)
            qr_data = product.get("qr_data", {})
            
            # Use Algorithm 4 for verification
            verification_context = {
                "resale_verification": True,
                "return_detailed": True
            }
            
            verification_result = await blockchain_service.verify_product_authenticity(
                product_id, qr_data, seller_address, verification_context
            )
            
            if isinstance(verification_result, dict):
                return {
                    "authentic": verification_result.get("authentic", False),
                    "verification_details": verification_result
                }
            else:
                # Handle string response (backward compatibility)
                return {
                    "authentic": verification_result == "Product is Authentic",
                    "verification_message": verification_result
                }
                
        except Exception as e:
            return {"authentic": False, "reason": f"Verification error: {str(e)}"}
    
    # === OWNERSHIP TRANSFER MECHANISMS ===
    
    async def initiate_ownership_transfer(
        self,
        listing_id: str,
        buyer_address: str,
        agreed_price: float,
        payment_method: str = "crypto",
        use_escrow: bool = True
    ) -> Dict:
        """
        Initiate ownership transfer for a marketplace purchase
        """
        try:
            self.logger.info(f"🔄 Initiating ownership transfer for listing: {listing_id}")
            
            # Get listing details
            listing = await self.database["marketplace_listings"].find_one({"listing_id": listing_id})
            if not listing:
                return {"success": False, "error": "Listing not found"}
            
            if listing["status"] != "active":
                return {"success": False, "error": f"Listing is not active (status: {listing['status']})"}
            
            # Verify buyer is not the seller
            if buyer_address.lower() == listing["seller_address"].lower():
                return {"success": False, "error": "Buyer cannot be the same as seller"}
            
            # Check if price matches
            if agreed_price != listing["listing_price"]:
                return {"success": False, "error": "Agreed price does not match listing price"}
            
            # Calculate fees
            platform_fee = agreed_price * self.platform_fee_percentage
            seller_receives = agreed_price - platform_fee
            
            # Create ownership transfer record
            transfer = OwnershipTransfer(
                transfer_id=f"TRANSFER-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}",
                product_id=listing["product_id"],
                from_address=listing["seller_address"],
                to_address=buyer_address,
                transaction_hash="",  # Will be filled when blockchain transaction completes
                transfer_price=agreed_price,
                transfer_fee=platform_fee,
                escrow_used=use_escrow,
                completed_at=datetime.utcnow(),
                verification_status="pending"
            )
            
            # Execute blockchain transfer
            if use_escrow:
                blockchain_result = await self._execute_escrow_transfer(transfer, listing)
            else:
                blockchain_result = await self._execute_direct_transfer(transfer, listing)
            
            if not blockchain_result["success"]:
                return {
                    "success": False,
                    "error": "Blockchain transfer failed",
                    "details": blockchain_result
                }
            
            # Update transfer with transaction hash
            transfer.transaction_hash = blockchain_result["transaction_hash"]
            transfer.verification_status = "completed"
            
            # Store transfer record
            await self.database["ownership_transfers"].insert_one({
                **transfer.__dict__,
                "blockchain_details": blockchain_result,
                "payment_method": payment_method
            })
            
            # Update listing status
            await self.database["marketplace_listings"].update_one(
                {"listing_id": listing_id},
                {
                    "$set": {
                        "status": "sold",
                        "sold_at": datetime.utcnow(),
                        "buyer_address": buyer_address,
                        "final_price": agreed_price
                    }
                }
            )
            
            # Update product ownership
            await self._update_product_ownership(listing["product_id"], buyer_address, transfer.__dict__)
            
            # Record in resale history
            await self._record_resale_transaction(listing, transfer.__dict__)
            
            self.logger.info(f"✅ Ownership transfer completed: {transfer.transfer_id}")
            
            return {
                "success": True,
                "transfer_id": transfer.transfer_id,
                "transaction_hash": transfer.transaction_hash,
                "transfer_details": transfer.__dict__,
                "fees": {
                    "platform_fee": platform_fee,
                    "seller_receives": seller_receives
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ownership transfer failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_escrow_transfer(self, transfer: OwnershipTransfer, listing: Dict) -> Dict:
        """Execute ownership transfer with escrow protection"""
        try:
            # In real implementation, this would call escrow smart contracts
            # For now, simulate the blockchain transaction
            mock_tx_hash = f"0x{uuid.uuid4().hex}"
            
            self.logger.info(f"🔐 Executing escrow transfer: {transfer.transfer_price} from {transfer.to_address}")
            
            # Simulate escrow contract interaction
            escrow_result = {
                "escrow_contract": "0x1234567890123456789012345678901234567890",
                "escrow_amount": transfer.transfer_price,
                "escrow_duration": self.escrow_duration_days,
                "release_conditions": [
                    "buyer_confirmation",
                    "authenticity_verification",
                    "dispute_resolution"
                ]
            }
            
            return {
                "success": True,
                "transaction_hash": mock_tx_hash,
                "escrow_details": escrow_result,
                "estimated_completion": (datetime.utcnow() + timedelta(days=self.escrow_duration_days)).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Escrow transfer failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_direct_transfer(self, transfer: OwnershipTransfer, listing: Dict) -> Dict:
        """Execute direct ownership transfer without escrow"""
        try:
            # In real implementation, this would call NFT transfer functions
            mock_tx_hash = f"0x{uuid.uuid4().hex}"
            
            self.logger.info(f"🚀 Executing direct transfer: {transfer.product_id} to {transfer.to_address}")
            
            return {
                "success": True,
                "transaction_hash": mock_tx_hash,
                "transfer_type": "direct",
                "completed_immediately": True
            }
            
        except Exception as e:
            self.logger.error(f"❌ Direct transfer failed: {e}")
            return {"success": False, "error": str(e)}
    
    # === PRODUCT VALUATION ALGORITHMS ===
    
    async def _calculate_product_valuation(self, product_id: str) -> Dict:
        """
        Calculate estimated market value for a product
        Algorithm 5: Value Assessment Algorithm
        """
        try:
            self.logger.info(f"💰 Calculating valuation for product: {product_id}")
            
            # Get product information
            product = await blockchain_service.get_product_by_token_id(product_id)
            if not product:
                return {"error": "Product not found"}
            
            # Get historical pricing data
            historical_prices = await self._get_historical_prices(product_id)
            
            # Calculate valuation factors
            valuation_factors = {
                "condition_score": await self._calculate_condition_score(product),
                "rarity_score": await self._calculate_rarity_score(product),
                "market_demand_score": await self._calculate_market_demand_score(product),
                "brand_reputation_score": await self._calculate_brand_reputation_score(product),
                "age_depreciation_factor": await self._calculate_age_depreciation(product)
            }
            
            # Base value calculation
            original_price = float(product.get("original_price", 0))
            base_value = original_price if original_price > 0 else 100.0  # Default fallback
            
            # Apply valuation factors
            estimated_value = base_value
            for factor, weight in self.valuation_weights.items():
                factor_score = valuation_factors.get(f"{factor}_score", 1.0)
                estimated_value *= (1 + (factor_score - 1.0) * weight)
            
            # Market adjustment based on recent sales
            market_adjustment = await self._calculate_market_adjustment(product, historical_prices)
            estimated_value *= market_adjustment
            
            # Create valuation object
            valuation = ProductValuation(
                product_id=product_id,
                current_estimated_value=round(estimated_value, 2),
                valuation_factors=valuation_factors,
                market_demand_score=valuation_factors["market_demand_score"],
                condition_score=valuation_factors["condition_score"],
                rarity_score=valuation_factors["rarity_score"],
                historical_prices=historical_prices,
                last_updated=datetime.utcnow()
            )
            
            # Store valuation in database
            await self.database["product_valuations"].replace_one(
                {"product_id": product_id},
                valuation.__dict__,
                upsert=True
            )
            
            self.logger.info(f"✅ Valuation calculated: {estimated_value} for {product_id}")
            
            return valuation.__dict__
            
        except Exception as e:
            self.logger.error(f"❌ Valuation calculation failed: {e}")
            return {"error": str(e)}
    
    async def _calculate_condition_score(self, product: Dict) -> float:
        """Calculate condition score (0.5 to 1.5)"""
        condition = product.get("condition", "good").lower()
        condition_scores = {
            "new": 1.5,
            "like_new": 1.3,
            "excellent": 1.2,
            "good": 1.0,
            "fair": 0.8,
            "poor": 0.5
        }
        return condition_scores.get(condition, 1.0)
    
    async def _calculate_rarity_score(self, product: Dict) -> float:
        """Calculate rarity score based on product uniqueness"""
        try:
            # Check how many similar products exist
            manufacturer = product.get("manufacturer", "")
            product_type = product.get("product_type", "")
            
            similar_products_count = await blockchain_service.database.products.count_documents({
                "manufacturer": manufacturer,
                "product_type": product_type
            })
            
            # Lower count = higher rarity
            if similar_products_count <= 1:
                return 2.0  # Very rare
            elif similar_products_count <= 5:
                return 1.5  # Rare
            elif similar_products_count <= 20:
                return 1.2  # Uncommon
            else:
                return 1.0  # Common
                
        except Exception:
            return 1.0  # Default score
    
    async def _calculate_market_demand_score(self, product: Dict) -> float:
        """Calculate market demand based on recent activity"""
        try:
            product_id = product.get("token_id", "")
            
            # Count recent verifications (indicates interest)
            recent_verifications = await blockchain_service.database.verification_history.count_documents({
                "product_id": product_id,
                "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}
            })
            
            # Count marketplace views (if available)
            marketplace_views = await self.database["marketplace_listings"].count_documents({
                "product_id": product_id
            })
            
            # Calculate demand score
            demand_score = 1.0 + (recent_verifications * 0.1) + (marketplace_views * 0.05)
            return min(demand_score, 2.0)  # Cap at 2.0
            
        except Exception:
            return 1.0
    
    async def _calculate_brand_reputation_score(self, product: Dict) -> float:
        """Calculate brand reputation score"""
        manufacturer = product.get("manufacturer", "").lower()
        
        # Brand reputation mapping (in real implementation, this would be more sophisticated)
        brand_scores = {
            "apple": 1.3,
            "samsung": 1.2,
            "nike": 1.2,
            "adidas": 1.15,
            "sony": 1.1,
            "microsoft": 1.1
        }
        
        # Check if manufacturer matches any known brands
        for brand, score in brand_scores.items():
            if brand in manufacturer:
                return score
        
        return 1.0  # Default score for unknown brands
    
    async def _calculate_age_depreciation(self, product: Dict) -> float:
        """Calculate age depreciation factor"""
        try:
            created_date = product.get("created_at")
            if not created_date:
                return 1.0
            
            if isinstance(created_date, str):
                created_date = datetime.fromisoformat(created_date)
            
            age_months = (datetime.utcnow() - created_date).days / 30.44
            
            # Depreciation curve: 5% per month for first 6 months, then 2% per month
            if age_months <= 6:
                depreciation = max(0.7, 1.0 - (age_months * 0.05))
            else:
                initial_depreciation = 0.7  # After 6 months
                additional_months = age_months - 6
                depreciation = max(0.5, initial_depreciation - (additional_months * 0.02))
            
            return depreciation
            
        except Exception:
            return 1.0
    
    # === MARKETPLACE QUERIES AND ANALYTICS ===
    
    async def get_marketplace_listings(
        self,
        filter_params: Dict = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0
    ) -> Dict:
        """Get marketplace listings with filtering and pagination"""
        try:
            # Build query filter
            query_filter = {"status": "active"}
            if filter_params:
                if filter_params.get("seller_address"):
                    query_filter["seller_address"] = filter_params["seller_address"]
                if filter_params.get("min_price"):
                    query_filter["listing_price"] = {"$gte": filter_params["min_price"]}
                if filter_params.get("max_price"):
                    if "listing_price" in query_filter:
                        query_filter["listing_price"]["$lte"] = filter_params["max_price"]
                    else:
                        query_filter["listing_price"] = {"$lte": filter_params["max_price"]}
                if filter_params.get("condition"):
                    query_filter["condition"] = filter_params["condition"]
                if filter_params.get("currency"):
                    query_filter["currency"] = filter_params["currency"]
            
            # Build sort criteria
            sort_direction = -1 if sort_order == "desc" else 1
            sort_criteria = [(sort_by, sort_direction)]
            
            # Execute query
            cursor = self.database["marketplace_listings"].find(query_filter).sort(sort_criteria).skip(offset).limit(limit)
            listings = await cursor.to_list(length=limit)
            
            # Get total count for pagination
            total_count = await self.database["marketplace_listings"].count_documents(query_filter)
            
            return {
                "success": True,
                "listings": listings,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Marketplace listings query failed: {e}")
            return {"success": False, "error": str(e)}
    
    # === HELPER METHODS ===
    
    async def _get_historical_prices(self, product_id: str) -> List[Dict]:
        """Get historical pricing data for a product"""
        try:
            cursor = self.database["ownership_transfers"].find({
                "product_id": product_id,
                "verification_status": "completed"
            }).sort("completed_at", -1).limit(10)
            
            transfers = await cursor.to_list(length=10)
            
            return [
                {
                    "price": transfer["transfer_price"],
                    "date": transfer["completed_at"].isoformat() if hasattr(transfer["completed_at"], "isoformat") else str(transfer["completed_at"]),
                    "currency": transfer.get("currency", "ETH")
                }
                for transfer in transfers
            ]
            
        except Exception:
            return []
    
    async def _calculate_market_adjustment(self, product: Dict, historical_prices: List[Dict]) -> float:
        """Calculate market adjustment factor based on recent sales"""
        if not historical_prices:
            return 1.0
        
        # Simple trend analysis
        if len(historical_prices) >= 2:
            recent_price = historical_prices[0]["price"]
            older_price = historical_prices[-1]["price"]
            
            if older_price > 0:
                trend = recent_price / older_price
                # Limit adjustment to reasonable range
                return max(0.8, min(1.2, trend))
        
        return 1.0
    
    async def _update_product_marketplace_status(self, product_id: str, status: str, listing_id: str = ""):
        """Update product marketplace status"""
        try:
            update_data = {
                "marketplace_status": status,
                "marketplace_updated_at": datetime.utcnow()
            }
            if listing_id:
                update_data["current_listing_id"] = listing_id
            
            await blockchain_service.database.products.update_one(
                {"token_id": product_id},
                {"$set": update_data}
            )
        except Exception as e:
            self.logger.error(f"⚠️ Product status update failed: {e}")
    
    async def _update_product_ownership(self, product_id: str, new_owner: str, transfer_details: Dict):
        """Update product ownership after successful transfer"""
        try:
            await blockchain_service.database.products.update_one(
                {"token_id": product_id},
                {
                    "$set": {
                        "current_owner": new_owner,
                        "ownership_updated_at": datetime.utcnow(),
                        "marketplace_status": "owned"
                    },
                    "$push": {
                        "ownership_history": {
                            "previous_owner": transfer_details["from_address"],
                            "new_owner": new_owner,
                            "transfer_date": transfer_details["completed_at"],
                            "transfer_id": transfer_details["transfer_id"],
                            "price": transfer_details["transfer_price"]
                        }
                    }
                }
            )
        except Exception as e:
            self.logger.error(f"⚠️ Product ownership update failed: {e}")
    
    async def _record_resale_transaction(self, listing: Dict, transfer_details: Dict):
        """Record resale transaction for analytics"""
        try:
            resale_record = {
                "product_id": listing["product_id"],
                "listing_id": listing["listing_id"],
                "seller": listing["seller_address"],
                "buyer": transfer_details["to_address"],
                "sale_price": transfer_details["transfer_price"],
                "original_price": 0,  # Would be fetched from original product data
                "platform_fee": transfer_details["transfer_fee"],
                "sale_date": transfer_details["completed_at"],
                "condition": listing["condition"],
                "days_owned": 0,  # Would be calculated based on previous ownership
                "roi_percentage": 0  # Return on investment for seller
            }
            
            await self.database["resale_history"].insert_one(resale_record)
            
        except Exception as e:
            self.logger.error(f"⚠️ Resale transaction recording failed: {e}")


# Global service instance
post_supply_chain_service = PostSupplyChainService()