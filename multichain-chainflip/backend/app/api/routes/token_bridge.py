"""
Token Bridge API Routes for Real Cross-Chain ETH Transfers
Updated to use real WETH contracts for actual token movement
"""
import time
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.services.real_weth_bridge_service import real_weth_bridge_service
from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service

router = APIRouter()

# Pydantic Models for Request/Response
class TokenTransferRequest(BaseModel):
    from_chain: str = Field(..., description="Source chain name (e.g., 'optimism_sepolia')")
    to_chain: str = Field(..., description="Destination chain name (e.g., 'zkevm_cardona')")
    from_address: str = Field(..., description="Sender wallet address")
    to_address: str = Field(..., description="Recipient wallet address")
    amount_eth: float = Field(..., gt=0, description="Amount in ETH to transfer")
    escrow_id: Optional[str] = Field(None, description="Associated escrow ID for tracking")

class BalanceRequest(BaseModel):
    chain_name: str = Field(..., description="Chain name to check balance on")
    address: str = Field(..., description="Wallet address to check")

class FeeEstimateRequest(BaseModel):
    from_chain: str = Field(..., description="Source chain name")
    to_chain: str = Field(..., description="Destination chain name")
    amount_eth: float = Field(..., gt=0, description="Amount in ETH")

class TransferStatusRequest(BaseModel):
    transfer_id: str = Field(..., description="Transfer ID to check status")

class TokenTransferResponse(BaseModel):
    success: bool
    transfer_id: Optional[str] = None
    wrap_transaction_hash: Optional[str] = None
    transfer_transaction_hash: Optional[str] = None
    amount_transferred: Optional[float] = None
    actual_token_movement: Optional[bool] = None
    gas_used: Optional[Dict[str, int]] = None
    error: Optional[str] = None

class BalanceResponse(BaseModel):
    success: bool
    chain: Optional[str] = None
    address: Optional[str] = None
    eth_balance: Optional[float] = None
    weth_balance: Optional[float] = None
    total_balance: Optional[float] = None
    using_real_contracts: Optional[bool] = None
    error: Optional[str] = None

class FeeEstimateResponse(BaseModel):
    success: bool
    from_chain: Optional[str] = None
    to_chain: Optional[str] = None
    estimated_gas_fee: Optional[float] = None
    layerzero_fee: Optional[float] = None
    total_fee_eth: Optional[float] = None
    error: Optional[str] = None

class TransferStatusResponse(BaseModel):
    success: bool
    transfer: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    completion_time: Optional[float] = None
    actual_token_movement: Optional[bool] = None
    error: Optional[str] = None

@router.get("/status", response_model=Dict[str, Any])
async def get_token_bridge_status():
    """Get real WETH bridge service status and chain connectivity"""
    try:
        # Check if real WETH bridge service is initialized
        if not hasattr(real_weth_bridge_service, 'database') or real_weth_bridge_service.database is None:
            await real_weth_bridge_service.initialize()
        
        # Get chain connection status
        chain_status = {}
        chains = ['optimism_sepolia', 'polygon_pos', 'zkevm_cardona', 'arbitrum_sepolia']
        
        for chain in chains:
            web3 = real_weth_bridge_service.web3_connections.get(chain)
            weth_config = real_weth_bridge_service.weth_contracts.get(chain)
            
            if web3 and web3.is_connected():
                try:
                    latest_block = web3.eth.block_number
                    chain_status[chain] = {
                        "connected": True,
                        "latest_block": latest_block,
                        "weth_contract": weth_config['address'] if weth_config else "N/A",
                        "chain_id": weth_config['chain_id'] if weth_config else "N/A",
                        "real_weth": True
                    }
                except Exception as e:
                    chain_status[chain] = {"connected": False, "error": str(e)}
            else:
                chain_status[chain] = {"connected": False, "error": "Web3 connection not available"}
        
        return {
            "success": True,
            "service_initialized": real_weth_bridge_service.database is not None,
            "chains": chain_status,
            "supported_chains": list(chains),
            "real_weth_enabled": True,
            "actual_token_movement": True,
            "bridge_type": "real_weth_contracts",
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }

