"""
Algorithm 1: Payment Release and Incentive Mechanism Service
Implements escrow payment system with automated release and performance-based incentives
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import uuid
import math
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorDatabase

from .blockchain_service import blockchain_service
from .multichain_service import multichain_service


@dataclass
class EscrowPayment:
    payment_id: str
    purchase_request_id: str
    buyer_address: str
    total_amount: float
    escrow_amount: float
    manufacturer_amount: float
    transporter_amounts: Dict[str, float]
    status: str  # "locked", "released", "disputed", "refunded"
    created_at: datetime
    release_conditions: Dict
    

@dataclass
class TransporterIncentive:
    transporter_address: str
    base_payment: float
    performance_bonus: float
    delivery_time_bonus: float
    rating_bonus: float
    total_incentive: float
    performance_metrics: Dict
    

@dataclass
class PaymentDistribution:
    manufacturer_payment: float
    transporter_payments: Dict[str, float]
    platform_fee: float
    total_distributed: float
    distribution_timestamp: datetime


class PaymentIncentiveService:
    """
    Algorithm 1: Payment Release and Incentive Mechanism
    
    Features:
    1. Escrow payment system - locks payment until delivery confirmation
    2. Automated release upon buyer delivery confirmation
    3. Performance-based incentive calculation for transporters
    4. Dispute resolution integration
    5. Multi-chain payment coordination
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.database: Optional[AsyncIOMotorDatabase] = None
        
        # Payment configuration
        self.platform_fee_percentage = 0.025  # 2.5% platform fee
        self.transporter_base_percentage = 0.15  # 15% base transporter payment
        self.manufacturer_percentage = 0.825  # 82.5% manufacturer payment (after platform fee)
        
        # Performance bonus multipliers
        self.performance_multipliers = {
            "on_time_delivery": 1.2,    # 20% bonus for on-time delivery
            "early_delivery": 1.5,      # 50% bonus for early delivery
            "excellent_rating": 1.3,    # 30% bonus for rating >= 4.5
            "perfect_tracking": 1.1,    # 10% bonus for complete location updates
            "damage_free": 1.1          # 10% bonus for damage-free delivery
        }
        
        # Payment release conditions
        self.auto_release_delay = timedelta(days=7)  # Auto-release after 7 days if no disputes
        self.dispute_timeout = timedelta(days=30)    # Max dispute period
        
    async def initialize(self):
        """Initialize the payment incentive service"""
        try:
            self.database = await self.get_database()
            await self._ensure_collections()
            self.logger.info("✅ Payment Incentive Service initialized")
        except Exception as e:
            self.logger.error(f"❌ Payment service initialization failed: {e}")
            raise
    
    async def get_database(self):
        """Get database instance"""
        if hasattr(blockchain_service, 'database') and blockchain_service.database is not None:
            return blockchain_service.database
        return None
    
    async def _ensure_collections(self):
        """Ensure required database collections exist"""
        if self.database is None:
            self.logger.warning("Database is None, skipping collection initialization")
            return
            
        collections = [
            "escrow_payments",
            "payment_distributions", 
            "transporter_incentives",
            "payment_disputes",
            "performance_metrics"
        ]
        
        for collection in collections:
            await self.database[collection].create_index("timestamp")
            
        # Create specific indexes
        await self.database["escrow_payments"].create_index("purchase_request_id")
        await self.database["escrow_payments"].create_index("status")
        await self.database["transporter_incentives"].create_index("transporter_address")
        await self.database["performance_metrics"].create_index("transporter_address")
    
    # === ESCROW PAYMENT SYSTEM ===
    
    async def create_escrow_payment(
        self,
        purchase_request_id: str,
        buyer_address: str,
        total_amount: float,
        transporter_addresses: List[str],
        estimated_delivery_date: datetime
    ) -> Dict:
        """
        Create escrow payment when purchase is initiated
        Locks payment until delivery confirmation
        """
        try:
            self.logger.info(f"💰 Creating escrow payment for purchase: {purchase_request_id}")
            
            # Calculate payment distribution
            payment_breakdown = await self._calculate_payment_breakdown(
                total_amount, 
                len(transporter_addresses)
            )
            
            # Calculate individual transporter amounts
            transporter_amounts = {}
            individual_transporter_amount = payment_breakdown["total_transporter_payment"] / len(transporter_addresses)
            
            for address in transporter_addresses:
                transporter_amounts[address] = individual_transporter_amount
            
            # Create escrow payment record
            escrow_payment = EscrowPayment(
                payment_id=f"ESCROW-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}",
                purchase_request_id=purchase_request_id,
                buyer_address=buyer_address,
                total_amount=total_amount,
                escrow_amount=total_amount,
                manufacturer_amount=payment_breakdown["manufacturer_payment"],
                transporter_amounts=transporter_amounts,
                status="locked",
                created_at=datetime.utcnow(),
                release_conditions={
                    "delivery_confirmed": False,
                    "estimated_delivery_date": estimated_delivery_date.isoformat(),
                    "auto_release_date": (datetime.utcnow() + self.auto_release_delay).isoformat(),
                    "dispute_deadline": (datetime.utcnow() + self.dispute_timeout).isoformat()
                }
            )
            
            # Store in database
            await self.database["escrow_payments"].insert_one({
                **escrow_payment.__dict__,
                "payment_breakdown": payment_breakdown
            })
            
            # Lock payment on blockchain (simulate for now)
            blockchain_lock_result = await self._lock_payment_on_blockchain(
                buyer_address, 
                total_amount, 
                escrow_payment.payment_id
            )
            
            self.logger.info(f"✅ Escrow payment created: {escrow_payment.payment_id}")
            
            return {
                "success": True,
                "payment_id": escrow_payment.payment_id,
                "escrow_amount": total_amount,
                "payment_breakdown": payment_breakdown,
                "blockchain_lock": blockchain_lock_result,
                "release_conditions": escrow_payment.release_conditions,
                "message": f"Payment of {total_amount} locked in escrow"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Escrow payment creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _calculate_payment_breakdown(self, total_amount: float, num_transporters: int) -> Dict:
        """Calculate payment distribution breakdown"""
        platform_fee = total_amount * self.platform_fee_percentage
        remaining_amount = total_amount - platform_fee
        
        total_transporter_payment = remaining_amount * self.transporter_base_percentage
        manufacturer_payment = remaining_amount - total_transporter_payment
        
        return {
            "total_amount": total_amount,
            "platform_fee": platform_fee,
            "manufacturer_payment": manufacturer_payment,
            "total_transporter_payment": total_transporter_payment,
            "individual_transporter_base": total_transporter_payment / num_transporters if num_transporters > 0 else 0,
            "num_transporters": num_transporters
        }
    
    async def _lock_payment_on_blockchain(self, buyer_address: str, amount: float, payment_id: str) -> Dict:
        """Lock payment on blockchain escrow contract"""
        try:
            # In real implementation, this would call an escrow smart contract
            # For now, simulate the blockchain transaction
            mock_tx_hash = f"0x{uuid.uuid4().hex}"
            
            self.logger.info(f"🔗 Payment locked on blockchain: {amount} from {buyer_address}")
            
            return {
                "transaction_hash": mock_tx_hash,
                "escrow_contract": "0x1234567890123456789012345678901234567890",
                "amount_locked": amount,
                "buyer_address": buyer_address,
                "payment_id": payment_id,
                "block_number": 12345678,
                "status": "locked"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Blockchain payment lock failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    # === PERFORMANCE-BASED INCENTIVE CALCULATION ===
    
    async def calculate_transporter_incentives(
        self,
        purchase_request_id: str,
        transporter_address: str,
        delivery_metrics: Dict
    ) -> Dict:
        """
        Calculate performance-based incentives for a transporter
        
        Performance factors:
        - Delivery time (early/on-time/late)
        - Customer rating
        - Tracking completeness
        - Damage-free delivery
        - Communication quality
        """
        try:
            self.logger.info(f"📊 Calculating incentives for transporter: {transporter_address}")
            
            # Get base payment amount
            escrow_payment = await self.database["escrow_payments"].find_one({
                "purchase_request_id": purchase_request_id
            })
            
            if not escrow_payment:
                return {"success": False, "error": "Escrow payment not found"}
            
            base_payment = escrow_payment["transporter_amounts"].get(transporter_address, 0)
            
            if base_payment == 0:
                return {"success": False, "error": "Transporter not assigned to this delivery"}
            
            # Calculate performance multipliers
            performance_multiplier = 1.0
            performance_details = {}
            
            # Delivery time performance
            if delivery_metrics.get("delivery_status") == "early":
                performance_multiplier *= self.performance_multipliers["early_delivery"]
                performance_details["early_delivery_bonus"] = True
            elif delivery_metrics.get("delivery_status") == "on_time":
                performance_multiplier *= self.performance_multipliers["on_time_delivery"]
                performance_details["on_time_bonus"] = True
            
            # Customer rating performance
            customer_rating = delivery_metrics.get("customer_rating", 0)
            if customer_rating >= 4.5:
                performance_multiplier *= self.performance_multipliers["excellent_rating"]
                performance_details["excellent_rating_bonus"] = True
            
            # Tracking completeness
            tracking_completeness = delivery_metrics.get("tracking_completeness", 0)
            if tracking_completeness >= 0.9:  # 90% or more updates provided
                performance_multiplier *= self.performance_multipliers["perfect_tracking"]
                performance_details["perfect_tracking_bonus"] = True
            
            # Damage-free delivery
            if delivery_metrics.get("damage_free", False):
                performance_multiplier *= self.performance_multipliers["damage_free"]
                performance_details["damage_free_bonus"] = True
            
            # Calculate final incentive amounts
            performance_bonus = base_payment * (performance_multiplier - 1.0)
            total_incentive = base_payment * performance_multiplier
            
            # Create incentive record
            incentive = TransporterIncentive(
                transporter_address=transporter_address,
                base_payment=base_payment,
                performance_bonus=performance_bonus,
                delivery_time_bonus=base_payment * (self.performance_multipliers.get("early_delivery", 1.0) - 1.0) if delivery_metrics.get("delivery_status") == "early" else 0,
                rating_bonus=base_payment * (self.performance_multipliers.get("excellent_rating", 1.0) - 1.0) if customer_rating >= 4.5 else 0,
                total_incentive=total_incentive,
                performance_metrics=delivery_metrics
            )
            
            # Store incentive calculation
            await self.database["transporter_incentives"].insert_one({
                **incentive.__dict__,
                "purchase_request_id": purchase_request_id,
                "calculated_at": datetime.utcnow(),
                "performance_multiplier": performance_multiplier,
                "performance_details": performance_details
            })
            
            self.logger.info(f"✅ Incentive calculated: {total_incentive} (base: {base_payment}, bonus: {performance_bonus})")
            
            return {
                "success": True,
                "transporter_address": transporter_address,
                "base_payment": base_payment,
                "performance_bonus": performance_bonus,
                "total_incentive": total_incentive,
                "performance_multiplier": performance_multiplier,
                "performance_details": performance_details,
                "delivery_metrics": delivery_metrics
            }
            
        except Exception as e:
            self.logger.error(f"❌ Incentive calculation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # === AUTOMATED PAYMENT RELEASE ===
    
    async def release_payment_on_delivery(
        self,
        purchase_request_id: str,
        buyer_address: str,
        delivery_confirmation: Dict,
        transporter_metrics: List[Dict]
    ) -> Dict:
        """
        Release escrow payment when buyer confirms delivery
        Integrates with buyer_confirm_delivery_and_trigger_nft_transfer flow
        """
        try:
            self.logger.info(f"🚀 Processing payment release for delivery: {purchase_request_id}")
            
            # Get escrow payment
            escrow_payment = await self.database["escrow_payments"].find_one({
                "purchase_request_id": purchase_request_id,
                "buyer_address": buyer_address
            })
            
            if not escrow_payment:
                return {"success": False, "error": "Escrow payment not found"}
            
            if escrow_payment["status"] != "locked":
                return {"success": False, "error": f"Payment status is {escrow_payment['status']}, cannot release"}
            
            # Calculate all transporter incentives
            transporter_final_payments = {}
            total_transporter_payment = 0
            
            for metric in transporter_metrics:
                transporter_address = metric["transporter_address"]
                incentive_result = await self.calculate_transporter_incentives(
                    purchase_request_id,
                    transporter_address,
                    metric["delivery_metrics"]
                )
                
                if incentive_result["success"]:
                    final_payment = incentive_result["total_incentive"]
                    transporter_final_payments[transporter_address] = final_payment
                    total_transporter_payment += final_payment
                else:
                    # Fallback to base payment if incentive calculation fails
                    base_payment = escrow_payment["transporter_amounts"].get(transporter_address, 0)
                    transporter_final_payments[transporter_address] = base_payment
                    total_transporter_payment += base_payment
            
            # Calculate final payment distribution
            platform_fee = escrow_payment["escrow_amount"] * self.platform_fee_percentage
            manufacturer_payment = escrow_payment["manufacturer_amount"]
            
            payment_distribution = PaymentDistribution(
                manufacturer_payment=manufacturer_payment,
                transporter_payments=transporter_final_payments,
                platform_fee=platform_fee,
                total_distributed=manufacturer_payment + total_transporter_payment + platform_fee,
                distribution_timestamp=datetime.utcnow()
            )
            
            # Execute payments on blockchain
            blockchain_release_result = await self._execute_payment_release_blockchain(
                escrow_payment, 
                payment_distribution,
                delivery_confirmation
            )
            
            # Update escrow payment status
            await self.database["escrow_payments"].update_one(
                {"payment_id": escrow_payment["payment_id"]},
                {
                    "$set": {
                        "status": "released",
                        "released_at": datetime.utcnow(),
                        "delivery_confirmation": delivery_confirmation,
                        "final_payment_distribution": payment_distribution.__dict__,
                        "blockchain_release": blockchain_release_result
                    }
                }
            )
            
            # Store payment distribution record
            await self.database["payment_distributions"].insert_one({
                **payment_distribution.__dict__,
                "purchase_request_id": purchase_request_id,
                "payment_id": escrow_payment["payment_id"],
                "blockchain_transactions": blockchain_release_result
            })
            
            # Update transporter performance history
            await self._update_transporter_performance_history(transporter_metrics)
            
            self.logger.info(f"✅ Payment released successfully: {payment_distribution.total_distributed}")
            
            return {
                "success": True,
                "payment_id": escrow_payment["payment_id"],
                "payment_distribution": payment_distribution.__dict__,
                "blockchain_transactions": blockchain_release_result,
                "total_released": payment_distribution.total_distributed,
                "manufacturer_payment": manufacturer_payment,
                "transporter_payments": transporter_final_payments,
                "platform_fee": platform_fee,
                "message": "Payment released successfully to all parties"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Payment release failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_payment_release_blockchain(
        self,
        escrow_payment: Dict,
        payment_distribution: PaymentDistribution,
        delivery_confirmation: Dict
    ) -> Dict:
        """Execute payment release on blockchain"""
        try:
            # In real implementation, this would call escrow contract release functions
            # For now, simulate multiple blockchain transactions
            
            transactions = []
            
            # Manufacturer payment
            manufacturer_tx = f"0x{uuid.uuid4().hex}"
            transactions.append({
                "type": "manufacturer_payment",
                "recipient": escrow_payment.get("manufacturer_address", "0x0"),
                "amount": payment_distribution.manufacturer_payment,
                "transaction_hash": manufacturer_tx
            })
            
            # Transporter payments
            for address, amount in payment_distribution.transporter_payments.items():
                transporter_tx = f"0x{uuid.uuid4().hex}"
                transactions.append({
                    "type": "transporter_payment",
                    "recipient": address,
                    "amount": amount,
                    "transaction_hash": transporter_tx
                })
            
            # Platform fee
            platform_tx = f"0x{uuid.uuid4().hex}"
            transactions.append({
                "type": "platform_fee",
                "recipient": "0xPlatformAddress",
                "amount": payment_distribution.platform_fee,
                "transaction_hash": platform_tx
            })
            
            self.logger.info(f"🔗 {len(transactions)} blockchain payment transactions executed")
            
            return {
                "success": True,
                "transactions": transactions,
                "total_transactions": len(transactions),
                "total_amount_released": payment_distribution.total_distributed,
                "escrow_contract_address": "0x1234567890123456789012345678901234567890",
                "release_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Blockchain payment release failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_transporter_performance_history(self, transporter_metrics: List[Dict]):
        """Update performance history for all transporters"""
        try:
            for metric in transporter_metrics:
                await self.database["performance_metrics"].insert_one({
                    "transporter_address": metric["transporter_address"],
                    "delivery_metrics": metric["delivery_metrics"],
                    "recorded_at": datetime.utcnow()
                })
            
            self.logger.info(f"📈 Performance history updated for {len(transporter_metrics)} transporters")
            
        except Exception as e:
            self.logger.error(f"❌ Performance history update failed: {e}")
    
    # === DISPUTE RESOLUTION INTEGRATION ===
    
    async def handle_dispute_payment(
        self,
        purchase_request_id: str,
        dispute_reason: str,
        dispute_details: Dict
    ) -> Dict:
        """Handle payment disputes"""
        try:
            # Get escrow payment
            escrow_payment = await self.database["escrow_payments"].find_one({
                "purchase_request_id": purchase_request_id
            })
            
            if not escrow_payment:
                return {"success": False, "error": "Escrow payment not found"}
            
            if escrow_payment["status"] != "locked":
                return {"success": False, "error": "Payment must be locked to dispute"}
            
            # Update payment status to disputed
            await self.database["escrow_payments"].update_one(
                {"payment_id": escrow_payment["payment_id"]},
                {
                    "$set": {
                        "status": "disputed",
                        "disputed_at": datetime.utcnow(),
                        "dispute_reason": dispute_reason,
                        "dispute_details": dispute_details
                    }
                }
            )
            
            # Create dispute record
            dispute_record = {
                "dispute_id": f"DISPUTE-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}",
                "payment_id": escrow_payment["payment_id"],
                "purchase_request_id": purchase_request_id,
                "dispute_reason": dispute_reason,
                "dispute_details": dispute_details,
                "created_at": datetime.utcnow(),
                "status": "open",
                "resolution": None
            }
            
            await self.database["payment_disputes"].insert_one(dispute_record)
            
            return {
                "success": True,
                "dispute_id": dispute_record["dispute_id"],
                "payment_status": "disputed",
                "message": "Payment dispute created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Payment dispute handling failed: {e}")
            return {"success": False, "error": str(e)}
    
    # === PAYMENT STATUS AND TRACKING ===
    
    async def get_payment_status(self, purchase_request_id: str) -> Dict:
        """Get current payment status for a purchase request"""
        try:
            escrow_payment = await self.database["escrow_payments"].find_one({
                "purchase_request_id": purchase_request_id
            })
            
            if not escrow_payment:
                return {"success": False, "error": "Payment not found"}
            
            # Get additional details if payment is released
            payment_distribution = None
            if escrow_payment["status"] == "released":
                payment_distribution = await self.database["payment_distributions"].find_one({
                    "purchase_request_id": purchase_request_id
                })
            
            return {
                "success": True,
                "payment_id": escrow_payment["payment_id"],
                "status": escrow_payment["status"],
                "total_amount": escrow_payment["escrow_amount"],
                "created_at": escrow_payment["created_at"],
                "release_conditions": escrow_payment["release_conditions"],
                "payment_distribution": payment_distribution.__dict__ if payment_distribution else None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Payment status check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_transporter_earnings_history(self, transporter_address: str, limit: int = 50) -> Dict:
        """Get earnings history for a transporter"""
        try:
            cursor = self.database["transporter_incentives"].find({
                "transporter_address": transporter_address
            }).sort("calculated_at", -1).limit(limit)
            
            earnings_history = await cursor.to_list(length=limit)
            
            # Calculate summary statistics
            total_earnings = sum(earning["total_incentive"] for earning in earnings_history)
            total_deliveries = len(earnings_history)
            average_incentive = total_earnings / total_deliveries if total_deliveries > 0 else 0
            
            return {
                "success": True,
                "transporter_address": transporter_address,
                "total_earnings": total_earnings,
                "total_deliveries": total_deliveries,
                "average_incentive": average_incentive,
                "earnings_history": earnings_history
            }
            
        except Exception as e:
            self.logger.error(f"❌ Earnings history retrieval failed: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
payment_incentive_service = PaymentIncentiveService()