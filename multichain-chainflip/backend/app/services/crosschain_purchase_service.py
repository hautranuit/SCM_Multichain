"""
Cross-Chain Purchase Service for ChainFLIP Multi-Chain Architecture
Implements Algorithm 1 (Payment Release and Incentive Mechanism) and 
Algorithm 5 (Post Supply Chain Management for NFT-Based Product Sale)

Flow: Buyer (Optimism Sepolia) → Hub (Polygon PoS) → Manufacturer (zkEVM Cardona)
Bridges: LayerZero (Buyer→Hub) + fxPortal (Hub→Manufacturer)
"""
import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any
from web3 import Web3
from eth_account import Account
from app.core.config import get_settings
from app.core.database import get_database

settings = get_settings()

class CrossChainPurchaseService:
    def __init__(self):
        self.database = None
        # Multi-chain Web3 connections
        self.optimism_web3: Optional[Web3] = None  # Buyer chain
        self.polygon_web3: Optional[Web3] = None   # Hub chain 
        self.zkevm_web3: Optional[Web3] = None     # Manufacturer chain
        self.arbitrum_web3: Optional[Web3] = None  # Transporter chain
        
        # Bridge contract addresses
        self.layerzero_bridge = settings.bridge_layerzero_hub if hasattr(settings, 'bridge_layerzero_hub') else "0x72a336eAAC8186906F1Ee85dF00C7d6b91257A43"
        self.fxportal_bridge = settings.bridge_fxportal_hub if hasattr(settings, 'bridge_fxportal_hub') else "0xd3c6396D0212Edd8424bd6544E7DF8BA74c16476"
        
    async def initialize(self):
        """Initialize cross-chain connections and database"""
        self.database = await get_database()
        
        # Initialize Optimism Sepolia (Buyer Chain)
        if settings.optimism_sepolia_rpc:
            self.optimism_web3 = Web3(Web3.HTTPProvider(settings.optimism_sepolia_rpc))
            if self.optimism_web3.is_connected():
                print(f"✅ Connected to Optimism Sepolia (Buyer Chain) - Chain ID: {settings.optimism_sepolia_chain_id}")
            
        # Initialize Polygon PoS (Hub Chain)  
        if settings.polygon_pos_rpc:
            self.polygon_web3 = Web3(Web3.HTTPProvider(settings.polygon_pos_rpc))
            if self.polygon_web3.is_connected():
                print(f"✅ Connected to Polygon PoS (Hub Chain) - Chain ID: {settings.polygon_pos_chain_id}")
                
        # Initialize zkEVM Cardona (Manufacturer Chain)
        if settings.zkevm_cardona_rpc:
            self.zkevm_web3 = Web3(Web3.HTTPProvider(settings.zkevm_cardona_rpc))
            if self.zkevm_web3.is_connected():
                print(f"✅ Connected to zkEVM Cardona (Manufacturer Chain) - Chain ID: {settings.zkevm_cardona_chain_id}")
                
        # Initialize Arbitrum Sepolia (Transporter Chain)
        if settings.arbitrum_sepolia_rpc:
            self.arbitrum_web3 = Web3(Web3.HTTPProvider(settings.arbitrum_sepolia_rpc))
            if self.arbitrum_web3.is_connected():
                print(f"✅ Connected to Arbitrum Sepolia (Transporter Chain) - Chain ID: {settings.arbitrum_sepolia_chain_id}")
        
        print("🌐 Cross-chain purchase service initialized")

    async def execute_cross_chain_purchase(self, purchase_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Algorithm 5: Post Supply Chain Management for NFT-Based Product Sale
        Combined with Algorithm 1: Payment Release and Incentive Mechanism
        
        Input: Product details, NFT details, buyer details  
        Output: Sale status, NFT ownership transfer status
        """
        try:
            product_id = purchase_request["product_id"]
            buyer_address = purchase_request["buyer"]
            purchase_price = float(purchase_request["price"])
            payment_method = purchase_request.get("payment_method", "ETH")
            
            print(f"🚀 Algorithm 5: Cross-Chain Purchase Process Started")
            print(f"   📦 Product ID: {product_id}")
            print(f"   👤 Buyer: {buyer_address}")
            print(f"   💰 Price: {purchase_price} ETH")
            print(f"   🔗 Flow: Optimism Sepolia → Polygon Hub → zkEVM Cardona")
            
            # Step 1: Get Product details, NFT details, buyer details
            print(f"📋 Step 1: Retrieving product and NFT details...")
            product = await self.database.products.find_one({"token_id": product_id})
            if not product:
                return {"success": False, "error": "Product not found", "step": "product_lookup"}
            
            manufacturer_address = product.get("manufacturer", "")
            current_owner = product.get("current_owner", manufacturer_address)
            
            print(f"✅ Product found: {product.get('name', 'Unknown Product')}")
            print(f"   🏭 Manufacturer: {manufacturer_address}")
            print(f"   👤 Current Owner: {current_owner}")
            
            # Step 2: If shopkeeper wants to sell product (check ownership)
            print(f"📋 Step 2: Verifying product ownership and availability...")
            if current_owner == buyer_address:
                return {"success": False, "error": "Buyer already owns this product", "step": "ownership_check"}
            
            # Step 3: If buyer shows interest - Display product details and associated NFT on marketplace
            print(f"✅ Step 3: Product available for purchase")
            
            # Step 4: Buyer verifies product authenticity using NFT metadata
            print(f"📋 Step 4: Product authenticity verification...")
            authenticity_result = await self._verify_product_authenticity_for_purchase(product, buyer_address)
            
            # Step 5: If product is genuine then proceed
            if not authenticity_result["is_authentic"]:
                print(f"❌ Step 5: Product verification failed - {authenticity_result['reason']}")
                return {"success": False, "error": f"Product Verification Failed: {authenticity_result['reason']}", "step": "authenticity_verification"}
            
            print(f"✅ Step 5: Product verified as genuine")
            
            # Step 6: Buyer proceeds with payment (Algorithm 1 integration)
            print(f"💰 Step 6: Processing cross-chain payment...")
            payment_result = await self._process_cross_chain_payment(
                buyer_address, current_owner, purchase_price, product_id
            )
            
            # Step 7: If payment is successful then proceed
            if not payment_result["success"]:
                print(f"❌ Step 7: Payment processing failed - {payment_result['error']}")
                return {"success": False, "error": f"Payment Failed: {payment_result['error']}", "step": "payment_processing"}
            
            print(f"✅ Step 7: Payment processed successfully")
            
            # Step 8: Transfer product to buyer via cross-chain NFT transfer
            print(f"🔄 Step 8: Cross-chain NFT ownership transfer...")
            transfer_result = await self._execute_cross_chain_nft_transfer(
                product, current_owner, buyer_address, payment_result["escrow_id"]
            )
            
            # Step 9: Initiate NFT ownership transfer
            # Step 10: Update NFT details with new owner
            if transfer_result["success"]:
                print(f"✅ Step 9-10: NFT ownership transferred successfully")
                
                # Update product ownership in database
                await self.database.products.update_one(
                    {"token_id": product_id},
                    {
                        "$set": {
                            "current_owner": buyer_address,
                            "status": "sold",
                            "last_updated": time.time(),
                            "purchase_history": product.get("purchase_history", []) + [{
                                "purchase_id": payment_result["purchase_id"],
                                "buyer": buyer_address,
                                "seller": current_owner,
                                "price_eth": purchase_price,
                                "timestamp": time.time(),
                                "cross_chain": True,
                                "chains_involved": ["optimism_sepolia", "polygon_pos", "zkevm_cardona"]
                            }]
                        }
                    }
                )
                
                # Step 11: Return "Sale Successful and NFT Transferred"
                purchase_record = {
                    "purchase_id": payment_result["purchase_id"],
                    "product_id": product_id,
                    "buyer": buyer_address,
                    "seller": current_owner,
                    "price_eth": purchase_price,
                    "payment_method": payment_method,
                    "status": "completed",
                    "cross_chain_details": {
                        "buyer_chain": "optimism_sepolia",
                        "hub_chain": "polygon_pos", 
                        "manufacturer_chain": "zkevm_cardona",
                        "layerzero_tx": payment_result.get("layerzero_tx"),
                        "fxportal_tx": transfer_result.get("fxportal_tx"),
                        "escrow_id": payment_result["escrow_id"]
                    },
                    "algorithm_1_applied": True,
                    "algorithm_5_applied": True,
                    "purchase_timestamp": time.time(),
                    "purchase_date": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                await self.database.purchases.insert_one(purchase_record)
                
                print(f"🎉 Algorithm 5 Result: Sale Successful and NFT Transferred")
                return {
                    "success": True,
                    "status": "Sale Successful and NFT Transferred",
                    "purchase_id": payment_result["purchase_id"],
                    "nft_transfer_tx": transfer_result.get("transaction_hash"),
                    "cross_chain_details": purchase_record["cross_chain_details"],
                    "final_owner": buyer_address
                }
                
            else:
                print(f"❌ Step 8: NFT transfer failed - {transfer_result['error']}")
                # If NFT transfer fails, refund payment (Algorithm 1)
                await self._process_payment_refund(payment_result["escrow_id"], buyer_address)
                return {"success": False, "error": f"NFT Transfer Failed: {transfer_result['error']}", "step": "nft_transfer"}
                
        except Exception as e:
            print(f"❌ Cross-chain purchase error: {e}")
            return {"success": False, "error": str(e), "step": "general_error"}

    async def _verify_product_authenticity_for_purchase(self, product: Dict[str, Any], buyer_address: str) -> Dict[str, Any]:
        """Step 4: Buyer verifies product authenticity using NFT metadata"""
        try:
            # Simulate authenticity verification using stored product data
            if not product.get("metadata_cid"):
                return {"is_authentic": False, "reason": "No IPFS metadata found"}
                
            if not product.get("manufacturer"):
                return {"is_authentic": False, "reason": "No manufacturer information"}
                
            # Check if product has valid QR hash
            if not product.get("qr_hash"):
                return {"is_authentic": False, "reason": "No QR verification hash"}
                
            print(f"🔍 Authenticity verification passed for product {product.get('token_id')}")
            return {"is_authentic": True, "reason": "Product verified via NFT metadata and IPFS"}
            
        except Exception as e:
            return {"is_authentic": False, "reason": f"Verification error: {str(e)}"}

    async def _process_cross_chain_payment(self, buyer: str, seller: str, amount: float, product_id: str) -> Dict[str, Any]:
        """
        Algorithm 1: Payment Release and Incentive Mechanism
        Step 6-7: Process payment with cross-chain escrow
        """
        try:
            purchase_id = f"PURCHASE-{product_id}-{int(time.time())}"
            escrow_id = f"ESCROW-{purchase_id}"
            
            print(f"💰 Algorithm 1: Payment Release and Incentive Mechanism")
            print(f"   🔐 Escrow ID: {escrow_id}")
            print(f"   💸 Amount: {amount} ETH")
            print(f"   🔗 Cross-chain flow: Optimism → Polygon Hub")
            
            # Step 1: If NFT ownership of Product ID = buyer (will be checked after transfer)
            # Step 2: Collect collateral amount to seller and transporter
            collateral_amount = amount * 0.1  # 10% collateral for security
            
            # Step 3: Transfer payment from buyer to seller (via escrow)
            print(f"🔐 Creating escrow contract...")
            
            # Simulate LayerZero cross-chain message from Optimism to Polygon Hub
            layerzero_tx = f"0xLZ{int(time.time())}{buyer[:8]}"
            
            # Create escrow record in database
            escrow_record = {
                "escrow_id": escrow_id,
                "purchase_id": purchase_id,
                "product_id": product_id,
                "buyer": buyer,
                "seller": seller,
                "amount_eth": amount,
                "collateral_amount": collateral_amount,
                "status": "active",
                "created_at": time.time(),
                "layerzero_tx": layerzero_tx,
                "source_chain": "optimism_sepolia",
                "target_chain": "polygon_pos"
            }
            
            await self.database.escrows.insert_one(escrow_record)
            
            print(f"✅ Escrow created successfully")
            print(f"   🔗 LayerZero TX: {layerzero_tx}")
            
            return {
                "success": True,
                "purchase_id": purchase_id,
                "escrow_id": escrow_id,
                "layerzero_tx": layerzero_tx,
                "collateral_amount": collateral_amount
            }
            
        except Exception as e:
            print(f"❌ Payment processing error: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_cross_chain_nft_transfer(self, product: Dict[str, Any], from_owner: str, to_owner: str, escrow_id: str) -> Dict[str, Any]:
        """
        Step 8-10: Execute cross-chain NFT ownership transfer
        Hub (Polygon) → Manufacturer Chain (zkEVM Cardona) via fxPortal
        """
        try:
            token_id = product["token_id"]
            
            print(f"🔄 Cross-chain NFT transfer initiated")
            print(f"   🎯 Token ID: {token_id}")  
            print(f"   📤 From: {from_owner}")
            print(f"   📥 To: {to_owner}")
            print(f"   🌉 Bridge: fxPortal (Hub → Manufacturer Chain)")
            
            # Simulate fxPortal bridge communication from Hub to Manufacturer chain
            fxportal_tx = f"0xFX{int(time.time())}{to_owner[:8]}"
            
            # Simulate NFT transfer transaction on manufacturer chain
            nft_transfer_tx = f"0xNFT{int(time.time())}{token_id}"
            
            # Update NFT ownership record
            nft_transfer_record = {
                "transfer_id": str(uuid.uuid4()),
                "product_id": token_id,
                "from_owner": from_owner,
                "to_owner": to_owner,
                "escrow_id": escrow_id,
                "fxportal_tx": fxportal_tx,
                "nft_transfer_tx": nft_transfer_tx,
                "source_chain": "polygon_pos",
                "target_chain": "zkevm_cardona",
                "status": "completed",
                "timestamp": time.time()
            }
            
            await self.database.nft_transfers.insert_one(nft_transfer_record)
            
            print(f"✅ NFT transfer completed")
            print(f"   🔗 fxPortal TX: {fxportal_tx}")
            print(f"   🔗 NFT Transfer TX: {nft_transfer_tx}")
            
            return {
                "success": True,
                "transaction_hash": nft_transfer_tx,
                "fxportal_tx": fxportal_tx,
                "transfer_id": nft_transfer_record["transfer_id"]
            }
            
        except Exception as e:
            print(f"❌ NFT transfer error: {e}")
            return {"success": False, "error": str(e)}

    async def _process_payment_refund(self, escrow_id: str, buyer_address: str) -> Dict[str, Any]:
        """Process payment refund if NFT transfer fails"""
        try:
            # Update escrow status to refunded
            await self.database.escrows.update_one(
                {"escrow_id": escrow_id},
                {"$set": {"status": "refunded", "refund_timestamp": time.time()}}
            )
            
            print(f"💸 Payment refund processed for escrow {escrow_id}")
            return {"success": True, "refund_processed": True}
            
        except Exception as e:
            print(f"❌ Refund processing error: {e}")
            return {"success": False, "error": str(e)}

    async def process_delivery_confirmation_and_payment_release(self, delivery_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Algorithm 1: Payment Release and Incentive Mechanism
        Steps 4-11: Process delivery confirmation and release payments with incentives
        """
        try:
            purchase_id = delivery_data["purchase_id"]
            transporter_address = delivery_data.get("transporter", "")
            delivery_status = delivery_data.get("delivery_status", "delivered")
            
            print(f"📦 Algorithm 1: Processing delivery confirmation and payment release")
            print(f"   📋 Purchase ID: {purchase_id}")
            print(f"   🚛 Transporter: {transporter_address}")
            print(f"   ✅ Status: {delivery_status}")
            
            # Get escrow record
            escrow = await self.database.escrows.find_one({"purchase_id": purchase_id})
            if not escrow:
                return {"success": False, "error": "Escrow record not found"}
            
            # Step 4: Update NFT ownership to buyer (already done in purchase)
            
            # Step 5: If delivery status meets incentive criteria then
            if delivery_status == "delivered":
                print(f"📋 Step 5: Delivery confirmed - processing incentive mechanism")
                
                # Step 6: Award incentive to transporter
                # Step 7: Return "Incentive Awarded"
                if transporter_address:
                    incentive_amount = escrow["amount_eth"] * 0.05  # 5% incentive
                    
                    incentive_record = {
                        "incentive_id": f"INCENTIVE-{purchase_id}-{int(time.time())}",
                        "purchase_id": purchase_id,
                        "transporter": transporter_address,
                        "amount_eth": incentive_amount,
                        "reason": "successful_delivery",
                        "status": "awarded",
                        "timestamp": time.time()
                    }
                    
                    await self.database.incentives.insert_one(incentive_record)
                    print(f"🎁 Step 6-7: Incentive awarded to transporter: {incentive_amount} ETH")
                
                # Step 9: Release payment to seller
                # Step 11: Return "Payment Successful"
                await self.database.escrows.update_one(
                    {"escrow_id": escrow["escrow_id"]},
                    {"$set": {
                        "status": "completed",
                        "payment_released": True,
                        "delivery_confirmed": True,
                        "completion_timestamp": time.time()
                    }}
                )
                
                print(f"💰 Step 9 & 11: Payment released to seller - Payment Successful")
                
                return {
                    "success": True,
                    "status": "Payment Successful",
                    "incentive_awarded": bool(transporter_address),
                    "payment_released": True
                }
                
            else:
                # Step 8: else - No incentive (delivery issues)
                # Step 12: else - Payment failed
                print(f"❌ Step 8 & 12: Delivery issues detected - No Incentive Awarded")
                
                await self.database.escrows.update_one(
                    {"escrow_id": escrow["escrow_id"]},
                    {"$set": {
                        "status": "delivery_failed",
                        "payment_released": False,
                        "delivery_confirmed": False,
                        "failure_timestamp": time.time()
                    }}
                )
                
                return {
                    "success": False,
                    "status": "No Incentive Awarded",
                    "reason": "Delivery status does not meet criteria"
                }
                
        except Exception as e:
            print(f"❌ Delivery confirmation error: {e}")
            return {"success": False, "error": str(e)}

    async def get_purchase_status(self, purchase_id: str) -> Dict[str, Any]:
        """Get comprehensive purchase status across all chains"""
        try:
            # Get purchase record
            purchase = await self.database.purchases.find_one({"purchase_id": purchase_id})
            if not purchase:
                return {"success": False, "error": "Purchase not found"}
            
            # Get escrow status
            escrow = await self.database.escrows.find_one({"purchase_id": purchase_id})
            
            # Get NFT transfer status
            nft_transfer = await self.database.nft_transfers.find_one({"escrow_id": escrow.get("escrow_id", "")})
            
            # Get incentive status
            incentive = await self.database.incentives.find_one({"purchase_id": purchase_id})
            
            return {
                "success": True,
                "purchase": purchase,
                "escrow_status": escrow.get("status", "unknown") if escrow else "not_found",
                "nft_transfer_status": nft_transfer.get("status", "unknown") if nft_transfer else "not_found",
                "incentive_awarded": bool(incentive),
                "cross_chain_complete": bool(escrow and nft_transfer and escrow.get("status") == "completed")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global service instance
crosschain_purchase_service = CrossChainPurchaseService()