@router.post("/transfer", response_model=Dict[str, Any])
async def transfer_tokens_cross_chain(request: TokenTransferRequest):
    """Execute cross-chain ETH transfer using LayerZero OFT or Real WETH bridge"""
    try:
        # Generate escrow ID if not provided
        escrow_id = request.escrow_id or f"BRIDGE-{int(time.time())}-{request.from_address[-6:]}"
        
        print(f"\n🌉 === CROSS-CHAIN TRANSFER REQUEST ===")
        print(f"From: {request.from_chain} → To: {request.to_chain}")
        print(f"Amount: {request.amount_eth} ETH")
        print(f"From: {request.from_address} → To: {request.to_address}")
        print(f"Escrow ID: {escrow_id}")
        
        # Try LayerZero OFT transfer first (new decentralized method)
        if layerzero_oft_bridge_service.database is None:
            await layerzero_oft_bridge_service.initialize()
        
        print(f"🔄 Attempting LayerZero OFT transfer...")
        oft_result = await layerzero_oft_bridge_service.transfer_eth_layerzero_oft(
            request.from_chain,
            request.to_chain,
            request.from_address,
            request.to_address,
            request.amount_eth,
            escrow_id
        )
        
        if oft_result["success"]:
            print(f"✅ LayerZero OFT transfer successful!")
            return {
                "success": True,
                "transfer_id": escrow_id,
                "bridge_type": "LayerZero OFT",
                "amount_transferred": request.amount_eth,
                "wrap_transaction_hash": oft_result.get("wrap_transaction_hash"),
                "approve_transaction_hash": oft_result.get("approve_transaction_hash"),
                "oft_transaction_hash": oft_result.get("oft_transaction_hash"),
                "layerzero_guid": oft_result.get("layerzero_guid"),
                "native_fee_paid": oft_result.get("native_fee_paid"),
                "is_decentralized": True,
                "message": "LayerZero OFT cross-chain transfer completed successfully",
                "timestamp": time.time()
            }
        
        # Check if it failed due to missing OFT deployment
        if oft_result.get("deployment_needed") or "OFT contracts not deployed" in oft_result.get("error", ""):
            print(f"⚠️ LayerZero OFT contracts not deployed yet, falling back to Real WETH bridge")
            
            # Fallback to Real WETH bridge (existing custodial method)
            if real_weth_bridge_service.database is None:
                await real_weth_bridge_service.initialize()
            
            print(f"🔄 Attempting Real WETH bridge transfer...")
            weth_result = await real_weth_bridge_service.transfer_eth_cross_chain(
                request.from_chain,
                request.to_chain,
                request.from_address,
                request.to_address,
                request.amount_eth,
                escrow_id
            )
            
            if weth_result["success"]:
                print(f"✅ Real WETH bridge transfer successful!")
                return {
                    "success": True,
                    "transfer_id": escrow_id,
                    "bridge_type": "Real WETH (Custodial)",
                    "amount_transferred": request.amount_eth,
                    "wrap_transaction_hash": weth_result.get("wrap_transaction_hash"),
                    "layerzero_transaction_hash": weth_result.get("bridge_transaction_hash"),
                    "is_decentralized": False,
                    "message": "Real WETH cross-chain transfer completed successfully",
                    "deployment_note": "Deploy LayerZero OFT contracts for decentralized bridging",
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "error": f"Both LayerZero OFT and Real WETH transfers failed. OFT: {oft_result.get('error')}. WETH: {weth_result.get('error')}",
                    "timestamp": time.time()
                }
        else:
            # OFT available but failed for other reasons
            return {
                "success": False,
                "error": f"LayerZero OFT transfer failed: {oft_result.get('error')}",
                "timestamp": time.time()
            }
        
    except Exception as e:
        print(f"❌ Transfer execution error: {e}")
        return {
            "success": False,
            "error": f"Transfer execution failed: {str(e)}",
            "timestamp": time.time()
        }

@router.post("/balance", response_model=BalanceResponse)
async def get_chain_balance(request: BalanceRequest):
    """Get ETH and WETH balance for an address using real contracts"""
    try:
        # Initialize service if needed
        if not hasattr(real_weth_bridge_service, 'database') or real_weth_bridge_service.database is None:
            await real_weth_bridge_service.initialize()
        
        result = await real_weth_bridge_service.get_balance_on_chain(
            chain_name=request.chain_name,
            address=request.address
        )
        
        if result["success"]:
            return BalanceResponse(
                success=True,
                chain=result.get("chain"),
                address=result.get("address"),
                eth_balance=result.get("eth_balance"),
                weth_balance=result.get("weth_balance"),
                total_balance=result.get("total_balance"),
                using_real_contracts=result.get("using_real_contracts", True)
            )
        else:
            return BalanceResponse(
                success=False,
                error=result.get("error", "Balance check failed")
            )
            
    except Exception as e:
        return BalanceResponse(
            success=False,
            error=f"Balance check error: {str(e)}"
        )

