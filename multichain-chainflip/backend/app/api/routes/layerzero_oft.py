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

@router.post("/test-enhanced-infrastructure")
async def test_enhanced_infrastructure_transfer():
    """
    Test cross-chain transfer with enhanced DVN/Executor infrastructure
    Uses the properly configured LayerZero V2 infrastructure
    """
    try:
        print(f"🚀 API: Testing enhanced infrastructure transfer")
        
        # Test with enhanced infrastructure
        test_request = {
            "from_chain": "arbitrum_sepolia",
            "to_chain": "base_sepolia",
            "from_address": "0xc6A050a538a9E857B4DCb4A33436280c202F6941",
            "to_address": "0x28918ecf013F32fAf45e05d62B4D9b207FCae784",
            "amount_eth": 0.001,
            "escrow_id": f"enhanced-infra-{int(time.time())}"
        }
        
        print(f"📤 From: {test_request['from_chain']} ({test_request['from_address']})")
        print(f"📥 To: {test_request['to_chain']} ({test_request['to_address']})")
        print(f"💰 Amount: {test_request['amount_eth']} ETH")
        print(f"🔧 Using: Enhanced DVN/Executor infrastructure")
        
        # Execute with enhanced infrastructure
        result = await layerzero_oft_bridge_service.transfer_eth_layerzero_oft(
            from_chain=test_request["from_chain"],
            to_chain=test_request["to_chain"],
            from_address=test_request["from_address"],
            to_address=test_request["to_address"],
            amount_eth=test_request["amount_eth"],
            escrow_id=test_request["escrow_id"]
        )
        
        if result["success"]:
            print(f"✅ API: Enhanced infrastructure transfer successful!")
            return {
                "success": True,
                "message": "Enhanced infrastructure transfer completed successfully",
                "infrastructure": "Enhanced DVN/Executor configuration",
                "test_parameters": test_request,
                "result": result
            }
        else:
            print(f"❌ API: Enhanced infrastructure transfer failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: Enhanced infrastructure transfer error: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced infrastructure transfer error: {str(e)}")

@router.get("/infrastructure-status")
async def get_infrastructure_status():
    """
    Get detailed LayerZero infrastructure status for all networks
    """
    try:
        # Get infrastructure status from the service
        networks = []
        
        for chain_name, config in layerzero_oft_bridge_service.oft_contracts.items():
            network_info = {
                "chain": chain_name,
                "chain_id": config["chain_id"],
                "layerzero_eid": config["layerzero_eid"],
                "oft_contract": config.get("oft_address"),
                "infrastructure": {
                    "endpoint": config.get("endpoint"),
                    "send_lib": config.get("send_lib"),
                    "receive_lib": config.get("receive_lib"),
                    "executor": config.get("executor"),
                    "dvn": config.get("dvn")
                },
                "rpc_url": config.get("rpc"),
                "status": "configured" if all([
                    config.get("send_lib"),
                    config.get("receive_lib"),
                    config.get("executor"),
                    config.get("dvn")
                ]) else "partial_config"
            }
            networks.append(network_info)
        
        return {
            "success": True,
            "message": "LayerZero infrastructure status",
            "infrastructure_version": "Enhanced DVN/Executor Configuration",
            "setup_required": "Run setup_layerzero_infrastructure.js if transfers fail",
            "chains": {
                chain_name: {
                    "status": "operational" if config.get("oft_address") else "not_configured",
                    "oft_address": config.get("oft_address"),
                    "layerzero_eid": config.get("layerzero_eid"),
                    "chain_id": config.get("chain_id")
                }
                for chain_name, config in layerzero_oft_bridge_service.oft_contracts.items()
            },
            "networks": networks,
            "test_endpoints": [
                "/test-enhanced-infrastructure - Test with enhanced config",
                "/test-transfer-arb-base - Alternative pathway test"
            ]
        }
        
    except Exception as e:
        print(f"❌ API: Infrastructure status error: {e}")
        raise HTTPException(status_code=500, detail=f"Infrastructure status error: {str(e)}")

@router.get("/transfers")
async def get_layerzero_transfers(limit: int = 20, offset: int = 0):
    """
    Get LayerZero transfer history
    """
    try:
        # Get database
        database = await layerzero_oft_bridge_service.get_database()
        
        # Query transfers from database
        cursor = database.transfers.find(
            {"bridge_type": {"$regex": "layerzero"}},
            sort=[("timestamp", -1)],
            limit=limit,
            skip=offset
        )
        
        transfers = []
        async for transfer in cursor:
            # Convert ObjectId to string if present
            if "_id" in transfer:
                del transfer["_id"]
            transfers.append(transfer)
        
        return {
            "success": True,
            "transfers": transfers,
            "count": len(transfers),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        print(f"❌ API: Get transfers error: {e}")
        raise HTTPException(status_code=500, detail=f"Get transfers error: {str(e)}")

@router.get("/status/{transfer_id}")
async def get_transfer_status(transfer_id: str):
    """
    Get status of a specific LayerZero transfer
    """
    try:
        # Get database
        database = await layerzero_oft_bridge_service.get_database()
        
        # Query specific transfer
        transfer = await database.transfers.find_one({"transfer_id": transfer_id})
        
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")
        
        # Convert ObjectId to string if present
        if "_id" in transfer:
            del transfer["_id"]
        
        return {
            "success": True,
            "transfer": transfer,
            "status": transfer.get("status", "unknown"),
            "transfer_id": transfer_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API: Get transfer status error: {e}")
        raise HTTPException(status_code=500, detail=f"Get transfer status error: {str(e)}")

# New Pydantic model for cross-chain messaging
class CrossChainMessageRequest(BaseModel):
    source_chain: str
    target_chain: str
    message_data: Dict[str, Any]
    recipient_address: str

@router.post("/send-message")
async def send_cross_chain_message(request: CrossChainMessageRequest):
    """
    Send cross-chain message using LayerZero OFT contracts
    This endpoint exposes the cross-chain messaging functionality
    """
    try:
        print(f"🌐 API: Sending cross-chain message")
        print(f"📤 From: {request.source_chain}")
        print(f"📥 To: {request.target_chain}")
        print(f"👤 Recipient: {request.recipient_address}")
        print(f"📋 Message Type: {request.message_data.get('type', 'Unknown')}")
        
        result = await layerzero_oft_bridge_service.send_cross_chain_message(
            source_chain=request.source_chain,
            target_chain=request.target_chain,
            message_data=request.message_data,
            recipient_address=request.recipient_address
        )
        
        if result["success"]:
            print(f"✅ API: Cross-chain message sent successfully!")
            return {
                "success": True,
                "message": "Cross-chain message sent successfully",
                "data": result
            }
        else:
            print(f"❌ API: Cross-chain message failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: Cross-chain message error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/send-cid-message")
async def send_cid_cross_chain_message(
    token_id: str,
    metadata_cid: str,
    manufacturer_address: str,
    source_chain: str = "base_sepolia",
    target_chain: str = "polygon_amoy",
    admin_address: str = "0x032041b4b356fEE1496805DD4749f181bC736FFA"
):
    """
    Send CID cross-chain message from manufacturer to admin
    Specifically for NFT CID synchronization after minting
    """
    try:
        print(f"📦 API: Sending CID cross-chain message")
        print(f"🆔 Token ID: {token_id}")
        print(f"📄 CID: {metadata_cid}")
        print(f"🏭 Manufacturer: {manufacturer_address}")
        print(f"🌐 Route: {source_chain} → {target_chain}")
        
        # Prepare message data for CID sync
        message_data = {
            "type": "CID_SYNC",
            "token_id": token_id,
            "metadata_cid": metadata_cid,
            "manufacturer": manufacturer_address,
            "timestamp": int(time.time()),
            "source_chain": source_chain
        }
        
        result = await layerzero_oft_bridge_service.send_cross_chain_message(
            source_chain=source_chain,
            target_chain=target_chain,
            message_data=message_data,
            recipient_address=admin_address
        )
        
        if result["success"]:
            print(f"✅ API: CID cross-chain message sent successfully!")
            return {
                "success": True,
                "message": "CID cross-chain message sent to admin successfully",
                "data": {
                    **result,
                    "cid_message": {
                        "token_id": token_id,
                        "metadata_cid": metadata_cid,
                        "manufacturer": manufacturer_address,
                        "admin_recipient": admin_address
                    }
                }
            }
        else:
            print(f"❌ API: CID cross-chain message failed: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        print(f"❌ API: CID cross-chain message error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")