"""
ChainFLIP Cross-Chain NFT Bridge API Routes
Provides endpoints for cross-chain NFT transfers
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.services.nft_bridge_service import nft_bridge_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nft-bridge", tags=["NFT Bridge"])

# Request Models
class CrossChainTransferRequest(BaseModel):
    token_id: int = Field(..., description="NFT Token ID to transfer")
    from_chain: str = Field(..., description="Source chain (base_sepolia, optimism_sepolia, arbitrum_sepolia, polygon_amoy)")
    to_chain: str = Field(..., description="Destination chain")
    from_address: str = Field(..., description="Current owner address on source chain")
    to_address: str = Field(..., description="Recipient address on destination chain")
    caller_private_key: Optional[str] = Field(None, description="Private key for transaction signing (optional)")

class TransferStatusRequest(BaseModel):
    transfer_id: str = Field(..., description="Transfer ID to check status")

# Response Models
class TransferResponse(BaseModel):
    success: bool
    transfer_id: Optional[str] = None
    burn_transaction: Optional[Dict[str, Any]] = None
    message_transaction: Optional[Dict[str, Any]] = None
    status: str
    estimated_completion: Optional[str] = None
    error: Optional[str] = None

class TransferStatusResponse(BaseModel):
    transfer_id: Optional[str] = None
    status: Optional[str] = None
    token_id: Optional[str] = None
    from_chain: Optional[str] = None
    to_chain: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

@router.post("/transfer", response_model=TransferResponse)
async def transfer_nft_cross_chain(request: CrossChainTransferRequest):
    """
    Transfer an NFT from one chain to another using LayerZero
    
    This endpoint:
    1. Verifies NFT ownership on source chain
    2. Burns the NFT on source chain 
    3. Sends cross-chain message via LayerZero
    4. The NFT will be minted on destination chain automatically
    
    Supported chains:
    - base_sepolia (Base Sepolia)
    - optimism_sepolia (OP Sepolia)
    - arbitrum_sepolia (Arbitrum Sepolia) 
    - polygon_amoy (Polygon Amoy)
    """
    try:
        logger.info(f"Cross-chain NFT transfer request: {request.dict()}")
        
        # Validate chain names
        supported_chains = ["base_sepolia", "optimism_sepolia", "arbitrum_sepolia", "polygon_amoy"]
        if request.from_chain not in supported_chains:
            raise HTTPException(status_code=400, detail=f"Unsupported source chain: {request.from_chain}")
        if request.to_chain not in supported_chains:
            raise HTTPException(status_code=400, detail=f"Unsupported destination chain: {request.to_chain}")
        if request.from_chain == request.to_chain:
            raise HTTPException(status_code=400, detail="Source and destination chains cannot be the same")
            
        # Execute cross-chain transfer
        result = await nft_bridge_service.transfer_nft_cross_chain(
            token_id=request.token_id,
            from_chain=request.from_chain,
            to_chain=request.to_chain,
            from_address=request.from_address,
            to_address=request.to_address,
            caller_private_key=request.caller_private_key
        )
        
        if result["success"]:
            return TransferResponse(
                success=True,
                transfer_id=result["transfer_id"],
                burn_transaction=result["burn_transaction"],
                message_transaction=result["message_transaction"],
                status=result["status"],
                estimated_completion=result["estimated_completion"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cross-chain transfer error: {e}")
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")

@router.get("/transfer/{transfer_id}", response_model=TransferStatusResponse)
async def get_transfer_status(transfer_id: str):
    """
    Get the status of a cross-chain NFT transfer
    
    Returns detailed information about the transfer including:
    - Current status (message_sent, completed, failed)
    - Transaction hashes for burn and message operations
    - Timestamp and completion details
    """
    try:
        logger.info(f"Getting transfer status for: {transfer_id}")
        
        result = await nft_bridge_service.get_transfer_status(transfer_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
            
        return TransferStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transfer status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transfer status: {str(e)}")

@router.get("/transfers", response_model=List[TransferStatusResponse])
async def get_all_transfers(limit: int = 50):
    """
    Get all cross-chain NFT transfers with optional limit
    
    Returns a list of all transfers, sorted by most recent first.
    Useful for monitoring and debugging cross-chain operations.
    """
    try:
        logger.info(f"Getting all transfers with limit: {limit}")
        
        transfers = await nft_bridge_service.get_all_transfers(limit)
        
        return [TransferStatusResponse(**transfer) for transfer in transfers]
        
    except Exception as e:
        logger.error(f"Error getting all transfers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transfers: {str(e)}")

@router.get("/networks")
async def get_supported_networks():
    """
    Get list of supported networks for cross-chain NFT transfers
    
    Returns network information including chain IDs, names, and contract addresses.
    """
    try:
        from app.services.nft_bridge_service import NETWORK_CONFIG
        
        networks = {}
        for key, config in NETWORK_CONFIG.items():
            networks[key] = {
                "name": config["name"],
                "chain_id": config["chain_id"],
                "nft_contract": config["nft_contract"],
                "layer_zero_eid": config["layer_zero_eid"]
            }
            
        return {
            "success": True,
            "supported_networks": networks,
            "total_networks": len(networks)
        }
        
    except Exception as e:
        logger.error(f"Error getting network information: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get network info: {str(e)}")

@router.get("/health")
async def nft_bridge_health_check():
    """
    Health check endpoint for NFT Bridge Service
    
    Returns the status of network connections and contract availability.
    """
    try:
        # Check if service is initialized
        if not hasattr(nft_bridge_service, 'web3_connections'):
            return {
                "status": "not_initialized",
                "message": "NFT Bridge Service not initialized"
            }
            
        # Check network connections
        connected_networks = len(nft_bridge_service.web3_connections)
        from app.services.nft_bridge_service import NETWORK_CONFIG
        total_networks = len(NETWORK_CONFIG)
        
        # Check contract availability
        loaded_contracts = len(nft_bridge_service.nft_contracts)
        
        health_status = {
            "status": "healthy" if connected_networks > 0 else "unhealthy",
            "connected_networks": connected_networks,
            "total_networks": total_networks,
            "loaded_contracts": loaded_contracts,
            "connection_percentage": (connected_networks / total_networks * 100) if total_networks > 0 else 0,
            "timestamp": str(datetime.utcnow())
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": str(datetime.utcnow())
        }

# Example usage endpoints for testing
@router.post("/example/base-to-optimism")
async def example_base_to_optimism_transfer():
    """
    Example endpoint: Transfer NFT from Base Sepolia to OP Sepolia
    
    This is a test endpoint that demonstrates cross-chain transfer.
    Replace with actual token ID and addresses for testing.
    """
    example_request = CrossChainTransferRequest(
        token_id=1,
        from_chain="base_sepolia",
        to_chain="optimism_sepolia", 
        from_address="0x5503a5B847e98B621d97695edf1bD84242C5862E",
        to_address="0x28918ecf013F32fAf45e05d62B4D9b207FCae784"
    )
    
    return {
        "message": "This is an example endpoint. Use POST /api/nft-bridge/transfer with your actual parameters.",
        "example_request": example_request.dict(),
        "note": "Make sure NFT contracts are deployed on both networks before attempting transfer"
    }