@router.post("/estimate-fee", response_model=Dict[str, Any])
async def estimate_transfer_fee(request: FeeEstimateRequest):
    """Estimate cross-chain transfer fees using LayerZero OFT or Real WETH"""
    try:
        # Try LayerZero OFT estimation first (new method)
        if layerzero_oft_bridge_service.database is None:
            await layerzero_oft_bridge_service.initialize()
        
        oft_estimate = await layerzero_oft_bridge_service.estimate_oft_transfer_fee(
            request.from_chain,
            request.to_chain,
            request.amount_eth
        )
        
        if oft_estimate["success"]:
            return {
                "success": True,
                "from_chain": request.from_chain,
                "to_chain": request.to_chain,
                "amount_eth": request.amount_eth,
                "bridge_type": "LayerZero OFT",
                "native_fee_eth": oft_estimate["native_fee_eth"],
                "total_fee_eth": oft_estimate["native_fee_eth"],
                "total_cost_eth": oft_estimate["total_cost_eth"],
                "is_decentralized": True,
                "deployment_needed": oft_estimate.get("deployment_needed", False),
                "timestamp": time.time()
            }
        
        # Fallback to Real WETH bridge if OFT not available
        print("⚠️ LayerZero OFT not available, falling back to Real WETH bridge")
        
        # Initialize WETH service if not already done
        if real_weth_bridge_service.database is None:
            await real_weth_bridge_service.initialize()
        
        # Simplified fee estimation for WETH bridge
        base_gas_fee = 0.005  # 0.005 ETH base gas fee
        layerzero_fee = 0.001  # 0.001 ETH LayerZero messaging fee
        total_fee = base_gas_fee + layerzero_fee
        
        return {
            "success": True,
            "from_chain": request.from_chain,
            "to_chain": request.to_chain,
            "amount_eth": request.amount_eth,
            "estimated_gas_fee": base_gas_fee,
            "layerzero_fee": layerzero_fee,
            "total_fee_eth": total_fee,
            "total_cost_eth": request.amount_eth + total_fee,
            "bridge_type": "Real WETH (Custodial)",
            "is_decentralized": False,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return FeeEstimateResponse(
            success=False,
            error=f"Fee estimation error: {str(e)}"
        )

@router.post("/status/{transfer_id}", response_model=TransferStatusResponse)
async def get_transfer_status(transfer_id: str):
    """Get status of a specific real WETH transfer"""
    try:
        # Initialize service if needed
        if not hasattr(real_weth_bridge_service, 'database') or real_weth_bridge_service.database is None:
            await real_weth_bridge_service.initialize()
        
        result = await real_weth_bridge_service.get_transfer_status(transfer_id)
        
        if result["success"]:
            return TransferStatusResponse(
                success=True,
                transfer=result.get("transfer"),
                status=result.get("status"),
                completion_time=result.get("completion_time"),
                actual_token_movement=result.get("actual_token_movement", True)
            )
        else:
            return TransferStatusResponse(
                success=False,
                error=result.get("error", "Transfer not found")
            )
            
    except Exception as e:
        return TransferStatusResponse(
            success=False,
            error=f"Status check error: {str(e)}"
        )

@router.get("/transfers", response_model=Dict[str, Any])
async def get_all_transfers(limit: int = 50, skip: int = 0):
    """Get list of all real WETH transfers"""
    try:
        # Initialize service if needed
        if not hasattr(real_weth_bridge_service, 'database') or real_weth_bridge_service.database is None:
            await real_weth_bridge_service.initialize()
        
        # Query transfers from database
        transfers = await real_weth_bridge_service.database.token_transfers.find(
            {},
            {"_id": 0}  # Exclude MongoDB _id field
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(length=limit)
        
        total_count = await real_weth_bridge_service.database.token_transfers.count_documents({})
        
        return {
            "success": True,
            "transfers": transfers,
            "total_count": total_count,
            "returned_count": len(transfers),
            "skip": skip,
            "limit": limit,
            "using_real_contracts": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch transfers: {str(e)}"
        }

@router.get("/chains", response_model=Dict[str, Any])
async def get_supported_chains():
    """Get list of supported chains with real WETH contracts"""
    try:
        chains_info = {
            "optimism_sepolia": {
                "name": "Optimism Sepolia",
                "role": "Buyer Chain", 
                "chain_id": 11155420,
                "weth_contract": "0x4200000000000000000000000000000000000006",
                "native_token": "ETH",
                "real_weth": True
            },
            "polygon_pos": {
                "name": "Polygon PoS (Amoy)",
                "role": "Hub Chain",
                "chain_id": 80002,
                "weth_contract": "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889",
                "native_token": "MATIC",
                "real_weth": True
            },
            "zkevm_cardona": {
                "name": "zkEVM Cardona",
                "role": "Manufacturer Chain",
                "chain_id": 2442,
                "weth_contract": "0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9",
                "native_token": "ETH",
                "real_weth": True
            },
            "arbitrum_sepolia": {
                "name": "Arbitrum Sepolia",
                "role": "Transporter Chain",
                "chain_id": 421614,
                "weth_contract": "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73",
                "native_token": "ETH",
                "real_weth": True
            }
        }
        
        # Check connectivity for each chain
        for chain_key in chains_info:
            if hasattr(real_weth_bridge_service, 'database') and real_weth_bridge_service.database:
                web3 = real_weth_bridge_service.web3_connections.get(chain_key)
                chains_info[chain_key]["connected"] = web3 is not None and web3.is_connected()
            else:
                chains_info[chain_key]["connected"] = False
        
        return {
            "success": True,
            "supported_chains": chains_info,
            "total_chains": len(chains_info),
            "real_weth_enabled": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get chain info: {str(e)}"
        }

@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_token_bridge():
    """Manually initialize the real WETH bridge service"""
    try:
        await real_weth_bridge_service.initialize()
        
        return {
            "success": True,
            "message": "Real WETH bridge service initialized successfully",
            "using_real_contracts": True,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Initialization failed: {str(e)}",
            "timestamp": time.time()
        }
