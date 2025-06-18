"""
ChainFLIP Messaging API Routes
Clean LayerZero-based cross-chain CID synchronization
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.chainflip_messaging_service import chainflip_messaging_service

router = APIRouter(prefix="/chainflip-messaging", tags=["ChainFLIP Messaging"])

class CIDSyncRequest(BaseModel):
    token_id: str
    metadata_cid: str
    manufacturer: str
    source_chain: str = "base_sepolia"
    product_data: Optional[Dict[str, Any]] = None

class ContractAddressUpdate(BaseModel):
    addresses: Dict[str, str]

@router.post("/sync-cid")
async def sync_cid_to_all_chains(request: CIDSyncRequest):
    """
    Sync CID to all chains using ChainFLIP Messenger
    This is the main endpoint for cross-chain CID synchronization
    """
    try:
        # Get manufacturer's private key from environment
        from app.core.config import get_settings
        settings = get_settings()
        
        # Look up manufacturer's private key based on address
        manufacturer_key_var = f"ACCOUNT_{request.manufacturer}"
        manufacturer_private_key = getattr(settings, manufacturer_key_var.lower(), None)
        
        if not manufacturer_private_key:
            raise HTTPException(
                status_code=400, 
                detail=f"Private key not found for manufacturer {request.manufacturer}. Add {manufacturer_key_var} to .env file"
            )
        
        result = await chainflip_messaging_service.send_cid_sync_to_all_chains(
            source_chain=request.source_chain,
            token_id=request.token_id,
            metadata_cid=request.metadata_cid,
            manufacturer=request.manufacturer,
            product_data=request.product_data or {},
            manufacturer_private_key=manufacturer_private_key
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "CID synced to all chains successfully",
                "sync_id": result["sync_id"],
                "transaction_hash": result["transaction_hash"],
                "layerzero_fee_paid": result["layerzero_fee_paid"],
                "events": result.get("events", [])
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CID sync failed: {str(e)}")

@router.get("/received-cids/{chain_name}")
async def get_received_cids(chain_name: str):
    """
    Get all CIDs received on a specific chain
    Useful for verifying cross-chain sync worked
    """
    try:
        result = await chainflip_messaging_service.get_received_cids(chain_name)
        
        if result["success"]:
            return {
                "success": True,
                "chain": result["chain"],
                "cid_count": result["cid_count"],
                "cids": result["cids"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get received CIDs: {str(e)}")

@router.post("/update-contract-addresses")
async def update_contract_addresses(request: ContractAddressUpdate):
    """
    Update contract addresses after deployment
    """
    try:
        await chainflip_messaging_service.update_contract_addresses(request.addresses)
        return {
            "success": True,
            "message": "Contract addresses updated successfully",
            "addresses": request.addresses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update contract addresses: {str(e)}")

@router.get("/status")
async def get_service_status():
    """
    Get ChainFLIP messaging service status
    """
    try:
        # Check if service is initialized
        is_initialized = len(chainflip_messaging_service.web3_connections) > 0
        
        # Get connection status for each chain
        chain_status = {}
        for chain_name, web3 in chainflip_messaging_service.web3_connections.items():
            try:
                latest_block = web3.eth.block_number
                chain_status[chain_name] = {
                    "connected": True,
                    "latest_block": latest_block,
                    "contract_address": chainflip_messaging_service.contract_addresses.get(chain_name, "Not set")
                }
            except Exception as e:
                chain_status[chain_name] = {
                    "connected": False,
                    "error": str(e),
                    "contract_address": chainflip_messaging_service.contract_addresses.get(chain_name, "Not set")
                }
        
        return {
            "success": True,
            "service_initialized": is_initialized,
            "chains": chain_status,
            "contract_addresses": chainflip_messaging_service.contract_addresses
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }