"""
Algorithm 5: Post Supply Chain Management API Routes
Provides comprehensive marketplace endpoints for secondary NFT product trading
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.post_supply_chain_service import post_supply_chain_service

router = APIRouter()

# Request/Response Models
class MarketplaceListingCreate(BaseModel):
    product_id: str
    seller_address: str
    listing_price: float = Field(gt=0)
    currency: str = Field(default="ETH")
    condition: str = Field(pattern="^(new|like_new|good|fair|poor)$")
    description: str = Field(max_length=1000)
    images: List[str] = Field(default=[])
    delivery_method: str = Field(default="physical")
    location: Optional[str] = None

class MarketplaceListingResponse(BaseModel):
    listing_id: str
    product_id: str
    seller_address: str
    listing_price: float
    currency: str
    condition: str
    description: str
    images: List[str]
    created_at: datetime
    updated_at: datetime
    status: str
    delivery_method: str
    location: Optional[str]
    authenticity_verified: bool
    transfer_history: List[Dict]

class OwnershipTransferRequest(BaseModel):
    listing_id: str
    buyer_address: str
    offered_price: float = Field(gt=0)
    use_escrow: bool = Field(default=True)
    payment_method: str = Field(default="ETH")

class ListingStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|sold|cancelled|expired)$")
    notes: Optional[str] = None

class MarketplaceFilters(BaseModel):
    product_type: Optional[str] = None
    condition: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: Optional[str] = None
    location: Optional[str] = None
    authenticity_verified: Optional[bool] = None
    seller_address: Optional[str] = None

# Marketplace Listing Endpoints
@router.post("/marketplace/list", response_model=Dict[str, Any])
async def create_marketplace_listing(
    listing_data: MarketplaceListingCreate
):
    """
    Create a new marketplace listing for a delivered NFT product
    
    Algorithm 5: Post Supply Chain Management - Marketplace Listing
    """
    try:
        # Validate product ownership and delivery status
        product_info = await post_supply_chain_service.validate_product_for_listing(
            listing_data.product_id,
            listing_data.seller_address
        )
        
        if not product_info["can_list"]:
            raise HTTPException(
                status_code=400,
                detail=f"Product cannot be listed: {product_info['reason']}"
            )
        
        # Create marketplace listing
        listing_result = await post_supply_chain_service.create_marketplace_listing(
            product_id=listing_data.product_id,
            seller_address=listing_data.seller_address,
            listing_price=listing_data.listing_price,
            currency=listing_data.currency,
            condition=listing_data.condition,
            description=listing_data.description,
            images=listing_data.images,
            delivery_method=listing_data.delivery_method,
            location=listing_data.location
        )
        
        return {
            "success": True,
            "listing_id": listing_result["listing_id"],
            "status": "active",
            "estimated_value": listing_result.get("estimated_value"),
            "market_analysis": listing_result.get("market_analysis"),
            "listing_fee": listing_result.get("listing_fee", 0),
            "message": "Marketplace listing created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create listing: {str(e)}")

@router.get("/marketplace/listings", response_model=Dict[str, Any])
async def browse_marketplace_listings(
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    product_type: Optional[str] = None,
    condition: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    currency: Optional[str] = None,
    location: Optional[str] = None,
    authenticity_verified: Optional[bool] = None
):
    """
    Browse marketplace listings with advanced filtering and sorting
    
    Algorithm 5: Post Supply Chain Management - Marketplace Browse
    """
    try:
        # Build filter criteria
        filters = {}
        if product_type:
            filters["product_type"] = product_type
        if condition:
            filters["condition"] = condition
        if price_min is not None or price_max is not None:
            filters["price_range"] = {"min": price_min, "max": price_max}
        if currency:
            filters["currency"] = currency
        if location:
            filters["location"] = location
        if authenticity_verified is not None:
            filters["authenticity_verified"] = authenticity_verified
        
        # Get marketplace listings
        listings_result = await post_supply_chain_service.get_marketplace_listings(
            filters=filters,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            "success": True,
            "listings": listings_result["listings"],
            "pagination": {
                "current_page": page,
                "total_pages": listings_result["total_pages"],
                "total_listings": listings_result["total_count"],
                "has_next": listings_result["has_next"],
                "has_previous": listings_result["has_previous"]
            },
            "filters_applied": filters,
            "market_stats": listings_result.get("market_stats", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to browse listings: {str(e)}")

@router.post("/marketplace/transfer", response_model=Dict[str, Any])
async def initiate_ownership_transfer(
    transfer_request: OwnershipTransferRequest
):
    """
    Initiate ownership transfer for a marketplace listing
    
    Algorithm 5: Post Supply Chain Management - Ownership Transfer
    """
    try:
        # Validate transfer request
        validation_result = await post_supply_chain_service.validate_transfer_request(
            transfer_request.listing_id,
            transfer_request.buyer_address,
            transfer_request.offered_price
        )
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Transfer not valid: {validation_result['reason']}"
            )
        
        # Initiate ownership transfer
        transfer_result = await post_supply_chain_service.initiate_ownership_transfer(
            listing_id=transfer_request.listing_id,
            buyer_address=transfer_request.buyer_address,
            offered_price=transfer_request.offered_price,
            use_escrow=transfer_request.use_escrow,
            payment_method=transfer_request.payment_method
        )
        
        return {
            "success": True,
            "transfer_id": transfer_result["transfer_id"],
            "escrow_address": transfer_result.get("escrow_address"),
            "required_confirmations": transfer_result.get("required_confirmations", 3),
            "estimated_completion": transfer_result.get("estimated_completion"),
            "transfer_fee": transfer_result.get("transfer_fee"),
            "platform_fee": transfer_result.get("platform_fee"),
            "total_cost": transfer_result.get("total_cost"),
            "status": "pending",
            "message": "Ownership transfer initiated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate transfer: {str(e)}")

# Product Valuation and History
@router.get("/marketplace/product/{product_id}/valuation", response_model=Dict[str, Any])
async def get_product_valuation(
    product_id: str
):
    """
    Get comprehensive product valuation for marketplace pricing
    
    Algorithm 5: Post Supply Chain Management - Product Valuation
    """
    try:
        valuation_result = await post_supply_chain_service.calculate_product_valuation(
            product_id=product_id
        )
        
        return {
            "success": True,
            "product_id": product_id,
            "current_valuation": valuation_result["current_value"],
            "valuation_range": valuation_result["value_range"],
            "factors": {
                "condition_score": valuation_result["condition_score"],
                "rarity_score": valuation_result["rarity_score"],
                "market_demand": valuation_result["market_demand"],
                "brand_reputation": valuation_result["brand_reputation"],
                "age_factor": valuation_result["age_factor"],
                "authenticity_premium": valuation_result["authenticity_premium"]
            },
            "comparable_sales": valuation_result.get("comparable_sales", []),
            "market_trends": valuation_result.get("market_trends", {}),
            "recommendation": valuation_result.get("pricing_recommendation"),
            "confidence_level": valuation_result.get("confidence_level", "medium")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get valuation: {str(e)}")

@router.get("/marketplace/product/{product_id}/history", response_model=Dict[str, Any])
async def get_product_resale_history(
    product_id: str
):
    """
    Get complete resale history for a product
    
    Algorithm 5: Post Supply Chain Management - Resale History
    """
    try:
        history_result = await post_supply_chain_service.get_product_resale_history(
            product_id=product_id
        )
        
        return {
            "success": True,
            "product_id": product_id,
            "total_transactions": history_result["transaction_count"],
            "transaction_history": history_result["transactions"],
            "ownership_chain": history_result["ownership_chain"],
            "price_history": history_result["price_evolution"],
            "average_holding_period": history_result.get("avg_holding_period"),
            "total_value_transferred": history_result.get("total_value"),
            "authenticity_verifications": history_result.get("verification_history", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

# User Activity and Analytics
@router.get("/marketplace/user/{user_address}/activity", response_model=Dict[str, Any])
async def get_user_marketplace_activity(
    user_address: str,
    activity_type: Optional[str] = None,  # "purchases", "sales", "listings"
    limit: int = 50
):
    """
    Get user's marketplace activity history
    
    Algorithm 5: Post Supply Chain Management - User Activity
    """
    try:
        activity_result = await post_supply_chain_service.get_user_activity(
            user_address=user_address,
            activity_type=activity_type,
            limit=limit
        )
        
        return {
            "success": True,
            "user_address": user_address,
            "activity_summary": {
                "total_purchases": activity_result["stats"]["total_purchases"],
                "total_sales": activity_result["stats"]["total_sales"],
                "active_listings": activity_result["stats"]["active_listings"],
                "total_value_bought": activity_result["stats"]["total_value_bought"],
                "total_value_sold": activity_result["stats"]["total_value_sold"],
                "reputation_score": activity_result["stats"]["reputation_score"]
            },
            "recent_activity": activity_result["activities"],
            "performance_metrics": activity_result.get("performance_metrics", {}),
            "user_rating": activity_result.get("user_rating", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity: {str(e)}")

@router.get("/marketplace/analytics", response_model=Dict[str, Any])
async def get_marketplace_analytics(
    time_range_days: int = 30
):
    """
    Get comprehensive marketplace analytics and insights
    
    Algorithm 5: Post Supply Chain Management - Analytics Dashboard
    """
    try:
        analytics_result = await post_supply_chain_service.get_marketplace_analytics(
            time_range_days=time_range_days
        )
        
        return {
            "success": True,
            "time_range_days": time_range_days,
            "marketplace_overview": {
                "total_listings": analytics_result["total_listings"],
                "active_listings": analytics_result["active_listings"],
                "completed_sales": analytics_result["completed_sales"],
                "total_volume": analytics_result["total_volume"],
                "average_sale_price": analytics_result["avg_sale_price"],
                "unique_buyers": analytics_result["unique_buyers"],
                "unique_sellers": analytics_result["unique_sellers"]
            },
            "category_breakdown": analytics_result.get("category_stats", {}),
            "price_trends": analytics_result.get("price_trends", []),
            "popular_products": analytics_result.get("popular_products", []),
            "market_health": {
                "liquidity_score": analytics_result.get("liquidity_score", 0),
                "price_stability": analytics_result.get("price_stability", 0),
                "seller_satisfaction": analytics_result.get("seller_satisfaction", 0),
                "buyer_satisfaction": analytics_result.get("buyer_satisfaction", 0)
            },
            "platform_metrics": {
                "platform_fees_collected": analytics_result.get("platform_fees", 0),
                "successful_transfer_rate": analytics_result.get("success_rate", 0),
                "average_time_to_sale": analytics_result.get("avg_time_to_sale")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

# Listing Management
@router.put("/marketplace/listing/{listing_id}/status", response_model=Dict[str, Any])
async def update_listing_status(
    listing_id: str,
    status_update: ListingStatusUpdate
):
    """
    Update marketplace listing status
    
    Algorithm 5: Post Supply Chain Management - Listing Management
    """
    try:
        update_result = await post_supply_chain_service.update_listing_status(
            listing_id=listing_id,
            new_status=status_update.status,
            notes=status_update.notes
        )
        
        if not update_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Status update failed: {update_result['reason']}"
            )
        
        return {
            "success": True,
            "listing_id": listing_id,
            "previous_status": update_result["previous_status"],
            "current_status": status_update.status,
            "updated_at": update_result["updated_at"],
            "message": "Listing status updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")

# Health Check
@router.get("/marketplace/health", response_model=Dict[str, Any])
async def marketplace_health_check():
    """
    Health check for marketplace service
    
    Algorithm 5: Post Supply Chain Management - Health Check
    """
    try:
        health_result = await post_supply_chain_service.health_check()
        
        return {
            "service": "Post Supply Chain Management (Algorithm 5)",
            "status": "healthy" if health_result["healthy"] else "unhealthy",
            "version": "1.0.0",
            "features": [
                "Secondary marketplace for delivered NFT products",
                "Ownership transfer mechanisms with escrow protection",
                "Product history tracking for resales",
                "Advanced value assessment algorithms",
                "Marketplace listing management",
                "User activity tracking and analytics",
                "Platform fee collection (2.5%)",
                "Condition-based pricing and rarity scoring"
            ],
            "database_status": health_result.get("database", "unknown"),
            "service_dependencies": {
                "blockchain_service": health_result.get("blockchain_service", "unknown"),
                "ipfs_service": health_result.get("ipfs_service", "unknown")
            },
            "marketplace_stats": health_result.get("marketplace_stats", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "service": "Post Supply Chain Management (Algorithm 5)",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }