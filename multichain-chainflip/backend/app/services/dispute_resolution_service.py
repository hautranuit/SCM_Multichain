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
            if blockchain_service.database is not None:
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
                    "expertise_areas": ["product_quality", "manufacturing", "damage_assessment"],
                    "reputation_score": 0.90,
                    "resolution_success_rate": 0.87,
                    "total_cases_handled": 174,
                    "neutrality_score": 0.82,
                    "is_available": True,
                    "chain_id": 421614  # Arbitrum Sepolia
                }
            ]
            
            await self.database["arbitrator_candidates"].insert_many(default_arbitrators)
            
            self.logger.info(f"✅ Initialized {len(default_arbitrators)} arbitrator candidates")
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator registry initialization failed: {e}")
            raise
    
    async def _initialize_stakeholder_registry(self):
        """Initialize stakeholder registry"""
        try:
            # Check if stakeholders already exist
            existing_count = await self.database["stakeholder_registry"].count_documents({})
            
            if existing_count > 0:
                self.logger.info(f"✅ Found {existing_count} existing stakeholders")
                return
            
            # Create default stakeholders
            default_stakeholders = [
                {
                    "stakeholder_id": "STK-MANUFACTURER-001",
                    "address": "0x032041b4b356fEE1496805DD4749f181bC736FFA",
                    "role": StakeholderRole.MANUFACTURER.value,
                    "reputation_score": 0.95,
                    "stake_amount": 2.0,
                    "voting_weight": 0.0,  # Will be calculated
                    "is_active": True
                },
                {
                    "stakeholder_id": "STK-BUYER-001", 
                    "address": "0x742d35Cc8A8E3c8c4e3bB2C4a2f5e1a2C3d4E5F6",
                    "role": StakeholderRole.BUYER.value,
                    "reputation_score": 0.88,
                    "stake_amount": 1.5,
                    "voting_weight": 0.0,
                    "is_active": True
                },
                {
                    "stakeholder_id": "STK-TRANSPORTER-001",
                    "address": "0x8E8b2A2f3C4d5E6f7G8h9I0j1K2l3M4n5O6p7Q8r",
                    "role": StakeholderRole.TRANSPORTER.value,
                    "reputation_score": 0.85,
                    "stake_amount": 1.2,
                    "voting_weight": 0.0,
                    "is_active": True
                },
                {
                    "stakeholder_id": "STK-INSPECTOR-001",
                    "address": "0x123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
                    "role": StakeholderRole.INSPECTOR.value,
                    "reputation_score": 0.92,
                    "stake_amount": 1.8,
                    "voting_weight": 0.0,
                    "is_active": True
                }
            ]
            
            # Calculate voting weights
            for stakeholder in default_stakeholders:
                stakeholder["voting_weight"] = self._calculate_voting_weight(
                    stakeholder["reputation_score"],
                    stakeholder["stake_amount"]
                )
            
            await self.database["stakeholder_registry"].insert_many(default_stakeholders)
            
            self.logger.info(f"✅ Initialized {len(default_stakeholders)} stakeholders")
            
        except Exception as e:
            self.logger.error(f"❌ Stakeholder registry initialization failed: {e}")
            raise
    
    # === ALGORITHM 2: DISPUTE RESOLUTION AND VOTING MECHANISM ===
    
    async def initiate_dispute(
        self,
        dispute_type: str,
        involved_parties: List[str],
        product_id: Optional[str],
        transaction_id: Optional[str],
        description: str,
        evidence: List[Dict],
        initiated_by: str
    ) -> Dict:
        """
        Step 1: Initiate dispute resolution process
        Implementation of Algorithm 2, line 1: if dispute arises then
        """
        try:
            # Create dispute ID
            dispute_id = f"DISPUTE-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}"
            
            # Get stakeholder list for voting
            stakeholder_list = await self._get_relevant_stakeholders(involved_parties, product_id)
            
            # Get suitable arbitrator candidates
            arbitrator_candidates = await self._get_suitable_arbitrators(dispute_type)
            
            if len(arbitrator_candidates) == 0:
                return {"success": False, "error": "No suitable arbitrator candidates available"}
            
            # Process evidence
            processed_evidence = []
            for evidence_data in evidence:
                evidence_obj = DisputeEvidence(
                    evidence_id=f"EVD-{uuid.uuid4().hex[:8]}",
                    evidence_type=evidence_data["evidence_type"],
                    content=evidence_data["content"],
                    ipfs_hash=evidence_data.get("ipfs_hash"),
                    blockchain_tx_hash=evidence_data.get("blockchain_tx_hash"),
                    nft_token_id=evidence_data.get("nft_token_id"),
                    submitted_by=initiated_by,
                    timestamp=datetime.utcnow(),
                    verified=False  # Will be verified later
                )
                processed_evidence.append(evidence_obj)
            
            # Create dispute record
            dispute = DisputeRecord(
                dispute_id=dispute_id,
                dispute_type=DisputeType(dispute_type),
                involved_parties=involved_parties,
                stakeholder_list=[s["stakeholder_id"] for s in stakeholder_list],
                product_id=product_id,
                transaction_id=transaction_id,
                description=description,
                evidence=processed_evidence,
                arbitrator_candidates=[a["arbitrator_id"] for a in arbitrator_candidates],
                selected_arbitrator=None,
                status=DisputeStatus.INITIATED,
                resolution_outcome=None,
                created_at=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(hours=self.voting_deadline_hours),
                resolved_at=None
            )
            
            # Store dispute record
            dispute_doc = {
                **dispute.__dict__,
                "dispute_type": dispute.dispute_type.value,
                "status": dispute.status.value,
                "evidence": [ev.__dict__ for ev in dispute.evidence]
            }
            
            await self.database["dispute_records"].insert_one(dispute_doc)
            
            # Store evidence separately for easier access
            for evidence in processed_evidence:
                await self.database["dispute_evidence"].insert_one({
                    **evidence.__dict__,
                    "dispute_id": dispute_id
                })
            
            # Initiate voting mechanism (Algorithm 2, line 2)
            voting_result = await self._initiate_arbitrator_voting(dispute_id, stakeholder_list, arbitrator_candidates)
            
            self.logger.info(f"✅ Dispute initiated: {dispute_id} with {len(arbitrator_candidates)} arbitrator candidates")
            
            return {
                "success": True,
                "dispute_id": dispute_id,
                "stakeholders_count": len(stakeholder_list),
                "arbitrator_candidates_count": len(arbitrator_candidates),
                "voting_deadline": dispute.deadline.isoformat(),
                "voting_result": voting_result
            }
            
        except Exception as e:
            self.logger.error(f"❌ Dispute initiation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _initiate_arbitrator_voting(
        self,
        dispute_id: str,
        stakeholders: List[Dict],
        arbitrator_candidates: List[Dict]
    ) -> Dict:
        """
        Step 2: Initiate voting mechanism
        Implementation of Algorithm 2, line 2: Initiate voting mechanism
        """
        try:
            # Update dispute status to voting
            await self.database["dispute_records"].update_one(
                {"dispute_id": dispute_id},
                {
                    "$set": {
                        "status": DisputeStatus.VOTING_ARBITRATOR.value,
                        "voting_started_at": datetime.utcnow()
                    }
                }
            )
            
            # Notify stakeholders to vote (in real implementation, cross-chain messages)
            notifications_sent = []
            for stakeholder in stakeholders:
                notification_result = await self._notify_stakeholder_to_vote(stakeholder, dispute_id, arbitrator_candidates)
                notifications_sent.append({
                    "stakeholder_id": stakeholder["stakeholder_id"],
                    "address": stakeholder["address"],
                    "notification_sent": notification_result
                })
            
            self.logger.info(f"✅ Arbitrator voting initiated for dispute {dispute_id}")
            
            return {
                "voting_initiated": True,
                "stakeholders_notified": len(stakeholders),
                "arbitrator_options": len(arbitrator_candidates),
                "notifications": notifications_sent
            }
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator voting initiation failed: {e}")
            return {"voting_initiated": False, "error": str(e)}
    
    async def submit_arbitrator_vote(
        self,
        dispute_id: str,
        stakeholder_address: str,
        arbitrator_candidate_id: str,
        reasoning: Optional[str] = None
    ) -> Dict:
        """
        Step 3: Stakeholder submits vote for arbitrator
        Implementation of Algorithm 2, lines 3-5: for each stakeholder in list of stakeholders do
        """
        try:
            # Verify dispute exists and is in voting phase
            dispute_doc = await self.database["dispute_records"].find_one({"dispute_id": dispute_id})
            if not dispute_doc:
                return {"success": False, "error": "Dispute not found"}
            
            if dispute_doc["status"] != DisputeStatus.VOTING_ARBITRATOR.value:
                return {"success": False, "error": "Dispute not in voting phase"}
            
            # Verify stakeholder is authorized
            stakeholder = await self.database["stakeholder_registry"].find_one({"address": stakeholder_address})
            if not stakeholder:
                return {"success": False, "error": "Stakeholder not found"}
            
            if stakeholder["stakeholder_id"] not in dispute_doc["stakeholder_list"]:
                return {"success": False, "error": "Stakeholder not authorized for this dispute"}
            
            # Verify arbitrator candidate exists
            arbitrator = await self.database["arbitrator_candidates"].find_one({"arbitrator_id": arbitrator_candidate_id})
            if not arbitrator:
                return {"success": False, "error": "Arbitrator candidate not found"}
            
            if arbitrator_candidate_id not in dispute_doc["arbitrator_candidates"]:
                return {"success": False, "error": "Arbitrator not a candidate for this dispute"}
            
            # Check if already voted
            existing_vote = await self.database["arbitrator_votes"].find_one({
                "dispute_id": dispute_id,
                "stakeholder_id": stakeholder["stakeholder_id"]
            })
            
            if existing_vote:
                return {"success": False, "error": "Stakeholder has already voted"}
            
            # Create vote record
            vote = ArbitratorVote(
                vote_id=f"VOTE-{uuid.uuid4().hex[:8]}",
                dispute_id=dispute_id,
                stakeholder_id=stakeholder["stakeholder_id"],
                stakeholder_address=stakeholder_address,
                arbitrator_candidate_id=arbitrator_candidate_id,
                vote_weight=stakeholder["voting_weight"],
                reasoning=reasoning,
                timestamp=datetime.utcnow()
            )
            
            # Store vote
            await self.database["arbitrator_votes"].insert_one(vote.__dict__)
            
            # Check if voting is complete
            voting_result = await self._check_arbitrator_voting_result(dispute_id)
            
            self.logger.info(f"✅ Arbitrator vote submitted: {vote.vote_id} for dispute {dispute_id}")
            
            return {
                "success": True,
                "vote_id": vote.vote_id,
                "dispute_id": dispute_id,
                "arbitrator_voted_for": arbitrator_candidate_id,
                "voting_result": voting_result
            }
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator vote submission failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_arbitrator_voting_result(self, dispute_id: str) -> Dict:
        """
        Step 4: Check voting results and select arbitrator
        Implementation of Algorithm 2, line 6: Arbitrator ← candidate with majority votes
        """
        try:
            # Get all votes for this dispute
            votes_cursor = self.database["arbitrator_votes"].find({"dispute_id": dispute_id})
            all_votes = await votes_cursor.to_list(length=100)
            
            # Get dispute info
            dispute_doc = await self.database["dispute_records"].find_one({"dispute_id": dispute_id})
            total_stakeholders = len(dispute_doc["stakeholder_list"])
            
            # Calculate weighted votes for each arbitrator
            arbitrator_votes = {}
            total_vote_weight = 0
            
            for vote in all_votes:
                arbitrator_id = vote["arbitrator_candidate_id"]
                vote_weight = vote["vote_weight"]
                
                if arbitrator_id not in arbitrator_votes:
                    arbitrator_votes[arbitrator_id] = 0
                
                arbitrator_votes[arbitrator_id] += vote_weight
                total_vote_weight += vote_weight
            
            # Check if all stakeholders voted or if we have a clear majority
            votes_received = len(all_votes)
            voting_complete = votes_received == total_stakeholders
            
            # Find candidate with highest weighted votes
            selected_arbitrator = None
            max_votes = 0
            
            for arbitrator_id, weighted_votes in arbitrator_votes.items():
                if weighted_votes > max_votes:
                    max_votes = weighted_votes
                    selected_arbitrator = arbitrator_id
            
            # Check if arbitrator has majority and meets requirements
            has_majority = max_votes >= (total_vote_weight * self.arbitrator_selection_threshold)
            
            if selected_arbitrator and (voting_complete or has_majority):
                # Verify arbitrator neutrality and trust (Algorithm 2, line 7)
                arbitrator_doc = await self.database["arbitrator_candidates"].find_one({
                    "arbitrator_id": selected_arbitrator
                })
                
                is_neutral_and_trusted = (
                    arbitrator_doc["neutrality_score"] >= self.min_neutrality_score and
                    arbitrator_doc["reputation_score"] >= self.min_arbitrator_reputation
                )
                
                if is_neutral_and_trusted:
                    # Select arbitrator and move to review phase
                    result = await self._select_arbitrator_and_start_review(dispute_id, selected_arbitrator)
                    
                    return {
                        "voting_complete": True,
                        "arbitrator_selected": selected_arbitrator,
                        "selection_result": result,
                        "weighted_votes": max_votes,
                        "total_weight": total_vote_weight
                    }
                else:
                    # Return "Dispute Resolution Failed" (Algorithm 2, line 14)
                    await self._mark_dispute_failed(dispute_id, "Selected arbitrator not neutral and trusted")
                    
                    return {
                        "voting_complete": True,
                        "arbitrator_selected": None,
                        "result": "Dispute Resolution Failed",
                        "reason": "Selected arbitrator not neutral and trusted"
                    }
            
            return {
                "voting_complete": False,
                "votes_received": votes_received,
                "total_stakeholders": total_stakeholders,
                "current_leader": selected_arbitrator,
                "leader_votes": max_votes,
                "total_weight": total_vote_weight
            }
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator voting result check failed: {e}")
            return {"voting_complete": False, "error": str(e)}
    
    async def _select_arbitrator_and_start_review(self, dispute_id: str, arbitrator_id: str) -> Dict:
        """
        Step 5: Select arbitrator and start dispute review
        Implementation of Algorithm 2, lines 8-12: Arbitrator review process
        """
        try:
            # Update dispute with selected arbitrator
            await self.database["dispute_records"].update_one(
                {"dispute_id": dispute_id},
                {
                    "$set": {
                        "selected_arbitrator": arbitrator_id,
                        "status": DisputeStatus.ARBITRATOR_SELECTED.value,
                        "arbitrator_selected_at": datetime.utcnow(),
                        "review_deadline": datetime.utcnow() + timedelta(days=self.resolution_deadline_days)
                    }
                }
            )
            
            # Get arbitrator details
            arbitrator_doc = await self.database["arbitrator_candidates"].find_one({
                "arbitrator_id": arbitrator_id
            })
            
            # Notify arbitrator to start review (Algorithm 2, line 8)
            notification_result = await self._notify_arbitrator_to_review(arbitrator_doc, dispute_id)
            
            # Start evidence verification process
            evidence_verification = await self._start_evidence_verification(dispute_id)
            
            self.logger.info(f"✅ Arbitrator {arbitrator_id} selected for dispute {dispute_id}")
            
            return {
                "arbitrator_selected": True,
                "arbitrator_id": arbitrator_id,
                "arbitrator_name": arbitrator_doc["name"],
                "review_deadline": (datetime.utcnow() + timedelta(days=self.resolution_deadline_days)).isoformat(),
                "notification_result": notification_result,
                "evidence_verification": evidence_verification
            }
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator selection failed: {e}")
            return {"arbitrator_selected": False, "error": str(e)}
    
    async def submit_arbitrator_decision(
        self,
        dispute_id: str,
        arbitrator_address: str,
        decision: Dict,
        reasoning: str
    ) -> Dict:
        """
        Step 6: Arbitrator submits decision
        Implementation of Algorithm 2, lines 10-12: Arbitrator decision process
        """
        try:
            # Verify dispute exists and arbitrator is authorized
            dispute_doc = await self.database["dispute_records"].find_one({"dispute_id": dispute_id})
            if not dispute_doc:
                return {"success": False, "error": "Dispute not found"}
            
            # Verify arbitrator
            arbitrator_doc = await self.database["arbitrator_candidates"].find_one({
                "arbitrator_id": dispute_doc["selected_arbitrator"],
                "address": arbitrator_address
            })
            
            if not arbitrator_doc:
                return {"success": False, "error": "Unauthorized arbitrator"}
            
            if dispute_doc["status"] != DisputeStatus.ARBITRATOR_SELECTED.value:
                return {"success": False, "error": "Dispute not in review phase"}
            
            # Process arbitrator decision
            resolution_outcome = {
                "decision": decision,
                "reasoning": reasoning,
                "arbitrator_id": dispute_doc["selected_arbitrator"],
                "arbitrator_name": arbitrator_doc["name"],
                "blockchain_evidence_reviewed": True,  # Simulated
                "nft_evidence_reviewed": True,  # Simulated
                "decision_timestamp": datetime.utcnow(),
                "execution_required": decision.get("execution_required", False)
            }
            
            # Update dispute record
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
            
            # Store resolution outcome separately
            await self.database["resolution_outcomes"].insert_one({
                "dispute_id": dispute_id,
                **resolution_outcome
            })
            
            # Execute decision if required (Algorithm 2, line 11)
            execution_result = None
            if decision.get("execution_required", False):
                execution_result = await self._execute_arbitrator_decision(dispute_id, resolution_outcome)
            
            # Update arbitrator statistics
            await self._update_arbitrator_statistics(dispute_doc["selected_arbitrator"], True)
            
            self.logger.info(f"✅ Arbitrator decision submitted for dispute {dispute_id}: {decision}")
            
            return {
                "success": True,
                "dispute_id": dispute_id,
                "decision": decision,
                "resolution_outcome": resolution_outcome,
                "execution_result": execution_result,
                "status": "Dispute Resolved"  # Algorithm 2, line 12
            }
            
        except Exception as e:
            self.logger.error(f"❌ Arbitrator decision submission failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_arbitrator_decision(self, dispute_id: str, resolution_outcome: Dict) -> Dict:
        """
        Execute arbitrator decision (Algorithm 2, line 11)
        """
        try:
            decision = resolution_outcome["decision"]
            
            # Examples of decision execution
            execution_actions = []
            
            if "refund_amount" in decision:
                # Process refund
                execution_actions.append({
                    "action": "refund",
                    "amount": decision["refund_amount"],
                    "recipient": decision.get("refund_recipient"),
                    "status": "simulated"  # In real implementation, would trigger actual transaction
                })
            
            if "penalty_amount" in decision:
                # Apply penalty
                execution_actions.append({
                    "action": "penalty",
                    "amount": decision["penalty_amount"],
                    "target": decision.get("penalty_target"),
                    "status": "simulated"
                })
            
            if "reputation_adjustment" in decision:
                # Adjust reputation scores
                for address, adjustment in decision["reputation_adjustment"].items():
                    await self.database["stakeholder_registry"].update_one(
                        {"address": address},
                        {"$inc": {"reputation_score": adjustment}}
                    )
                    execution_actions.append({
                        "action": "reputation_adjustment",
                        "address": address,
                        "adjustment": adjustment,
                        "status": "executed"
                    })
            
            return {
                "execution_completed": True,
                "actions_performed": execution_actions,
                "execution_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Decision execution failed: {e}")
            return {"execution_completed": False, "error": str(e)}
    
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