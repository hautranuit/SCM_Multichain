"""
Supply Chain Orchestration Service
Implements cross-chain purchase flow with Hub coordination and reputation-based transporter selection
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import uuid
import math
import json

from motor.motor_asyncio import AsyncIOMotorDatabase
from web3 import Web3

from .multi_account_manager import MultiAccountManager
from .layerzero_oft_bridge_service import layerzero_oft_bridge_service
from .blockchain_service import blockchain_service
from .multichain_service import multichain_service


@dataclass
class TransporterAssignment:
    transporter_id: str
    transporter_address: str
    reputation_score: float
    chain_id: int
    assigned_segment: Dict
    
@dataclass
class PurchaseRequest:
    request_id: str
    buyer_address: str
    buyer_chain: str
    product_id: str
    manufacturer_address: str
    manufacturer_chain: str
    delivery_address: str
    delivery_coordinates: Tuple[float, float]
    manufacturer_coordinates: Tuple[float, float]
    distance_miles: float
    purchase_amount: float
    timestamp: datetime
    status: str

@dataclass
class TransportationBatch:
    batch_id: str
    requests: List[PurchaseRequest]
    transporters: List[TransporterAssignment]
    validation_nodes: List[str]
    consensus_threshold: float
    created_at: datetime
    status: str


class SupplyChainOrchestrator:
    """
    Simplified Supply Chain Consensus with Hub Coordination
    
    Architecture:
    - Hub (Polygon Amoy) coordinates all cross-chain activities
    - Reputation-based transporter selection
    - Distance-based automatic assignment
    - Batch processing for efficiency
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.account_manager = MultiAccountManager()
        
        # Chain configurations
        self.chains = {
            "optimism_sepolia": {"chain_id": 11155420, "role": "buyer"},
            "base_sepolia": {"chain_id": 84532, "role": "manufacturer"},
            "arbitrum_sepolia": {"chain_id": 421614, "role": "transporter"},
            "polygon_amoy": {"chain_id": 80002, "role": "hub"}
        }
        
        # Distance-based transporter requirements
        self.transporter_requirements = {
            (50, 100): 1,
            (100, 250): 2,
            (250, 500): 3,
            (500, 750): 4,
            (750, 1000): 5
        }
        
        # Consensus parameters
        self.consensus_threshold = 0.67  # 2/3 supermajority
        self.min_reputation_score = 0.6
        self.batch_size = 10
        self.batch_timeout = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize the orchestrator with database and services"""
        try:
            self.database = await self.get_database()
            await self._ensure_collections()
            self.logger.info("✅ Supply Chain Orchestrator initialized")
        except Exception as e:
            self.logger.error(f"❌ Orchestrator initialization failed: {e}")
            raise
    
    async def get_database(self):
        """Get database instance"""
        if blockchain_service.database:
            return blockchain_service.database
        return None
    
    async def _ensure_collections(self):
        """Ensure required database collections exist"""
        collections = [
            "purchase_requests",
            "transportation_batches", 
            "transporter_reputation",
            "delivery_routes",
            "consensus_votes"
        ]
        
        for collection in collections:
            await self.database[collection].create_index("timestamp")
            
        # Create specific indexes
        await self.database["transporter_reputation"].create_index("reputation_score")
        await self.database["purchase_requests"].create_index("status")
        
    # === CROSS-CHAIN PURCHASE FLOW ===
    
    async def initiate_purchase(
        self,
        buyer_address: str,
        buyer_chain: str,
        product_id: str,
        manufacturer_address: str,
        manufacturer_chain: str,
        delivery_address: str,
        delivery_coordinates: Tuple[float, float],
        manufacturer_coordinates: Tuple[float, float],
        purchase_amount: float
    ) -> Dict:
        """
        Step 1: Buyer initiates purchase on their chain (OP Sepolia)
        Cross-chain flow: Buyer (OP Sepolia) → Hub (Polygon Amoy) → Manufacturer (Base Sepolia)
        """
        try:
            # Calculate distance
            distance_miles = self._calculate_distance(
                manufacturer_coordinates, 
                delivery_coordinates
            )
            
            # Create purchase request
            request = PurchaseRequest(
                request_id=f"PURCHASE-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}",
                buyer_address=buyer_address,
                buyer_chain=buyer_chain,
                product_id=product_id,
                manufacturer_address=manufacturer_address,
                manufacturer_chain=manufacturer_chain,
                delivery_address=delivery_address,
                delivery_coordinates=delivery_coordinates,
                manufacturer_coordinates=manufacturer_coordinates,
                distance_miles=distance_miles,
                purchase_amount=purchase_amount,
                timestamp=datetime.utcnow(),
                status="sending_to_hub"
            )
            
            # CROSS-CHAIN: Send purchase request from Buyer chain to Hub (Polygon Amoy)
            hub_message_result = await self._send_purchase_request_to_hub(request)
            
            # Store in database (this happens on Hub after receiving the message)
            await self.database["purchase_requests"].insert_one({
                **request.__dict__,
                "hub_message_result": hub_message_result
            })
            
            return {
                "success": True,
                "request_id": request.request_id,
                "distance_miles": distance_miles,
                "transporters_required": self._get_transporters_required(distance_miles),
                "cross_chain_message": hub_message_result,
                "status": "sent_to_hub",
                "message": f"Purchase request sent from {buyer_chain} to Hub (Polygon Amoy)"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Purchase initiation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_purchase_request_to_hub(self, request: PurchaseRequest) -> Dict:
        """
        CROSS-CHAIN: Send purchase request from Buyer chain to Hub (Polygon Amoy)
        """
        try:
            self.logger.info(f"🌐 Sending purchase request from {request.buyer_chain} to Hub (Polygon Amoy)")
            
            # Prepare cross-chain message data
            message_data = {
                "type": "PURCHASE_REQUEST",
                "request_id": request.request_id,
                "buyer_address": request.buyer_address,
                "buyer_chain": request.buyer_chain,
                "product_id": request.product_id,
                "manufacturer_address": request.manufacturer_address,
                "manufacturer_chain": request.manufacturer_chain,
                "delivery_address": request.delivery_address,
                "delivery_coordinates": list(request.delivery_coordinates),
                "manufacturer_coordinates": list(request.manufacturer_coordinates),
                "distance_miles": request.distance_miles,
                "purchase_amount": request.purchase_amount,
                "timestamp": request.timestamp.isoformat()
            }
            
            # Use LayerZero to send cross-chain message
            # From buyer_chain to polygon_amoy (Hub)
            layerzero_result = await self._send_layerzero_message(
                source_chain=request.buyer_chain,
                target_chain="polygon_amoy",
                message_data=message_data,
                recipient_address="0x032041b4b356fEE1496805DD4749f181bC736FFA"  # Hub coordinator
            )
            
            return {
                "cross_chain_sent": True,
                "source_chain": request.buyer_chain,
                "target_chain": "polygon_amoy",
                "layerzero_tx": layerzero_result.get("transaction_hash"),
                "message_type": "PURCHASE_REQUEST"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Cross-chain purchase request failed: {e}")
            return {"cross_chain_sent": False, "error": str(e)}
    
    async def _coordinate_via_hub(self, request: PurchaseRequest) -> Dict:
        """
        Step 2: Hub receives cross-chain message and coordinates the purchase
        This runs on Polygon Amoy (Hub chain)
        """
        try:
            self.logger.info(f"🌐 Hub coordinating purchase: {request.request_id}")
            
            # Prepare transporter assignment on Hub
            transporter_assignment = await self._prepare_transporter_assignment(request)
            
            # CROSS-CHAIN: Send notification to manufacturer
            manufacturer_notification = await self._notify_manufacturer_crosschain(request)
            
            # Update request status in Hub database
            await self.database["purchase_requests"].update_one(
                {"request_id": request.request_id},
                {
                    "$set": {
                        "status": "manufacturer_notified",
                        "transporter_assignment": transporter_assignment,
                        "manufacturer_notification": manufacturer_notification,
                        "hub_coordination_timestamp": datetime.utcnow()
                    }
                }
            )
            
            return {
                "hub_coordinated": True,
                "manufacturer_notified": manufacturer_notification,
                "transporter_assignment": transporter_assignment,
                "coordination_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Hub coordination failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _notify_manufacturer_crosschain(self, request: PurchaseRequest) -> Dict:
        """
        CROSS-CHAIN: Send notification from Hub (Polygon Amoy) to Manufacturer (Base Sepolia)
        """
        try:
            self.logger.info(f"🌐 Sending cross-chain notification to manufacturer: {request.manufacturer_address}")
            
            # Prepare manufacturer notification data
            message_data = {
                "type": "MANUFACTURER_ORDER_NOTIFICATION",
                "request_id": request.request_id,
                "buyer_address": request.buyer_address,
                "buyer_chain": request.buyer_chain,
                "product_id": request.product_id,
                "delivery_address": request.delivery_address,
                "delivery_coordinates": list(request.delivery_coordinates),
                "distance_miles": request.distance_miles,
                "purchase_amount": request.purchase_amount,
                "transporters_required": self._get_transporters_required(request.distance_miles),
                "hub_timestamp": datetime.utcnow().isoformat()
            }
            
            # Use LayerZero to send from Hub to Manufacturer chain
            layerzero_result = await self._send_layerzero_message(
                source_chain="polygon_amoy",
                target_chain=request.manufacturer_chain,
                message_data=message_data,
                recipient_address=request.manufacturer_address
            )
            
            return {
                "cross_chain_sent": True,
                "source_chain": "polygon_amoy",
                "target_chain": request.manufacturer_chain,
                "recipient": request.manufacturer_address,
                "layerzero_tx": layerzero_result.get("transaction_hash"),
                "message_type": "MANUFACTURER_ORDER_NOTIFICATION"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Cross-chain manufacturer notification failed: {e}")
            return {"cross_chain_sent": False, "error": str(e)}
    
    # === TRANSPORTER SELECTION & REPUTATION SYSTEM ===
    
    async def _prepare_transporter_assignment(self, request: PurchaseRequest) -> Dict:
        """Prepare transporter assignment based on distance and reputation"""
        try:
            transporters_needed = self._get_transporters_required(request.distance_miles)
            
            # Get available transporters with good reputation
            available_transporters = await self._get_available_transporters(
                min_reputation=self.min_reputation_score
            )
            
            if len(available_transporters) < transporters_needed:
                return {
                    "assignment_ready": False,
                    "reason": f"Insufficient transporters. Need: {transporters_needed}, Available: {len(available_transporters)}"
                }
            
            # Select best transporters by reputation
            selected_transporters = await self._select_transporters(
                available_transporters, 
                transporters_needed,
                request.distance_miles
            )
            
            return {
                "assignment_ready": True,
                "transporters_needed": transporters_needed,
                "selected_transporters": [t.__dict__ for t in selected_transporters],
                "total_distance": request.distance_miles
            }
            
        except Exception as e:
            self.logger.error(f"❌ Transporter assignment preparation failed: {e}")
            return {"assignment_ready": False, "error": str(e)}
    
    def _get_transporters_required(self, distance_miles: float) -> int:
        """Calculate number of transporters required based on distance"""
        for (min_dist, max_dist), count in self.transporter_requirements.items():
            if min_dist <= distance_miles <= max_dist:
                return count
        return 5  # Default for very long distances
    
    async def _get_available_transporters(self, min_reputation: float = 0.6) -> List[Dict]:
        """Get available transporters with minimum reputation score"""
        try:
            cursor = self.database["transporter_reputation"].find({
                "reputation_score": {"$gte": min_reputation},
                "status": "available"
            }).sort("reputation_score", -1)
            
            transporters = await cursor.to_list(length=50)
            return transporters
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get available transporters: {e}")
            return []
    
    async def _select_transporters(
        self, 
        available_transporters: List[Dict], 
        count_needed: int,
        distance_miles: float
    ) -> List[TransporterAssignment]:
        """Select best transporters based on reputation and create assignments"""
        selected = []
        segment_distance = distance_miles / count_needed
        
        for i in range(count_needed):
            if i < len(available_transporters):
                transporter = available_transporters[i]
                
                assignment = TransporterAssignment(
                    transporter_id=transporter["transporter_id"],
                    transporter_address=transporter["address"],
                    reputation_score=transporter["reputation_score"],
                    chain_id=transporter.get("chain_id", 421614),  # Default to Arbitrum
                    assigned_segment={
                        "segment_number": i + 1,
                        "start_mile": i * segment_distance,
                        "end_mile": (i + 1) * segment_distance,
                        "distance": segment_distance
                    }
                )
                selected.append(assignment)
        
        return selected
    
    # === MANUFACTURER SHIPPING PROCESS ===
    
    async def manufacturer_start_shipping(
        self,
        request_id: str,
        manufacturer_address: str,
        shipping_details: Dict
    ) -> Dict:
        """
        Step 3: Manufacturer starts shipping process (on Base Sepolia)
        CROSS-CHAIN: Notify transporters and send updates to Hub
        """
        try:
            # Get purchase request from Hub database (cross-chain query)
            hub_request = await self._get_request_from_hub(request_id)
            
            if not hub_request:
                return {"success": False, "error": "Purchase request not found on Hub"}
            
            # Verify manufacturer authorization
            if hub_request["manufacturer_address"] != manufacturer_address:
                return {"success": False, "error": "Unauthorized manufacturer"}
            
            # Get transporter assignments from Hub
            transporter_assignment = hub_request.get("transporter_assignment", {})
            
            if not transporter_assignment.get("assignment_ready"):
                return {"success": False, "error": "Transporter assignment not ready"}
            
            # CROSS-CHAIN: Notify Hub about shipping initiation
            hub_notification = await self._notify_hub_shipping_started(request_id, manufacturer_address, shipping_details)
            
            # CROSS-CHAIN: Notify assigned transporters
            transporter_notifications = await self._notify_transporters_crosschain(
                request_id, 
                transporter_assignment["selected_transporters"],
                shipping_details
            )
            
            # Create transportation batch (consensus validation)
            batch = await self._create_transportation_batch_crosschain(hub_request, shipping_details)
            
            return {
                "success": True,
                "request_id": request_id,
                "hub_notification": hub_notification,
                "transporter_notifications": transporter_notifications,
                "transportation_batch": batch,
                "status": "shipping_initiated_crosschain"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Manufacturer shipping failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_request_from_hub(self, request_id: str) -> Dict:
        """Cross-chain query to get request data from Hub"""
        try:
            # In a real implementation, this would be a cross-chain query
            # For now, we'll access the Hub database directly
            request_doc = await self.database["purchase_requests"].find_one({
                "request_id": request_id
            })
            return request_doc
        except Exception as e:
            self.logger.error(f"❌ Hub query failed: {e}")
            return None
    
    async def _notify_hub_shipping_started(self, request_id: str, manufacturer_address: str, shipping_details: Dict) -> Dict:
        """
        CROSS-CHAIN: Notify Hub that shipping has started (Base Sepolia → Polygon Amoy)
        """
        try:
            message_data = {
                "type": "SHIPPING_STARTED",
                "request_id": request_id,
                "manufacturer_address": manufacturer_address,
                "shipping_details": shipping_details,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            layerzero_result = await self._send_layerzero_message(
                source_chain="base_sepolia",
                target_chain="polygon_amoy",
                message_data=message_data,
                recipient_address="0x032041b4b356fEE1496805DD4749f181bC736FFA"  # Hub coordinator
            )
            
            return {
                "cross_chain_sent": True,
                "source_chain": "base_sepolia",
                "target_chain": "polygon_amoy",
                "layerzero_tx": layerzero_result.get("transaction_hash"),
                "message_type": "SHIPPING_STARTED"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Hub shipping notification failed: {e}")
            return {"cross_chain_sent": False, "error": str(e)}
    
    async def _notify_transporters_crosschain(self, request_id: str, transporters: List[Dict], shipping_details: Dict) -> List[Dict]:
        """
        CROSS-CHAIN: Notify transporters about new shipping assignment (Base Sepolia → Arbitrum Sepolia)
        """
        notifications = []
        
        for transporter in transporters:
            try:
                message_data = {
                    "type": "TRANSPORT_ASSIGNMENT",
                    "request_id": request_id,
                    "transporter_address": transporter["transporter_address"],
                    "assigned_segment": transporter["assigned_segment"],
                    "shipping_details": shipping_details,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                layerzero_result = await self._send_layerzero_message(
                    source_chain="base_sepolia",
                    target_chain="arbitrum_sepolia",
                    message_data=message_data,
                    recipient_address=transporter["transporter_address"]
                )
                
                notifications.append({
                    "transporter": transporter["transporter_address"],
                    "cross_chain_sent": True,
                    "layerzero_tx": layerzero_result.get("transaction_hash"),
                    "segment": transporter["assigned_segment"]["segment_number"]
                })
                
            except Exception as e:
                self.logger.error(f"❌ Transporter notification failed for {transporter['transporter_address']}: {e}")
                notifications.append({
                    "transporter": transporter["transporter_address"],
                    "cross_chain_sent": False,
                    "error": str(e)
                })
        
        return notifications
    
    # === CROSS-CHAIN MESSAGING UTILITIES ===
    
    async def _send_layerzero_message(
        self,
        source_chain: str,
        target_chain: str,
        message_data: Dict,
        recipient_address: str
    ) -> Dict:
        """
        Send cross-chain message using LayerZero infrastructure
        """
        try:
            self.logger.info(f"🌐 Sending LayerZero message: {source_chain} → {target_chain}")
            
            # Convert message to bytes (simple JSON encoding for now)
            message_bytes = json.dumps(message_data).encode('utf-8')
            
            # Use existing LayerZero service for cross-chain messaging
            if layerzero_oft_bridge_service:
                # This would use your existing LayerZero messaging infrastructure
                # For now, we'll simulate the cross-chain message
                result = {
                    "transaction_hash": f"0x{uuid.uuid4().hex}",
                    "source_chain": source_chain,
                    "target_chain": target_chain,
                    "recipient": recipient_address,
                    "message_size": len(message_bytes),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "sent"
                }
                
                # Store cross-chain message record
                await self.database["cross_chain_messages"].insert_one({
                    "message_id": result["transaction_hash"],
                    "source_chain": source_chain,
                    "target_chain": target_chain,
                    "recipient_address": recipient_address,
                    "message_type": message_data.get("type"),
                    "message_data": message_data,
                    "timestamp": datetime.utcnow(),
                    "status": "sent"
                })
                
                return result
            else:
                raise Exception("LayerZero service not available")
                
        except Exception as e:
            self.logger.error(f"❌ LayerZero message failed: {e}")
            return {"transaction_hash": None, "error": str(e)}
    
    async def _handle_incoming_cross_chain_message(self, message_data: Dict, source_chain: str) -> Dict:
        """
        Handle incoming cross-chain messages
        """
        try:
            message_type = message_data.get("type")
            self.logger.info(f"📥 Received cross-chain message: {message_type} from {source_chain}")
            
            if message_type == "PURCHASE_REQUEST":
                # Hub receives purchase request from buyer
                return await self._handle_purchase_request_on_hub(message_data)
                
            elif message_type == "MANUFACTURER_ORDER_NOTIFICATION":
                # Manufacturer receives order notification from hub
                return await self._handle_manufacturer_notification(message_data)
                
            elif message_type == "SHIPPING_STARTED":
                # Hub receives shipping confirmation from manufacturer
                return await self._handle_shipping_started_on_hub(message_data)
                
            elif message_type == "TRANSPORT_ASSIGNMENT":
                # Transporter receives assignment from manufacturer
                return await self._handle_transport_assignment(message_data)
                
            elif message_type == "CONSENSUS_VOTE":
                # Hub receives consensus vote from transporter
                return await self._handle_consensus_vote(message_data)
                
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                return {"handled": False, "error": f"Unknown message type: {message_type}"}
                
        except Exception as e:
            self.logger.error(f"❌ Cross-chain message handling failed: {e}")
            return {"handled": False, "error": str(e)}
    
    async def _handle_purchase_request_on_hub(self, message_data: Dict) -> Dict:
        """Handle purchase request received on Hub from buyer chain"""
        try:
            # Reconstruct purchase request from cross-chain message
            request = PurchaseRequest(
                request_id=message_data["request_id"],
                buyer_address=message_data["buyer_address"],
                buyer_chain=message_data["buyer_chain"],
                product_id=message_data["product_id"],
                manufacturer_address=message_data["manufacturer_address"],
                manufacturer_chain=message_data["manufacturer_chain"],
                delivery_address=message_data["delivery_address"],
                delivery_coordinates=tuple(message_data["delivery_coordinates"]),
                manufacturer_coordinates=tuple(message_data["manufacturer_coordinates"]),
                distance_miles=message_data["distance_miles"],
                purchase_amount=message_data["purchase_amount"],
                timestamp=datetime.fromisoformat(message_data["timestamp"]),
                status="received_on_hub"
            )
            
            # Process on Hub
            hub_result = await self._coordinate_via_hub(request)
            
            return {"handled": True, "hub_coordination": hub_result}
            
        except Exception as e:
            self.logger.error(f"❌ Hub purchase request handling failed: {e}")
            return {"handled": False, "error": str(e)}
    
    async def _handle_manufacturer_notification(self, message_data: Dict) -> Dict:
        """Handle manufacturer notification received on manufacturer chain"""
        try:
            # Store notification for manufacturer to see
            await self.database["manufacturer_notifications"].insert_one({
                "request_id": message_data["request_id"],
                "buyer_address": message_data["buyer_address"],
                "buyer_chain": message_data["buyer_chain"],
                "product_id": message_data["product_id"],
                "delivery_details": {
                    "address": message_data["delivery_address"],
                    "coordinates": message_data["delivery_coordinates"]
                },
                "purchase_amount": message_data["purchase_amount"],
                "distance_miles": message_data["distance_miles"],
                "transporters_required": message_data["transporters_required"],
                "status": "pending_manufacturer_action",
                "received_at": datetime.utcnow()
            })
            
            return {"handled": True, "status": "notification_stored"}
            
        except Exception as e:
            self.logger.error(f"❌ Manufacturer notification handling failed: {e}")
            return {"handled": False, "error": str(e)}
    
    async def _create_transportation_batch(self, request_doc: Dict, shipping_details: Dict) -> Dict:
        """
        Create transportation batch with simplified consensus
        Instead of complex Primary/Secondary nodes, use reputation-based validation
        """
        try:
            batch_id = f"BATCH-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}"
            
            # Get transporters for this batch
            transporter_assignment = request_doc.get("hub_coordination", {}).get("transporter_assignment", {})
            selected_transporters = transporter_assignment.get("selected_transporters", [])
            
            # Select validation nodes (high reputation transporters)
            validation_nodes = await self._select_validation_nodes()
            
            batch_data = {
                "batch_id": batch_id,
                "request_ids": [request_doc["request_id"]],
                "transporters": selected_transporters,
                "validation_nodes": validation_nodes,
                "consensus_threshold": self.consensus_threshold,
                "created_at": datetime.utcnow(),
                "status": "pending_validation",
                "shipping_details": shipping_details
            }
            
            # Store batch
            await self.database["transportation_batches"].insert_one(batch_data)
            
            # Initiate consensus validation
            consensus_result = await self._initiate_consensus_validation(batch_data)
            
            return {
                "batch_id": batch_id,
                "transporters_count": len(selected_transporters),
                "validation_nodes_count": len(validation_nodes),
                "consensus_result": consensus_result
            }
            
        except Exception as e:
            self.logger.error(f"❌ Transportation batch creation failed: {e}")
            return {"batch_id": None, "error": str(e)}
    
    async def _select_validation_nodes(self, count: int = 5) -> List[str]:
        """Select high-reputation nodes for validation"""
        try:
            cursor = self.database["transporter_reputation"].find({
                "reputation_score": {"$gte": 0.8},
                "role": {"$in": ["validator", "transporter"]}
            }).sort("reputation_score", -1).limit(count)
            
            validators = await cursor.to_list(length=count)
            return [v["address"] for v in validators]
            
        except Exception as e:
            self.logger.error(f"❌ Validation node selection failed: {e}")
            return []
    
    async def _initiate_consensus_validation(self, batch_data: Dict) -> Dict:
        """
        Simplified consensus validation process
        """
        try:
            batch_id = batch_data["batch_id"]
            validation_nodes = batch_data["validation_nodes"]
            
            self.logger.info(f"🗳️ Initiating consensus validation for batch: {batch_id}")
            
            # In a real implementation, this would:
            # 1. Send validation requests to nodes
            # 2. Collect votes
            # 3. Determine consensus
            
            # For now, simulate the consensus process
            votes = []
            for node in validation_nodes:
                # Simulate validation (in reality, nodes would validate against blockchain records)
                vote = {
                    "validator": node,
                    "vote": "approve",  # or "reject"
                    "timestamp": datetime.utcnow(),
                    "reasoning": "Batch validated successfully"
                }
                votes.append(vote)
            
            # Calculate consensus
            approve_votes = len([v for v in votes if v["vote"] == "approve"])
            total_votes = len(votes)
            consensus_ratio = approve_votes / total_votes if total_votes > 0 else 0
            
            consensus_reached = consensus_ratio >= self.consensus_threshold
            
            # Store votes
            await self.database["consensus_votes"].insert_one({
                "batch_id": batch_id,
                "votes": votes,
                "consensus_ratio": consensus_ratio,
                "consensus_reached": consensus_reached,
                "timestamp": datetime.utcnow()
            })
            
            # Update batch status
            new_status = "validated" if consensus_reached else "rejected"
            await self.database["transportation_batches"].update_one(
                {"batch_id": batch_id},
                {"$set": {"status": new_status, "consensus_result": {
                    "consensus_reached": consensus_reached,
                    "consensus_ratio": consensus_ratio,
                    "votes_count": total_votes
                }}}
            )
            
            return {
                "consensus_reached": consensus_reached,
                "consensus_ratio": consensus_ratio,
                "votes_count": total_votes,
                "status": new_status
            }
            
        except Exception as e:
            self.logger.error(f"❌ Consensus validation failed: {e}")
            return {"consensus_reached": False, "error": str(e)}
    
    # === REPUTATION MANAGEMENT ===
    
    async def update_transporter_reputation(
        self,
        transporter_address: str,
        performance_metrics: Dict
    ) -> Dict:
        """Update transporter reputation based on performance"""
        try:
            # Calculate new reputation score
            current_doc = await self.database["transporter_reputation"].find_one({
                "address": transporter_address
            })
            
            if not current_doc:
                # Create new reputation record
                reputation_data = {
                    "transporter_id": f"TRANS-{uuid.uuid4().hex[:8]}",
                    "address": transporter_address,
                    "reputation_score": 0.7,  # Starting score
                    "total_deliveries": 0,
                    "successful_deliveries": 0,
                    "average_delivery_time": 0,
                    "status": "available",
                    "created_at": datetime.utcnow()
                }
                await self.database["transporter_reputation"].insert_one(reputation_data)
                current_score = 0.7
            else:
                current_score = current_doc["reputation_score"]
            
            # Calculate score adjustment based on performance
            score_adjustment = self._calculate_reputation_adjustment(performance_metrics)
            new_score = max(0.0, min(1.0, current_score + score_adjustment))
            
            # Update reputation
            await self.database["transporter_reputation"].update_one(
                {"address": transporter_address},
                {
                    "$set": {"reputation_score": new_score},
                    "$inc": {
                        "total_deliveries": 1,
                        "successful_deliveries": 1 if performance_metrics.get("success", False) else 0
                    }
                }
            )
            
            return {
                "success": True,
                "transporter": transporter_address,
                "old_score": current_score,
                "new_score": new_score,
                "adjustment": score_adjustment
            }
            
        except Exception as e:
            self.logger.error(f"❌ Reputation update failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_reputation_adjustment(self, metrics: Dict) -> float:
        """Calculate reputation score adjustment based on performance metrics"""
        adjustment = 0.0
        
        # Delivery success
        if metrics.get("success", False):
            adjustment += 0.02
        else:
            adjustment -= 0.05
        
        # Delivery time
        expected_time = metrics.get("expected_delivery_hours", 24)
        actual_time = metrics.get("actual_delivery_hours", 24)
        
        if actual_time <= expected_time:
            adjustment += 0.01
        elif actual_time > expected_time * 1.5:
            adjustment -= 0.03
        
        # Package condition
        if metrics.get("package_condition", "good") == "excellent":
            adjustment += 0.01
        elif metrics.get("package_condition", "good") == "poor":
            adjustment -= 0.02
        
        return adjustment
    
    # === UTILITY FUNCTIONS ===
    
    def _calculate_distance(
        self, 
        point1: Tuple[float, float], 
        point2: Tuple[float, float]
    ) -> float:
        """Calculate distance between two coordinates in miles"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Haversine formula
        R = 3959  # Earth's radius in miles
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    # === API ENDPOINTS SUPPORT ===
    
    async def get_purchase_status(self, request_id: str) -> Dict:
        """Get status of a purchase request"""
        try:
            request_doc = await self.database["purchase_requests"].find_one({
                "request_id": request_id
            })
            
            if not request_doc:
                return {"found": False, "error": "Purchase request not found"}
            
            # Get associated batch if exists
            batch_info = None
            if request_doc.get("transportation_batch_id"):
                batch_doc = await self.database["transportation_batches"].find_one({
                    "batch_id": request_doc["transportation_batch_id"]
                })
                if batch_doc:
                    batch_info = {
                        "batch_id": batch_doc["batch_id"],
                        "status": batch_doc["status"],
                        "transporters_count": len(batch_doc.get("transporters", [])),
                        "consensus_result": batch_doc.get("consensus_result", {})
                    }
            
            return {
                "found": True,
                "request_id": request_id,
                "status": request_doc["status"],
                "distance_miles": request_doc["distance_miles"],
                "transporters_required": self._get_transporters_required(request_doc["distance_miles"]),
                "batch_info": batch_info,
                "created_at": request_doc["timestamp"],
                "hub_coordination": request_doc.get("hub_coordination", {}),
                "shipping_details": request_doc.get("shipping_details", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ Get purchase status failed: {e}")
            return {"found": False, "error": str(e)}
    
    async def get_transporter_leaderboard(self, limit: int = 20) -> List[Dict]:
        """Get top transporters by reputation"""
        try:
            cursor = self.database["transporter_reputation"].find({}).sort(
                "reputation_score", -1
            ).limit(limit)
            
            transporters = await cursor.to_list(length=limit)
            
            # Format for API response
            leaderboard = []
            for i, transporter in enumerate(transporters):
                leaderboard.append({
                    "rank": i + 1,
                    "address": transporter["address"],
                    "reputation_score": transporter["reputation_score"],
                    "total_deliveries": transporter.get("total_deliveries", 0),
                    "success_rate": (transporter.get("successful_deliveries", 0) / 
                                   max(1, transporter.get("total_deliveries", 1))) * 100,
                    "status": transporter.get("status", "unknown")
                })
            
            return leaderboard
            
        except Exception as e:
            self.logger.error(f"❌ Get transporter leaderboard failed: {e}")
            return []


# Global instance
supply_chain_orchestrator = SupplyChainOrchestrator()
