"""
Comprehensive Multi-Chain Shipping Service
Handles the complete shipping workflow from purchase to delivery
Integrates with LayerZero messaging for cross-chain notifications
"""
import time
import uuid
import asyncio
from typing import Dict, List, Any, Optional
from app.core.database import get_database
from app.services.chainflip_messaging_service import chainflip_messaging_service

class ShippingService:
    def __init__(self):
        self.database = None
        
        # Distance-based transporter calculation
        self.distance_ranges = {
            (0, 200): 1,      # 0-200 miles: 1 transporter
            (201, 500): 2,    # 201-500 miles: 2 transporters
            (501, 1000): 3,   # 501-1000 miles: 3 transporters
            (1001, 2000): 4,  # 1001-2000 miles: 4 transporters
            (2001, float('inf')): 5  # 2000+ miles: 5 transporters
        }
        
    async def initialize(self):
        """Initialize shipping service"""
        self.database = await get_database()
        print("✅ Shipping Service initialized")
    
    def calculate_transporters_needed(self, distance_miles: int) -> int:
        """Calculate number of transporters needed based on distance"""
        for (min_dist, max_dist), transporters in self.distance_ranges.items():
            if min_dist <= distance_miles <= max_dist:
                return transporters
        return 1  # Default fallback
    
    async def collect_shipping_information(self, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect shipping information from buyer during purchase process
        """
        try:
            purchase_id = purchase_data.get("purchase_id")
            buyer_address = purchase_data.get("buyer")
            
            print(f"📋 Collecting shipping information for purchase: {purchase_id}")
            
            # This would typically be collected from frontend form
            # For now, return a template structure
            shipping_info = {
                "shipping_id": f"SHIP-{purchase_id}",
                "purchase_id": purchase_id,
                "buyer_address": buyer_address,
                "delivery_address": {
                    "street": "",
                    "city": "",
                    "state": "",
                    "zip_code": "",
                    "country": "USA"
                },
                "contact_info": {
                    "phone": "",
                    "email": "",
                    "name": ""
                },
                "shipping_preferences": {
                    "priority": "standard",  # standard, express, overnight
                    "delivery_instructions": "",
                    "signature_required": True
                },
                "status": "pending_manufacturer_start",
                "created_at": time.time()
            }
            
            # Store shipping information
            await self.database.shipping_requests.insert_one(shipping_info)
            
            print(f"✅ Shipping information template created")
            return {
                "success": True,
                "shipping_id": shipping_info["shipping_id"],
                "status": "pending_manufacturer_start",
                "message": "Shipping information collected, waiting for manufacturer to start shipping process"
            }
            
        except Exception as e:
            print(f"❌ Error collecting shipping information: {e}")
            return {"success": False, "error": str(e)}
    
    async def notify_purchase_stakeholders(self, purchase_data: Dict[str, Any], shipping_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send LayerZero cross-chain notifications to Hub admin and Manufacturer
        """
        try:
            purchase_id = purchase_data.get("purchase_id")
            product_id = purchase_data.get("product_id")
            buyer_address = purchase_data.get("buyer")
            manufacturer_address = purchase_data.get("seller")
            
            print(f"📡 Sending cross-chain notifications for purchase: {purchase_id}")
            
            # Prepare notification data
            notification_data = {
                "event_type": "purchase_completed",
                "purchase_id": purchase_id,
                "product_id": product_id,
                "buyer": buyer_address,
                "manufacturer": manufacturer_address,
                "shipping_id": shipping_data.get("shipping_id"),
                "amount_eth": purchase_data.get("amount_eth"),
                "cfweth_minted": purchase_data.get("cfweth_minted"),
                "timestamp": int(time.time()),
                "status": "waiting_for_manufacture_shipping"
            }
            
            # Send notification to Hub admin on Polygon Amoy
            hub_notification = await chainflip_messaging_service.send_purchase_notification_to_hub(
                notification_data
            )
            
            # Send notification to Manufacturer on Base Sepolia
            manufacturer_notification = await chainflip_messaging_service.send_purchase_notification_to_manufacturer(
                manufacturer_address,
                notification_data
            )
            
            # Store notification records
            notification_record = {
                "notification_id": str(uuid.uuid4()),
                "purchase_id": purchase_id,
                "hub_notification": hub_notification,
                "manufacturer_notification": manufacturer_notification,
                "status": "sent",
                "created_at": time.time()
            }
            
            await self.database.purchase_notifications.insert_one(notification_record)
            
            print(f"✅ Cross-chain notifications sent successfully")
            return {
                "success": True,
                "hub_notification": hub_notification,
                "manufacturer_notification": manufacturer_notification
            }
            
        except Exception as e:
            print(f"❌ Error sending purchase notifications: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_manufacturer_shipping_requests(self, manufacturer_address: str) -> List[Dict[str, Any]]:
        """
        Get shipping requests waiting for manufacturer to start shipping
        """
        try:
            # Get purchases waiting for shipping
            cursor = self.database.purchases.find({
                "seller": manufacturer_address,
                "status": "paid_waiting_shipping",
                "stage": "waiting_for_manufacture_shipping"
            }).sort("created_at", -1)
            
            shipping_requests = []
            async for purchase in cursor:
                purchase["_id"] = str(purchase["_id"])
                
                # Get product details
                product = await self.database.products.find_one({
                    "token_id": purchase.get("product_id")
                })
                
                # Get shipping information
                shipping_info = await self.database.shipping_requests.find_one({
                    "purchase_id": purchase.get("purchase_id")
                })
                
                request_data = {
                    "purchase": purchase,
                    "product": product,
                    "shipping_info": shipping_info,
                    "waiting_since": purchase.get("created_at"),
                    "cfweth_amount": purchase.get("cfweth_minted", 0)
                }
                
                shipping_requests.append(request_data)
            
            print(f"📋 Found {len(shipping_requests)} shipping requests for manufacturer {manufacturer_address}")
            return shipping_requests
            
        except Exception as e:
            print(f"❌ Error getting shipping requests: {e}")
            return []
    
    async def start_shipping_process(self, manufacturer_address: str, purchase_id: str, distance_miles: int) -> Dict[str, Any]:
        """
        Manufacturer starts shipping process with distance calculation
        """
        try:
            print(f"🚛 Starting shipping process for purchase: {purchase_id}")
            print(f"📏 Distance: {distance_miles} miles")
            
            # Calculate transporters needed
            transporters_needed = self.calculate_transporters_needed(distance_miles)
            print(f"🚛 Transporters needed: {transporters_needed}")
            
            # Create shipping record
            shipping_record = {
                "shipping_id": f"SHIPPING-{purchase_id}-{int(time.time())}",
                "purchase_id": purchase_id,
                "manufacturer": manufacturer_address,
                "distance_miles": distance_miles,
                "transporters_needed": transporters_needed,
                "status": "transporter_selection",
                "stage": "selecting_transporters",
                "created_at": time.time(),
                "started_by": manufacturer_address
            }
            
            # Update purchase status
            await self.database.purchases.update_one(
                {"purchase_id": purchase_id},
                {"$set": {
                    "status": "shipping_initiated",
                    "stage": "transporter_selection",
                    "shipping_started_at": time.time(),
                    "distance_miles": distance_miles,
                    "transporters_needed": transporters_needed
                }}
            )
            
            # Store shipping record
            await self.database.shipping_records.insert_one(shipping_record)
            
            # Send shipping information to Hub for transporter selection
            hub_shipping_data = {
                "event_type": "shipping_initiated",
                "shipping_id": shipping_record["shipping_id"],
                "purchase_id": purchase_id,
                "manufacturer": manufacturer_address,
                "distance_miles": distance_miles,
                "transporters_needed": transporters_needed,
                "timestamp": int(time.time())
            }
            
            hub_notification = await chainflip_messaging_service.send_shipping_request_to_hub(
                hub_shipping_data
            )
            
            print(f"✅ Shipping process started successfully")
            return {
                "success": True,
                "shipping_id": shipping_record["shipping_id"],
                "transporters_needed": transporters_needed,
                "status": "transporter_selection",
                "hub_notification": hub_notification
            }
            
        except Exception as e:
            print(f"❌ Error starting shipping process: {e}")
            return {"success": False, "error": str(e)}
    
    async def assign_transporters(self, shipping_id: str, transporter_addresses: List[str]) -> Dict[str, Any]:
        """
        Hub admin assigns transporters to shipping request
        """
        try:
            print(f"👥 Assigning transporters to shipping: {shipping_id}")
            print(f"🚛 Transporters: {transporter_addresses}")
            
            # Update shipping record with assigned transporters
            await self.database.shipping_records.update_one(
                {"shipping_id": shipping_id},
                {"$set": {
                    "assigned_transporters": transporter_addresses,
                    "status": "transporters_assigned",
                    "stage": "awaiting_pickup",
                    "assigned_at": time.time()
                }}
            )
            
            # Create transporter assignments
            for i, transporter in enumerate(transporter_addresses):
                assignment = {
                    "assignment_id": f"ASSIGN-{shipping_id}-{i+1}",
                    "shipping_id": shipping_id,
                    "transporter": transporter,
                    "stage_number": i + 1,
                    "total_stages": len(transporter_addresses),
                    "status": "assigned" if i == 0 else "waiting",
                    "assigned_at": time.time()
                }
                
                await self.database.transporter_assignments.insert_one(assignment)
            
            # Notify first transporter
            if transporter_addresses:
                first_transporter = transporter_addresses[0]
                notification_data = {
                    "event_type": "transporter_assigned",
                    "shipping_id": shipping_id,
                    "stage_number": 1,
                    "transporter": first_transporter,
                    "timestamp": int(time.time())
                }
                
                await chainflip_messaging_service.send_transporter_assignment(
                    first_transporter, 
                    notification_data
                )
            
            print(f"✅ Transporters assigned successfully")
            return {
                "success": True,
                "assigned_transporters": transporter_addresses,
                "status": "transporters_assigned"
            }
            
        except Exception as e:
            print(f"❌ Error assigning transporters: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_transporter_handoff(self, current_transporter: str, shipping_id: str, handoff_message: str) -> Dict[str, Any]:
        """
        Process handoff between transporters
        """
        try:
            print(f"🔄 Processing transporter handoff for shipping: {shipping_id}")
            print(f"📦 From: {current_transporter}")
            
            # Get current assignment
            current_assignment = await self.database.transporter_assignments.find_one({
                "shipping_id": shipping_id,
                "transporter": current_transporter,
                "status": "active"
            })
            
            if not current_assignment:
                return {"success": False, "error": "Active assignment not found"}
            
            current_stage = current_assignment["stage_number"]
            total_stages = current_assignment["total_stages"]
            
            # Mark current stage as completed
            await self.database.transporter_assignments.update_one(
                {"assignment_id": current_assignment["assignment_id"]},
                {"$set": {
                    "status": "completed",
                    "completed_at": time.time(),
                    "handoff_message": handoff_message
                }}
            )
            
            # If not final stage, activate next transporter
            if current_stage < total_stages:
                next_assignment = await self.database.transporter_assignments.find_one({
                    "shipping_id": shipping_id,
                    "stage_number": current_stage + 1
                })
                
                if next_assignment:
                    await self.database.transporter_assignments.update_one(
                        {"assignment_id": next_assignment["assignment_id"]},
                        {"$set": {
                            "status": "active",
                            "activated_at": time.time()
                        }}
                    )
                    
                    # Notify next transporter
                    notification_data = {
                        "event_type": "handoff_received",
                        "shipping_id": shipping_id,
                        "stage_number": current_stage + 1,
                        "from_transporter": current_transporter,
                        "handoff_message": handoff_message,
                        "timestamp": int(time.time())
                    }
                    
                    await chainflip_messaging_service.send_transporter_handoff(
                        next_assignment["transporter"],
                        notification_data
                    )
                    
                    print(f"✅ Handoff to next transporter: {next_assignment['transporter']}")
            else:
                # Final delivery - notify buyer
                await self._notify_buyer_for_delivery(shipping_id)
                print(f"✅ Final delivery stage - buyer notified")
            
            # Notify Hub admin
            await chainflip_messaging_service.send_handoff_notification_to_hub({
                "shipping_id": shipping_id,
                "current_stage": current_stage,
                "total_stages": total_stages,
                "transporter": current_transporter,
                "handoff_message": handoff_message
            })
            
            return {
                "success": True,
                "current_stage": current_stage,
                "total_stages": total_stages,
                "next_stage": current_stage + 1 if current_stage < total_stages else "delivery"
            }
            
        except Exception as e:
            print(f"❌ Error processing transporter handoff: {e}")
            return {"success": False, "error": str(e)}
    
    async def _notify_buyer_for_delivery(self, shipping_id: str):
        """
        Notify buyer for final delivery with encrypted QR key
        """
        try:
            # Get shipping record
            shipping_record = await self.database.shipping_records.find_one({
                "shipping_id": shipping_id
            })
            
            # Get purchase record
            purchase = await self.database.purchases.find_one({
                "purchase_id": shipping_record["purchase_id"]
            })
            
            # Get product with encryption keys
            product = await self.database.products.find_one({
                "token_id": purchase["product_id"]
            })
            
            # Prepare delivery notification with encryption keys
            delivery_data = {
                "event_type": "ready_for_delivery",
                "shipping_id": shipping_id,
                "purchase_id": purchase["purchase_id"],
                "buyer": purchase["buyer"],
                "product_id": purchase["product_id"],
                "encryption_keys": product.get("encryption_keys"),  # Send product-specific keys
                "timestamp": int(time.time())
            }
            
            # Send to buyer via LayerZero
            await chainflip_messaging_service.send_delivery_notification_to_buyer(
                purchase["buyer"],
                delivery_data
            )
            
            print(f"✅ Buyer notified for delivery with encryption keys")
            
        except Exception as e:
            print(f"❌ Error notifying buyer for delivery: {e}")
    
    async def confirm_delivery(self, buyer_address: str, shipping_id: str, qr_verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Buyer confirms delivery after QR verification
        """
        try:
            print(f"✅ Processing delivery confirmation for shipping: {shipping_id}")
            
            # Update shipping status
            await self.database.shipping_records.update_one(
                {"shipping_id": shipping_id},
                {"$set": {
                    "status": "delivered",
                    "delivered_at": time.time(),
                    "delivered_to": buyer_address,
                    "qr_verification": qr_verification_data
                }}
            )
            
            # Update purchase status
            purchase = await self.database.purchases.find_one({
                "shipping_id": shipping_id
            })
            
            if purchase:
                await self.database.purchases.update_one(
                    {"purchase_id": purchase["purchase_id"]},
                    {"$set": {
                        "status": "delivered",
                        "delivered_at": time.time()
                    }}
                )
            
            print(f"✅ Delivery confirmed successfully")
            return {
                "success": True,
                "status": "delivered",
                "message": "Delivery confirmed, payment will be released to seller"
            }
            
        except Exception as e:
            print(f"❌ Error confirming delivery: {e}")
            return {"success": False, "error": str(e)}

# Global service instance
shipping_service = ShippingService()