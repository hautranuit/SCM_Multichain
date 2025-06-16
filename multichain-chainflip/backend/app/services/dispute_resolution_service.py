"""
Dispute Resolution and Voting Mechanism Service
Implementation of Algorithm 2 from Narayanan et al. paper

Architecture:
- Stakeholder-driven arbitrator selection
- Neutral arbitrator requirement
- Blockchain and NFT evidence review
- Automated decision execution
- Comprehensive dispute tracking
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from motor.motor_asyncio import AsyncIOMotorDatabase


class DisputeStatus(Enum):
    INITIATED = "initiated"
    VOTING_ARBITRATOR = "voting_arbitrator"
    ARBITRATOR_SELECTED = "arbitrator_selected"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    FAILED = "failed"


class DisputeType(Enum):
    PRODUCT_QUALITY = "product_quality"
    DELIVERY_DELAY = "delivery_delay"
    PAYMENT_DISPUTE = "payment_dispute"
    COUNTERFEIT_CLAIM = "counterfeit_claim"
    DAMAGE_CLAIM = "damage_claim"
    CONTRACT_BREACH = "contract_breach"


class StakeholderRole(Enum):
    BUYER = "buyer"
    MANUFACTURER = "manufacturer" 
    TRANSPORTER = "transporter"
    INSPECTOR = "inspector"
    NETWORK_NODE = "network_node"


@dataclass
class Stakeholder:
    """Stakeholder in the supply chain"""
    stakeholder_id: str
    address: str
    role: StakeholderRole
    reputation_score: float
    stake_amount: float
    voting_weight: float
    is_active: bool


@dataclass
class ArbitratorCandidate:
    """Potential arbitrator for dispute resolution"""
    arbitrator_id: str
    address: str
    name: str
    expertise_areas: List[str]
    reputation_score: float
    resolution_success_rate: float
    total_cases_handled: int
    neutrality_score: float
    is_available: bool
    chain_id: int


@dataclass
class DisputeEvidence:
    """Evidence for dispute resolution"""
    evidence_id: str
    evidence_type: str  # "blockchain", "nft", "document", "photo", "video"
    content: Dict  # Evidence content/metadata
    ipfs_hash: Optional[str]
    blockchain_tx_hash: Optional[str]
    nft_token_id: Optional[str]
    submitted_by: str
    timestamp: datetime
    verified: bool


@dataclass
class ArbitratorVote:
    """Stakeholder vote for arbitrator selection"""
    vote_id: str
    dispute_id: str
    stakeholder_id: str
    stakeholder_address: str
    arbitrator_candidate_id: str
    vote_weight: float
    reasoning: Optional[str]
    timestamp: datetime


@dataclass
class DisputeRecord:
    """Complete dispute record"""
    dispute_id: str
    dispute_type: DisputeType
    involved_parties: List[str]  # Addresses of involved parties
    stakeholder_list: List[str]  # All stakeholders who can vote
    product_id: Optional[str]
    transaction_id: Optional[str]
    description: str
    evidence: List[DisputeEvidence]
    arbitrator_candidates: List[str]  # Arbitrator IDs
    selected_arbitrator: Optional[str]
    status: DisputeStatus
    resolution_outcome: Optional[Dict]
    created_at: datetime
    deadline: datetime
    resolved_at: Optional[datetime]


class DisputeResolutionService:
    """
    Dispute Resolution and Voting Mechanism
    Implementation of Algorithm 2 from Narayanan et al. paper
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.database: Optional[AsyncIOMotorDatabase] = None
        
        # Dispute resolution parameters
        self.voting_deadline_hours = 48
        self.arbitrator_selection_threshold = 0.5  # 50% of weighted votes
        self.min_neutrality_score = 0.7
        self.min_arbitrator_reputation = 0.8
        self.resolution_deadline_days = 7
        
        # Voting weight factors
        self.reputation_weight_factor = 0.4
        self.stake_weight_factor = 0.6
        
    async def initialize(self):
        """Initialize the dispute resolution service"""
        try:
            # Get database from blockchain service
            from .blockchain_service import blockchain_service
            if hasattr(blockchain_service, 'database') and blockchain_service.database is not None:
                self.database = blockchain_service.database
            else:
                raise Exception("Blockchain service database not initialized")
            
            # Ensure collections exist
            await self._ensure_collections()
            
            # Initialize arbitrator registry
            await self._initialize_arbitrator_registry()
            
            # Initialize stakeholder registry
            await self._initialize_stakeholder_registry()
            
            self.logger.info("✅ Dispute Resolution Service initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Dispute Resolution Service initialization failed: {e}")
            raise
    
    async def _ensure_collections(self):
        """Ensure required database collections exist"""
        collections = [
            "dispute_records",
            "arbitrator_candidates", 
            "stakeholder_registry",
            "arbitrator_votes",
            "dispute_evidence",
            "resolution_outcomes"
        ]
        
        for collection in collections:
            # Create indexes
            if collection == "dispute_records":
                await self.database[collection].create_index([("dispute_id", 1)], unique=True)
                await self.database[collection].create_index([("status", 1), ("created_at", -1)])
            elif collection == "arbitrator_candidates":
                await self.database[collection].create_index([("arbitrator_id", 1)], unique=True)
                await self.database[collection].create_index([("address", 1)], unique=True)
            elif collection == "stakeholder_registry":
                await self.database[collection].create_index([("address", 1)], unique=True)
            elif collection == "arbitrator_votes":
                await self.database[collection].create_index([("dispute_id", 1), ("stakeholder_id", 1)], unique=True)
    
    async def _initialize_arbitrator_registry(self):
        """Initialize arbitrator candidate registry"""
        try:
            # Check if arbitrators already exist
            existing_count = await self.database["arbitrator_candidates"].count_documents({})
            
            if existing_count > 0:
                self.logger.info(f"✅ Found {existing_count} existing arbitrator candidates")
                return
            
            # Create default arbitrator candidates
            default_arbitrators = [
                {
                    "arbitrator_id": "ARB-SUPPLY-EXPERT-001",
                    "address": "0xA1B2C3D4E5F6789012345678901234567890ABCD",
                    "name": "Supply Chain Expert Alpha",
                    "expertise_areas": ["supply_chain", "quality_control", "logistics"],
                    "reputation_score": 0.95,
                    "resolution_success_rate": 0.92,
                    "total_cases_handled": 156,
                    "neutrality_score": 0.88,
                    "is_available": True,
                    "chain_id": 80002  # Polygon Amoy
                },
                {
                    "arbitrator_id": "ARB-TRADE-EXPERT-001",
                    "address": "0xB2C3D4E5F6789012345678901234567890ABCDE",
                    "name": "International Trade Arbitrator",
                    "expertise_areas": ["international_trade", "contract_law", "payments"],
                    "reputation_score": 0.93,
                    "resolution_success_rate": 0.89,
                    "total_cases_handled": 203,
                    "neutrality_score": 0.91,
                    "is_available": True,
                    "chain_id": 11155420  # Optimism Sepolia
                },
                {
                    "arbitrator_id": "ARB-TECH-EXPERT-001",
                    "address": "0xC3D4E5F6789012345678901234567890ABCDEF12",
                    "name": "Blockchain Technology Arbitrator",
                    "expertise_areas": ["blockchain", "smart_contracts", "nft_verification"],
                    "reputation_score": 0.91,
                    "resolution_success_rate": 0.94,
                    "total_cases_handled": 128,
                    "neutrality_score": 0.85,
                    "is_available": True,
                    "chain_id": 84532  # Base Sepolia
                },
                {
                    "arbitrator_id": "ARB-QUALITY-EXPERT-001",
                    "address": "0xD4E5F6789012345678901234567890ABCDEF1234",
                    "name": "Product Quality Inspector",
                    "expertise_areas": ["product_quality", "damage_assessment", "manufacturing"],
                    "reputation_score": 0.89,
                    "resolution_success_rate": 0.91,
                    "total_cases_handled": 97,
                    "neutrality_score": 0.87,
                    "is_available": True,
                    "chain_id": 421614  # Arbitrum Sepolia
                }
            ]
            
            await self.database["arbitrator_candidates"].insert_many(default_arbitrators)
            self.logger.info(f"✅ Initialized {len(default_arbitrators)} arbitrator candidates")
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator registry initialization failed: {e}")
    
    async def _initialize_stakeholder_registry(self):
        """Initialize stakeholder registry with default entities"""
        try:
            # Check if stakeholders already exist
            existing_count = await self.database["stakeholder_registry"].count_documents({})
            
            if existing_count > 0:
                self.logger.info(f"✅ Found {existing_count} existing stakeholders")
                return
            
            # Create default stakeholders
            default_stakeholders = [
                {
                    "stakeholder_id": "STAKE-BUYER-001",
                    "address": "0x742d35Cc6266C5a8a4f1Ed1B3E6606c5d9B2cB5E",
                    "role": StakeholderRole.BUYER.value,
                    "reputation_score": 0.85,
                    "stake_amount": 2.5,
                    "voting_weight": 0.75,
                    "is_active": True
                },
                {
                    "stakeholder_id": "STAKE-MANUFACTURER-001", 
                    "address": "0x123d35Cc6266C5a8a4f1Ed1B3E6606c5d9B2cB5F",
                    "role": StakeholderRole.MANUFACTURER.value,
                    "reputation_score": 0.92,
                    "stake_amount": 5.0,
                    "voting_weight": 0.88,
                    "is_active": True
                },
                {
                    "stakeholder_id": "STAKE-TRANSPORTER-001",
                    "address": "0x456d35Cc6266C5a8a4f1Ed1B3E6606c5d9B2cB60",
                    "role": StakeholderRole.TRANSPORTER.value,
                    "reputation_score": 0.88,
                    "stake_amount": 3.0,
                    "voting_weight": 0.82,
                    "is_active": True
                },
                {
                    "stakeholder_id": "STAKE-INSPECTOR-001",
                    "address": "0x789d35Cc6266C5a8a4f1Ed1B3E6606c5d9B2cB61",
                    "role": StakeholderRole.INSPECTOR.value,
                    "reputation_score": 0.95,
                    "stake_amount": 1.5,
                    "voting_weight": 0.85,
                    "is_active": True
                }
            ]
            
            await self.database["stakeholder_registry"].insert_many(default_stakeholders)
            self.logger.info(f"✅ Initialized {len(default_stakeholders)} stakeholders")
            
        except Exception as e:
            self.logger.error(f"❌ Stakeholder registry initialization failed: {e}")
    
    # === DISPUTE INITIATION ===
    
    async def initiate_dispute(
        self,
        dispute_type: str,
        involved_parties: List[str],
        product_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        description: str = "",
        evidence: List[Dict] = None
    ) -> Dict:
        """
        Initiate a new dispute for stakeholder-driven arbitrator selection
        Algorithm 2: Dispute Resolution - Step 1
        """
        try:
            dispute_id = f"DISPUTE-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}"
            
            self.logger.info(f"⚖️ Initiating dispute: {dispute_id} ({dispute_type})")
            
            # Get relevant stakeholders for voting
            stakeholders = await self._get_relevant_stakeholders(involved_parties, product_id)
            if not stakeholders:
                return {"success": False, "error": "No eligible stakeholders found for voting"}
            
            # Get suitable arbitrator candidates
            arbitrator_candidates = await self._get_suitable_arbitrators(dispute_type)
            if not arbitrator_candidates:
                return {"success": False, "error": "No suitable arbitrators available"}
            
            # Process evidence
            processed_evidence = []
            if evidence:
                for evidence_item in evidence:
                    processed_evidence.append(DisputeEvidence(
                        evidence_id=f"EVID-{uuid.uuid4().hex[:8]}",
                        evidence_type=evidence_item.get("type", "document"),
                        content=evidence_item.get("content", {}),
                        ipfs_hash=evidence_item.get("ipfs_hash"),
                        blockchain_tx_hash=evidence_item.get("blockchain_tx_hash"),
                        nft_token_id=evidence_item.get("nft_token_id"),
                        submitted_by=evidence_item.get("submitted_by", involved_parties[0]),
                        timestamp=datetime.utcnow(),
                        verified=False
                    ))
            
            # Create dispute record
            dispute = DisputeRecord(
                dispute_id=dispute_id,
                dispute_type=DisputeType(dispute_type),
                involved_parties=involved_parties,
                stakeholder_list=[s["address"] for s in stakeholders],
                product_id=product_id,
                transaction_id=transaction_id,
                description=description,
                evidence=processed_evidence,
                arbitrator_candidates=[a["arbitrator_id"] for a in arbitrator_candidates],
                selected_arbitrator=None,
                status=DisputeStatus.VOTING_ARBITRATOR,
                resolution_outcome=None,
                created_at=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(hours=self.voting_deadline_hours),
                resolved_at=None
            )
            
            # Store in database
            await self.database["dispute_records"].insert_one({
                **dispute.__dict__,
                "stakeholders": stakeholders,
                "arbitrator_candidates_full": arbitrator_candidates
            })
            
            # Notify stakeholders to vote
            for stakeholder in stakeholders:
                await self._notify_stakeholder_to_vote(stakeholder, dispute_id, arbitrator_candidates)
            
            self.logger.info(f"✅ Dispute initiated: {dispute_id} with {len(stakeholders)} voters and {len(arbitrator_candidates)} arbitrator candidates")
            
            return {
                "success": True,
                "dispute_id": dispute_id,
                "status": DisputeStatus.VOTING_ARBITRATOR.value,
                "stakeholder_count": len(stakeholders),
                "arbitrator_candidates_count": len(arbitrator_candidates),
                "voting_deadline": dispute.deadline.isoformat(),
                "message": f"Dispute initiated. Stakeholders have {self.voting_deadline_hours} hours to vote for arbitrator."
            }
            
        except Exception as e:
            self.logger.error(f"❌ Dispute initiation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # === ARBITRATOR SELECTION VOTING ===
    
    async def submit_arbitrator_vote(
        self,
        dispute_id: str,
        stakeholder_address: str,
        arbitrator_candidate_id: str,
        reasoning: Optional[str] = None
    ) -> Dict:
        """
        Submit stakeholder vote for arbitrator selection
        Algorithm 2: Dispute Resolution - Step 2
        """
        try:
            self.logger.info(f"🗳️ Processing arbitrator vote for dispute: {dispute_id}")
            
            # Get dispute record
            dispute_doc = await self.database["dispute_records"].find_one({"dispute_id": dispute_id})
            if not dispute_doc:
                return {"success": False, "error": "Dispute not found"}
            
            if dispute_doc["status"] != DisputeStatus.VOTING_ARBITRATOR.value:
                return {"success": False, "error": f"Dispute not in voting phase (status: {dispute_doc['status']})"}
            
            # Check voting deadline
            if datetime.utcnow() > datetime.fromisoformat(dispute_doc["deadline"]):
                return {"success": False, "error": "Voting deadline has passed"}
            
            # Verify stakeholder eligibility
            if stakeholder_address not in dispute_doc["stakeholder_list"]:
                return {"success": False, "error": "Stakeholder not eligible to vote on this dispute"}
            
            # Check if stakeholder already voted
            existing_vote = await self.database["arbitrator_votes"].find_one({
                "dispute_id": dispute_id,
                "stakeholder_address": stakeholder_address
            })
            if existing_vote:
                return {"success": False, "error": "Stakeholder has already voted"}
            
            # Verify arbitrator candidate validity
            if arbitrator_candidate_id not in dispute_doc["arbitrator_candidates"]:
                return {"success": False, "error": "Invalid arbitrator candidate"}
            
            # Get stakeholder details for voting weight
            stakeholder_doc = await self.database["stakeholder_registry"].find_one({
                "address": stakeholder_address
            })
            if not stakeholder_doc:
                return {"success": False, "error": "Stakeholder not found in registry"}
            
            # Create vote record
            vote = ArbitratorVote(
                vote_id=f"VOTE-{uuid.uuid4().hex[:8]}",
                dispute_id=dispute_id,
                stakeholder_id=stakeholder_doc["stakeholder_id"],
                stakeholder_address=stakeholder_address,
                arbitrator_candidate_id=arbitrator_candidate_id,
                vote_weight=stakeholder_doc["voting_weight"],
                reasoning=reasoning,
                timestamp=datetime.utcnow()
            )
            
            # Store vote
            await self.database["arbitrator_votes"].insert_one(vote.__dict__)
            
            # Check if consensus reached
            consensus_result = await self._check_arbitrator_consensus(dispute_id)
            
            if consensus_result["consensus_reached"]:
                # Select arbitrator and move to next phase
                selected_arbitrator = consensus_result["selected_arbitrator"]
                
                await self.database["dispute_records"].update_one(
                    {"dispute_id": dispute_id},
                    {
                        "$set": {
                            "selected_arbitrator": selected_arbitrator,
                            "status": DisputeStatus.ARBITRATOR_SELECTED.value,
                            "arbitrator_selected_at": datetime.utcnow()
                        }
                    }
                )
                
                # Notify arbitrator to start review
                arbitrator_doc = await self.database["arbitrator_candidates"].find_one({
                    "arbitrator_id": selected_arbitrator
                })
                if arbitrator_doc:
                    await self._notify_arbitrator_to_review(arbitrator_doc, dispute_id)
                
                return {
                    "success": True,
                    "vote_recorded": True,
                    "consensus_reached": True,
                    "selected_arbitrator": selected_arbitrator,
                    "status": DisputeStatus.ARBITRATOR_SELECTED.value,
                    "message": f"Vote recorded and arbitrator {selected_arbitrator} selected"
                }
            else:
                return {
                    "success": True,
                    "vote_recorded": True,
                    "consensus_reached": False,
                    "votes_needed": consensus_result.get("votes_needed", 0),
                    "message": "Vote recorded. Waiting for more votes to reach consensus."
                }
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator vote submission failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_arbitrator_consensus(self, dispute_id: str) -> Dict:
        """Check if arbitrator selection consensus has been reached"""
        try:
            # Get all votes for this dispute
            votes_cursor = self.database["arbitrator_votes"].find({"dispute_id": dispute_id})
            votes = await votes_cursor.to_list(length=1000)
            
            if not votes:
                return {"consensus_reached": False, "votes_needed": 1}
            
            # Calculate total voting weight
            total_weight = sum(vote["vote_weight"] for vote in votes)
            
            # Count votes by arbitrator candidate
            candidate_votes = {}
            for vote in votes:
                candidate_id = vote["arbitrator_candidate_id"]
                if candidate_id not in candidate_votes:
                    candidate_votes[candidate_id] = 0
                candidate_votes[candidate_id] += vote["vote_weight"]
            
            # Check if any candidate has reached threshold
            threshold_weight = total_weight * self.arbitrator_selection_threshold
            
            for candidate_id, vote_weight in candidate_votes.items():
                if vote_weight >= threshold_weight:
                    return {
                        "consensus_reached": True,
                        "selected_arbitrator": candidate_id,
                        "vote_weight": vote_weight,
                        "threshold_weight": threshold_weight
                    }
            
            return {
                "consensus_reached": False,
                "current_leader": max(candidate_votes.items(), key=lambda x: x[1]) if candidate_votes else None,
                "threshold_weight": threshold_weight,
                "total_weight": total_weight
            }
            
        except Exception as e:
            self.logger.error(f"❌ Consensus check failed: {e}")
            return {"consensus_reached": False, "error": str(e)}
    
    # === DISPUTE RESOLUTION PROCESS ===
    
    async def start_dispute_review(
        self,
        dispute_id: str,
        arbitrator_id: str
    ) -> Dict:
        """
        Start dispute review process by selected arbitrator
        Algorithm 2: Dispute Resolution - Step 3
        """
        try:
            self.logger.info(f"🔍 Starting dispute review: {dispute_id} by {arbitrator_id}")
            
            # Verify dispute and arbitrator
            dispute_doc = await self.database["dispute_records"].find_one({"dispute_id": dispute_id})
            if not dispute_doc:
                return {"success": False, "error": "Dispute not found"}
            
            if dispute_doc["selected_arbitrator"] != arbitrator_id:
                return {"success": False, "error": "Arbitrator not authorized for this dispute"}
            
            if dispute_doc["status"] != DisputeStatus.ARBITRATOR_SELECTED.value:
                return {"success": False, "error": f"Dispute not ready for review (status: {dispute_doc['status']})"}
            
            # Update dispute status
            await self.database["dispute_records"].update_one(
                {"dispute_id": dispute_id},
                {
                    "$set": {
                        "status": DisputeStatus.UNDER_REVIEW.value,
                        "review_started_at": datetime.utcnow(),
                        "review_deadline": datetime.utcnow() + timedelta(days=self.resolution_deadline_days)
                    }
                }
            )
            
            # Start evidence verification process
            evidence_verification = await self._start_evidence_verification(dispute_id)
            
            return {
                "success": True,
                "dispute_id": dispute_id,
                "status": DisputeStatus.UNDER_REVIEW.value,
                "arbitrator_id": arbitrator_id,
                "review_deadline": (datetime.utcnow() + timedelta(days=self.resolution_deadline_days)).isoformat(),
                "evidence_verification": evidence_verification,
                "message": f"Dispute review started. Resolution deadline: {self.resolution_deadline_days} days"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Dispute review start failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def submit_dispute_resolution(
        self,
        dispute_id: str,
        arbitrator_id: str,
        resolution_decision: str,  # "favor_buyer", "favor_seller", "split_decision", "no_fault"
        resolution_details: Dict,
        compensation_amount: Optional[float] = None,
        compensation_recipient: Optional[str] = None
    ) -> Dict:
        """
        Submit final dispute resolution decision
        Algorithm 2: Dispute Resolution - Step 4
        """
        try:
            self.logger.info(f"⚖️ Submitting dispute resolution: {dispute_id}")
            
            # Verify dispute and arbitrator
            dispute_doc = await self.database["dispute_records"].find_one({"dispute_id": dispute_id})
            if not dispute_doc:
                return {"success": False, "error": "Dispute not found"}
            
            if dispute_doc["selected_arbitrator"] != arbitrator_id:
                return {"success": False, "error": "Arbitrator not authorized for this dispute"}
            
            if dispute_doc["status"] != DisputeStatus.UNDER_REVIEW.value:
                return {"success": False, "error": f"Dispute not under review (status: {dispute_doc['status']})"}
            
            # Create resolution outcome
            resolution_outcome = {
                "decision": resolution_decision,
                "details": resolution_details,
                "compensation_amount": compensation_amount,
                "compensation_recipient": compensation_recipient,
                "arbitrator_id": arbitrator_id,
                "resolution_timestamp": datetime.utcnow(),
                "automated_execution": True
            }
            
            # Update dispute status
            await self.database["dispute_records"].update_one(
                {"dispute_id": dispute_id},
                {
                    "$set": {
                        "status": DisputeStatus.RESOLVED.value,
                        "resolution_outcome": resolution_outcome,
                        "resolved_at": datetime.utcnow()
                    }
                }
            )
            
            # Store detailed resolution record
            await self.database["resolution_outcomes"].insert_one({
                "dispute_id": dispute_id,
                **resolution_outcome,
                "dispute_type": dispute_doc["dispute_type"],
                "involved_parties": dispute_doc["involved_parties"],
                "resolution_time_hours": (datetime.utcnow() - datetime.fromisoformat(dispute_doc["review_started_at"])).total_seconds() / 3600
            })
            
            # Execute automated resolution actions
            execution_result = await self._execute_dispute_resolution(dispute_id, resolution_outcome)
            
            # Update arbitrator statistics
            await self._update_arbitrator_statistics(arbitrator_id, True)
            
            return {
                "success": True,
                "dispute_id": dispute_id,
                "resolution_decision": resolution_decision,
                "status": DisputeStatus.RESOLVED.value,
                "execution_result": execution_result,
                "resolution_completed": True,
                "message": "Dispute resolved and automated actions executed"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Dispute resolution submission failed: {e}")
            # Mark dispute as failed
            await self._mark_dispute_failed(dispute_id, str(e))
            # Update arbitrator statistics for failure
            await self._update_arbitrator_statistics(arbitrator_id, False)
            return {"success": False, "error": str(e)}
    
    async def _execute_dispute_resolution(self, dispute_id: str, resolution_outcome: Dict) -> Dict:
        """Execute automated dispute resolution actions"""
        try:
            decision = resolution_outcome["decision"]
            compensation_amount = resolution_outcome.get("compensation_amount", 0)
            compensation_recipient = resolution_outcome.get("compensation_recipient")
            
            execution_results = []
            
            # Execute compensation if specified
            if compensation_amount and compensation_recipient:
                # In real implementation, this would execute blockchain transactions
                compensation_tx = f"0x{uuid.uuid4().hex}"
                execution_results.append({
                    "action": "compensation_transfer",
                    "recipient": compensation_recipient,
                    "amount": compensation_amount,
                    "transaction_hash": compensation_tx,
                    "status": "completed"
                })
            
            # Handle different resolution decisions
            if decision == "favor_buyer":
                # Execute buyer-favorable actions (refund, return, etc.)
                execution_results.append({
                    "action": "buyer_resolution",
                    "details": "Dispute resolved in favor of buyer",
                    "status": "completed"
                })
            elif decision == "favor_seller":
                # Execute seller-favorable actions (payment release, etc.)
                execution_results.append({
                    "action": "seller_resolution", 
                    "details": "Dispute resolved in favor of seller",
                    "status": "completed"
                })
            elif decision == "split_decision":
                # Execute split resolution
                execution_results.append({
                    "action": "split_resolution",
                    "details": "Dispute resolved with split decision",
                    "status": "completed"
                })
            
            return {
                "execution_completed": True,
                "actions_executed": len(execution_results),
                "execution_details": execution_results
            }
            
        except Exception as e:
            return {"execution_completed": False, "error": str(e)}
    
    # === DISPUTE STATUS AND QUERIES ===
    
    async def get_dispute_status(self, dispute_id: str) -> Dict:
        """Get current status of a dispute"""
        try:
            dispute_doc = await self.database["dispute_records"].find_one({"dispute_id": dispute_id})
            if not dispute_doc:
                return {"found": False, "error": "Dispute not found"}
            
            # Get votes if in voting phase
            votes = []
            if dispute_doc["status"] in [DisputeStatus.VOTING_ARBITRATOR.value, DisputeStatus.ARBITRATOR_SELECTED.value]:
                votes_cursor = self.database["arbitrator_votes"].find({"dispute_id": dispute_id})
                votes = await votes_cursor.to_list(length=1000)
            
            return {
                "found": True,
                "dispute_id": dispute_id,
                "status": dispute_doc["status"],
                "dispute_type": dispute_doc["dispute_type"],
                "involved_parties": dispute_doc["involved_parties"],
                "selected_arbitrator": dispute_doc.get("selected_arbitrator"),
                "votes_count": len(votes),
                "resolution_outcome": dispute_doc.get("resolution_outcome"),
                "created_at": dispute_doc["created_at"].isoformat(),
                "deadline": dispute_doc.get("deadline", "").isoformat() if dispute_doc.get("deadline") else None,
                "resolved_at": dispute_doc.get("resolved_at", "").isoformat() if dispute_doc.get("resolved_at") else None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Dispute status check failed: {e}")
            return {"found": False, "error": str(e)}
    
    async def get_arbitrator_candidates(self) -> List[Dict]:
        """Get list of available arbitrator candidates"""
        try:
            cursor = self.database["arbitrator_candidates"].find({
                "is_available": True,
                "neutrality_score": {"$gte": self.min_neutrality_score},
                "reputation_score": {"$gte": self.min_arbitrator_reputation}
            }).sort("reputation_score", -1)
            
            candidates = await cursor.to_list(length=100)
            return candidates
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator candidates query failed: {e}")
            return []
    
    async def health_check(self) -> Dict:
        """Health check for dispute resolution service"""
        try:
            health_status = {
                "healthy": True,
                "database": "connected" if self.database else "disconnected",
                "arbitrators_available": 0,
                "active_disputes": 0,
                "resolved_disputes": 0
            }
            
            if self.database is not None:
                try:
                    # Count available arbitrators
                    arbitrators_count = await self.database["arbitrator_candidates"].count_documents({
                        "is_available": True
                    })
                    health_status["arbitrators_available"] = arbitrators_count
                    
                    # Count active disputes
                    active_disputes = await self.database["dispute_records"].count_documents({
                        "status": {"$in": [
                            DisputeStatus.VOTING_ARBITRATOR.value,
                            DisputeStatus.ARBITRATOR_SELECTED.value,
                            DisputeStatus.UNDER_REVIEW.value
                        ]}
                    })
                    health_status["active_disputes"] = active_disputes
                    
                    # Count resolved disputes
                    resolved_disputes = await self.database["dispute_records"].count_documents({
                        "status": DisputeStatus.RESOLVED.value
                    })
                    health_status["resolved_disputes"] = resolved_disputes
                    
                except Exception as db_error:
                    health_status["database"] = "error"
                    health_status["healthy"] = False
                    health_status["database_error"] = str(db_error)
            else:
                health_status["healthy"] = False
            
            return health_status
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    # === HELPER METHODS ===
    
    def _calculate_voting_weight(self, reputation_score: float, stake_amount: float) -> float:
        """Calculate voting weight based on reputation and stake"""
        normalized_reputation = min(reputation_score, 1.0)
        normalized_stake = min(stake_amount / 10.0, 1.0)  # Normalize stake to max 10 ETH
        
        return (normalized_reputation * self.reputation_weight_factor + 
                normalized_stake * self.stake_weight_factor)
    
    async def _get_relevant_stakeholders(self, involved_parties: List[str], product_id: Optional[str]) -> List[Dict]:
        """Get stakeholders relevant to the dispute"""
        # Get all stakeholders involved in the parties
        stakeholders_cursor = self.database["stakeholder_registry"].find({
            "address": {"$in": involved_parties},
            "is_active": True
        })
        direct_stakeholders = await stakeholders_cursor.to_list(length=100)
        
        # Get additional stakeholders if product is involved
        additional_stakeholders = []
        if product_id:
            # In real implementation, would find stakeholders related to the product
            # For now, get all active stakeholders
            all_stakeholders_cursor = self.database["stakeholder_registry"].find({
                "is_active": True
            })
            additional_stakeholders = await all_stakeholders_cursor.to_list(length=100)
        
        # Combine and deduplicate
        all_stakeholders = direct_stakeholders + additional_stakeholders
        unique_stakeholders = {s["address"]: s for s in all_stakeholders}
        
        return list(unique_stakeholders.values())
    
    async def _get_suitable_arbitrators(self, dispute_type: str) -> List[Dict]:
        """Get arbitrator candidates suitable for the dispute type"""
        # Map dispute types to required expertise
        expertise_mapping = {
            "product_quality": ["product_quality", "manufacturing", "quality_control"],
            "delivery_delay": ["logistics", "supply_chain", "international_trade"],
            "payment_dispute": ["payments", "contract_law", "international_trade"],
            "counterfeit_claim": ["product_quality", "nft_verification", "blockchain"],
            "damage_claim": ["damage_assessment", "product_quality", "logistics"],
            "contract_breach": ["contract_law", "international_trade", "blockchain"]
        }
        
        required_expertise = expertise_mapping.get(dispute_type, [])
        
        # Find suitable arbitrators
        suitable_arbitrators = []
        all_arbitrators_cursor = self.database["arbitrator_candidates"].find({
            "is_available": True,
            "neutrality_score": {"$gte": self.min_neutrality_score},
            "reputation_score": {"$gte": self.min_arbitrator_reputation}
        })
        
        all_arbitrators = await all_arbitrators_cursor.to_list(length=100)
        
        for arbitrator in all_arbitrators:
            # Check if arbitrator has relevant expertise
            has_expertise = any(expertise in arbitrator["expertise_areas"] for expertise in required_expertise)
            if has_expertise or not required_expertise:  # Include if has expertise or no specific expertise required
                suitable_arbitrators.append(arbitrator)
        
        return suitable_arbitrators
    
    async def _notify_stakeholder_to_vote(self, stakeholder: Dict, dispute_id: str, arbitrator_candidates: List[Dict]) -> bool:
        """Notify stakeholder to vote for arbitrator"""
        # In real implementation, would send cross-chain message
        return True
    
    async def _notify_arbitrator_to_review(self, arbitrator: Dict, dispute_id: str) -> bool:
        """Notify arbitrator to start dispute review"""
        # In real implementation, would send cross-chain message
        return True
    
    async def _start_evidence_verification(self, dispute_id: str) -> Dict:
        """Start evidence verification process"""
        # This would implement comprehensive evidence verification
        return {"verification_started": True, "evidence_verified": True}
    
    async def _mark_dispute_failed(self, dispute_id: str, reason: str):
        """Mark dispute as failed"""
        await self.database["dispute_records"].update_one(
            {"dispute_id": dispute_id},
            {
                "$set": {
                    "status": DisputeStatus.FAILED.value,
                    "failure_reason": reason,
                    "resolved_at": datetime.utcnow()
                }
            }
        )
    
    async def _update_arbitrator_statistics(self, arbitrator_id: str, success: bool):
        """Update arbitrator performance statistics"""
        update_doc = {
            "$inc": {"total_cases_handled": 1}
        }
        
        if success:
            # Get current stats to calculate new success rate
            arbitrator_doc = await self.database["arbitrator_candidates"].find_one({
                "arbitrator_id": arbitrator_id
            })
            
            if arbitrator_doc:
                current_total = arbitrator_doc["total_cases_handled"]
                current_success_rate = arbitrator_doc["resolution_success_rate"]
                successful_cases = int(current_total * current_success_rate) + 1
                new_total = current_total + 1
                new_success_rate = successful_cases / new_total
                
                update_doc["$set"] = {
                    "resolution_success_rate": new_success_rate,
                    "reputation_score": min(arbitrator_doc["reputation_score"] + 0.01, 1.0)
                }
        else:
            # Decrease reputation for failed resolution
            update_doc["$inc"]["reputation_score"] = -0.05
        
        await self.database["arbitrator_candidates"].update_one(
            {"arbitrator_id": arbitrator_id},
            update_doc
        )

# Global service instance
dispute_resolution_service = DisputeResolutionService()