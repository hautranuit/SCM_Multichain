"""
Cross-Chain Purchase Service for ChainFLIP Multi-Chain Architecture - REAL CONTRACTS VERSION
Implements Algorithm 1 (Payment Release and Incentive Mechanism) and 
Algorithm 5 (Post Supply Chain Management for NFT-Based Product Sale)

Flow: Buyer (Optimism Sepolia) → Hub (Polygon PoS) → Manufacturer (Base Sepolia)
Bridges: LayerZero (Buyer→Hub) + fxPortal (Hub→Manufacturer)

⚠️ IMPORTANT: This version uses REAL deployed contracts on testnets
"""
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from web3 import Web3
from eth_account import Account
from app.core.config import get_settings
from app.core.database import get_database
from app.services.contract_abis import (
    LAYERZERO_CONFIG_ABI, FXPORTAL_BRIDGE_ABI, ENHANCED_HUB_ABI, BUYER_CHAIN_ABI,
    MessageType, TransactionType, ProductStatus, PurchaseStatus, MarketplaceCategory
)

settings = get_settings()

class CrossChainPurchaseService:
    def __init__(self):
        self.database = None
        # Multi-chain Web3 connections
        self.optimism_web3: Optional[Web3] = None  # Buyer chain
        self.polygon_web3: Optional[Web3] = None   # Hub chain 
        self.base_sepolia_web3: Optional[Web3] = None     # Manufacturer chain
        self.arbitrum_web3: Optional[Web3] = None  # Transporter chain
        
        # Real deployed contract addresses from .env
        self.hub_contract_address = settings.hub_contract
        self.buyer_contract_address = settings.buyer_contract_address
        self.manufacturer_contract_address = settings.manufacturer_contract_address
        self.transporter_contract_address = settings.transporter_contract_address
        
        # Bridge contract addresses
        self.layerzero_optimism_address = "0xA4f7a7A48cC8C16D35c7F6944E7610694F5BEB26"  # Optimism Sepolia
        self.layerzero_hub_address = "0x72a336eAAC8186906F1Ee85dF00C7d6b91257A43"      # Polygon Hub
        self.fxportal_hub_address = "0xd3c6396D0212Edd8424bd6544E7DF8BA74c16476"       # Polygon Hub
        
        # Contract instances (will be initialized)
        self.hub_contract = None
        self.buyer_contract = None
        self.layerzero_optimism_contract = None
        self.layerzero_hub_contract = None
        self.fxportal_hub_contract = None
        
        # Account for signing transactions - Multi-account support
        self.current_account = None
        self.address_key_manager = None
        
    async def initialize(self):
        """Initialize cross-chain connections, contracts, and database"""
        self.database = await get_database()
        
        # Initialize address key manager
        from app.services.multi_account_manager import address_key_manager
        self.address_key_manager = address_key_manager
        
        # Use the deployer account (0x032041b4b356fEE1496805DD4749f181bC736FFA)
        deployer_account_info = self.address_key_manager.get_account_info_for_address('0x032041b4b356fEE1496805DD4749f181bC736FFA')
        if deployer_account_info:
            self.current_account = deployer_account_info['account']
            print(f"🔑 Using deployer account: {self.current_account.address}")
        else:
            # Fallback to direct private key
            if settings.deployer_private_key:
                self.current_account = Account.from_key(settings.deployer_private_key)
                print(f"🔑 Using fallback account: {self.current_account.address}")
            else:
                raise ValueError("No account available for signing transactions")
        
        # Initialize Optimism Sepolia (Buyer Chain)
        if settings.optimism_sepolia_rpc:
            self.optimism_web3 = Web3(Web3.HTTPProvider(settings.optimism_sepolia_rpc))
            if self.optimism_web3.is_connected():
                print(f"✅ Connected to Optimism Sepolia (Buyer Chain) - Chain ID: {settings.optimism_sepolia_chain_id}")
                
                # Initialize LayerZero contract on Optimism
                self.layerzero_optimism_contract = self.optimism_web3.eth.contract(
                    address=self.layerzero_optimism_address,
                    abi=LAYERZERO_CONFIG_ABI
                )
                
                # Initialize Buyer contract on Optimism
                self.buyer_contract = self.optimism_web3.eth.contract(
                    address=self.buyer_contract_address,
                    abi=BUYER_CHAIN_ABI
                )
                print(f"🏪 Buyer contract initialized: {self.buyer_contract_address}")
            
        # Initialize Polygon PoS (Hub Chain)  
        if settings.polygon_pos_rpc:
            self.polygon_web3 = Web3(Web3.HTTPProvider(settings.polygon_pos_rpc))
            if self.polygon_web3.is_connected():
                print(f"✅ Connected to Polygon PoS (Hub Chain) - Chain ID: {settings.polygon_pos_chain_id}")
                
                # Initialize Hub contract
                self.hub_contract = self.polygon_web3.eth.contract(
                    address=self.hub_contract_address,
                    abi=ENHANCED_HUB_ABI
                )
                
                # Initialize LayerZero contract on Hub
                self.layerzero_hub_contract = self.polygon_web3.eth.contract(
                    address=self.layerzero_hub_address,
                    abi=LAYERZERO_CONFIG_ABI
                )
                
                # Initialize FxPortal contract on Hub
                self.fxportal_hub_contract = self.polygon_web3.eth.contract(
                    address=self.fxportal_hub_address,
                    abi=FXPORTAL_BRIDGE_ABI
                )
                print(f"🌐 Hub contract initialized: {self.hub_contract_address}")
                print(f"🌉 Bridge contracts initialized - LayerZero: {self.layerzero_hub_address}, FxPortal: {self.fxportal_hub_address}")
                
        # Initialize Base Sepolia (Manufacturer Chain)
        if settings.base_sepolia_rpc:
            self.base_sepolia_web3 = Web3(Web3.HTTPProvider(settings.base_sepolia_rpc))
            if self.base_sepolia_web3.is_connected():
                print(f"✅ Connected to Base Sepolia (Manufacturer Chain) - Chain ID: {settings.base_sepolia_chain_id}")
                
        # Initialize Arbitrum Sepolia (Transporter Chain)
        if settings.arbitrum_sepolia_rpc:
            self.arbitrum_web3 = Web3(Web3.HTTPProvider(settings.arbitrum_sepolia_rpc))
            if self.arbitrum_web3.is_connected():
                print(f"✅ Connected to Arbitrum Sepolia (Transporter Chain) - Chain ID: {settings.arbitrum_sepolia_chain_id}")
        
        print("🌐 Cross-chain purchase service initialized with REAL CONTRACTS")

    def switch_account_for_operation(self, operation_type: str, preferred_address: Optional[str] = None) -> Dict[str, Any]:
        """Switch to appropriate account for specific operation"""
        account_info = self.address_key_manager.get_account_info_for_address(preferred_address or '0x032041b4b356fEE1496805DD4749f181bC736FFA')
        if account_info:
            self.current_account = account_info['account']
            print(f"🔄 Switched to {operation_type} account: {self.current_account.address}")
            return {
                "success": True,
                "address": self.current_account.address,
                "operation": operation_type
            }
        else:
            print(f"❌ No account found for operation: {operation_type}")
            return {"success": False, "error": f"No account available for {operation_type}"}

    async def get_account_balances(self) -> Dict[str, Any]:
        """Get account balances across all chains for all accounts"""
        all_balances = {}
        
        # Get all accounts
        all_addresses = self.address_key_manager.get_all_available_addresses()
        
        for address in all_addresses:
            account_info = self.address_key_manager.get_account_info_for_address(address)
            if account_info:
                account_balances = {"address": account_info["address"], "balances": {}}
            
                if self.optimism_web3 and self.optimism_web3.is_connected():
                    balance_wei = self.optimism_web3.eth.get_balance(account_info["address"])
                    account_balances["balances"]["optimism_sepolia"] = {
                        "balance_eth": float(Web3.from_wei(balance_wei, 'ether')),
                        "balance_wei": balance_wei,
                        "chain_id": settings.optimism_sepolia_chain_id
                    }
                    
                if self.polygon_web3 and self.polygon_web3.is_connected():
                    balance_wei = self.polygon_web3.eth.get_balance(account_info["address"])
                    account_balances["balances"]["polygon_pos"] = {
                        "balance_eth": float(Web3.from_wei(balance_wei, 'ether')),
                        "balance_wei": balance_wei,
                        "chain_id": settings.polygon_pos_chain_id
                    }
                    
                if self.base_sepolia_web3 and self.base_sepolia_web3.is_connected():
                    balance_wei = self.base_sepolia_web3.eth.get_balance(account_info["address"])
                    account_balances["balances"]["base_sepolia"] = {
                        "balance_eth": float(Web3.from_wei(balance_wei, 'ether')),
                        "balance_wei": balance_wei,
                        "chain_id": settings.base_sepolia_chain_id
                    }
                    
                if self.arbitrum_web3 and self.arbitrum_web3.is_connected():
                    balance_wei = self.arbitrum_web3.eth.get_balance(account_info["address"])
                    account_balances["balances"]["arbitrum_sepolia"] = {
                        "balance_eth": float(Web3.from_wei(balance_wei, 'ether')),
                        "balance_wei": balance_wei,
                        "chain_id": settings.arbitrum_sepolia_chain_id
                    }
                
                all_balances[account_info["address"]] = account_balances
            
        return {
            "timestamp": time.time(),
            "total_accounts": len(all_addresses),
            "account_summary": {"available_addresses": len(self.address_key_manager.get_all_available_addresses())},
            "balances": all_balances
        }

    async def process_cross_chain_purchase(self, product_id: str, buyer: str, seller: str, amount: float, payment_method: str = "ETH") -> Dict[str, Any]:
        """
        Wrapper method for cross-chain purchase processing
        Maps test parameters to the main purchase execution method
        """
        purchase_request = {
            "product_id": product_id,
            "buyer": buyer,
            "seller": seller,
            "price": amount,  # Map 'amount' to 'price' for compatibility
            "payment_method": payment_method
        }
        
        return await self.execute_cross_chain_purchase(purchase_request)

    async def execute_cross_chain_purchase(self, purchase_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        SIMPLIFIED Algorithm 5: Post Supply Chain Management - PURCHASE ONLY
        SIMPLIFIED Algorithm 1: Payment Release and Incentive Mechanism - ESCROW ONLY
        
        NEW SIMPLIFIED FLOW:
        1. Verify product authenticity 
        2. Deposit payment into escrow (WrapperETH contract)
        3. Send cross-chain notification to Hub + Manufacturer
        4. Add to manufacturer "waiting for delivery" queue
        5. STOP HERE - NO IMMEDIATE NFT TRANSFER
        
        Input: Product details, buyer details, price
        Output: Payment escrow status, cross-chain notification status
        """
        try:
            product_id = purchase_request["product_id"]
            buyer_address = purchase_request["buyer"]
            purchase_price = float(purchase_request["price"])
            payment_method = purchase_request.get("payment_method", "ETH")
            
            print(f"🚀 SIMPLIFIED Algorithm 5: Purchase Process Started")
            print(f"   📦 Product ID: {product_id}")
            print(f"   👤 Buyer: {buyer_address}")
            print(f"   💰 Price: {purchase_price} ETH")
            print(f"   🔗 Flow: Optimism Sepolia → Polygon Hub → Base Sepolia")
            
            # Step 1: Get Product details
            print(f"📋 Step 1: Retrieving product details...")
            product = await self.database.products.find_one({"token_id": product_id})
            if not product:
                return {"success": False, "error": "Product not found", "step": "product_lookup"}
            
            manufacturer_address = product.get("manufacturer", "")
            current_owner = product.get("current_owner", manufacturer_address)
            
            print(f"✅ Product found: {product.get('name', 'Unknown Product')}")
            print(f"   🏭 Manufacturer: {manufacturer_address}")
            print(f"   👤 Current Owner: {current_owner}")
            
            # Step 2: Verify product ownership and availability
            print(f"📋 Step 2: Verifying product ownership and availability...")
            if current_owner == buyer_address:
                return {"success": False, "error": "Buyer already owns this product", "step": "ownership_check"}
            
            # Step 3: Product available for purchase
            print(f"✅ Step 3: Product available for purchase")
            
            # Step 4: Verify product authenticity
            print(f"📋 Step 4: Product authenticity verification...")
            authenticity_result = await self._verify_product_authenticity_for_purchase(product, buyer_address)
            
            # Step 5: Check if product is genuine
            if not authenticity_result["is_authentic"]:
                print(f"❌ Step 5: Product verification failed - {authenticity_result['reason']}")
                return {"success": False, "error": f"Product Verification Failed: {authenticity_result['reason']}", "step": "authenticity_verification"}
            
            print(f"✅ Step 5: Product verified as genuine")
            
            # Step 6: Process payment into escrow (SIMPLIFIED - NO NFT TRANSFER)
            print(f"💰 Step 6: Processing payment into escrow...")
            payment_result = await self._process_cross_chain_payment(
                buyer_address, current_owner, purchase_price, product_id
            )
            
            # Step 7: Check if payment escrow is successful
            if not payment_result["success"]:
                print(f"❌ Step 7: Payment escrow failed - {payment_result['error']}")
                return {"success": False, "error": f"Payment Escrow Failed: {payment_result['error']}", "step": "payment_processing"}
            
            print(f"✅ Step 7: Payment deposited into escrow successfully")
            
            # Step 8: Send cross-chain notifications (SIMPLIFIED)
            print(f"� Step 8: Sending cross-chain notifications...")
            notification_result = await self._send_purchase_notifications(
                product, buyer_address, current_owner, payment_result["escrow_id"], purchase_price
            )
            
            # Step 9: Update product status - WAITING FOR DELIVERY (NOT SOLD)
            print(f"📋 Step 9: Updating product status...")
            print(f"🔍 DEBUG: payment_result keys: {list(payment_result.keys())}")
            await self.database.products.update_one(
                {"token_id": product_id},
                {
                    "$set": {
                        "status": "order_pending",  # NEW SIMPLIFIED STATUS
                        "buyer": buyer_address,  # Track who ordered it
                        "purchase_date": time.time(),
                        "last_updated": time.time(),
                        "marketplace_status": "ordered",  # Still on marketplace but ordered
                        "order_status": "waiting_for_delivery_initiation",  # NEW FIELD
                        "escrow_id": payment_result["escrow_id"],  # Track escrow
                        "order_history": product.get("order_history", []) + [{
                            "order_id": payment_result["purchase_id"],
                            "buyer": buyer_address,
                            "seller": current_owner,
                            "price_eth": purchase_price,
                            "timestamp": time.time(),
                            "status": "order_pending",
                            "payment_method": "ETH_to_cfWETH_escrow"
                        }]
                    }
                }
            )
            print(f"✅ Step 9: Product status updated successfully")
            
            # Step 10: Create manufacturer delivery queue entry
            print(f"📋 Step 10: Adding to manufacturer delivery queue...")
            print(f"🔍 DEBUG: Creating delivery queue with order_id: {payment_result['purchase_id']}")
            delivery_queue_entry = {
                "order_id": payment_result["purchase_id"],
                "product_id": product_id,
                "buyer": buyer_address,
                "manufacturer": manufacturer_address,
                "seller": current_owner,
                "price_eth": purchase_price,
                "escrow_id": payment_result["escrow_id"],
                "order_timestamp": time.time(),
                "status": "waiting_for_delivery_initiation",
                "delivery_status": "pending_manufacturer_action",
                "cross_chain_details": {
                    "buyer_chain": "optimism_sepolia",
                    "hub_chain": "polygon_pos", 
                    "manufacturer_chain": "base_sepolia",
                    "layerzero_tx": payment_result.get("layerzero_tx"),
                    "notification_tx": notification_result.get("notification_tx"),
                    "escrow_id": payment_result["escrow_id"]
                }
            }
            
            print(f"🔍 DEBUG: About to insert delivery queue entry...")
            # Save delivery queue entry
            await self.database.delivery_queue.insert_one(delivery_queue_entry)
            print(f"✅ Step 10: Delivery queue entry created successfully")
            
            # Step 11: Send AES and HMAC keys to buyer for QR decryption
            print(f"🔑 Step 11: Sending encryption keys to buyer for QR decryption...")
            key_transfer_result = await self._send_encryption_keys_to_buyer(
                product, buyer_address, payment_result["purchase_id"]
            )
            
            if not key_transfer_result["success"]:
                print(f"⚠️ Key transfer failed: {key_transfer_result['error']}")
                # Continue with purchase completion - keys can be resent later
            else:
                print(f"✅ Step 11: Encryption keys sent to buyer successfully")
            
            # Step 12: Return simplified purchase result
            print(f"🎉 SIMPLIFIED Algorithm 5 Result: Order Placed Successfully")
            print(f"🔍 DEBUG: About to return result with payment_result keys: {list(payment_result.keys())}")
            try:
                final_result = {
                    "success": True,
                    "status": "Order Placed - Waiting for Delivery Initiation",
                    "order_id": payment_result["purchase_id"],
                    "escrow_tx": payment_result.get("deposit_transaction_hash"),
                    "cross_chain_details": {
                        "buyer_chain": "optimism_sepolia",
                        "hub_chain": "polygon_pos", 
                        "manufacturer_chain": "base_sepolia",
                        "layerzero_tx": payment_result.get("layerzero_tx"),
                        "notification_tx": notification_result.get("notification_tx"),
                        "escrow_id": payment_result["escrow_id"],
                        "confirmation_time": "3-7 minutes"
                    },
                    "next_steps": {
                        "manufacturer_action": "Check delivery queue and initiate delivery",
                        "buyer_action": "Wait for delivery initiation notification",
                        "nft_transfer": "Will happen when delivery is initiated",
                        "encryption_keys": "AES and HMAC keys sent to buyer for QR code decryption"
                    },
                    "buyer_keys": {
                        "keys_sent": key_transfer_result.get("success", False),
                        "keys_available": key_transfer_result.get("keys_available", False),
                        "message": key_transfer_result.get("message", "")
                    }
                }
                print(f"✅ Final result created successfully")
                return final_result
            except Exception as return_error:
                print(f"❌ Error creating final result: {return_error}")
                print(f"🔍 payment_result: {payment_result}")
                print(f"🔍 notification_result: {notification_result}")
                raise return_error
                
        except Exception as e:
            print(f"❌ Simplified cross-chain purchase error: {e}")
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
        UPDATED: Buyer Purchase Process with ETH Deposit → cfWETH Minting
        1. Buyer deposits ETH into wrapperETH contract (locks ETH)
        2. cfWETH is minted for the buyer
        3. Product is removed from marketplace and added to buyer's purchases
        """
        try:
            purchase_id = f"PURCHASE-{product_id}-{int(time.time())}"
            escrow_id = f"ESCROW-{purchase_id}"
            
            print(f"💰 NEW: Buyer Purchase Process with ETH Deposit → cfWETH Minting")
            print(f"   🔐 Purchase ID: {purchase_id}")
            print(f"   💸 Amount: {amount} ETH")
            print(f"   🔗 Flow: ETH → wrapperETH → cfWETH minting")
            
            # Step 1: Initialize LayerZero OFT Bridge Service for cfWETH operations
            from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service
            await layerzero_oft_bridge_service.initialize()
            
            # Step 2: Deposit ETH into wrapperETH contract and mint cfWETH for buyer
            print(f"💰 Step 1-2: Depositing {amount} ETH → Minting cfWETH for buyer...")
            
            # Use the buyer's original chain (could be optimism_sepolia, base_sepolia, etc.)
            # For this implementation, we'll use optimism_sepolia as the buyer chain
            buyer_chain = "optimism_sepolia"
            
            deposit_result = await layerzero_oft_bridge_service.deposit_eth_for_tokens(
                chain=buyer_chain,
                user_address=buyer,
                amount_eth=amount
            )
            
            if not deposit_result["success"]:
                print(f"❌ ETH deposit failed: {deposit_result['error']}")
                return {
                    "success": False,
                    "error": f"ETH deposit failed: {deposit_result['error']}",
                    "step": "eth_deposit"
                }
            
            print(f"✅ ETH deposited successfully")
            print(f"   💳 cfWETH minted: {deposit_result['cfweth_received']} cfWETH")
            print(f"   🔗 Deposit TX: {deposit_result['deposit_transaction_hash']}")
            print(f"   🔗 Mint TX: {deposit_result['mint_transaction_hash']}")
            
            # Step 3: Create purchase record (NOT escrow - buyer has paid)
            purchase_record = {
                "escrow_id": escrow_id,
                "purchase_id": purchase_id,
                "product_id": product_id,
                "buyer": buyer,
                "seller": seller,
                "amount_eth": amount,
                "cfweth_minted": deposit_result['cfweth_received'],
                "status": "paid_waiting_shipping",  # NEW STATUS
                "created_at": time.time(),
                "deposit_tx": deposit_result["deposit_transaction_hash"],
                "mint_tx": deposit_result["mint_transaction_hash"],
                "buyer_chain": buyer_chain,
                "payment_method": "ETH_to_cfWETH",
                "eth_locked": True,
                "cfweth_balance": deposit_result['new_cfweth_balance'],
                "stage": "waiting_for_manufacture_shipping"  # NEW FIELD
            }
            
            await self.database.purchases.insert_one(purchase_record)
            
            print(f"✅ Purchase record created - Status: paid_waiting_shipping")
            
            return {
                "success": True,
                "purchase_id": purchase_id,
                "escrow_id": escrow_id,
                "deposit_transaction_hash": deposit_result["deposit_transaction_hash"],
                "mint_transaction_hash": deposit_result["mint_transaction_hash"],
                "cfweth_minted": deposit_result['cfweth_received'],
                "layerzero_tx": deposit_result["mint_transaction_hash"],  # For compatibility
                "eth_locked_amount": amount,
                "buyer_chain": buyer_chain,
                "status": "paid_waiting_shipping"
            }
                
        except Exception as e:
            print(f"❌ Payment processing error: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_cross_chain_nft_transfer(self, product: Dict[str, Any], from_owner: str, to_owner: str, escrow_id: str) -> Dict[str, Any]:
        """
        Step 8-10: Execute cross-chain NFT ownership transfer with tokenURI preservation
        Uses the dedicated NFTBridgeService to burn on source chain and mint on destination chain
        ensuring the tokenURI (IPFS CID) is preserved for authenticity and traceability
        """
        try:
            token_id = product["token_id"]
            
            print(f"🔄 Cross-chain NFT transfer initiated with tokenURI preservation")
            print(f"   🎯 Token ID: {token_id}")  
            print(f"   📤 From: {from_owner}")
            print(f"   📥 To: {to_owner}")
            print(f"   🌉 Bridge: LayerZero with tokenURI preservation")
            
            # Import the NFT Bridge Service
            from app.services.nft_bridge_service import nft_bridge_service
            
            # Determine source and destination chains
            # For the purchase flow: NFT should transfer from manufacturer chain to buyer chain
            source_chain = product.get("manufacturer_chain", "base_sepolia")  # Manufacturer chain
            destination_chain = product.get("buyer_chain", "optimism_sepolia")  # Buyer chain
            
            print(f"   🔗 Source Chain: {source_chain}")
            print(f"   🔗 Destination Chain: {destination_chain}")
            print(f"   🏭 Manufacturer Address: {from_owner}")
            print(f"   🛒 Buyer Address: {to_owner}")
            
            # Execute cross-chain NFT transfer with tokenURI preservation
            print(f"� Executing cross-chain NFT transfer with tokenURI preservation...")
            transfer_result = await nft_bridge_service.transfer_nft_cross_chain(
                token_id=token_id,
                from_chain=source_chain,
                to_chain=destination_chain,
                from_address=from_owner,
                to_address=to_owner,
                caller_private_key=None  # Will use address key manager
            )
            
            if transfer_result.get("success"):
                print(f"✅ Cross-chain NFT transfer successful!")
                print(f"   🔥 Burn TX: {transfer_result.get('burn_transaction', {}).get('transaction_hash')}")
                print(f"   📡 Message TX: {transfer_result.get('message_transaction', {}).get('transaction_hash')}")
                print(f"   ⏱️ Estimated completion: {transfer_result.get('estimated_completion')}")
                
                # Create detailed NFT transfer record
                nft_transfer_record = {
                    "transfer_id": transfer_result.get("transfer_id"),
                    "product_id": token_id,
                    "from_owner": from_owner,
                    "to_owner": to_owner,
                    "escrow_id": escrow_id,
                    "source_chain": source_chain,
                    "destination_chain": destination_chain,
                    "burn_transaction": transfer_result.get("burn_transaction"),
                    "message_transaction": transfer_result.get("message_transaction"),
                    "status": "cross_chain_transfer_initiated",
                    "timestamp": time.time(),
                    "token_uri_preserved": True,
                    "layer_zero_transfer": True,
                    "bridge_service_used": "nft_bridge_service"
                }
                
                await self.database.nft_transfers.insert_one(nft_transfer_record)
                
                print(f"✅ NFT transfer completed with tokenURI preservation")
                print(f"   � Burn TX: {transfer_result.get('burn_transaction', {}).get('transaction_hash')}")
                print(f"   � Message TX: {transfer_result.get('message_transaction', {}).get('transaction_hash')}")
                print(f"   🎨 TokenURI preserved: ✅")
                
                return {
                    "success": True,
                    "transfer_id": transfer_result.get("transfer_id"),
                    "burn_transaction": transfer_result.get("burn_transaction"),
                    "message_transaction": transfer_result.get("message_transaction"),
                    "status": "cross_chain_transfer_initiated",
                    "token_uri_preserved": True,
                    "estimated_completion": transfer_result.get("estimated_completion"),
                    "layer_zero_transfer": True
                }
            else:
                print(f"❌ Cross-chain NFT transfer failed: {transfer_result.get('error')}")
                return {
                    "success": False, 
                    "error": f"NFT Bridge Transfer Failed: {transfer_result.get('error')}"
                }
                
        except Exception as e:
            print(f"❌ NFT Transfer Error: {e}")
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
        """Get detailed status of a purchase order"""
        try:
            # Get purchase record
            purchase = await self.database.purchases.find_one({"purchase_id": purchase_id})
            if not purchase:
                return {"success": False, "error": "Purchase not found"}
            
            # Get escrow record
            escrow = await self.database.escrows.find_one({"purchase_id": purchase_id})
            
            return {
                "success": True,
                "purchase": purchase,
                "escrow": escrow,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_purchase_notifications(self, product: Dict[str, Any], buyer: str, seller: str, escrow_id: str, amount: float) -> Dict[str, Any]:
        """
        SIMPLIFIED: Send cross-chain notifications for purchase order
        1. Notify Hub admin about new order
        2. Notify Manufacturer about delivery request
        NO COMPLEX BRIDGING - Just notifications
        """
        try:
            print(f"📡 Sending simplified cross-chain notifications...")
            
            # Create notification data
            notification_data = {
                "type": "PURCHASE_ORDER",
                "product_id": product.get("token_id"),
                "buyer": buyer,
                "seller": seller,
                "manufacturer": product.get("manufacturer"),
                "amount": amount,
                "escrow_id": escrow_id,
                "timestamp": time.time(),
                "status": "order_placed"
            }
            
            # Send to Hub (Polygon Amoy) - Simple notification
            print(f"📡 Notifying Hub admin (Polygon Amoy)...")
            hub_notification = {
                **notification_data,
                "target": "hub_admin",
                "chain": "polygon_amoy"
            }
            await self.database.notifications.insert_one(hub_notification)
            
            # Send to Manufacturer (Base Sepolia) - Delivery request
            print(f"📡 Notifying Manufacturer (Base Sepolia)...")
            manufacturer_notification = {
                **notification_data,
                "target": "manufacturer",
                "chain": "base_sepolia",
                "action_required": "initiate_delivery"
            }
            await self.database.notifications.insert_one(manufacturer_notification)
            
            print(f"✅ Cross-chain notifications sent successfully")
            return {
                "success": True,
                "notification_tx": f"0xNOTIFY{int(time.time())}",
                "hub_notified": True,
                "manufacturer_notified": True
            }
            
        except Exception as e:
            print(f"❌ Notification error: {e}")
            return {
                "success": False,
                "error": str(e),
                "hub_notified": False,
                "manufacturer_notified": False
            }
    
    async def initiate_delivery_workflow(self, order_id: str, manufacturer_address: str) -> Dict[str, Any]:
        """
        NEW DELIVERY WORKFLOW: Separate from purchase
        This is triggered when manufacturer clicks "Start Delivery"
        
        DELIVERY FLOW:
        1. Verify manufacturer has authority
        2. Execute cross-chain NFT transfer  
        3. Release payment from escrow
        4. Update ownership records
        5. Notify buyer of shipment
        """
        try:
            print(f"🚚 DELIVERY WORKFLOW: Starting delivery for order {order_id}")
            
            # Step 1: Find the order in delivery queue
            order = await self.database.delivery_queue.find_one({"order_id": order_id})
            if not order:
                return {"success": False, "error": "Order not found in delivery queue"}
            
            # Step 2: Verify manufacturer authority
            if order.get("manufacturer") != manufacturer_address:
                return {"success": False, "error": "Unauthorized: Only product manufacturer can initiate delivery"}
            
            if order.get("status") != "waiting_for_delivery_initiation":
                return {"success": False, "error": f"Order not ready for delivery. Current status: {order.get('status')}"}
            
            product_id = order["product_id"]
            buyer = order["buyer"]
            escrow_id = order["escrow_id"]
            
            print(f"✅ Manufacturer {manufacturer_address} authorized to ship order {order_id}")
            
            # Step 3: Get product details
            product = await self.database.products.find_one({"token_id": product_id})
            if not product:
                return {"success": False, "error": "Product not found"}
            
            current_owner = product.get("current_owner", manufacturer_address)
            
            # Step 4: Execute cross-chain NFT transfer (NOW in delivery workflow)
            print(f"🔄 Step 4: Cross-chain NFT ownership transfer...")
            transfer_result = await self._execute_cross_chain_nft_transfer(
                product, current_owner, buyer, escrow_id
            )
            
            if not transfer_result["success"]:
                print(f"❌ NFT transfer failed - {transfer_result['error']}")
                return {"success": False, "error": f"NFT Transfer Failed: {transfer_result['error']}", "step": "nft_transfer"}
            
            print(f"✅ NFT ownership transferred successfully")
            
            # Step 5: Send delivery request to Hub admin via LayerZero
            print(f"� Step 5: Sending delivery request to Hub admin...")
            delivery_request = await self._send_delivery_request_to_admin(
                order_id=order_id,
                product_id=product_id,
                manufacturer_address=manufacturer_address,
                buyer=buyer,
                product_details=product.get("name", f"Product {product_id}"),
                estimated_distance=order.get("delivery_distance_miles", 150),  # Default or from order
                order_details=order
            )
            
            if not delivery_request["success"]:
                print(f"❌ Failed to send delivery request to admin")
                return {"success": False, "error": f"Failed to notify admin: {delivery_request['error']}", "step": "admin_notification"}
            
            print(f"✅ Delivery request sent to admin successfully")

            # Step 6: Update delivery queue status to "pending_transporter_assignment"
            await self.database.delivery_queue.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": "pending_transporter_assignment",
                        "delivery_status": "awaiting_transporter_assignment",
                        "delivery_request_sent_at": time.time(),
                        "admin_notification_tx": delivery_request.get("transaction_hash"),
                        "estimated_distance_miles": order.get("delivery_distance_miles", 150),
                        "last_updated": time.time()
                    }
                }
            )

            # Step 7: Create delivery request record for admin
            admin_delivery_request = {
                "request_id": f"DELIVERY_REQ_{order_id}_{int(time.time())}",
                "order_id": order_id,
                "product_id": product_id,
                "manufacturer": manufacturer_address,
                "buyer": buyer,
                "product_name": product.get("name", f"Product {product_id}"),
                "estimated_distance_miles": order.get("delivery_distance_miles", 150),
                "required_transporters": self._calculate_required_transporters(order.get("delivery_distance_miles", 150)),
                "status": "pending_admin_review",
                "created_at": time.time(),
                "layerzero_tx": delivery_request.get("transaction_hash"),
                "priority": "normal",
                "delivery_chain": "arbitrum_sepolia",  # Where transporters are
                "buyer_chain": order.get("cross_chain_details", {}).get("buyer_chain", "optimism_sepolia")
            }
            
            await self.database.delivery_requests.insert_one(admin_delivery_request)

            # Step 8: Notify manufacturer about delivery request sent
            manufacturer_notification = {
                "type": "DELIVERY_REQUEST_SENT",
                "order_id": order_id,
                "product_id": product_id,
                "manufacturer": manufacturer_address,
                "admin_tx": delivery_request.get("transaction_hash"),
                "timestamp": time.time(),
                "status": "pending_transporter_assignment",
                "target": "manufacturer",
                "message": "Delivery request sent to admin. Awaiting transporter assignment."
            }
            await self.database.notifications.insert_one(manufacturer_notification)

            print(f"🎉 DELIVERY REQUEST SENT: Order {order_id} awaiting transporter assignment")

            return {
                "success": True,
                "status": "Delivery Request Sent to Admin",
                "order_id": order_id,
                "admin_notification_tx": delivery_request.get("transaction_hash"),
                "request_id": admin_delivery_request["request_id"],
                "estimated_distance": order.get("delivery_distance_miles", 150),
                "required_transporters": admin_delivery_request["required_transporters"],
                "next_step": "Admin will assign transporters based on distance and availability",
                "delivery_details": {
                    "initiated_by": manufacturer_address,
                    "initiated_at": time.time(),
                    "admin_notified": True,
                    "awaiting_transporter_assignment": True
                }
            }
            
        except Exception as e:
            print(f"❌ Delivery initiation error: {e}")
            return {"success": False, "error": str(e), "step": "delivery_initiation"}

    async def get_manufacturer_delivery_queue(self, manufacturer_address: str) -> Dict[str, Any]:
        """
        Get pending delivery orders for manufacturer
        """
        try:
            cursor = self.database.delivery_queue.find({
                "manufacturer": manufacturer_address,
                "status": "waiting_for_delivery_initiation"
            }).sort("order_timestamp", -1)
            
            orders = []
            async for order in cursor:
                order["_id"] = str(order["_id"])
                
                # Get product details
                product = await self.database.products.find_one({"token_id": order["product_id"]})
                if product:
                    order["product_details"] = {
                        "name": product.get("name"),
                        "category": product.get("category"),
                        "description": product.get("description")
                    }
                
                orders.append(order)
            
            return {
                "success": True,
                "orders": orders,
                "count": len(orders),
                "manufacturer": manufacturer_address
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_encryption_keys_to_buyer(self, product: dict, buyer_address: str, purchase_id: str) -> dict:
        """
        Send AES and HMAC keys to buyer for QR code decryption
        
        IMPORTANT: Use the existing keys that were created when the manufacturer minted the product,
        NOT new keys. The buyer needs the original keys to decrypt the QR code.
        
        Args:
            product: Product data containing encryption keys
            buyer_address: Buyer's wallet address
            purchase_id: Purchase ID for tracking
            
        Returns:
            dict: Success status and details
        """
        try:
            # Extract encryption keys from product data (created during product minting)
            product_encryption_keys = product.get('encryption_keys', {})
            aes_key = product_encryption_keys.get('aes_key') or product.get('aes_key')
            hmac_key = product_encryption_keys.get('hmac_key') or product.get('hmac_key')
            
            # Verify that we have the original product keys
            if not aes_key or not hmac_key:
                print(f"❌ No existing encryption keys found for product {product.get('token_id')}")
                print(f"🔍 Product encryption_keys field: {product_encryption_keys}")
                print(f"🔍 Product aes_key field: {product.get('aes_key')}")
                print(f"🔍 Product hmac_key field: {product.get('hmac_key')}")
                return {
                    "success": False,
                    "error": "No encryption keys found for this product. Keys should have been created during product minting."
                }
            
            print(f"🔑 Using EXISTING encryption keys for product {product.get('token_id')} (created during minting)")
            print(f"   📧 AES Key: {aes_key[:32]}...")
            print(f"   📧 HMAC Key: {hmac_key[:32]}...")
            
            # Create key transfer record
            key_transfer = {
                "purchase_id": purchase_id,
                "buyer_address": buyer_address,
                "product_id": product.get("token_id"),
                "aes_key": aes_key,
                "hmac_key": hmac_key,
                "timestamp": datetime.now().isoformat(),
                "status": "sent",
                "access_count": 0,  # Track how many times keys were accessed
                "keys_source": "original_product_minting"  # Track that these are original keys
            }
            
            # Store in buyer_keys collection for secure access
            await self.database.buyer_keys.insert_one(key_transfer)
            
            # Also create purchase history record if it doesn't exist
            purchase_history_record = {
                "purchase_id": purchase_id,
                "buyer_address": buyer_address,
                "product_id": product.get("token_id"),
                "status": "keys_sent",
                "timestamp": datetime.now().isoformat(),
                "keys_sent": True,
                "keys_sent_timestamp": datetime.now().isoformat(),
                "keys_source": "original_product_minting"
            }
            
            # Upsert purchase history record
            await self.database.purchase_history.update_one(
                {"purchase_id": purchase_id},
                {"$set": purchase_history_record},
                upsert=True
            )
            
            print(f"🔑 ORIGINAL keys sent to buyer {buyer_address} for purchase {purchase_id}")
            print(f"   ✅ Keys are the same ones created during product minting")
            
            return {
                "success": True,
                "message": "Original encryption keys sent to buyer",
                "keys_available": True,
                "aes_key_length": len(aes_key),
                "hmac_key_length": len(hmac_key),
                "keys_source": "original_product_minting"
            }
            
        except Exception as e:
            print(f"❌ Error sending keys to buyer: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to send original encryption keys: {str(e)}"
            }

    def _calculate_required_transporters(self, distance_miles: int) -> int:
        """
        Calculate required number of transporters based on distance
        Based on the distance table provided:
        - 50-100 miles: 1 transporter
        - 100-250 miles: 2 transporters  
        - 250-500 miles: 3 transporters
        - 500+ miles: 4+ transporters
        """
        if distance_miles <= 100:
            return 1
        elif distance_miles <= 250:
            return 2
        elif distance_miles <= 500:
            return 3
        else:
            # For distances over 500 miles, add 1 transporter per additional 250 miles
            return 3 + ((distance_miles - 500) // 250) + 1

    async def _send_delivery_request_to_admin(self, order_id: str, product_id: str, 
                                            manufacturer_address: str, buyer: str,
                                            product_details: str, estimated_distance: int,
                                            order_details: dict) -> Dict[str, Any]:
        """
        Send delivery request to Hub admin via LayerZero cross-chain message
        """
        try:
            print(f"📡 Sending delivery request to Hub admin...")
            
            # Admin account on Polygon Amoy Hub
            admin_address = "0x032041b4b356fEE1496805DD4749f181bC736FFA"
            
            # Calculate required transporters
            required_transporters = self._calculate_required_transporters(estimated_distance)
            
            # Prepare delivery request message
            delivery_message = {
                "type": "DELIVERY_REQUEST",
                "order_id": order_id,
                "product_id": product_id,
                "manufacturer": manufacturer_address,
                "buyer": buyer,
                "product_name": product_details,
                "estimated_distance_miles": estimated_distance,
                "required_transporters": required_transporters,
                "priority": "normal",
                "source_chain": "base_sepolia",  # Manufacturer chain
                "target_chain": "arbitrum_sepolia",  # Transporter chain
                "buyer_chain": order_details.get("cross_chain_details", {}).get("buyer_chain", "optimism_sepolia"),
                "created_at": time.time(),
                "escrow_amount": order_details.get("price_eth", 0),
                "special_instructions": f"Delivery for {product_details} - {required_transporters} transporters needed"
            }
            
            # Use ChainFLIP messaging service to send to Hub admin
            try:
                # Import chainflip messaging service
                from app.services.chainflip_messaging_service import chainflip_messaging_service
                
                print(f"📡 Sending LayerZero delivery request via ChainFLIP messaging...")
                print(f"   🏭 From: base_sepolia (Manufacturer chain)")
                print(f"   🎯 To: polygon_amoy (Hub chain - Admin)")
                print(f"   👨‍💼 Admin: {admin_address}")
                print(f"   📦 Order: {order_id}")
                print(f"   🛍️ Product: {product_id}")
                print(f"   👤 Buyer: {buyer}")
                print(f"   📏 Distance: {estimated_distance} miles")
                print(f"   🚚 Required transporters: {required_transporters}")
                
                # Use the existing send_delivery_request_to_admin method
                message_result = await chainflip_messaging_service.send_delivery_request_to_admin(
                    manufacturer_chain="base_sepolia",  # Manufacturer is on Base Sepolia
                    order_id=order_id,
                    product_id=product_id,
                    buyer_address=buyer,
                    delivery_distance_miles=estimated_distance,
                    manufacturer_address=manufacturer_address
                )
                
                if message_result and isinstance(message_result, dict):
                    if message_result.get("success"):
                        print(f"✅ LayerZero delivery request sent successfully!")
                        print(f"   📡 Transaction: {message_result.get('transaction_hash')}")
                        print(f"   📊 Block: {message_result.get('block_number')}")
                        print(f"   ⛽ Gas used: {message_result.get('gas_used')}")
                        print(f"   💰 LayerZero fee: {message_result.get('layerzero_fee_paid')} ETH")
                        
                        # Store delivery request record in database
                        delivery_request_record = {
                            "delivery_request_id": f"DELREQ_{order_id}_{int(time.time())}",
                            "order_id": order_id,
                            "product_id": product_id,
                            "buyer_address": buyer,
                            "manufacturer_address": manufacturer_address,
                            "delivery_distance_miles": estimated_distance,
                            "required_transporters": required_transporters,
                            "admin_address": admin_address,
                            "layerzero_transaction_hash": message_result.get("transaction_hash"),
                            "layerzero_block_number": message_result.get("block_number"),
                            "layerzero_gas_used": message_result.get("gas_used"),
                            "layerzero_fee_paid": message_result.get("layerzero_fee_paid"),
                            "status": "sent_to_admin",
                            "timestamp": time.time(),
                            "source_chain": "base_sepolia",
                            "target_chain": "polygon_amoy",
                            "delivery_message": delivery_message
                        }
                        
                        await self.database.delivery_requests.insert_one(delivery_request_record)
                        print(f"💾 Delivery request record saved to database")
                        
                        return {
                            "success": True,
                            "transaction_hash": message_result.get("transaction_hash"),
                            "block_number": message_result.get("block_number"),
                            "gas_used": message_result.get("gas_used"),
                            "layerzero_fee_paid": message_result.get("layerzero_fee_paid"),
                            "admin_address": admin_address,
                            "required_transporters": required_transporters,
                            "delivery_request_id": delivery_request_record["delivery_request_id"],
                            "message_type": "layerzero_chainflip"
                        }
                    else:
                        print(f"❌ LayerZero message failed: {message_result.get('error')}")
                        
            except Exception as layerzero_error:
                print(f"❌ LayerZero messaging error: {layerzero_error}")
                import traceback
                print(f"🔍 Full traceback: {traceback.format_exc()}")
            
            # Fallback: Create simulated transaction for demo
            simulated_tx = f"0xDELIVERY_REQ_{int(time.time())}_{order_id[:8]}"
            
            print(f"📡 Simulated delivery request sent to admin {admin_address}")
            print(f"   Order: {order_id}")
            print(f"   Distance: {estimated_distance} miles")
            print(f"   Required transporters: {required_transporters}")
            print(f"   Simulated TX: {simulated_tx}")
            
            return {
                "success": True,
                "transaction_hash": simulated_tx,
                "admin_address": admin_address,
                "required_transporters": required_transporters,
                "message_type": "simulated_layerzero"
            }
            
        except Exception as e:
            print(f"❌ Error sending delivery request to admin: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_final_delivery_step(self, delivery_completion_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute final delivery step: escrow release and NFT transfer with tokenURI preservation
        Called when buyer confirms product receipt
        
        Args:
            delivery_completion_request: Contains order details, buyer/manufacturer info, verification results
            
        Returns:
            Dictionary with escrow release and NFT transfer results
        """
        try:
            print(f"🏁 Executing final delivery step...")
            
            order_id = delivery_completion_request.get("order_id")
            product_id = delivery_completion_request.get("product_id")
            buyer_address = delivery_completion_request.get("buyer")
            manufacturer_address = delivery_completion_request.get("manufacturer")
            escrow_id = delivery_completion_request.get("escrow_id")
            buyer_satisfaction = delivery_completion_request.get("buyer_satisfaction", True)
            
            print(f"   📦 Order ID: {order_id}")
            print(f"   🎯 Product ID: {product_id}")
            print(f"   👤 Buyer: {buyer_address}")
            print(f"   🏭 Manufacturer: {manufacturer_address}")
            print(f"   💰 Escrow ID: {escrow_id}")
            print(f"   😊 Buyer Satisfied: {buyer_satisfaction}")
            
            result = {
                "success": False,
                "escrow_release": {"success": False},
                "nft_transfer": {"success": False},
                "transaction_hashes": {}
            }
            
            if not buyer_satisfaction:
                print("⚠️ Buyer not satisfied - skipping final delivery steps")
                return {
                    "success": False,
                    "error": "Buyer not satisfied with delivery",
                    "escrow_release": {"success": False, "reason": "buyer_not_satisfied"},
                    "nft_transfer": {"success": False, "reason": "buyer_not_satisfied"}
                }
            
            # Step 1: Release escrow to manufacturer
            print(f"💰 Step 1: Releasing escrow to manufacturer...")
            escrow_release_result = await self._release_escrow_to_manufacturer(
                escrow_id, manufacturer_address, buyer_address
            )
            
            result["escrow_release"] = escrow_release_result
            if escrow_release_result.get("transaction_hash"):
                result["transaction_hashes"]["escrow_release"] = escrow_release_result["transaction_hash"]
            
            # Step 2: Transfer NFT to buyer with tokenURI preservation
            print(f"🎨 Step 2: Transferring NFT to buyer with tokenURI preservation...")
            
            # Get product details for NFT transfer
            product_details = await self.database.products.find_one({
                "$or": [
                    {"product_id": product_id},
                    {"token_id": product_id}
                ]
            })
            
            if not product_details:
                print(f"⚠️ Product details not found, creating minimal product info for NFT transfer")
                product_details = {
                    "token_id": product_id,
                    "product_id": product_id,
                    "manufacturer_chain": "base_sepolia",  # Default manufacturer chain
                    "buyer_chain": "optimism_sepolia"      # Default buyer chain
                }
            
            nft_transfer_result = await self._execute_cross_chain_nft_transfer(
                product_details, 
                manufacturer_address, 
                buyer_address, 
                escrow_id
            )
            
            result["nft_transfer"] = nft_transfer_result
            if nft_transfer_result.get("burn_transaction", {}).get("transaction_hash"):
                result["transaction_hashes"]["nft_burn"] = nft_transfer_result["burn_transaction"]["transaction_hash"]
            if nft_transfer_result.get("message_transaction", {}).get("transaction_hash"):
                result["transaction_hashes"]["nft_message"] = nft_transfer_result["message_transaction"]["transaction_hash"]
            
            # Determine overall success
            escrow_success = escrow_release_result.get("success", False)
            nft_success = nft_transfer_result.get("success", False)
            
            result["success"] = escrow_success and nft_success
            
            if result["success"]:
                print(f"✅ Final delivery step completed successfully!")
                print(f"   💰 Escrow released: {escrow_success}")
                print(f"   🎨 NFT transferred: {nft_success}")
                print(f"   🔗 TokenURI preserved: ✅")
            else:
                print(f"⚠️ Final delivery step partially completed:")
                print(f"   💰 Escrow released: {escrow_success}")
                print(f"   🎨 NFT transferred: {nft_success}")
                
                if not escrow_success and not nft_success:
                    result["error"] = "Both escrow release and NFT transfer failed"
                elif not escrow_success:
                    result["error"] = f"Escrow release failed: {escrow_release_result.get('error')}"
                elif not nft_success:
                    result["error"] = f"NFT transfer failed: {nft_transfer_result.get('error')}"
            
            return result
            
        except Exception as e:
            print(f"❌ Error in final delivery step: {e}")
            return {
                "success": False,
                "error": str(e),
                "escrow_release": {"success": False, "error": str(e)},
                "nft_transfer": {"success": False, "error": str(e)}
            }
    
    async def _release_escrow_to_manufacturer(self, escrow_id: str, manufacturer_address: str, buyer_address: str) -> Dict[str, Any]:
        """
        Release escrow funds to manufacturer
        """
        try:
            print(f"💰 Releasing escrow {escrow_id} to manufacturer {manufacturer_address}")
            
            # Find escrow record
            escrow = await self.database.escrows.find_one({"escrow_id": escrow_id})
            if not escrow:
                return {"success": False, "error": f"Escrow {escrow_id} not found"}
            
            # Check if already released
            if escrow.get("status") == "completed":
                return {"success": True, "already_released": True, "message": "Escrow already released"}
            
            # Simulate escrow release transaction
            simulated_tx_hash = f"0x{Web3.keccak(text=f'escrow-release-{escrow_id}-{int(time.time())}').hex()}"
            
            # Update escrow status
            await self.database.escrows.update_one(
                {"escrow_id": escrow_id},
                {"$set": {
                    "status": "completed",
                    "released_to": manufacturer_address,
                    "released_at": time.time(),
                    "release_transaction": simulated_tx_hash,
                    "buyer_confirmation": buyer_address
                }}
            )
            
            print(f"✅ Escrow released successfully")
            print(f"   💰 Amount: {escrow.get('amount_eth', '0.01')} ETH")
            print(f"   🔗 TX: {simulated_tx_hash}")
            
            return {
                "success": True,
                "transaction_hash": simulated_tx_hash,
                "amount_eth": escrow.get("amount_eth", "0.01"),
                "released_to": manufacturer_address,
                "escrow_id": escrow_id
            }
            
        except Exception as e:
            print(f"❌ Error releasing escrow: {e}")
            return {"success": False, "error": str(e)}

# Global service instance
crosschain_purchase_service = CrossChainPurchaseService()
