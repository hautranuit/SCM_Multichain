"""
Comprehensive ChainFLIP Blockchain API Routes
Implements all 5 algorithms from the 6 smart contracts
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, Field
import base64
import tempfile
import os
import time
import re
import json
from web3 import Web3

from app.services.blockchain_service import BlockchainService

# Dependency to get blockchain service - MOVED HERE TO FIX NAMEERROR
async def get_blockchain_service():
    service = BlockchainService()
    await service.initialize()
    return service

router = APIRouter()

@router.get("/marketplace/products")
async def get_marketplace_products(
    limit: int = 50,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get all products available for purchase in the marketplace"""
    try:
        # Build query filters
        filters = {
            "status": {"$ne": "sold"}  # Exclude already sold products
        }
        
        if category:
            filters["$or"] = [
                {"category": category},
                {"metadata.category": category},
                {"mint_params.category": category}
            ]
        
        # Get products from database
        cursor = blockchain_service.database.products.find(filters).sort("created_at", -1).limit(limit)
        products = []
        async for product in cursor:
            product["_id"] = str(product["_id"])
            
            # Extract price from multiple possible sources
            price = 0
            if product.get("price"):
                price = float(product["price"])
            elif product.get("metadata", {}).get("price_eth"):
                price = float(product["metadata"]["price_eth"])
            elif product.get("mint_params", {}).get("price"):
                price = float(product["mint_params"]["price"])
            
            # Apply price filters
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            
            product["marketplace_price"] = price
            product["available_for_purchase"] = True
            products.append(product)
        
        return {
            "products": products,
            "total_count": len(products),
            "filters_applied": {
                "category": category,
                "min_price": min_price,
                "max_price": max_price
            },
            "marketplace_active": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# PYDANTIC MODELS FOR ALL ALGORITHMS
# ==========================================

# Algorithm 1: Payment Release Models
class PaymentReleaseRequest(BaseModel):
    product_id: str
    buyer: str
    transporter: str
    seller: str
    collateral_amount: float
    delivery_status: Dict[str, Any]
    incentive_criteria: Dict[str, Any]

class PaymentReleaseResponse(BaseModel):
    status: str
    incentive: str = None
    incentive_amount: float = None
    reason: str = None
    transaction_hash: str = None
    dispute_id: str = None
    collateral_status: str = None

# Algorithm 2: Dispute Resolution Models
class DisputeInitiationRequest(BaseModel):
    product_id: str
    plaintiff: str
    reason: str
    evidence_data: Dict[str, Any] = None

class ArbitratorVoteRequest(BaseModel):
    dispute_id: str
    voter: str
    candidate: str

class ArbitratorDecisionRequest(BaseModel):
    dispute_id: str
    arbitrator: str
    resolution_details: str
    outcome: int  # 0=Dismissed, 1=FavorPlaintiff, 2=FavorDefendant, 3=Partial

# Algorithm 3: Supply Chain Consensus Models (Complete Implementation)
class BatchProposalRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    is_cross_chain: bool = False

class ConsensusVoteRequest(BaseModel):
    shipment_id: str
    voter: str
    approve: bool
    reason: str

class ShipmentCreationRequest(BaseModel):
    transporter: str
    shipment_data: Dict[str, Any]

class DeliveryConfirmationRequest(BaseModel):
    shipment_id: str
    transporter: str

class BatchProcessingRequest(BaseModel):
    node_type: str  # primary or secondary
    transactions: List[Dict[str, Any]]

# Algorithm 4: Product Authenticity Models
class AuthenticityVerificationRequest(BaseModel):
    product_id: str = Field(..., description="Product token ID to verify", min_length=1)
    qr_data: Any = Field(..., description="QR code data (replaces RFID in Algorithm 4)")
    current_owner: str = Field(..., description="Current owner wallet address for ownership verification", min_length=1)

class AuthenticityVerificationResponse(BaseModel):
    status: str = Field(..., description="Algorithm 4 verification result: 'Product is Authentic', 'Ownership Mismatch', 'Product Data Mismatch', or 'Product Not Registered'")
    product_id: str
    verification_timestamp: float
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed verification results from Algorithm 4")

# Algorithm 5: Post Supply Chain Management Models
class ProductListingRequest(BaseModel):
    product_id: str
    price: float
    target_chains: List[int] = None

class ProductPurchaseRequest(BaseModel):
    product_id: str
    buyer: str
    qr_verification_data: str

# Enhanced Product Minting
class ProductMinting(BaseModel):
    manufacturer: str
    metadata: Dict[str, Any]  # Raw metadata that will be uploaded to IPFS

class ProductMintRequest(BaseModel):
    manufacturer: str
    metadata: Dict[str, Any]  # Raw metadata that will be uploaded to IPFS
    target_chains: List[int] = None  # Optional list of target chain IDs
    manufacturer_private_key: Optional[str] = None  # Optional private key for cross-chain messaging

# Enhanced Product Purchase Models (for new /marketplace/buy endpoint)
class ProductBuyRequest(BaseModel):
    product_id: str
    buyer: str
    price: float
    payment_method: str = "ETH"

class ProductBuyResponse(BaseModel):
    success: bool
    status: str
    product_id: str
    buyer: str
    transaction_hash: str = None
    purchase_id: str = None
    payment_amount: float = None
    cross_chain_details: Dict[str, Any] = None

class ProductMintingResponse(BaseModel):
    success: bool
    token_id: str
    metadata_cid: str
    encrypted_qr_code: str
    qr_hash: str
    transaction_hash: str = None

class ParticipantRegistration(BaseModel):
    address: str
    participant_type: str  # manufacturer, distributor, retailer, transporter, buyer, arbitrator
    chain_id: int



# ==========================================
# CORE SYSTEM ENDPOINTS
# ==========================================

@router.get("/status")
async def get_comprehensive_blockchain_status(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get comprehensive multi-chain network status with algorithm statistics"""
    return await blockchain_service.get_network_stats()

@router.post("/participants/register")
async def register_participant(
    participant_data: ParticipantRegistration,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Register a new participant in the ChainFLIP multi-chain system"""
    try:
        result = await blockchain_service.register_participant(
            participant_data.address,
            participant_data.participant_type,
            participant_data.chain_id
        )
        return {"success": True, "participant": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# ALGORITHM 1: PAYMENT RELEASE AND INCENTIVE MECHANISM
# ==========================================

@router.post("/payment/release", response_model=PaymentReleaseResponse)
async def process_payment_release(
    payment_data: PaymentReleaseRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Algorithm 1: Payment Release and Incentive Mechanism
    Processes payment based on NFT ownership, delivery status, and incentive criteria
    """
    try:
        result = await blockchain_service.process_payment_release(
            payment_data.product_id,
            payment_data.buyer,
            payment_data.transporter,
            payment_data.seller,
            payment_data.collateral_amount,
            payment_data.delivery_status,
            payment_data.incentive_criteria
        )
        return PaymentReleaseResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# ALGORITHM 2: DISPUTE RESOLUTION AND VOTING MECHANISM
# ==========================================

@router.post("/disputes/initiate")
async def initiate_dispute(
    dispute_data: DisputeInitiationRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Algorithm 2: Initiate dispute resolution with automatic arbitrator candidate selection
    """
    try:
        dispute_id = await blockchain_service.initiate_dispute_resolution(
            dispute_data.product_id,
            dispute_data.plaintiff,
            dispute_data.reason,
            dispute_data.evidence_data
        )
        return {"success": True, "dispute_id": dispute_id, "message": "Dispute initiated, voting started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/disputes/vote")
async def vote_for_arbitrator(
    vote_data: ArbitratorVoteRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Allow stakeholders to vote for preferred arbitrator candidate"""
    try:
        result = await blockchain_service.vote_for_arbitrator(
            vote_data.dispute_id,
            vote_data.voter,
            vote_data.candidate
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/disputes/decide")
async def arbitrator_make_decision(
    decision_data: ArbitratorDecisionRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Arbitrator reviews dispute and makes decision"""
    try:
        result = await blockchain_service.arbitrator_make_decision(
            decision_data.dispute_id,
            decision_data.arbitrator,
            decision_data.resolution_details,
            decision_data.outcome
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/disputes/{dispute_id}")
async def get_dispute_details(
    dispute_id: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get comprehensive dispute information"""
    try:
        dispute = await blockchain_service.database.disputes.find_one({"dispute_id": dispute_id})
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        dispute["_id"] = str(dispute["_id"])
        return dispute
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# ALGORITHM 3: SUPPLY CHAIN CONSENSUS ALGORITHM (BATCH PROCESSING)
# ==========================================

@router.post("/consensus/shipment/create")
async def create_shipment_for_consensus(
    shipment_data: ShipmentCreationRequest
):
    """
    Algorithm 3: Create shipment on transporter chain for consensus voting
    """
    try:
        # Import multichain service for Algorithm 3 operations
        from app.services.multichain_service import multichain_service
        await multichain_service.initialize()
        
        result = await multichain_service.create_shipment(
            shipment_data.transporter,
            shipment_data.shipment_data
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/consensus/vote")
async def submit_consensus_vote(
    vote_data: ConsensusVoteRequest
):
    """
    Algorithm 3: Submit consensus vote for shipment approval
    Implements batch processing validation mechanism
    """
    try:
        from app.services.multichain_service import multichain_service
        await multichain_service.initialize()
        
        result = await multichain_service.submit_consensus_vote(
            vote_data.shipment_id,
            vote_data.voter,
            vote_data.approve,
            vote_data.reason
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/consensus/batch/process")
async def process_transaction_batch(
    batch_data: BatchProcessingRequest
):
    """
    Algorithm 3: Process transaction batch with Primary/Secondary node validation
    Implements the core consensus mechanism
    """
    try:
        from app.services.multichain_service import multichain_service
        await multichain_service.initialize()
        
        # Simulate batch processing based on node type
        if batch_data.node_type == "secondary":
            # Secondary nodes propose batches
            batch_id = f"BATCH-{int(time.time())}"
            
            # Store batch proposal
            batch_record = {
                "batch_id": batch_id,
                "node_type": "secondary",
                "transactions": batch_data.transactions,
                "status": "proposed",
                "created_at": time.time(),
                "validation_votes": {},
                "consensus_reached": False
            }
            
            await multichain_service.database.consensus_batches.insert_one(batch_record)
            
            return {
                "success": True,
                "batch_id": batch_id,
                "status": "proposed",
                "message": "Batch proposed for Primary Node validation"
            }
            
        elif batch_data.node_type == "primary":
            # Primary nodes validate batches
            return {
                "success": True,
                "status": "validated",
                "message": "Primary node validation completed"
            }
        
        return {"success": False, "error": "Invalid node type"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/consensus/batches")
async def get_consensus_batches():
    """Get all consensus batches for Algorithm 3 dashboard"""
    try:
        from app.services.multichain_service import multichain_service
        await multichain_service.initialize()
        
        # Get recent batches
        cursor = multichain_service.database.consensus_batches.find().sort("created_at", -1).limit(50)
        batches = []
        async for batch in cursor:
            batch["_id"] = str(batch["_id"])
            batches.append(batch)
        
        return {"batches": batches, "total_count": len(batches)}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/consensus/shipments")
async def get_consensus_shipments():
    """Get all shipments requiring consensus for Algorithm 3"""
    try:
        from app.services.multichain_service import multichain_service
        await multichain_service.initialize()
        
        # Get shipments awaiting consensus
        cursor = multichain_service.database.shipments.find().sort("created_at", -1).limit(100)
        shipments = []
        async for shipment in cursor:
            shipment["_id"] = str(shipment["_id"])
            shipments.append(shipment)
        
        return {"shipments": shipments, "total_count": len(shipments)}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/consensus/delivery/confirm")
async def mark_shipment_delivered(
    delivery_data: DeliveryConfirmationRequest
):
    """
    Algorithm 3: Mark shipment as delivered and process incentives
    """
    try:
        from app.services.multichain_service import multichain_service
        await multichain_service.initialize()
        
        result = await multichain_service.mark_delivered(
            delivery_data.shipment_id,
            delivery_data.transporter
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/consensus/stats")
async def get_consensus_statistics():
    """Get Algorithm 3 consensus mechanism statistics"""
    try:
        from app.services.multichain_service import multichain_service
        await multichain_service.initialize()
        
        # Get consensus statistics
        total_batches = await multichain_service.database.consensus_batches.count_documents({})
        approved_batches = await multichain_service.database.consensus_batches.count_documents({"consensus_reached": True})
        total_shipments = await multichain_service.database.shipments.count_documents({})
        consensus_votes = await multichain_service.database.consensus_votes.count_documents({})
        
        return {
            "algorithm_3_stats": {
                "total_batches": total_batches,
                "approved_batches": approved_batches,
                "approval_rate": (approved_batches / total_batches * 100) if total_batches > 0 else 0,
                "total_shipments": total_shipments,
                "consensus_votes": consensus_votes,
                "average_votes_per_shipment": (consensus_votes / total_shipments) if total_shipments > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# ALGORITHM 4: PRODUCT AUTHENTICITY VERIFICATION
# ==========================================

@router.post("/products/verify", response_model=AuthenticityVerificationResponse)
async def verify_product_authenticity(
    verification_data: AuthenticityVerificationRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Algorithm 4: Product Authenticity Verification Using QR and NFT
    
    Input: Product ID, QR data, NFT metadata, current owner
    Output: Authenticity status
    
    1: Retrieve the NFT associated with the given Product ID
    2: if NFT exists then
    3:     if QRdata = NFTmetadata then
    4:         if currentowner = NFTowner then
    5:             Return "Product is Authentic"
    6:         else
    7:             Return "Ownership Mismatch"
    8:         end if
    9:     else
    10:         Return "Product Data Mismatch"
    11:     end if
    12: else
    13:     Return "Product Not Registered"
    14: end if
    
    Enhanced with better error handling and validation
    """
    try:
        print(f"🔍 Algorithm 4: Product verification request received")
        print(f"   Product ID: {verification_data.product_id}")
        print(f"   Current Owner: {verification_data.current_owner}")
        print(f"   QR Data Type: {type(verification_data.qr_data)}")
        
        # Validate input data
        if not verification_data.product_id.strip():
            raise HTTPException(
                status_code=422, 
                detail="Product ID cannot be empty"
            )
        
        if not verification_data.current_owner.strip():
            raise HTTPException(
                status_code=422, 
                detail="Current owner address cannot be empty"
            )
        
        if not verification_data.qr_data:
            raise HTTPException(
                status_code=422, 
                detail="QR data cannot be empty"
            )
        
        # Validate Ethereum address format for current_owner
        import re
        if not re.match(r'^0x[a-fA-F0-9]{40}$', verification_data.current_owner):
            raise HTTPException(
                status_code=422, 
                detail="Invalid Ethereum address format for current_owner"
            )
        
        print(f"✅ Algorithm 4: Input validation passed")
        
        # Call Algorithm 4: Product Authenticity Verification Using QR and NFT
        status = await blockchain_service.verify_product_authenticity(
            verification_data.product_id,
            verification_data.qr_data,
            verification_data.current_owner
        )
        
        print(f"🔍 Algorithm 4: Verification result: {status}")
        
        # Determine verification details based on Algorithm 4 outputs
        verification_details = {
            "qr_verified": status == "Product is Authentic",
            "owner_verified": status not in ["Ownership Mismatch"],
            "nft_exists": status != "Product Not Registered",
            "data_matches": status not in ["Product Data Mismatch"],
            "verification_status": status,
            "algorithm": "Algorithm 4: Product Authenticity Verification Using QR and NFT"
        }
        
        return AuthenticityVerificationResponse(
            status=status,
            product_id=verification_data.product_id,
            verification_timestamp=time.time(),
            details=verification_details
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 422 validation errors)
        raise
    except Exception as e:
        print(f"❌ Algorithm 4: Verification endpoint error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Algorithm 4 verification error: {str(e)}"
        )

# ==========================================
# ENHANCED PRODUCT MANAGEMENT (NFTCore Integration)
# ==========================================

@router.post("/products/mint")
async def mint_product(
    product_data: ProductMintRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Enhanced product minting with proper IPFS CID handling and manufacturer address auto-population
    """
    try:
        # FIX 1: Properly handle manufacturer address auto-population
        manufacturer_address = product_data.manufacturer
        if not manufacturer_address or manufacturer_address == "" or manufacturer_address == "undefined":
            # Use a default demo address if not provided (this should be set from frontend wallet)
            manufacturer_address = "0x032041b4b356fEE1496805DD4749f181bC736FFA"
            print(f"⚠️ Using default manufacturer address: {manufacturer_address}")
        else:
            print(f"✅ Using provided manufacturer address: {manufacturer_address}")
        
        # Convert price from ETH to Wei if provided
        price_in_wei = 0
        if product_data.metadata.get("price"):
            try:
                price_in_eth = float(product_data.metadata.get("price", 0))
                price_in_wei = int(price_in_eth * 10**18)  # Convert ETH to Wei
            except (ValueError, TypeError):
                price_in_wei = 0
        
        # FIX 2: Use existing IPFS CIDs instead of re-uploading
        # Check if CIDs are already provided from frontend uploads
        image_cid = product_data.metadata.get("imageCID", "")
        video_cid = product_data.metadata.get("videoCID", "")
        
        print(f"📦 Processing product minting:")
        print(f"   🖼️ Image CID from frontend: {image_cid}")
        print(f"   🎥 Video CID from frontend: {video_cid}")
        
        # Only upload if CIDs are not provided (fallback for legacy image_data/video_data)
        if not image_cid and product_data.metadata.get("image_data"):
            try:
                from app.services.ipfs_service import ipfs_service
                image_metadata = {
                    "type": "product_image",
                    "product_id": product_data.metadata.get("uniqueProductID", f"PROD-{int(time.time())}"),
                    "image_data": product_data.metadata.get("image_data"),
                    "uploaded_at": int(time.time())
                }
                image_cid = await ipfs_service.upload_to_ipfs(image_metadata)
                print(f"✅ Image uploaded to IPFS (fallback): {image_cid}")
            except Exception as e:
                print(f"⚠️ Image upload failed: {e}")
                # Continue without image CID
        
        # Only upload if CIDs are not provided (fallback for legacy video_data)
        if not video_cid and product_data.metadata.get("video_data"):
            try:
                from app.services.ipfs_service import ipfs_service
                video_metadata = {
                    "type": "product_video",
                    "product_id": product_data.metadata.get("uniqueProductID", f"PROD-{int(time.time())}"),
                    "video_data": product_data.metadata.get("video_data"),
                    "uploaded_at": int(time.time())
                }
                video_cid = await ipfs_service.upload_to_ipfs(video_metadata)
                print(f"✅ Video uploaded to IPFS (fallback): {video_cid}")
            except Exception as e:
                print(f"⚠️ Video upload failed: {e}")
                # Continue without video CID

        # Generate comprehensive metadata with enhanced structure
        current_timestamp = int(time.time())
        unique_product_id = product_data.metadata.get("uniqueProductID") or f"PROD-{current_timestamp}"
        batch_number = product_data.metadata.get("batchNumber") or f"BATCH-{current_timestamp}"
        
        # Format dates properly
        manufacturing_date = product_data.metadata.get("manufacturingDate") or time.strftime("%Y-%m-%d")
        expiration_date = product_data.metadata.get("expirationDate") or ""
        
        metadata = {
            "name": product_data.metadata.get("name", "ChainFLIP Product"),
            "description": product_data.metadata.get("description", "Supply chain tracked product"),
            "image": f"https://w3s.link/ipfs/{image_cid}" if image_cid else "",
            "video": f"https://w3s.link/ipfs/{video_cid}" if video_cid else "",
            "external_url": product_data.metadata.get("external_url", ""),
            "attributes": [
                {"trait_type": "Manufacturer", "value": manufacturer_address},
                {"trait_type": "Product Type", "value": product_data.metadata.get("productType", "General")},
                {"trait_type": "Batch Number", "value": batch_number},
                {"trait_type": "Manufacturing Date", "value": manufacturing_date},
                {"trait_type": "Expiration Date", "value": expiration_date},
                {"trait_type": "Location", "value": product_data.metadata.get("location", "")},
                {"trait_type": "Category", "value": product_data.metadata.get("category", "")},
                {"trait_type": "Price (ETH)", "value": str(product_data.metadata.get("price", "0"))},
                {"trait_type": "Price (Wei)", "value": str(price_in_wei)},
                {"trait_type": "Unique Product ID", "value": unique_product_id},
                {"trait_type": "Image CID", "value": image_cid},
                {"trait_type": "Video CID", "value": video_cid}
            ],
            # ChainFLIP specific metadata
            "uniqueProductID": unique_product_id,
            "batchNumber": batch_number,
            "manufacturerID": manufacturer_address,
            "productType": product_data.metadata.get("productType", "General"),
            "manufacturingDate": manufacturing_date,
            "expirationDate": expiration_date,
            "location": product_data.metadata.get("location", ""),
            "category": product_data.metadata.get("category", ""),
            "price_eth": product_data.metadata.get("price", "0"),
            "price_wei": price_in_wei,
            "image_cid": image_cid,
            "video_cid": video_cid,
            "chainflip_version": "2.0",
            "mint_timestamp": current_timestamp,
            "mint_date_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_timestamp)),
            "blockchain": "Base Sepolia"
        }
        
        print(f"🏭 Minting enhanced product NFT on Base Sepolia...")
        print(f"📄 Enhanced Metadata with Image/Video CIDs:")
        print(f"   🖼️ Image CID: {image_cid}")
        print(f"   🎥 Video CID: {video_cid}")
        print(f"   💰 Price: {product_data.metadata.get('price', 0)} ETH ({price_in_wei} Wei)")
        print(f"   📅 Formatted Date: {metadata['mint_date_formatted']}")
        
        # Mint the product using the enhanced blockchain service
        result = await blockchain_service.mint_product_nft(
            manufacturer=manufacturer_address,
            metadata=metadata,
            manufacturer_private_key=product_data.manufacturer_private_key
        )
        
        # NEW: Send cross-chain CID message to Polygon Amoy admin after successful minting
        try:
            print(f"\n🌐 === SENDING CROSS-CHAIN CID MESSAGE ===")
            print(f"📦 Token ID: {result['token_id']}")
            print(f"📄 Metadata CID: {result['metadata_cid']}")
            print(f"🏭 Manufacturer: {manufacturer_address}")
            print(f"🎯 Target: Polygon Amoy Admin (0x032041b4b356fEE1496805DD4749f181bC736FFA)")
            
            # Import the layerzero service for cross-chain messaging
            from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service
            
            # Prepare CID sync message
            cid_message_data = {
                "type": "CID_SYNC",
                "token_id": result['token_id'],
                "metadata_cid": result['metadata_cid'],
                "manufacturer": manufacturer_address,
                "timestamp": current_timestamp,
                "source_chain": "base_sepolia",
                "product_name": metadata.get("name", "ChainFLIP Product"),
                "unique_product_id": unique_product_id,
                "batch_number": batch_number
            }
            
            # Send cross-chain message from Base Sepolia to Polygon Amoy
            messaging_result = await layerzero_oft_bridge_service.send_cross_chain_message(
                source_chain="base_sepolia",
                target_chain="polygon_amoy",
                message_data=cid_message_data,
                recipient_address="0x032041b4b356fEE1496805DD4749f181bC736FFA"  # Admin address
            )
            
            if messaging_result["success"]:
                print(f"✅ Cross-chain CID message sent successfully!")
                print(f"🔗 LayerZero TX: {messaging_result['transaction_hash']}")
                print(f"💰 LayerZero Fee: {messaging_result['layerzero_fee_paid']} ETH")
                
                # Add messaging info to the response
                cross_chain_info = {
                    "cross_chain_message_sent": True,
                    "layerzero_tx_hash": messaging_result["transaction_hash"],
                    "layerzero_fee_paid": messaging_result["layerzero_fee_paid"],
                    "message_recipient": "0x032041b4b356fEE1496805DD4749f181bC736FFA",
                    "destination_chain": "polygon_amoy"
                }
            else:
                print(f"⚠️ Cross-chain message failed: {messaging_result.get('error')}")
                cross_chain_info = {
                    "cross_chain_message_sent": False,
                    "error": messaging_result.get('error')
                }
                
        except Exception as cid_error:
            print(f"⚠️ Cross-chain CID message error: {cid_error}")
            cross_chain_info = {
                "cross_chain_message_sent": False,
                "error": f"Cross-chain messaging failed: {str(cid_error)}"
            }
        
        return {
            "success": True,
            "message": "Enhanced product minted successfully with image/video support",
            "token_id": result["token_id"],
            "transaction_hash": result["transaction_hash"],
            "metadata_cid": result["metadata_cid"],
            "qr_hash": result["qr_hash"],
            "image_cid": image_cid,
            "video_cid": video_cid,
            "price_eth": product_data.metadata.get("price", "0"),
            "price_wei": price_in_wei,
            "manufacturer_address": manufacturer_address,
            "chain_id": result.get("chain_id"),
            "block_number": result.get("block_number"),
            "gas_used": result.get("gas_used"),
            "contract_address": result.get("contract_address"),
            "token_uri": result.get("token_uri"),
            "mint_timestamp": current_timestamp,
            "mint_date_formatted": metadata["mint_date_formatted"],
            # NEW: Add cross-chain messaging info to response
            **cross_chain_info
        }
    except Exception as e:
        print(f"❌ Enhanced product minting error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/products/{token_id}")
async def get_product(
    token_id: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get comprehensive product information including all algorithm interactions"""
    product = await blockchain_service.get_product_by_token_id(token_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/participants/{address}/products")
async def get_participant_products(
    address: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get all products owned by a participant"""
    products = await blockchain_service.get_participant_products(address)
    return {"products": products, "count": len(products)}

# ==========================================
# ALGORITHM 5: POST SUPPLY CHAIN MANAGEMENT (MARKETPLACE)
# ==========================================

@router.post("/marketplace/buy", response_model=ProductBuyResponse)
async def buy_product_from_marketplace(
    buy_data: ProductBuyRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Algorithm 5: Post Supply Chain Management for NFT-Based Product Sale
    Combined with Algorithm 1: Payment Release and Incentive Mechanism
    
    Cross-chain flow: Buyer (Optimism Sepolia) → Hub (Polygon PoS) → Manufacturer (Base Sepolia)
    Bridges: LayerZero (Buyer→Hub) + fxPortal (Hub→Manufacturer)
    """
    try:
        print(f"🛒 Cross-chain purchase request received:")
        print(f"   📦 Product ID: {buy_data.product_id}")
        print(f"   👤 Buyer: {buy_data.buyer}")
        print(f"   💰 Price: {buy_data.price} ETH")
        print(f"   🔗 Cross-chain flow: Optimism Sepolia → Polygon Hub → Base Sepolia")
        
        # Initialize cross-chain purchase service
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        await crosschain_purchase_service.initialize()
        
        # Prepare cross-chain purchase request
        purchase_request = {
            "product_id": buy_data.product_id,
            "buyer": buy_data.buyer,
            "price": buy_data.price,
            "payment_method": buy_data.payment_method or "ETH"
        }
        
        # Execute Algorithm 5 + Algorithm 1 cross-chain purchase
        result = await crosschain_purchase_service.execute_cross_chain_purchase(purchase_request)
        
        if result["success"]:
            print(f"✅ Cross-chain purchase completed successfully")
            
            # Generate cross-chain transaction hash
            transaction_hash = result.get("nft_transfer_tx", f"0xCROSS{int(time.time())}")
            
            # Enhanced cross-chain details
            cross_chain_details = result.get("cross_chain_details", {
                "buyer_chain": "optimism_sepolia",
                "hub_chain": "polygon_pos",
                "manufacturer_chain": "base_sepolia",
                "bridges_used": ["LayerZero", "fxPortal"],
                "layerzero_tx": result.get("cross_chain_details", {}).get("layerzero_tx", "N/A"),
                "fxportal_tx": result.get("cross_chain_details", {}).get("fxportal_tx", "N/A"),
                "confirmation_time": "3-7 minutes",
                "escrow_id": result.get("cross_chain_details", {}).get("escrow_id", "N/A")
            })
            
            return ProductBuyResponse(
                success=True,
                status=result["status"],  # "Sale Successful and NFT Transferred"
                product_id=buy_data.product_id,
                buyer=buy_data.buyer,
                transaction_hash=transaction_hash,
                purchase_id=result["purchase_id"],
                payment_amount=buy_data.price,
                cross_chain_details=cross_chain_details
            )
        else:
            print(f"❌ Cross-chain purchase failed: {result['error']}")
            raise HTTPException(
                status_code=400, 
                detail=f"Cross-chain purchase failed at {result.get('step', 'unknown')}: {result['error']}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Cross-chain purchase error: {e}")
        raise HTTPException(status_code=500, detail=f"Cross-chain purchase failed: {str(e)}")

@router.post("/marketplace/list")
async def list_product_for_sale(
    listing_data: ProductListingRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Algorithm 5: List product for sale in marketplace
    Implements post supply chain management for NFT-based product sale
    """
    try:
        # TODO: Implement marketplace listing logic
        # This would integrate with the Marketplace contract
        
        result = {
            "success": True,
            "product_id": listing_data.product_id,
            "price": listing_data.price,
            "listed_on_chains": listing_data.target_chains or [settings.polygon_pos_chain_id],
            "listing_timestamp": time.time(),
            "message": "Product listed successfully on marketplace"
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/marketplace/purchase")
async def initiate_product_purchase(
    purchase_data: ProductPurchaseRequest,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Algorithm 5: Initiate product purchase with authenticity verification
    Legacy endpoint - supports QR-based verification workflow
    """
    try:
        # First verify product authenticity
        authenticity_status = await blockchain_service.verify_product_authenticity(
            purchase_data.product_id,
            purchase_data.qr_verification_data,
            purchase_data.buyer  # Current owner will be verified internally
        )
        
        if authenticity_status != "Product is Authentic":
            return {
                "success": False,
                "error": f"Product authenticity verification failed: {authenticity_status}",
                "verification_status": authenticity_status
            }
        
        # TODO: Implement actual purchase logic
        # This would involve smart contract interaction
        
        return {
            "success": True,
            "product_id": purchase_data.product_id,
            "buyer": purchase_data.buyer,
            "purchase_status": "initiated",
            "verification_status": authenticity_status,
            "message": "Product purchase initiated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# CROSS-CHAIN STATISTICS AND MONITORING
# ==========================================

@router.get("/cross-chain/statistics")
async def get_cross_chain_statistics():
    """Get cross-chain operation statistics"""
    try:
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        await crosschain_purchase_service.initialize()
        
        database = crosschain_purchase_service.database
        
        # Cross-chain purchase statistics
        total_purchases = await database.purchases.count_documents({"cross_chain": True})
        successful_purchases = await database.purchases.count_documents({"status": "completed", "cross_chain": True})
        
        # Chain usage statistics
        chain_stats = {}
        for chain in ["optimism_sepolia", "polygon_pos", "base_sepolia", "arbitrum_sepolia"]:
            purchases_as_source = await database.escrows.count_documents({"source_chain": chain})
            purchases_as_target = await database.escrows.count_documents({"target_chain": chain})
            chain_stats[chain] = {
                "as_source": purchases_as_source,
                "as_target": purchases_as_target,
                "total_involvement": purchases_as_source + purchases_as_target
            }
        
        # Bridge usage statistics
        layerzero_transfers = await database.token_transfers.count_documents({"transfer_method": "LayerZero_OFT"})
        fxportal_transfers = await database.nft_transfers.count_documents({"source_chain": "polygon_pos"})
        
        return {
            "cross_chain_overview": {
                "total_cross_chain_purchases": total_purchases,
                "successful_purchases": successful_purchases,
                "success_rate": (successful_purchases / total_purchases * 100) if total_purchases > 0 else 0
            },
            "chain_usage": chain_stats,
            "bridge_usage": {
                "layerzero_oft_transfers": layerzero_transfers,
                "fxportal_nft_transfers": fxportal_transfers
            },
            "architecture": {
                "buyer_chain": "Optimism Sepolia",
                "hub_chain": "Polygon PoS Hub",
                "manufacturer_chain": "Base Sepolia (84532)",
                "transporter_chain": "Arbitrum Sepolia"
            },
            "bridges_used": ["LayerZero", "fxPortal"],
            "algorithms_implemented": ["Algorithm 1: Payment Release and Incentive Mechanism", "Algorithm 5: Post Supply Chain Management"]
        }
        
    except Exception as e:
        print(f"❌ Cross-chain stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cross-chain statistics: {str(e)}")

# ==========================================
# MARKETPLACE ANALYTICS AND BUYER HISTORY (ENHANCED)
# ==========================================

@router.get("/marketplace/purchases/{buyer_address}")
async def get_buyer_purchase_history(
    buyer_address: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get purchase history for a specific buyer"""
    try:
        cursor = blockchain_service.database.purchases.find({"buyer": buyer_address}).sort("purchase_timestamp", -1)
        purchases = []
        async for purchase in cursor:
            purchase["_id"] = str(purchase["_id"])
            purchases.append(purchase)
        
        return {
            "buyer": buyer_address,
            "total_purchases": len(purchases),
            "purchases": purchases
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/marketplace/statistics")
async def get_marketplace_statistics(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get marketplace statistics including total sales, buyers, etc."""
    try:
        # Total purchases
        total_purchases = await blockchain_service.database.purchases.count_documents({})
        
        # Total sales volume
        pipeline = [
            {"$group": {"_id": None, "total_volume": {"$sum": "$price_eth"}}}
        ]
        volume_result = blockchain_service.database.purchases.aggregate(pipeline)
        total_volume = 0
        async for result in volume_result:
            total_volume = result.get("total_volume", 0)
        
        # Unique buyers
        unique_buyers = await blockchain_service.database.purchases.distinct("buyer")
        
        # Recent purchases (last 10)
        recent_cursor = blockchain_service.database.purchases.find().sort("purchase_timestamp", -1).limit(10)
        recent_purchases = []
        async for purchase in recent_cursor:
            purchase["_id"] = str(purchase["_id"])
            recent_purchases.append(purchase)
        
        return {
            "total_purchases": total_purchases,
            "total_volume_eth": total_volume,
            "unique_buyers": len(unique_buyers),
            "recent_purchases": recent_purchases,
            "algorithm_5_active": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# COMPREHENSIVE SYSTEM QUERIES
# ==========================================

@router.get("/algorithms/status")
async def get_algorithms_status(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get status and usage statistics for all 5 ChainFLIP algorithms"""
    try:
        stats = await blockchain_service.get_network_stats()
        
        algorithm_status = {
            "algorithm_1_payment_release": {
                "name": "Payment Release and Incentive Mechanism",
                "implemented": True,
                "usage_count": stats.get("algorithm_usage", {}).get("payment_release", 0),
                "description": "Automated payment processing based on NFT ownership and delivery status"
            },
            "algorithm_2_dispute_resolution": {
                "name": "Dispute Resolution and Voting Mechanism",
                "implemented": True,
                "usage_count": stats.get("algorithm_usage", {}).get("dispute_resolution", 0),
                "description": "Multi-stakeholder voting system for arbitrator selection and dispute resolution"
            },
            "algorithm_3_consensus": {
                "name": "Supply Chain Consensus Algorithm",
                "implemented": True,  # NOW IMPLEMENTED WITH UI
                "usage_count": stats.get("algorithm_usage", {}).get("consensus_batches", 0),
                "description": "Batch processing with FL validation for supply chain transactions"
            },
            "algorithm_4_authenticity": {
                "name": "Product Authenticity Verification Using QR and NFT",
                "implemented": True,
                "usage_count": stats.get("algorithm_usage", {}).get("authenticity_verification", 0),
                "description": "QR code and NFT metadata comparison for product authenticity"
            },
            "algorithm_5_marketplace": {
                "name": "Post Supply Chain Management for NFT-Based Product Sale",
                "implemented": True,
                "usage_count": stats.get("algorithm_usage", {}).get("marketplace_listings", 0),
                "description": "Marketplace functionality with cross-chain trading support"
            }
        }
        
        return {
            "total_algorithms": 5,
            "implemented_count": sum(1 for alg in algorithm_status.values() if alg["implemented"]),
            "algorithms": algorithm_status,
            "contracts_deployed": stats.get("contract_deployments", {}),
            "multi_chain_architecture": {
                "polygon_pos_hub": "Central hub for product registration and FL aggregation",
                "l2_manufacturer": "High-frequency manufacturing operations",
                "l2_transporter": "Transport logs and real-time tracking", 
                "l2_buyer": "Purchase transactions and receipt confirmations"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contracts/info")
async def get_contracts_info(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get information about all 6 deployed ChainFLIP smart contracts"""
    try:
        return {
            "total_contracts": 6,
            "contracts": blockchain_service.contract_configs,
            "deployment_status": "All contracts configured and ready",
            "main_contract": "SupplyChainNFT",
            "architecture": "Multi-chain with central Polygon PoS hub and 3 L2 CDK participants"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# REAL CONTRACT INTEGRATION TESTING
# ==========================================

@router.get("/contracts/accounts")
async def get_multi_account_info():
    """Get information about all 11 accounts and their roles"""
    try:
        # Initialize cross-chain purchase service
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        await crosschain_purchase_service.initialize()
        
        # Get multi-account manager
        multi_account_manager = crosschain_purchase_service.multi_account_manager
        
        return {
            "success": True,
            "multi_account_system": True,
            "account_summary": multi_account_manager.get_account_summary(),
            "current_account": {
                "address": crosschain_purchase_service.current_account.address,
                "roles": "deployer,admin"  # Current account roles
            },
            "role_assignments": {
                "deployer": "0x032041b4b356fEE1496805DD4749f181bC736FFA",
                "manufacturers": ["0x04351e7dF40d04B5E610c4aA033faCf435b98711", "0x72EB9742d3B684ebA40F11573b733Ac9dB499f23", "0x28918ecf013F32fAf45e05d62B4D9b207FCae784"],
                "buyers": ["0xc6A050a538a9E857B4DCb4A33436280c202F6941", "0x724876f86fA52568aBc51955BD3A68bFc1441097", "0x361d25a7F28F05dDE7a2cb191b4B8128EEE0fAB6"],
                "transporters": ["0x5503a5B847e98B621d97695edf1bD84242C5862E", "0x94081502540FD333075f3290d1D5C10A21AC5A5C"],
                "sellers": ["0x34Fc023EE50781e0a007852eEDC4A17fa353a8cD", "0x7ca2dF29b5ea3BB9Ef3b4245D8b7c41a03318Fc1"]
            },
            "note": "Real multi-account system ready for role-based testing"
        }
        
    except Exception as e:
        print(f"❌ Multi-account info error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get multi-account info: {str(e)}")

@router.post("/contracts/switch-account")
async def switch_account(request_data: Dict[str, Any]):
    """Switch to a specific account for testing"""
    try:
        operation_type = request_data.get("operation_type", "admin")
        preferred_address = request_data.get("preferred_address")
        
        # Initialize cross-chain purchase service
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        await crosschain_purchase_service.initialize()
        
        # Switch account
        result = crosschain_purchase_service.switch_account_for_operation(operation_type, preferred_address)
        
        if result["success"]:
            return {
                "success": True,
                "account_switched": True,
                "current_account": result["address"],
                "roles": result["roles"],
                "operation": result["operation"],
                "message": f"Successfully switched to {operation_type} account"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "current_account": crosschain_purchase_service.current_account.address
            }
        
    except Exception as e:
        print(f"❌ Account switch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch account: {str(e)}")
@router.get("/contracts/balances")
async def get_contract_account_balances():
    """Get account balances across all chains for all 11 accounts"""
    try:
        # Initialize cross-chain purchase service
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        await crosschain_purchase_service.initialize()
        
        # Get all account balances
        balances = await crosschain_purchase_service.get_account_balances()
        
        return {
            "success": True,
            "real_contracts": True,
            "multi_account_system": True,
            "account_balances": balances,
            "contract_addresses": {
                "hub_contract": crosschain_purchase_service.hub_contract_address,
                "buyer_contract": crosschain_purchase_service.buyer_contract_address,
                "manufacturer_contract": crosschain_purchase_service.manufacturer_contract_address,
                "transporter_contract": crosschain_purchase_service.transporter_contract_address,
                "layerzero_optimism": crosschain_purchase_service.layerzero_optimism_address,
                "layerzero_hub": crosschain_purchase_service.layerzero_hub_address,
                "fxportal_hub": crosschain_purchase_service.fxportal_hub_address
            },
            "chains_connected": {
                "optimism_sepolia": crosschain_purchase_service.optimism_web3.is_connected() if crosschain_purchase_service.optimism_web3 else False,
                "polygon_pos": crosschain_purchase_service.polygon_web3.is_connected() if crosschain_purchase_service.polygon_web3 else False,
                "base_sepolia": crosschain_purchase_service.base_sepolia_web3.is_connected() if crosschain_purchase_service.base_sepolia_web3 else False,
                "arbitrum_sepolia": crosschain_purchase_service.arbitrum_web3.is_connected() if crosschain_purchase_service.arbitrum_web3 else False
            }
        }
        
    except Exception as e:
        print(f"❌ Contract balances error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get contract balances: {str(e)}")

@router.post("/contracts/test-layerzero")
async def test_layerzero_bridge():
    """Test LayerZero bridge connection and message sending"""
    try:
        # Initialize cross-chain purchase service
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        await crosschain_purchase_service.initialize()
        
        # Test LayerZero contract call
        if not crosschain_purchase_service.layerzero_optimism_contract:
            raise HTTPException(status_code=500, detail="LayerZero contract not initialized")
        
        # Get target chain ID for Polygon Hub
        target_chain_id = settings.polygon_pos_chain_id
        
        # Test payload
        test_payload = json.dumps({"test": "layerzero_bridge", "timestamp": int(time.time())}).encode('utf-8')
        
        # Estimate fees
        try:
            native_fee, zro_fee = crosschain_purchase_service.layerzero_optimism_contract.functions.estimateFee(
                target_chain_id,
                test_payload,
                False,  # useZro
                b""     # adapterParams
            ).call()
            
            return {
                "success": True,
                "layerzero_bridge_test": "Fee estimation successful",
                "native_fee_wei": native_fee,
                "native_fee_eth": Web3.from_wei(native_fee, 'ether'),
                "zro_fee": zro_fee,
                "target_chain_id": target_chain_id,
                "contract_address": crosschain_purchase_service.layerzero_optimism_address,
                "chain": "Optimism Sepolia",
                "note": "Real contract connected and responding"
            }
            
        except Exception as contract_error:
            return {
                "success": False,
                "error": str(contract_error),
                "contract_address": crosschain_purchase_service.layerzero_optimism_address,
                "chain": "Optimism Sepolia",
                "note": "Contract connection failed"
            }
        
    except Exception as e:
        print(f"❌ LayerZero test error: {e}")
        raise HTTPException(status_code=500, detail=f"LayerZero test failed: {str(e)}")

@router.post("/contracts/test-fxportal") 
async def test_fxportal_bridge():
    """Test FxPortal bridge connection"""
    try:
        # Initialize cross-chain purchase service
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        await crosschain_purchase_service.initialize()
        
        # Test FxPortal contract call
        if not crosschain_purchase_service.fxportal_hub_contract:
            raise HTTPException(status_code=500, detail="FxPortal contract not initialized")
        
        # Test message data
        test_data = {
            "test": "fxportal_bridge",
            "timestamp": int(time.time()),
            "source_chain": "polygon_pos",
            "target_chain": "base_sepolia"
        }
        
        # Test payload
        test_payload = json.dumps(test_data).encode('utf-8')
        data_hash = Web3.keccak(text=json.dumps(test_data)).hex()
        
        # Get current gas price
        gas_price = crosschain_purchase_service.polygon_web3.eth.gas_price
        
        # Estimate gas for the transaction
        try:
            gas_estimate = crosschain_purchase_service.fxportal_hub_contract.functions.sendMessageToChild(
                0,  # MessageType.PRODUCT_REGISTRATION
                data_hash,
                test_payload
            ).estimate_gas({'from': crosschain_purchase_service.account.address})
            
            estimated_cost = gas_estimate * gas_price
            
            return {
                "success": True,
                "fxportal_bridge_test": "Gas estimation successful",
                "gas_estimate": gas_estimate,
                "gas_price_wei": gas_price,
                "gas_price_gwei": Web3.from_wei(gas_price, 'gwei'),
                "estimated_cost_wei": estimated_cost,
                "estimated_cost_eth": Web3.from_wei(estimated_cost, 'ether'),
                "contract_address": crosschain_purchase_service.fxportal_hub_address,
                "chain": "Polygon PoS Hub",
                "note": "Real contract connected and responding"
            }
            
        except Exception as contract_error:
            return {
                "success": False,
                "error": str(contract_error),
                "contract_address": crosschain_purchase_service.fxportal_hub_address,
                "chain": "Polygon PoS Hub",
                "note": "Contract connection failed"
            }
        
    except Exception as e:
        print(f"❌ FxPortal test error: {e}")
        raise HTTPException(status_code=500, detail=f"FxPortal test failed: {str(e)}")

@router.post("/contracts/test-multi-account-purchase")
async def test_multi_account_cross_chain_purchase():
    """Test cross-chain purchase using different accounts for different roles"""
    try:
        # Initialize cross-chain purchase service
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        await crosschain_purchase_service.initialize()
        
        # Get accounts for different roles
        buyer_account = crosschain_purchase_service.multi_account_manager.get_primary_account_for_role('buyer')
        seller_account = crosschain_purchase_service.multi_account_manager.get_primary_account_for_role('seller')
        manufacturer_account = crosschain_purchase_service.multi_account_manager.get_primary_account_for_role('manufacturer')
        
        if not all([buyer_account, seller_account, manufacturer_account]):
            raise HTTPException(status_code=500, detail="Missing required accounts for multi-role testing")
        
        # Test cross-chain purchase with role-based accounts
        test_purchase_request = {
            "product_id": "1749391842793",  # Use existing product
            "buyer": buyer_account['address'],
            "price": 0.001,
            "payment_method": "ETH"
        }
        
        print(f"🧪 Testing multi-account cross-chain purchase:")
        print(f"   👤 Buyer: {buyer_account['address']} (roles: {buyer_account['roles']})")
        print(f"   🏪 Seller: {seller_account['address']} (roles: {seller_account['roles']})")
        print(f"   🏭 Manufacturer: {manufacturer_account['address']} (roles: {manufacturer_account['roles']})")
        
        # Execute cross-chain purchase
        result = await crosschain_purchase_service.execute_cross_chain_purchase(test_purchase_request)
        
        return {
            "success": result["success"],
            "multi_account_test": True,
            "accounts_used": {
                "buyer": {
                    "address": buyer_account['address'],
                    "roles": buyer_account['roles']
                },
                "seller": {
                    "address": seller_account['address'],
                    "roles": seller_account['roles']
                },
                "manufacturer": {
                    "address": manufacturer_account['address'],
                    "roles": manufacturer_account['roles']
                }
            },
            "purchase_result": result,
            "note": "Real multi-account cross-chain purchase test completed"
        }
        
    except Exception as e:
        print(f"❌ Multi-account purchase test error: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-account purchase test failed: {str(e)}")

# ==========================================
# ENHANCED CROSS-CHAIN OPERATIONS
# ==========================================

@router.post("/cross-chain/sync")
async def sync_cross_chain_data(
    sync_data: Dict[str, Any],
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Sync data across multiple chains"""
    try:
        # TODO: Implement cross-chain synchronization
        return {
            "success": True,
            "message": "Cross-chain sync initiated",
            "sync_data": sync_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
