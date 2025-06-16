"""
NFT Product Transfer Orchestration Service
Handles cross-chain NFT transfers through transporter chain with escrow management

Transfer Flow:
1. Manufacturer mints NFT on their chain
2. NFT transferred to Transporter 1 on their chain
3. NFT passed through transporter chain (Transporter 1 → Transporter 2 → ... → Transporter N)
4. Final transfer to Buyer with escrow release
"""
import asyncio
import logging
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from motor.motor_asyncio import AsyncIOMotorDatabase
from web3 import Web3

from .supply_chain_orchestrator import supply_chain_orchestrator
from .layerzero_oft_bridge_service import layerzero_oft_bridge_service
from .blockchain_service import blockchain_service


class TransferStatus(Enum):
    PENDING = "pending"
    MINTED = "minted"
    ESCROWED = "escrowed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class NFTTransferStep:
    step_number: int
    from_address: str
    from_chain: str
    to_address: str
    to_chain: str
    step_type: str  # "mint", "transfer", "delivery"
    status: str
    transaction_hash: Optional[str] = None
    timestamp: Optional[datetime] = None
    gas_used: Optional[int] = None
    block_number: Optional[int] = None


@dataclass
class EscrowDetails:
    escrow_id: str
    buyer_address: str
    purchase_amount: float
    escrow_chain: str
    status: str  # "locked", "released", "refunded"
    created_at: datetime
    release_conditions: Dict[str, Any]


@dataclass
class ProductNFT:
    token_id: str
    contract_address: str
    current_owner: str
    current_chain: str
    metadata_uri: str
    product_id: str
    manufacturer: str
    status: str


