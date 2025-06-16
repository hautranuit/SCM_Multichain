"""
Supply Chain Consensus (SCC) Algorithm Service
Implementation of Algorithm 3 from Narayanan et al. paper with enhancements

Architecture:
- Primary Nodes (PNs): High-stake validators (manufacturers, verified transporters)
- Secondary Nodes (SNs): Transaction batchers (hub coordinators, distributors) 
- Supermajority threshold: 2/3 of PNs for validation
- Batch processing for efficiency
- Cross-chain integration with LayerZero
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import random
import math

from motor.motor_asyncio import AsyncIOMotorDatabase


class NodeType(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    VALIDATOR = "validator"


class NodeRole(Enum):
    MANUFACTURER = "manufacturer"
    TRANSPORTER = "transporter"
    BUYER = "buyer"
    HUB_COORDINATOR = "hub_coordinator"
    INSPECTOR = "inspector"
    NETWORK_NODE = "network_node"


class BatchStatus(Enum):
    PROPOSED = "proposed"
    VALIDATING = "validating"
    COMMITTED = "committed"
    REJECTED = "rejected"
    FLAGGED = "flagged"


@dataclass
class ConsensusNode:
    """Consensus network node representation"""
    node_id: str
    address: str
    node_type: NodeType
    role: NodeRole
    stake_amount: float
    trust_score: float
    reputation: float
    chain_id: int
    is_active: bool
    last_activity: datetime
    

@dataclass
class Transaction:
    """Individual transaction in the supply chain"""
    tx_id: str
    from_address: str
    to_address: str
    product_id: str
    transaction_type: str  # "manufacture", "transfer", "purchase", "deliver"
    value: float
    metadata: Dict
    timestamp: datetime
    chain_id: int
    

@dataclass
class TransactionBatch:
    """Batch of transactions for consensus validation"""
    batch_id: str
    proposer_id: str  # Secondary Node that created batch
    transactions: List[Transaction]
    nft_references: List[str]  # NFT token IDs involved
    batch_hash: str
    created_at: datetime
    proposed_at: Optional[datetime] = None
    status: BatchStatus = BatchStatus.PROPOSED
    validation_deadline: Optional[datetime] = None
    

@dataclass
class ValidationVote:
    """Individual validation vote from a Primary Node"""
    vote_id: str
    batch_id: str
    validator_id: str
    validator_address: str
    vote: bool  # True = approve, False = reject
    reasoning: str
    nft_validation_results: Dict  # Results of NFT verification
    blockchain_verification: Dict  # On-chain verification results
    timestamp: datetime
    signature: Optional[str] = None
    

@dataclass
class ConsensusResult:
    """Final consensus result for a batch"""
    batch_id: str
    total_validators: int
    approve_votes: int
    reject_votes: int
    supermajority_achieved: bool
    result: str  # "committed", "rejected", "flagged"
    rewards_distributed: bool
    penalties_applied: bool
    reconciliation_needed: bool
    finalized_at: datetime


class SCCConsensusService:
    """
    Supply Chain Consensus (SCC) Algorithm Implementation
    Based on Algorithm 3 from Narayanan et al. paper
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.database: Optional[AsyncIOMotorDatabase] = None
        
        # Consensus parameters (configurable)
        self.supermajority_threshold = 2/3  # 67% for supermajority
        self.min_validators_required = 3
        self.batch_timeout_minutes = 30
        self.max_batch_size = 50
        self.stake_weight_factor = 0.4
        self.trust_weight_factor = 0.6
        
        # Node classification thresholds
        self.primary_node_min_stake = 1.0  # ETH
        self.primary_node_min_trust = 0.7
        self.secondary_node_min_stake = 0.1  # ETH
        
        # Reward and penalty parameters
        self.successful_validation_reward = 0.01  # ETH
        self.malicious_penalty = 0.1  # ETH
        self.false_vote_penalty = 0.05  # ETH
        
    async def initialize(self):
        """Initialize the SCC consensus service"""
        try:
            # Get database from blockchain service
            from .blockchain_service import blockchain_service
            if blockchain_service.database:
                self.database = blockchain_service.database
                # Ensure collections exist
                await self._ensure_collections()
                # Initialize node registry
                await self._initialize_node_registry()
                self.logger.info("✅ SCC Consensus Service initialized with database")
            else:
                self.logger.warning("⚠️ Blockchain service database not initialized - SCC will initialize later")
                # Set a flag to retry initialization later
                self.database = None
            
            self.logger.info("✅ SCC Consensus Service initialized")
            
        except Exception as e:
            self.logger.error(f"❌ SCC initialization failed: {e}")
            raise
    
    async def _ensure_collections(self):
        """Ensure required database collections exist"""
        collections = [
            "scc_nodes",
            "scc_transaction_batches", 
            "scc_validation_votes",
            "scc_consensus_results",
            "scc_rewards_penalties",
            "scc_reconciliation_logs"
        ]
        
        for collection in collections:
            # Create indexes
            if collection == "scc_nodes":
                await self.database[collection].create_index([("address", 1)], unique=True)
                await self.database[collection].create_index([("node_type", 1), ("is_active", 1)])
            elif collection == "scc_transaction_batches":
                await self.database[collection].create_index([("batch_id", 1)], unique=True)
                await self.database[collection].create_index([("status", 1), ("created_at", -1)])
            elif collection == "scc_validation_votes":
                await self.database[collection].create_index([("batch_id", 1), ("validator_id", 1)], unique=True)
            elif collection == "scc_consensus_results":
                await self.database[collection].create_index([("batch_id", 1)], unique=True)
    
    async def _initialize_node_registry(self):
        """Initialize the consensus node registry with default nodes"""
        try:
            # Check if nodes already exist
            existing_count = await self.database["scc_nodes"].count_documents({})
            
            if existing_count > 0:
                self.logger.info(f"✅ Found {existing_count} existing consensus nodes")
                return
            
            # Create default primary nodes (high-stake validators)
            default_primary_nodes = [
                {
                    "node_id": "PN-MANUFACTURER-001",
                    "address": "0x032041b4b356fEE1496805DD4749f181bC736FFA",
                    "node_type": NodeType.PRIMARY.value,
                    "role": NodeRole.MANUFACTURER.value,
                    "stake_amount": 2.0,
                    "trust_score": 0.95,
                    "reputation": 0.95,
                    "chain_id": 84532,  # Base Sepolia
                    "is_active": True,
                    "last_activity": datetime.utcnow()
                },
                {
                    "node_id": "PN-INSPECTOR-001", 
                    "address": "0x742d35Cc8A8E3c8c4e3bB2C4a2f5e1a2C3d4E5F6",
                    "node_type": NodeType.PRIMARY.value,
                    "role": NodeRole.INSPECTOR.value,
                    "stake_amount": 1.5,
                    "trust_score": 0.90,
                    "reputation": 0.90,
                    "chain_id": 80002,  # Polygon Amoy
                    "is_active": True,
                    "last_activity": datetime.utcnow()
                },
                {
                    "node_id": "PN-TRANSPORTER-001",
                    "address": "0x8E8b2A2f3C4d5E6f7G8h9I0j1K2l3M4n5O6p7Q8r",
                    "node_type": NodeType.PRIMARY.value,
                    "role": NodeRole.TRANSPORTER.value,
                    "stake_amount": 1.2,
                    "trust_score": 0.85,
                    "reputation": 0.85,
                    "chain_id": 421614,  # Arbitrum Sepolia
                    "is_active": True,
                    "last_activity": datetime.utcnow()
                },
                {
                    "node_id": "PN-NETWORK-001",
                    "address": "0x123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
                    "node_type": NodeType.PRIMARY.value,
                    "role": NodeRole.NETWORK_NODE.value,
                    "stake_amount": 1.8,
                    "trust_score": 0.92,
                    "reputation": 0.92,
                    "chain_id": 11155420,  # Optimism Sepolia
                    "is_active": True,
                    "last_activity": datetime.utcnow()
                }
            ]
            
            # Create default secondary nodes (transaction batchers)
            default_secondary_nodes = [
                {
                    "node_id": "SN-HUB-001",
                    "address": "0x542E1d35Aa5c8A6b9B2C3d4e5F6a7B8c9D0e1F2a",
                    "node_type": NodeType.SECONDARY.value,
                    "role": NodeRole.HUB_COORDINATOR.value,
                    "stake_amount": 0.5,
                    "trust_score": 0.88,
                    "reputation": 0.88,
                    "chain_id": 80002,  # Polygon Amoy (Hub)
                    "is_active": True,
                    "last_activity": datetime.utcnow()
                },
                {
                    "node_id": "SN-DISTRIBUTOR-001",
                    "address": "0x9F8c2D2e3F4a5B6c7D8e9F0a1B2c3D4e5F6a7B8c",
                    "node_type": NodeType.SECONDARY.value,
                    "role": NodeRole.HUB_COORDINATOR.value,
                    "stake_amount": 0.4,
                    "trust_score": 0.85,
                    "reputation": 0.85,
                    "chain_id": 84532,  # Base Sepolia
                    "is_active": True,
                    "last_activity": datetime.utcnow()
                },
                {
                    "node_id": "SN-COORDINATOR-001",
                    "address": "0x1A2b3C4d5E6f7G8h9I0j1K2l3M4n5O6p7Q8r9S0t",
                    "node_type": NodeType.SECONDARY.value,
                    "role": NodeRole.HUB_COORDINATOR.value,
                    "stake_amount": 0.3,
                    "trust_score": 0.82,
                    "reputation": 0.82,
                    "chain_id": 421614,  # Arbitrum Sepolia
                    "is_active": True,
                    "last_activity": datetime.utcnow()
                }
            ]
            
            # Insert all nodes
            all_nodes = default_primary_nodes + default_secondary_nodes
            await self.database["scc_nodes"].insert_many(all_nodes)
            
            self.logger.info(f"✅ Initialized {len(all_nodes)} consensus nodes ({len(default_primary_nodes)} Primary, {len(default_secondary_nodes)} Secondary)")
            
        except Exception as e:
            self.logger.error(f"❌ Node registry initialization failed: {e}")
            raise
    
    # === ALGORITHM 3: SUPPLY CHAIN CONSENSUS ALGORITHM ===
    
    async def create_transaction_batch(
        self,
        proposer_address: str,
        transactions: List[Dict],
        nft_references: Optional[List[str]] = None
    ) -> Dict:
        """
        Step 1: Secondary Node creates transaction batch
        Implementation of Algorithm 3, lines 4-7: Transaction Batching
        """
        try:
            # Verify proposer is a Secondary Node
            proposer = await self._get_node_by_address(proposer_address)
            if not proposer or proposer["node_type"] != NodeType.SECONDARY.value:
                return {"success": False, "error": "Only Secondary Nodes can propose batches"}
            
            # Convert transaction dictionaries to Transaction objects
            batch_transactions = []
            for tx_data in transactions:
                transaction = Transaction(
                    tx_id=tx_data.get("tx_id", f"TX-{uuid.uuid4().hex[:8]}"),
                    from_address=tx_data["from_address"],
                    to_address=tx_data["to_address"],
                    product_id=tx_data["product_id"],
                    transaction_type=tx_data["transaction_type"],
                    value=tx_data["value"],
                    metadata=tx_data.get("metadata", {}),
                    timestamp=datetime.fromisoformat(tx_data["timestamp"]) if isinstance(tx_data["timestamp"], str) else tx_data["timestamp"],
                    chain_id=tx_data["chain_id"]
                )
                batch_transactions.append(transaction)
            
            # Create batch
            batch_id = f"BATCH-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}"
            batch_hash = self._calculate_batch_hash(batch_transactions)
            
            batch = TransactionBatch(
                batch_id=batch_id,
                proposer_id=proposer["node_id"],
                transactions=batch_transactions,
                nft_references=nft_references or [],
                batch_hash=batch_hash,
                created_at=datetime.utcnow(),
                proposed_at=datetime.utcnow(),
                status=BatchStatus.PROPOSED,
                validation_deadline=datetime.utcnow() + timedelta(minutes=self.batch_timeout_minutes)
            )
            
            # Store batch in database
            batch_doc = {
                **batch.__dict__,
                "transactions": [tx.__dict__ for tx in batch.transactions],
                "status": batch.status.value
            }
            
            await self.database["scc_transaction_batches"].insert_one(batch_doc)
            
            # Initiate batch proposal to Primary Nodes
            proposal_result = await self._propose_batch_to_primary_nodes(batch)
            
            self.logger.info(f"✅ Transaction batch created: {batch_id} with {len(batch_transactions)} transactions")
            
            return {
                "success": True,
                "batch_id": batch_id,
                "batch_hash": batch_hash,
                "transactions_count": len(batch_transactions),
                "validation_deadline": batch.validation_deadline.isoformat(),
                "proposal_result": proposal_result
            }
            
        except Exception as e:
            self.logger.error(f"❌ Batch creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _propose_batch_to_primary_nodes(self, batch: TransactionBatch) -> Dict:
        """
        Step 2: Propose batch to Primary Nodes for validation
        Implementation of Algorithm 3, lines 8-11: Batch Proposal
        """
        try:
            # Get active Primary Nodes
            primary_nodes = await self._get_active_primary_nodes()
            
            if len(primary_nodes) < self.min_validators_required:
                return {"success": False, "error": f"Insufficient Primary Nodes. Need: {self.min_validators_required}, Available: {len(primary_nodes)}"}
            
            # Randomly select subset of Primary Nodes for validation (Algorithm 3, line 13)
            validators_needed = min(len(primary_nodes), max(self.min_validators_required, int(len(primary_nodes) * 0.75)))
            selected_validators = random.sample(primary_nodes, validators_needed)
            
            # Update batch status to validating
            await self.database["scc_transaction_batches"].update_one(
                {"batch_id": batch.batch_id},
                {
                    "$set": {
                        "status": BatchStatus.VALIDATING.value,
                        "selected_validators": [v["node_id"] for v in selected_validators],
                        "validation_started_at": datetime.utcnow()
                    }
                }
            )
            
            # Notify selected validators (in real implementation, this would be cross-chain messages)
            notification_results = []
            for validator in selected_validators:
                notification_result = await self._notify_validator(validator, batch)
                notification_results.append({
                    "validator_id": validator["node_id"],
                    "address": validator["address"],
                    "notification_sent": notification_result
                })
            
            self.logger.info(f"✅ Batch {batch.batch_id} proposed to {len(selected_validators)} Primary Nodes")
            
            return {
                "success": True,
                "validators_selected": len(selected_validators),
                "notification_results": notification_results,
                "validation_deadline": batch.validation_deadline.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Batch proposal failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def submit_validation_vote(
        self,
        batch_id: str,
        validator_address: str,
        vote: bool,
        reasoning: str,
        nft_validation_results: Optional[Dict] = None,
        blockchain_verification: Optional[Dict] = None
    ) -> Dict:
        """
        Step 3: Primary Node submits validation vote
        Implementation of Algorithm 3, lines 12-18: Validation Process
        """
        try:
            # Verify validator is authorized for this batch
            batch_doc = await self.database["scc_transaction_batches"].find_one({"batch_id": batch_id})
            if not batch_doc:
                return {"success": False, "error": "Batch not found"}
            
            validator = await self._get_node_by_address(validator_address)
            if not validator or validator["node_type"] != NodeType.PRIMARY.value:
                return {"success": False, "error": "Only Primary Nodes can vote"}
            
            if validator["node_id"] not in batch_doc.get("selected_validators", []):
                return {"success": False, "error": "Validator not selected for this batch"}
            
            # Check if already voted
            existing_vote = await self.database["scc_validation_votes"].find_one({
                "batch_id": batch_id,
                "validator_id": validator["node_id"]
            })
            
            if existing_vote:
                return {"success": False, "error": "Validator has already voted"}
            
            # Validate batch against records and NFTs (Algorithm 3, line 15)
            validation_results = await self._validate_batch_against_records(batch_doc, nft_validation_results or {})
            
            # Create validation vote
            vote_id = f"VOTE-{uuid.uuid4().hex[:8]}"
            validation_vote = ValidationVote(
                vote_id=vote_id,
                batch_id=batch_id,
                validator_id=validator["node_id"],
                validator_address=validator_address,
                vote=vote,
                reasoning=reasoning,
                nft_validation_results=validation_results,
                blockchain_verification=blockchain_verification or {},
                timestamp=datetime.utcnow()
            )
            
            # Store vote
            await self.database["scc_validation_votes"].insert_one(validation_vote.__dict__)
            
            # Check if all validators have voted or supermajority reached
            consensus_check = await self._check_consensus(batch_id)
            
            self.logger.info(f"✅ Validation vote submitted: {vote_id} for batch {batch_id}")
            
            return {
                "success": True,
                "vote_id": vote_id,
                "batch_id": batch_id,
                "vote": vote,
                "consensus_check": consensus_check
            }
            
        except Exception as e:
            self.logger.error(f"❌ Validation vote failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_consensus(self, batch_id: str) -> Dict:
        """
        Step 4: Check if consensus is reached
        Implementation of Algorithm 3, lines 19-25: Batch Commitment
        """
        try:
            # Get all votes for this batch
            votes_cursor = self.database["scc_validation_votes"].find({"batch_id": batch_id})
            all_votes = await votes_cursor.to_list(length=100)
            
            # Get batch info
            batch_doc = await self.database["scc_transaction_batches"].find_one({"batch_id": batch_id})
            total_validators = len(batch_doc.get("selected_validators", []))
            
            # Count votes
            approve_votes = sum(1 for vote in all_votes if vote["vote"])
            reject_votes = sum(1 for vote in all_votes if not vote["vote"])
            votes_received = len(all_votes)
            
            # Check if supermajority reached (Algorithm 3, line 20)
            supermajority_threshold = math.ceil(total_validators * self.supermajority_threshold)
            supermajority_achieved = approve_votes >= supermajority_threshold
            
            result_status = "pending"
            
            # If supermajority of PNs validate the batch (Algorithm 3, line 20)
            if supermajority_achieved:
                result_status = "committed"
                await self._commit_batch(batch_id, approve_votes, reject_votes, total_validators)
            
            # Check if all validators voted or deadline passed
            elif votes_received == total_validators or datetime.utcnow() > batch_doc["validation_deadline"]:
                if approve_votes > reject_votes:
                    result_status = "committed"
                    await self._commit_batch(batch_id, approve_votes, reject_votes, total_validators)
                else:
                    result_status = "rejected"
                    await self._reject_batch(batch_id, approve_votes, reject_votes, total_validators)
            
            return {
                "consensus_reached": result_status != "pending",
                "result": result_status,
                "approve_votes": approve_votes,
                "reject_votes": reject_votes,
                "total_validators": total_validators,
                "supermajority_threshold": supermajority_threshold,
                "supermajority_achieved": supermajority_achieved
            }
            
        except Exception as e:
            self.logger.error(f"❌ Consensus check failed: {e}")
            return {"consensus_reached": False, "error": str(e)}
    
    async def _commit_batch(self, batch_id: str, approve_votes: int, reject_votes: int, total_validators: int):
        """
        Commit batch to blockchain (Algorithm 3, line 21)
        """
        try:
            # Update batch status
            await self.database["scc_transaction_batches"].update_one(
                {"batch_id": batch_id},
                {
                    "$set": {
                        "status": BatchStatus.COMMITTED.value,
                        "finalized_at": datetime.utcnow(),
                        "consensus_result": {
                            "approve_votes": approve_votes,
                            "reject_votes": reject_votes,
                            "total_validators": total_validators,
                            "result": "committed"
                        }
                    }
                }
            )
            
            # Create consensus result record
            consensus_result = ConsensusResult(
                batch_id=batch_id,
                total_validators=total_validators,
                approve_votes=approve_votes,
                reject_votes=reject_votes,
                supermajority_achieved=True,
                result="committed",
                rewards_distributed=False,
                penalties_applied=False,
                reconciliation_needed=False,
                finalized_at=datetime.utcnow()
            )
            
            await self.database["scc_consensus_results"].insert_one(consensus_result.__dict__)
            
            # Distribute rewards (Algorithm 3, lines 26-30)
            await self._distribute_rewards_and_penalties(batch_id, "committed")
            
            self.logger.info(f"✅ Batch {batch_id} committed to blockchain")
            
        except Exception as e:
            self.logger.error(f"❌ Batch commit failed: {e}")
            raise
    
    async def _reject_batch(self, batch_id: str, approve_votes: int, reject_votes: int, total_validators: int):
        """
        Reject batch or flag for review (Algorithm 3, lines 22-24)
        """
        try:
            # Update batch status
            await self.database["scc_transaction_batches"].update_one(
                {"batch_id": batch_id},
                {
                    "$set": {
                        "status": BatchStatus.REJECTED.value,
                        "finalized_at": datetime.utcnow(),
                        "consensus_result": {
                            "approve_votes": approve_votes,
                            "reject_votes": reject_votes,
                            "total_validators": total_validators,
                            "result": "rejected"
                        }
                    }
                }
            )
            
            # Create consensus result record
            consensus_result = ConsensusResult(
                batch_id=batch_id,
                total_validators=total_validators,
                approve_votes=approve_votes,
                reject_votes=reject_votes,
                supermajority_achieved=False,
                result="rejected",
                rewards_distributed=False,
                penalties_applied=False,
                reconciliation_needed=True,  # Rejected batches need reconciliation
                finalized_at=datetime.utcnow()
            )
            
            await self.database["scc_consensus_results"].insert_one(consensus_result.__dict__)
            
            # Apply penalties for malicious nodes (Algorithm 3, lines 31-33)
            await self._distribute_rewards_and_penalties(batch_id, "rejected")
            
            self.logger.info(f"✅ Batch {batch_id} rejected")
            
        except Exception as e:
            self.logger.error(f"❌ Batch rejection failed: {e}")
            raise
    
    async def _distribute_rewards_and_penalties(self, batch_id: str, result: str):
        """
        Distribute rewards and penalties (Algorithm 3, lines 26-33)
        """
        try:
            # Get all votes for this batch
            votes_cursor = self.database["scc_validation_votes"].find({"batch_id": batch_id})
            all_votes = await votes_cursor.to_list(length=100)
            
            rewards_penalties = []
            
            for vote in all_votes:
                validator_id = vote["validator_id"]
                validator_address = vote["validator_address"]
                
                if result == "committed":
                    # Reward all validators for successful batch (Algorithm 3, line 28-29)
                    reward_amount = self.successful_validation_reward
                    rewards_penalties.append({
                        "batch_id": batch_id,
                        "node_id": validator_id,
                        "address": validator_address,
                        "type": "reward",
                        "amount": reward_amount,
                        "reason": "successful_validation",
                        "timestamp": datetime.utcnow()
                    })
                    
                    # Update node reputation positively
                    await self.database["scc_nodes"].update_one(
                        {"node_id": validator_id},
                        {
                            "$inc": {"reputation": 0.01},
                            "$set": {"last_activity": datetime.utcnow()}
                        }
                    )
                    
                elif result == "rejected":
                    # Penalize nodes that voted incorrectly (Algorithm 3, line 31-32)
                    if vote["vote"]:  # Voted approve but batch was rejected
                        penalty_amount = self.false_vote_penalty
                        rewards_penalties.append({
                            "batch_id": batch_id,
                            "node_id": validator_id,
                            "address": validator_address,
                            "type": "penalty",
                            "amount": penalty_amount,
                            "reason": "false_positive_vote",
                            "timestamp": datetime.utcnow()
                        })
                        
                        # Update node reputation negatively
                        await self.database["scc_nodes"].update_one(
                            {"node_id": validator_id},
                            {
                                "$inc": {"reputation": -0.05, "trust_score": -0.02},
                                "$set": {"last_activity": datetime.utcnow()}
                            }
                        )
                    else:
                        # Voted reject correctly, small reward
                        reward_amount = self.successful_validation_reward * 0.5
                        rewards_penalties.append({
                            "batch_id": batch_id,
                            "node_id": validator_id,
                            "address": validator_address,
                            "type": "reward",
                            "amount": reward_amount,
                            "reason": "correct_rejection",
                            "timestamp": datetime.utcnow()
                        })
            
            # Store rewards and penalties
            if rewards_penalties:
                await self.database["scc_rewards_penalties"].insert_many(rewards_penalties)
            
            # Update consensus result
            await self.database["scc_consensus_results"].update_one(
                {"batch_id": batch_id},
                {
                    "$set": {
                        "rewards_distributed": True,
                        "penalties_applied": True
                    }
                }
            )
            
            self.logger.info(f"✅ Rewards and penalties distributed for batch {batch_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Rewards/penalties distribution failed: {e}")
            raise
    
    async def perform_periodic_reconciliation(self) -> Dict:
        """
        Periodic reconciliation process (Algorithm 3, lines 34-39)
        """
        try:
            reconciliation_id = f"RECON-{int(datetime.utcnow().timestamp())}"
            
            # Get all nodes for cross-reference
            all_nodes_cursor = self.database["scc_nodes"].find({"is_active": True})
            all_nodes = await all_nodes_cursor.to_list(length=100)
            
            # Get recent batches that need reconciliation
            recent_batches_cursor = self.database["scc_consensus_results"].find({
                "reconciliation_needed": True,
                "finalized_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
            })
            recent_batches = await recent_batches_cursor.to_list(length=100)
            
            discrepancies_found = []
            
            for batch_result in recent_batches:
                batch_id = batch_result["batch_id"]
                
                # Cross-reference records (Algorithm 3, line 36)
                discrepancy = await self._detect_batch_discrepancies(batch_id, all_nodes)
                
                if discrepancy:
                    discrepancies_found.append(discrepancy)
                    
                    # Flag and resolve via majority consensus (Algorithm 3, line 37-38)
                    resolution_result = await self._resolve_discrepancy_via_consensus(batch_id, discrepancy)
                    discrepancy["resolution"] = resolution_result
            
            # Log reconciliation results
            reconciliation_log = {
                "reconciliation_id": reconciliation_id,
                "timestamp": datetime.utcnow(),
                "nodes_checked": len(all_nodes),
                "batches_reconciled": len(recent_batches),
                "discrepancies_found": len(discrepancies_found),
                "discrepancies": discrepancies_found
            }
            
            await self.database["scc_reconciliation_logs"].insert_one(reconciliation_log)
            
            self.logger.info(f"✅ Periodic reconciliation completed: {reconciliation_id}")
            
            return {
                "success": True,
                "reconciliation_id": reconciliation_id,
                "nodes_checked": len(all_nodes),
                "batches_reconciled": len(recent_batches),
                "discrepancies_found": len(discrepancies_found),
                "discrepancies": discrepancies_found
            }
            
        except Exception as e:
            self.logger.error(f"❌ Periodic reconciliation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # === HELPER METHODS ===
    
    async def _get_node_by_address(self, address: str) -> Optional[Dict]:
        """Get consensus node by address"""
        return await self.database["scc_nodes"].find_one({"address": address})
    
    async def _get_active_primary_nodes(self) -> List[Dict]:
        """Get all active Primary Nodes"""
        cursor = self.database["scc_nodes"].find({
            "node_type": NodeType.PRIMARY.value,
            "is_active": True
        })
        return await cursor.to_list(length=100)
    
    def _calculate_batch_hash(self, transactions: List[Transaction]) -> str:
        """Calculate hash for transaction batch"""
        import hashlib
        
        # Create deterministic string from transactions
        tx_strings = []
        for tx in sorted(transactions, key=lambda x: x.tx_id or ""):
            tx_string = f"{tx.tx_id}:{tx.from_address}:{tx.to_address}:{tx.product_id}:{tx.value}"
            tx_strings.append(tx_string)
        
        batch_string = "|".join(tx_strings)
        return hashlib.sha256(batch_string.encode()).hexdigest()
    
    async def _validate_batch_against_records(self, batch_doc: Dict, nft_validation_results: Dict) -> Dict:
        """Validate batch against blockchain records and NFTs"""
        # This would implement comprehensive validation logic
        # For now, return mock validation results
        return {
            "blockchain_verified": True,
            "nft_verified": True,
            "supply_chain_verified": True,
            "validation_score": 0.95,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _notify_validator(self, validator: Dict, batch: TransactionBatch) -> bool:
        """Notify validator about new batch to validate"""
        # In real implementation, this would send cross-chain message
        # For now, just return success
        return True
    
    async def _detect_batch_discrepancies(self, batch_id: str, nodes: List[Dict]) -> Optional[Dict]:
        """Detect discrepancies in batch records across nodes"""
        # This would implement cross-node record comparison
        # For now, return None (no discrepancies)
        return None
    
    async def _resolve_discrepancy_via_consensus(self, batch_id: str, discrepancy: Dict) -> Dict:
        """Resolve discrepancy via majority consensus"""
        # This would implement discrepancy resolution logic
        return {"resolved": True, "method": "majority_consensus"}

# Global service instance
scc_consensus_service = SCCConsensusService()