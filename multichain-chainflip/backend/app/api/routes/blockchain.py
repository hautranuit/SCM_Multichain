"""
Blockchain API Routes - Multi-Chain Operations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
from pydantic import BaseModel

from app.services.blockchain_service import BlockchainService

router = APIRouter()

# Pydantic models for request/response
class ParticipantRegistration(BaseModel):
    address: str
    participant_type: str  # manufacturer, distributor, retailer, etc.
    chain_id: int

class ProductMinting(BaseModel):
    manufacturer: str
    metadata_cid: str
    initial_qr_data: Dict[str, Any]

class ProductTransfer(BaseModel):
    token_id: str
    from_address: str
    to_address: str
    transport_data: Dict[str, Any]

class CrossChainMessage(BaseModel):
    source_chain: int
    target_chain: int
    message_data: Dict[str, Any]

# Dependency to get blockchain service
async def get_blockchain_service():
    service = BlockchainService()
    await service.initialize()
    return service

@router.get("/status")
async def get_blockchain_status(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get multi-chain network status"""
    return await blockchain_service.get_network_stats()

@router.post("/participants/register")
async def register_participant(
    participant_data: ParticipantRegistration,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Register a new participant in the multi-chain system"""
    try:
        result = await blockchain_service.register_participant(
            participant_data.address,
            participant_data.participant_type,
            participant_data.chain_id
        )
        return {"success": True, "participant": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/products/mint")
async def mint_product(
    product_data: ProductMinting,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Mint a new product NFT on Polygon PoS Hub"""
    try:
        result = await blockchain_service.mint_product_nft(
            product_data.manufacturer,
            product_data.metadata_cid,
            product_data.initial_qr_data
        )
        return {"success": True, "product": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/products/transfer")
async def transfer_product(
    transfer_data: ProductTransfer,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Transfer product between participants"""
    try:
        result = await blockchain_service.transfer_product(
            transfer_data.token_id,
            transfer_data.from_address,
            transfer_data.to_address,
            transfer_data.transport_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/products/{token_id}")
async def get_product(
    token_id: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get product information by token ID"""
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

@router.post("/cross-chain/message")
async def send_cross_chain_message(
    message_data: CrossChainMessage,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Send cross-chain message using FxPortal bridge"""
    try:
        result = await blockchain_service.cross_chain_message(
            message_data.source_chain,
            message_data.target_chain,
            message_data.message_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/contracts/deploy/pos-hub")
async def deploy_pos_hub(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Deploy Polygon PoS Hub contract"""
    try:
        # This will be implemented when contracts are ready
        return {"message": "PoS Hub contract deployment endpoint - TODO"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/contracts/deploy/l2-participant/{participant_id}")
async def deploy_l2_participant(
    participant_id: str,
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Deploy L2 CDK Participant contract"""
    try:
        # This will be implemented when contracts are ready
        return {"message": f"L2 Participant contract deployment for {participant_id} - TODO"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
