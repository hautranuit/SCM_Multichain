"""
Direct LayerZero API Routes
Handles cross-chain CID sync using DirectLayerZeroMessenger contracts
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time

router = APIRouter()

class CIDSyncRequest(BaseModel):
    manufacturer_address: str
    token_id: str
    metadata_cid: str
    product_data: Dict[str, Any]

class CIDSyncResponse(BaseModel):
    success: bool
    transaction_hash: Optional[str] = None
    sync_id: Optional[str] = None
    message: str
    layerzero_fee_paid: Optional[float] = None
    target_chains: Optional[list] = None

async def get_direct_layerzero_service():
    """Dependency to get DirectLayerZero messaging service"""
    from app.services.direct_layerzero_messaging_service import direct_layerzero_messaging_service
    return direct_layerzero_messaging_service

@router.post("/sync-cid", response_model=CIDSyncResponse)
async def sync_cid_cross_chain(
    request: CIDSyncRequest,
    service = Depends(get_direct_layerzero_service)
):
    """
    Sync CID across all chains using DirectLayerZero messaging
    This is the main endpoint for cross-chain CID synchronization
    """
    try:
        print(f"🌐 === CROSS-CHAIN CID SYNC REQUEST ===")
        print(f"🏭 Manufacturer: {request.manufacturer_address}")
        print(f"🔖 Token ID: {request.token_id}")
        print(f"📦 CID: {request.metadata_cid}")
        
        # Get manufacturer private key from environment
        from app.services.blockchain_service import get_private_key_for_address
        manufacturer_private_key = get_private_key_for_address(request.manufacturer_address)
        
        # Execute cross-chain CID sync using DirectLayerZero messaging
        result = await service.send_cid_sync_to_all_chains(
            source_chain="base_sepolia",
            token_id=request.token_id,
            metadata_cid=request.metadata_cid,
            manufacturer=request.manufacturer_address,
            product_data=request.product_data,
            manufacturer_private_key=manufacturer_private_key
        )
        
        if result.get("success"):
            return CIDSyncResponse(
                success=True,
                transaction_hash=result.get("transaction_hash"),
                sync_id=result.get("sync_id"),
                message="Cross-chain CID sync completed successfully",
                layerzero_fee_paid=result.get("layerzero_fee_paid"),
                target_chains=["polygon_amoy", "op_sepolia", "arbitrum_sepolia"]
            )
        else:
            # Handle specific errors like SENDER_ROLE permission issue
            error_message = result.get("error", "Unknown error")
            solution = result.get("solution", "")
            
            if "SENDER_ROLE" in error_message:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": error_message,
                        "solution": solution,
                        "action_required": "Grant SENDER_ROLE to manufacturer account on DirectLayerZeroMessenger contract",
                        "script_to_run": "cd /app/multichain-chainflip && npx hardhat run src/scripts/grant-sender-role.js --network base_sepolia"
                    }
                )
            else:
                raise HTTPException(status_code=400, detail=error_message)
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ CID sync error: {e}")
        raise HTTPException(status_code=500, detail=f"CID sync failed: {str(e)}")

@router.get("/sync-status/{sync_id}")
async def get_sync_status(
    sync_id: str,
    service = Depends(get_direct_layerzero_service)
):
    """Get status of a cross-chain sync operation"""
    try:
        result = await service.get_sync_status(sync_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trusted-remotes")
async def check_trusted_remotes(
    service = Depends(get_direct_layerzero_service)
):
    """Check trusted remote configurations between DirectLayerZeroMessenger contracts"""
    try:
        result = await service.check_trusted_remotes()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check trusted remotes: {str(e)}")

@router.get("/health")
async def layerzero_health_check(
    service = Depends(get_direct_layerzero_service)
):
    """Health check for DirectLayerZero messaging service"""
    try:
        # Check if service is initialized
        if not hasattr(service, 'web3_connections') or not service.web3_connections:
            return {
                "healthy": False,
                "error": "DirectLayerZero service not initialized",
                "message": "Service needs initialization"
            }
        
        # Check Web3 connections
        connected_chains = []
        failed_chains = []
        
        for chain_name, web3 in service.web3_connections.items():
            try:
                latest_block = web3.eth.block_number
                connected_chains.append({
                    "chain": chain_name,
                    "latest_block": latest_block,
                    "connected": True
                })
            except Exception as e:
                failed_chains.append({
                    "chain": chain_name,
                    "error": str(e),
                    "connected": False
                })
        
        # Check contract instances
        contract_status = {}
        for chain_name, contract in service.messenger_contracts.items():
            contract_status[chain_name] = {
                "contract_available": contract is not None,
                "contract_address": service.contract_addresses.get(chain_name, "N/A")
            }
        
        return {
            "healthy": len(connected_chains) > 0,
            "service_initialized": True,
            "connected_chains": connected_chains,
            "failed_chains": failed_chains,
            "contract_status": contract_status,
            "total_chains": len(service.web3_connections),
            "healthy_chains": len(connected_chains)
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "message": "Health check failed"
        }