"""
LayerZero OFT Bridge API Routes
Official LayerZero V2 OFT cross-chain transfer endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import time
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

@router.post("/test-transfer")
async def test_cross_chain_transfer():
    """
    Test cross-chain transfer: 0.01 ETH from OP Sepolia to Base Sepolia
    Using the exact addresses specified by the user
    """
    try:
        print(f"🧪 API: Testing cross-chain transfer")
        
        # Fixed test parameters as requested by user
        test_request = {
            "from_chain": "optimism_sepolia",
            "to_chain": "base_sepolia", 
            "from_address": "0xc6A050a538a9E857B4DCb4A33436280c202F6941",  # OP Sepolia
            "to_address": "0x28918ecf013F32fAf45e05d62B4D9b207FCae784",    # Base Sepolia
            "amount_eth": 0.01,
            "escrow_id": f"test-transfer-{int(time.time())}"
        }
        
        print(f"📤 From: {test_request['from_chain']} ({test_request['from_address']})")
        print(f"📥 To: {test_request['to_chain']} ({test_request['to_address']})")
        print(f"💰 Amount: {test_request['amount_eth']} ETH")
        
        # Execute the transfer
        result = await layerzero_oft_bridge_service.transfer_eth_layerzero_oft(
            from_chain=test_request["from_chain"],
            to_chain=test_request["to_chain"],
            from_address=test_request["from_address"],
            to_address=test_request["to_address"],
            amount_eth=test_request["amount_eth"],
            escrow_id=test_request["escrow_id"]
        )
        
        if result["success"]:
            print(f"✅ API: Test transfer successful!")
            return {
                "success": True,
                "message": "Test cross-chain transfer completed successfully",
                "test_parameters": test_request,
                "result": result
            }
        else:
            print(f"❌ API: Test transfer failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: Test transfer error: {e}")
        raise HTTPException(status_code=500, detail=f"Test transfer error: {str(e)}")

@router.post("/test-transfer-arb-base")
async def test_cross_chain_transfer_arb_base():
    """
    Test cross-chain transfer: Arbitrum Sepolia → Base Sepolia
    Alternative pathway that might have better LayerZero support
    """
    try:
        print(f"🧪 API: Testing Arbitrum → Base transfer")
        
        # Use Arbitrum to Base pathway
        test_request = {
            "from_chain": "arbitrum_sepolia", 
            "to_chain": "base_sepolia",
            "from_address": "0xc6A050a538a9E857B4DCb4A33436280c202F6941",  # Same test address
            "to_address": "0x28918ecf013F32fAf45e05d62B4D9b207FCae784",    # Same target
            "amount_eth": 0.001,
            "escrow_id": f"arb-base-test-{int(time.time())}"
        }
        
        print(f"📤 From: {test_request['from_chain']} ({test_request['from_address']})")
        print(f"📥 To: {test_request['to_chain']} ({test_request['to_address']})")
        print(f"💰 Amount: {test_request['amount_eth']} ETH")
        
        # Execute the transfer
        result = await layerzero_oft_bridge_service.transfer_eth_layerzero_oft(
            from_chain=test_request["from_chain"],
            to_chain=test_request["to_chain"],
            from_address=test_request["from_address"],
            to_address=test_request["to_address"],
            amount_eth=test_request["amount_eth"],
            escrow_id=test_request["escrow_id"]
        )
        
        if result["success"]:
            print(f"✅ API: Arbitrum → Base transfer successful!")
            return {
                "success": True,
                "message": "Arbitrum → Base cross-chain transfer completed successfully",
                "test_parameters": test_request,
                "result": result
            }
        else:
            print(f"❌ API: Arbitrum → Base transfer failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: Arbitrum → Base transfer error: {e}")
        raise HTTPException(status_code=500, detail=f"Arbitrum → Base transfer error: {str(e)}")

@router.post("/test-transfer-base-arb")
async def test_cross_chain_transfer_base_arb():
    """
    Test cross-chain transfer: Base Sepolia → Arbitrum Sepolia
    Reverse direction test
    """
    try:
        print(f"🧪 API: Testing Base → Arbitrum transfer")
        
        # Use Base to Arbitrum pathway  
        test_request = {
            "from_chain": "base_sepolia",
            "to_chain": "arbitrum_sepolia", 
            "from_address": "0xc6A050a538a9E857B4DCb4A33436280c202F6941",  # Same test address
            "to_address": "0x28918ecf013F32fAf45e05d62B4D9b207FCae784",    # Same target
            "amount_eth": 0.001,
            "escrow_id": f"base-arb-test-{int(time.time())}"
        }
        
        print(f"📤 From: {test_request['from_chain']} ({test_request['from_address']})")
        print(f"📥 To: {test_request['to_chain']} ({test_request['to_address']})")
        print(f"💰 Amount: {test_request['amount_eth']} ETH")
        
        # Execute the transfer
        result = await layerzero_oft_bridge_service.transfer_eth_layerzero_oft(
            from_chain=test_request["from_chain"],
            to_chain=test_request["to_chain"],
            from_address=test_request["from_address"],
            to_address=test_request["to_address"],
            amount_eth=test_request["amount_eth"],
            escrow_id=test_request["escrow_id"]
        )
        
        if result["success"]:
            print(f"✅ API: Base → Arbitrum transfer successful!")
            return {
                "success": True,
                "message": "Base → Arbitrum cross-chain transfer completed successfully",
                "test_parameters": test_request,
                "result": result
            }
        else:
            print(f"❌ API: Base → Arbitrum transfer failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: Base → Arbitrum transfer error: {e}")
        raise HTTPException(status_code=500, detail=f"Base → Arbitrum transfer error: {str(e)}")