class NFTTransferOrchestrator:
    """
    Orchestrates cross-chain NFT transfers through the supply chain
    Integrates with LayerZero for cross-chain transfers and manages escrow
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.database: Optional[AsyncIOMotorDatabase] = None
        
        # Chain configurations for NFT transfers
        self.nft_chains = {
            "base_sepolia": {
                "chain_id": 84532,
                "role": "manufacturer",
                "nft_contract": "0x60C466cF52cb9705974a89b72DeA045c45cb7572"  # SupplyChainNFT
            },
            "arbitrum_sepolia": {
                "chain_id": 421614,
                "role": "transporter",
                "nft_contract": "0x47FaF4084F4F69b705A6f947f020B59AA1993FD9"  # Cross-chain NFT
            },
            "optimism_sepolia": {
                "chain_id": 11155420,
                "role": "buyer",
                "nft_contract": "0x76D43CEC28775032A7EC8895ad178c660246c8Ec"  # Cross-chain NFT
            },
            "polygon_amoy": {
                "chain_id": 80002,
                "role": "hub",
                "nft_contract": "0x36DDc43D2FfA30588CcAC8C2979b69225c292a73"  # Hub NFT contract
            }
        }
        
        # Escrow configuration
        self.escrow_timeout = 7200  # 2 hours in seconds
        self.min_escrow_amount = 0.001  # Minimum escrow amount in ETH
        
    async def initialize(self):
        """Initialize the NFT transfer orchestrator"""
        try:
            self.database = await self.get_database()
            await self._ensure_collections()
            self.logger.info("✅ NFT Transfer Orchestrator initialized")
        except Exception as e:
            self.logger.error(f"❌ NFT Transfer Orchestrator initialization failed: {e}")
            raise
    
    async def get_database(self):
        """Get database instance"""
        if supply_chain_orchestrator.database:
            return supply_chain_orchestrator.database
        return None
    
    async def _ensure_collections(self):
        """Ensure required database collections exist"""
        collections = [
            "nft_transfers",
            "nft_escrows",
            "nft_transfer_steps",
            "nft_ownership_history"
        ]
        
        for collection in collections:
            await self.database[collection].create_index("timestamp")
        
        # Create specific indexes
        await self.database["nft_transfers"].create_index("token_id")
        await self.database["nft_transfers"].create_index("purchase_request_id")
        await self.database["nft_escrows"].create_index("escrow_id")
        await self.database["nft_transfer_steps"].create_index("transfer_id")
    
    # === MAIN TRANSFER ORCHESTRATION ===
    
    async def initiate_nft_transfer_flow(
        self,
        purchase_request_id: str,
        product_id: str,
        manufacturer_address: str,
        transporter_addresses: List[str],
        buyer_address: str,
        purchase_amount: float,
        product_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main function to initiate the complete NFT transfer flow
        
        1. Mint NFT (Manufacturer)
        2. Create Escrow (Buyer chain)
        3. Transfer through transporter chain
        4. Final delivery to buyer with escrow release
        """
        try:
            self.logger.info(f"🚀 Initiating NFT transfer flow for purchase: {purchase_request_id}")
            
            # Generate unique transfer ID
            transfer_id = f"NFT-TRANSFER-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}"
            
            # Step 1: Mint NFT on manufacturer chain
            self.logger.info(f"🏭 Step 1: Minting NFT on manufacturer chain")
            mint_result = await self.mint_product_nft(
                manufacturer_address=manufacturer_address,
                product_id=product_id,
                metadata=product_metadata,
                transfer_id=transfer_id
            )
            
            if not mint_result["success"]:
                return {"success": False, "error": f"NFT minting failed: {mint_result['error']}"}
            
            token_id = mint_result["token_id"]
            self.logger.info(f"✅ NFT minted successfully: Token ID {token_id}")
            
            # Step 2: Create escrow on buyer chain
            self.logger.info(f"💰 Step 2: Creating escrow on buyer chain")
            escrow_result = await self.create_escrow(
                buyer_address=buyer_address,
                purchase_amount=purchase_amount,
                token_id=token_id,
                transfer_id=transfer_id
            )
            
            if not escrow_result["success"]:
                return {"success": False, "error": f"Escrow creation failed: {escrow_result['error']}"}
            
            escrow_id = escrow_result["escrow_id"]
            self.logger.info(f"✅ Escrow created successfully: {escrow_id}")
            
            # Step 3: Plan transfer route through transporters
            transfer_route = await self._plan_transfer_route(
                manufacturer_address=manufacturer_address,
                transporter_addresses=transporter_addresses,
                buyer_address=buyer_address,
                token_id=token_id
            )
            
            # Step 4: Store transfer data in database
            transfer_data = {
                "transfer_id": transfer_id,
                "purchase_request_id": purchase_request_id,
                "token_id": token_id,
                "product_id": product_id,
                "manufacturer_address": manufacturer_address,
                "buyer_address": buyer_address,
                "transporter_addresses": transporter_addresses,
                "purchase_amount": purchase_amount,
                "escrow_id": escrow_id,
                "status": TransferStatus.MINTED.value,
                "transfer_route": transfer_route,
                "mint_transaction": mint_result.get("transaction_hash"),
                "escrow_transaction": escrow_result.get("transaction_hash"),
                "created_at": datetime.utcnow(),
                "current_step": 0,
                "total_steps": len(transfer_route)
            }
            
            await self.database["nft_transfers"].insert_one(transfer_data)
            
            return {
                "success": True,
                "transfer_id": transfer_id,
                "token_id": token_id,
                "escrow_id": escrow_id,
                "total_steps": len(transfer_route),
                "status": TransferStatus.MINTED.value,
                "mint_transaction": mint_result.get("transaction_hash"),
                "escrow_transaction": escrow_result.get("transaction_hash"),
                "message": f"NFT transfer flow initiated with {len(transporter_addresses)} transporters"
            }
            
        except Exception as e:
            self.logger.error(f"❌ NFT transfer flow initiation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_next_transfer_step(self, transfer_id: str) -> Dict[str, Any]:
        """
        Execute the next step in the NFT transfer chain
        Called by transporters or automatically by the system
        """
        try:
            self.logger.info(f"🔄 Executing next transfer step for: {transfer_id}")
            
            # Get transfer data
            transfer_doc = await self.database["nft_transfers"].find_one({"transfer_id": transfer_id})
            if not transfer_doc:
                return {"success": False, "error": "Transfer not found"}
            
            current_step = transfer_doc["current_step"]
            transfer_route = transfer_doc["transfer_route"]
            
            if current_step >= len(transfer_route):
                return {"success": False, "error": "All transfer steps completed"}
            
            # Get current step details
            step_data = transfer_route[current_step]
            step_number = current_step + 1
            
            self.logger.info(f"📦 Executing step {step_number}: {step_data['from_address']} → {step_data['to_address']}")
            
            # Execute the transfer based on step type
            if step_data["step_type"] == "cross_chain_transfer":
                transfer_result = await self._execute_cross_chain_transfer(
                    transfer_id=transfer_id,
                    step_data=step_data,
                    token_id=transfer_doc["token_id"]
                )
            elif step_data["step_type"] == "final_delivery":
                transfer_result = await self._execute_final_delivery(
                    transfer_id=transfer_id,
                    step_data=step_data,
                    token_id=transfer_doc["token_id"],
                    escrow_id=transfer_doc["escrow_id"]
                )
            else:
                return {"success": False, "error": f"Unknown step type: {step_data['step_type']}"}
            
            if transfer_result["success"]:
                # Update transfer progress
                await self._update_transfer_progress(transfer_id, step_number, transfer_result)
                
                # Check if this is the final step
                if step_number >= len(transfer_route):
                    await self._complete_transfer(transfer_id)
                    return {
                        "success": True,
                        "step_completed": step_number,
                        "transfer_completed": True,
                        "transaction_hash": transfer_result.get("transaction_hash"),
                        "message": "NFT transfer flow completed successfully!"
                    }
                else:
                    return {
                        "success": True,
                        "step_completed": step_number,
                        "next_step": step_number + 1,
                        "transaction_hash": transfer_result.get("transaction_hash"),
                        "message": f"Step {step_number} completed. Ready for next step."
                    }
            else:
                await self._handle_transfer_failure(transfer_id, step_number, transfer_result)
                return {"success": False, "error": f"Step {step_number} failed: {transfer_result['error']}"}
            
        except Exception as e:
            self.logger.error(f"❌ Transfer step execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    # === NFT MINTING ===
    
    async def mint_product_nft(
        self,
        manufacturer_address: str,
        product_id: str,
        metadata: Dict[str, Any],
        transfer_id: str
    ) -> Dict[str, Any]:
        """
        Mint NFT on manufacturer chain (Base Sepolia)
        """
        try:
            self.logger.info(f"🏭 Minting NFT for product: {product_id}")
            
            # Use existing blockchain service to mint NFT
            mint_result = await blockchain_service.mint_product_nft(
                manufacturer=manufacturer_address,
                metadata=metadata
            )
            
            if mint_result["success"]:
                # Record NFT ownership
                await self._record_nft_ownership(
                    token_id=mint_result["token_id"],
                    owner_address=manufacturer_address,
                    chain="base_sepolia",
                    transaction_hash=mint_result["transaction_hash"],
                    action="mint"
                )
                
                return {
                    "success": True,
                    "token_id": mint_result["token_id"],
                    "transaction_hash": mint_result["transaction_hash"],
                    "contract_address": mint_result.get("contract_address"),
                    "metadata_uri": mint_result.get("token_uri")
                }
            else:
                return {"success": False, "error": "NFT minting failed"}
                
        except Exception as e:
            self.logger.error(f"❌ NFT minting error: {e}")
            return {"success": False, "error": str(e)}
    
    # === ESCROW MANAGEMENT ===
    
    async def create_escrow(
        self,
        buyer_address: str,
        purchase_amount: float,
        token_id: str,
        transfer_id: str
    ) -> Dict[str, Any]:
        """
        Create escrow on buyer chain (Optimism Sepolia)
        """
        try:
            self.logger.info(f"💰 Creating escrow: {purchase_amount} ETH for token {token_id}")
            
            if purchase_amount < self.min_escrow_amount:
                return {"success": False, "error": f"Escrow amount must be at least {self.min_escrow_amount} ETH"}
            
            # Generate unique escrow ID
            escrow_id = f"ESCROW-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}"
            
            # For now, we'll simulate escrow creation
            # In a real implementation, this would deploy a smart contract or use LayerZero
            mock_tx_hash = f"0x{uuid.uuid4().hex}"
            
            # Store escrow details
            escrow_data = {
                "escrow_id": escrow_id,
                "transfer_id": transfer_id,
                "buyer_address": buyer_address,
                "token_id": token_id,
                "purchase_amount": purchase_amount,
                "escrow_chain": "optimism_sepolia",
                "status": "locked",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow().timestamp() + self.escrow_timeout,
                "transaction_hash": mock_tx_hash,
                "release_conditions": {
                    "nft_delivery_confirmed": False,
                    "buyer_confirmation": False,
                    "timeout_reached": False
                }
            }
            
            await self.database["nft_escrows"].insert_one(escrow_data)
            
            self.logger.info(f"✅ Escrow created: {escrow_id}")
            
            return {
                "success": True,
                "escrow_id": escrow_id,
                "transaction_hash": mock_tx_hash,
                "amount": purchase_amount,
                "expires_at": escrow_data["expires_at"]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Escrow creation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def release_escrow(self, escrow_id: str) -> Dict[str, Any]:
        """
        Release escrow funds to manufacturer after successful delivery
        """
        try:
            self.logger.info(f"🔓 Releasing escrow: {escrow_id}")
            
            # Get escrow data
            escrow_doc = await self.database["nft_escrows"].find_one({"escrow_id": escrow_id})
            if not escrow_doc:
                return {"success": False, "error": "Escrow not found"}
            
            if escrow_doc["status"] != "locked":
                return {"success": False, "error": f"Escrow not in locked state: {escrow_doc['status']}"}
            
            # Simulate escrow release transaction
            release_tx_hash = f"0x{uuid.uuid4().hex}"
            
            # Update escrow status
            await self.database["nft_escrows"].update_one(
                {"escrow_id": escrow_id},
                {
                    "$set": {
                        "status": "released",
                        "released_at": datetime.utcnow(),
                        "release_transaction": release_tx_hash
                    }
                }
            )
            
            self.logger.info(f"✅ Escrow released: {escrow_id}")
            
            return {
                "success": True,
                "escrow_id": escrow_id,
                "release_transaction": release_tx_hash,
                "amount_released": escrow_doc["purchase_amount"]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Escrow release error: {e}")
            return {"success": False, "error": str(e)}
    
    # === TRANSFER ROUTE PLANNING ===
    
    async def _plan_transfer_route(
        self,
        manufacturer_address: str,
        transporter_addresses: List[str],
        buyer_address: str,
        token_id: str
    ) -> List[Dict[str, Any]]:
        """
        Plan the transfer route through the transporter chain
        """
        route = []
        step_number = 1
        
        # Current holder starts with manufacturer
        current_holder = manufacturer_address
        current_chain = "base_sepolia"  # Manufacturer chain
        
        # Transfer through each transporter
        for i, transporter_address in enumerate(transporter_addresses):
            target_chain = "arbitrum_sepolia"  # Transporters are on Arbitrum
            
            route.append({
                "step_number": step_number,
                "from_address": current_holder,
                "from_chain": current_chain,
                "to_address": transporter_address,
                "to_chain": target_chain,
                "step_type": "cross_chain_transfer",
                "status": "pending"
            })
            
            current_holder = transporter_address
            current_chain = target_chain
            step_number += 1
        
        # Final transfer to buyer
        buyer_chain = "optimism_sepolia"  # Buyers are on Optimism
        route.append({
            "step_number": step_number,
            "from_address": current_holder,
            "from_chain": current_chain,
            "to_address": buyer_address,
            "to_chain": buyer_chain,
            "step_type": "final_delivery",
            "status": "pending"
        })
        
        return route
    
    # === CROSS-CHAIN TRANSFER EXECUTION ===
    
    async def _execute_cross_chain_transfer(
        self,
        transfer_id: str,
        step_data: Dict[str, Any],
        token_id: str
    ) -> Dict[str, Any]:
        """
        Execute cross-chain NFT transfer using LayerZero
        """
        try:
            self.logger.info(f"🌐 Executing cross-chain transfer: {step_data['from_chain']} → {step_data['to_chain']}")
            
            # Use LayerZero service for cross-chain NFT transfer
            # For now, we'll simulate this since we need specific NFT transfer contracts
            transfer_result = await self._simulate_cross_chain_nft_transfer(
                from_address=step_data["from_address"],
                from_chain=step_data["from_chain"],
                to_address=step_data["to_address"],
                to_chain=step_data["to_chain"],
                token_id=token_id
            )
            
            if transfer_result["success"]:
                # Record ownership change
                await self._record_nft_ownership(
                    token_id=token_id,
                    owner_address=step_data["to_address"],
                    chain=step_data["to_chain"],
                    transaction_hash=transfer_result["transaction_hash"],
                    action="cross_chain_transfer"
                )
            
            return transfer_result
            
        except Exception as e:
            self.logger.error(f"❌ Cross-chain transfer error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_final_delivery(
        self,
        transfer_id: str,
        step_data: Dict[str, Any],
        token_id: str,
        escrow_id: str
    ) -> Dict[str, Any]:
        """
        Execute final delivery to buyer and release escrow
        """
        try:
            self.logger.info(f"📦 Executing final delivery to buyer: {step_data['to_address']}")
            
            # Transfer NFT to buyer
            transfer_result = await self._execute_cross_chain_transfer(transfer_id, step_data, token_id)
            
            if transfer_result["success"]:
                # Release escrow
                escrow_result = await self.release_escrow(escrow_id)
                
                if escrow_result["success"]:
                    return {
                        "success": True,
                        "transaction_hash": transfer_result["transaction_hash"],
                        "escrow_release_tx": escrow_result["release_transaction"],
                        "message": "Final delivery completed and escrow released"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"NFT transferred but escrow release failed: {escrow_result['error']}"
                    }
            else:
                return transfer_result
                
        except Exception as e:
            self.logger.error(f"❌ Final delivery error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _simulate_cross_chain_nft_transfer(
        self,
        from_address: str,
        from_chain: str,
        to_address: str,
        to_chain: str,
        token_id: str
    ) -> Dict[str, Any]:
        """
        Simulate cross-chain NFT transfer
        In production, this would use LayerZero OFT for NFTs
        """
        try:
            # Generate realistic transaction hash
            tx_hash = f"0x{uuid.uuid4().hex}"
            
            # Simulate network delay
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "from_address": from_address,
                "from_chain": from_chain,
                "to_address": to_address,
                "to_chain": to_chain,
                "token_id": token_id,
                "gas_used": 150000,
                "block_number": int(time.time()),
                "transfer_method": "layerzero_oft_simulation"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # === HELPER FUNCTIONS ===
    
    async def _record_nft_ownership(
        self,
        token_id: str,
        owner_address: str,
        chain: str,
        transaction_hash: str,
        action: str
    ):
        """Record NFT ownership change in history"""
        try:
            ownership_record = {
                "token_id": token_id,
                "owner_address": owner_address,
                "chain": chain,
                "action": action,
                "transaction_hash": transaction_hash,
                "timestamp": datetime.utcnow(),
                "block_number": int(time.time())  # Simulated
            }
            
            await self.database["nft_ownership_history"].insert_one(ownership_record)
            self.logger.info(f"📝 Recorded NFT ownership: {token_id} → {owner_address} on {chain}")
            
        except Exception as e:
            self.logger.error(f"❌ Ownership recording error: {e}")
    
    async def _update_transfer_progress(
        self,
        transfer_id: str,
        completed_step: int,
        transfer_result: Dict[str, Any]
    ):
        """Update transfer progress in database"""
        try:
            # Update main transfer record
            await self.database["nft_transfers"].update_one(
                {"transfer_id": transfer_id},
                {
                    "$set": {
                        "current_step": completed_step,
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            # Record step completion
            step_record = {
                "transfer_id": transfer_id,
                "step_number": completed_step,
                "status": "completed",
                "transaction_hash": transfer_result.get("transaction_hash"),
                "gas_used": transfer_result.get("gas_used"),
                "block_number": transfer_result.get("block_number"),
                "completed_at": datetime.utcnow()
            }
            
            await self.database["nft_transfer_steps"].insert_one(step_record)
            
        except Exception as e:
            self.logger.error(f"❌ Progress update error: {e}")
    
    async def _complete_transfer(self, transfer_id: str):
        """Mark transfer as completed"""
        try:
            await self.database["nft_transfers"].update_one(
                {"transfer_id": transfer_id},
                {
                    "$set": {
                        "status": TransferStatus.DELIVERED.value,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            self.logger.info(f"✅ Transfer completed: {transfer_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Transfer completion error: {e}")
    
    async def _handle_transfer_failure(
        self,
        transfer_id: str,
        failed_step: int,
        error_result: Dict[str, Any]
    ):
        """Handle transfer failure"""
        try:
            await self.database["nft_transfers"].update_one(
                {"transfer_id": transfer_id},
                {
                    "$set": {
                        "status": TransferStatus.FAILED.value,
                        "failed_at": datetime.utcnow(),
                        "failed_step": failed_step,
                        "failure_reason": error_result.get("error")
                    }
                }
            )
            
            self.logger.error(f"❌ Transfer failed: {transfer_id} at step {failed_step}")
            
        except Exception as e:
            self.logger.error(f"❌ Transfer failure handling error: {e}")
    
    # === PUBLIC API METHODS ===
    
    async def get_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Get detailed status of an NFT transfer"""
        try:
            transfer_doc = await self.database["nft_transfers"].find_one({"transfer_id": transfer_id})
            
            if not transfer_doc:
                return {"found": False, "error": "Transfer not found"}
            
            # Get transfer steps
            steps_cursor = self.database["nft_transfer_steps"].find(
                {"transfer_id": transfer_id}
            ).sort("step_number", 1)
            
            steps = await steps_cursor.to_list(length=100)
            
            # Get escrow status
            escrow_doc = await self.database["nft_escrows"].find_one({"escrow_id": transfer_doc["escrow_id"]})
            
            return {
                "found": True,
                "transfer_id": transfer_id,
                "token_id": transfer_doc["token_id"],
                "status": transfer_doc["status"],
                "current_step": transfer_doc["current_step"],
                "total_steps": transfer_doc["total_steps"],
                "progress_percentage": (transfer_doc["current_step"] / transfer_doc["total_steps"]) * 100,
                "escrow_status": escrow_doc["status"] if escrow_doc else "unknown",
                "completed_steps": len(steps),
                "steps": [
                    {
                        "step_number": step["step_number"],
                        "status": step["status"],
                        "transaction_hash": step.get("transaction_hash"),
                        "completed_at": step.get("completed_at").isoformat() if step.get("completed_at") else None
                    }
                    for step in steps
                ],
                "created_at": transfer_doc["created_at"].isoformat(),
                "last_updated": transfer_doc.get("last_updated", transfer_doc["created_at"]).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Transfer status error: {e}")
            return {"found": False, "error": str(e)}


# Global instance
nft_transfer_orchestrator = NFTTransferOrchestrator()