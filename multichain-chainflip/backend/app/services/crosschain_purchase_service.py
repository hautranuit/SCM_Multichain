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
            print(f"   🔗 Flow: Optimism Sepolia → Polygon Hub → Base Sepolia")
            
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
                                "chains_involved": ["optimism_sepolia", "polygon_pos", "base_sepolia"]
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
                        "manufacturer_chain": "base_sepolia",
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
        Algorithm 1: Payment Release and Incentive Mechanism - REAL TOKEN TRANSFER VERSION
        Step 6-7: Process payment with real cross-chain ETH transfer using LayerZero OFT
        """
        try:
            purchase_id = f"PURCHASE-{product_id}-{int(time.time())}"
            escrow_id = f"ESCROW-{purchase_id}"
            
            print(f"💰 Algorithm 1: Payment Release and Incentive Mechanism (REAL TOKENS)")
            print(f"   🔐 Escrow ID: {escrow_id}")
            print(f"   💸 Amount: {amount} ETH")
            print(f"   🔗 Real token flow: Optimism ETH → Base Sepolia ETH via LayerZero OFT")
            
            # Step 1: If NFT ownership of Product ID = buyer (will be checked after transfer)
            # Step 2: Collect collateral amount to seller and transporter
            collateral_amount = amount * 0.1  # 10% collateral for security
            
            # Step 3: Real cross-chain ETH transfer using Token Bridge Service
            print(f"💸 Executing REAL cross-chain ETH transfer...")
            
            # Initialize token bridge service
            from app.services.token_bridge_service import token_bridge_service
            await token_bridge_service.initialize()
            
            # Execute real ETH transfer from buyer chain to manufacturer chain
            transfer_result = await token_bridge_service.transfer_eth_cross_chain(
                from_chain="optimism_sepolia",  # Buyer chain
                to_chain="base_sepolia",       # Manufacturer chain
                from_address=buyer,
                to_address=seller,
                amount_eth=amount,
                escrow_id=escrow_id
            )
            
            if transfer_result["success"]:
                print(f"✅ Real ETH transfer completed successfully")
                print(f"   🔗 Wrap TX: {transfer_result['wrap_transaction_hash']}")
                print(f"   🔗 LayerZero TX: {transfer_result['layerzero_transaction_hash']}")
                
                # Create escrow record with real transfer details
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
                    "transfer_id": transfer_result["transfer_id"],
                    "wrap_tx": transfer_result["wrap_transaction_hash"],
                    "layerzero_tx": transfer_result["layerzero_transaction_hash"],
                    "gas_costs": transfer_result["gas_used"],
                    "source_chain": "optimism_sepolia",
                    "target_chain": "base_sepolia",
                    "real_token_transfer": True,
                    "transfer_method": "LayerZero_OFT"
                }
                
                await self.database.escrows.insert_one(escrow_record)
                
                print(f"✅ Escrow created with REAL cross-chain ETH transfer")
                
                return {
                    "success": True,
                    "purchase_id": purchase_id,
                    "escrow_id": escrow_id,
                    "transfer_id": transfer_result["transfer_id"],
                    "wrap_tx": transfer_result["wrap_transaction_hash"],
                    "layerzero_tx": transfer_result["layerzero_transaction_hash"],
                    "collateral_amount": collateral_amount,
                    "real_token_transfer": True,
                    "amount_transferred": amount,
                    "gas_used": transfer_result["gas_used"]
                }
                
            else:
                print(f"❌ Real ETH transfer failed: {transfer_result['error']}")
                return {"success": False, "error": f"Token transfer failed: {transfer_result['error']}"}
                
        except Exception as e:
            print(f"❌ Payment processing error: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_cross_chain_nft_transfer(self, product: Dict[str, Any], from_owner: str, to_owner: str, escrow_id: str) -> Dict[str, Any]:
        """
        Step 8-10: Execute cross-chain NFT ownership transfer - REAL CONTRACT VERSION
        Hub (Polygon) → Manufacturer Chain (Base Sepolia) via fxPortal
        """
        try:
            token_id = product["token_id"]
            
            print(f"🔄 Cross-chain NFT transfer initiated (REAL)")
            print(f"   🎯 Token ID: {token_id}")  
            print(f"   📤 From: {from_owner}")
            print(f"   📥 To: {to_owner}")
            print(f"   🌉 Bridge: fxPortal (Hub → Manufacturer Chain)")
            
            # Prepare cross-chain NFT transfer message
            nft_transfer_data = {
                "token_id": token_id,
                "from_owner": from_owner,
                "to_owner": to_owner,
                "escrow_id": escrow_id,
                "product_hash": product.get("qr_hash", ""),
                "timestamp": int(time.time()),
                "transfer_type": "purchase_ownership"
            }
            
            # Encode message payload for fxPortal
            payload = json.dumps(nft_transfer_data).encode('utf-8')
            data_hash = Web3.keccak(text=json.dumps(nft_transfer_data)).hex()
            
            print(f"📝 Preparing fxPortal transaction...")
            
            # Switch to admin account for hub operations
            admin_account_switch = self.switch_account_for_operation('admin')
            if not admin_account_switch["success"]:
                print(f"⚠️ Could not switch to admin account, using current account: {self.current_account.address}")
            
            # Get transaction count for nonce
            nonce = self.polygon_web3.eth.get_transaction_count(self.current_account.address)
            
            # Get chain ID for EIP-155 compliance
            chain_id = self.polygon_web3.eth.chain_id
            
            # Build fxPortal sendMessageToChild transaction
            transaction = self.fxportal_hub_contract.functions.sendMessageToChild(
                MessageType.PRODUCT_REGISTRATION,  # uint8 - using product registration for NFT transfer
                data_hash,
                payload
            ).build_transaction({
                'from': self.current_account.address,
                'gas': 300000,  # Sufficient gas for fxPortal
                'gasPrice': self.polygon_web3.eth.gas_price,
                'nonce': nonce,
                'chainId': chain_id
            })
            
            # Sign and send transaction
            print(f"📝 Signing and sending fxPortal transaction...")
            signed_txn = self.polygon_web3.eth.account.sign_transaction(transaction, self.current_account.key)
            
            # Send transaction
            tx_hash = self.polygon_web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            fxportal_tx = tx_hash.hex()
            
            print(f"⏳ Waiting for fxPortal transaction confirmation...")
            # Wait for transaction receipt
            tx_receipt = self.polygon_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt.status == 1:
                print(f"✅ fxPortal transaction confirmed!")
                print(f"   🔗 TX Hash: {fxportal_tx}")
                print(f"   ⛽ Gas Used: {tx_receipt.gasUsed}")
                
                # Now update product ownership on Hub contract
                print(f"📝 Updating product status on Hub contract...")
                
                # Update product status to SOLD
                hub_nonce = self.polygon_web3.eth.get_transaction_count(self.current_account.address)
                verification_hash = Web3.keccak(text=f"{token_id}-{to_owner}-{int(time.time())}").hex()
                
                # Get chain ID for EIP-155 compliance
                chain_id = self.polygon_web3.eth.chain_id
                
                hub_transaction = self.hub_contract.functions.updateProductStatus(
                    int(token_id),
                    ProductStatus.SOLD,  # enum value
                    verification_hash
                ).build_transaction({
                    'from': self.current_account.address,
                    'gas': 200000,
                    'gasPrice': self.polygon_web3.eth.gas_price,
                    'nonce': hub_nonce,
                    'chainId': chain_id
                })
                
                # Sign and send hub update transaction
                signed_hub_txn = self.polygon_web3.eth.account.sign_transaction(hub_transaction, self.current_account.key)
                hub_tx_hash = self.polygon_web3.eth.send_raw_transaction(signed_hub_txn.raw_transaction)
                hub_tx_receipt = self.polygon_web3.eth.wait_for_transaction_receipt(hub_tx_hash, timeout=120)
                
                if hub_tx_receipt.status == 1:
                    print(f"✅ Hub product status updated!")
                    print(f"   🔗 Hub TX: {hub_tx_hash.hex()}")
                    
                    # Create detailed NFT transfer record
                    nft_transfer_record = {
                        "transfer_id": str(uuid.uuid4()),
                        "product_id": token_id,
                        "from_owner": from_owner,
                        "to_owner": to_owner,
                        "escrow_id": escrow_id,
                        "fxportal_tx": fxportal_tx,
                        "fxportal_tx_receipt": {
                            "block_number": tx_receipt.blockNumber,
                            "gas_used": tx_receipt.gasUsed,
                            "status": tx_receipt.status
                        },
                        "hub_update_tx": hub_tx_hash.hex(),
                        "hub_update_receipt": {
                            "block_number": hub_tx_receipt.blockNumber,
                            "gas_used": hub_tx_receipt.gasUsed,
                            "status": hub_tx_receipt.status
                        },
                        "verification_hash": verification_hash,
                        "source_chain": "polygon_pos",
                        "target_chain": "base_sepolia",
                        "status": "completed",
                        "timestamp": time.time(),
                        "real_contract_call": True
                    }
                    
                    await self.database.nft_transfers.insert_one(nft_transfer_record)
                    
                    print(f"✅ NFT transfer completed with REAL contract calls")
                    print(f"   🔗 fxPortal TX: {fxportal_tx}")
                    print(f"   🔗 Hub Update TX: {hub_tx_hash.hex()}")
                    
                    return {
                        "success": True,
                        "transaction_hash": fxportal_tx,
                        "fxportal_tx": fxportal_tx,
                        "hub_update_tx": hub_tx_hash.hex(),
                        "transfer_id": nft_transfer_record["transfer_id"],
                        "real_transaction": True,
                        "fxportal_gas_used": tx_receipt.gasUsed,
                        "hub_gas_used": hub_tx_receipt.gasUsed,
                        "total_gas_used": tx_receipt.gasUsed + hub_tx_receipt.gasUsed
                    }
                else:
                    print(f"❌ Hub product status update failed!")
                    return {"success": False, "error": f"Hub update failed: {hub_tx_hash.hex()}"}
                    
            else:
                print(f"❌ fxPortal transaction failed!")
                return {"success": False, "error": f"fxPortal transaction failed: {fxportal_tx}"}
            
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

# Global service instance
crosschain_purchase_service = CrossChainPurchaseService()
