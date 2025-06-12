"""
LayerZero OFT Bridge API Routes
Official LayerZero V2 OFT cross-chain transfer endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service

router = APIRouter()

class LayerZeroTransferRequest(BaseModel):
    from_chain: str
    to_chain: str
    from_address: str
    to_address: str
    amount_eth: float
    escrow_id: Optional[str] = None

class LayerZeroFeeEstimateRequest(BaseModel):
    from_chain: str
    to_chain: str
    amount_eth: float

class LayerZeroDepositRequest(BaseModel):
    chain: str
    user_address: str
    amount_eth: float

@router.post("/transfer")
async def execute_layerzero_oft_transfer(request: LayerZeroTransferRequest):
    """
    Execute LayerZero OFT cross-chain ETH transfer
    
    Automatically handles:
    - ETH → cfWETH conversion (deposit)
    - LayerZero cross-chain transfer
    - Transaction recording
    """
    try:
        print(f"🌉 API: Executing LayerZero OFT transfer")
        print(f"📤 From: {request.from_chain} ({request.from_address})")
        print(f"📥 To: {request.to_chain} ({request.to_address})")
        print(f"💰 Amount: {request.amount_eth} ETH")
        
        # Generate escrow ID if not provided
        if not request.escrow_id:
            import time
            request.escrow_id = f"layerzero-{int(time.time())}"
        
        # Execute the transfer
        result = await layerzero_oft_bridge_service.transfer_eth_layerzero_oft(
            from_chain=request.from_chain,
            to_chain=request.to_chain,
            from_address=request.from_address,
            to_address=request.to_address,
            amount_eth=request.amount_eth,
            escrow_id=request.escrow_id
        )
        
        if result["success"]:
            print(f"✅ API: LayerZero transfer successful!")
            return {
                "success": True,
                "message": "LayerZero OFT transfer completed successfully",
                "data": result
            }
        else:
            print(f"❌ API: LayerZero transfer failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: LayerZero transfer error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/estimate-fee")
async def estimate_layerzero_fee(request: LayerZeroFeeEstimateRequest):
    """
    Estimate LayerZero OFT transfer fee
    
    Returns the native token fee required for cross-chain transfer
    """
    try:
        print(f"💰 API: Estimating LayerZero fee for {request.from_chain} → {request.to_chain}")
        
        result = await layerzero_oft_bridge_service.estimate_oft_transfer_fee(
            from_chain=request.from_chain,
            to_chain=request.to_chain,
            amount_eth=request.amount_eth
        )
        
        if result["success"]:
            print(f"✅ API: Fee estimation successful: {result['native_fee_eth']} ETH")
            return {
                "success": True,
                "message": "Fee estimation completed",
                "data": result
            }
        else:
            print(f"❌ API: Fee estimation failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: Fee estimation error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/deposit")
async def deposit_eth_for_cfweth(request: LayerZeroDepositRequest):
    """
    Deposit ETH to get cfWETH tokens (1:1 ratio)
    
    NEW FEATURE: Users can deposit ETH and receive cfWETH tokens
    """
    try:
        print(f"💳 API: Depositing {request.amount_eth} ETH for cfWETH on {request.chain}")
        
        result = await layerzero_oft_bridge_service.deposit_eth_for_tokens(
            chain=request.chain,
            user_address=request.user_address,
            amount_eth=request.amount_eth
        )
        
        if result["success"]:
            print(f"✅ API: ETH deposit successful!")
            return {
                "success": True,
                "message": "ETH deposited for cfWETH tokens successfully",
                "data": result
            }
        else:
            print(f"❌ API: ETH deposit failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: ETH deposit error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status")
async def get_layerzero_status():
    """
    Get LayerZero OFT Bridge service status
    """
    try:
        # Check if service is initialized
        if not layerzero_oft_bridge_service.web3_connections:
            return {
                "success": False,
                "message": "LayerZero OFT Bridge service not initialized",
                "status": "offline"
            }
        
        networks = []
        for chain_name, config in layerzero_oft_bridge_service.oft_contracts.items():
            web3 = layerzero_oft_bridge_service.web3_connections.get(chain_name)
            oft_contract = layerzero_oft_bridge_service.oft_instances.get(chain_name)
            
            network_status = {
                "chain": chain_name,
                "chain_id": config["chain_id"],
                "layerzero_eid": config["layerzero_eid"],
                "oft_contract": config.get("oft_address", "Not configured"),
                "wrapper_contract": config.get("wrapper_address", "Not configured"),
                "rpc_connected": web3 is not None and web3.is_connected() if web3 else False,
                "contract_loaded": oft_contract is not None
            }
            networks.append(network_status)
        
        return {
            "success": True,
            "message": "LayerZero OFT Bridge service status",
            "status": "online",
            "networks": networks,
            "features": [
                "Cross-chain ETH transfers",
                "ETH deposit for cfWETH tokens",
                "Official LayerZero V2 OFT interface",
                "Separated architecture (ChainFlipOFT + ETHWrapper)",
                "Automatic fee estimation"
            ]
        }
        
    except Exception as e:
        print(f"❌ API: Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/networks")
async def get_supported_networks():
    """
    Get list of supported networks for LayerZero OFT transfers
    """
    try:
        networks = []
        for chain_name, config in layerzero_oft_bridge_service.oft_contracts.items():
            network_info = {
                "name": chain_name,
                "chain_id": config["chain_id"],
                "layerzero_eid": config["layerzero_eid"],
                "rpc_url": config["rpc"],
                "oft_contract": config.get("oft_address"),
                "wrapper_contract": config.get("wrapper_address"),
                "layerzero_endpoint": config.get("layerzero_endpoint")
            }
            networks.append(network_info)
        
        return {
            "success": True,
            "message": "Supported LayerZero OFT networks",
            "networks": networks,
            "total_networks": len(networks)
        }
        
    except Exception as e:
        print(f"❌ API: Networks list error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")