"""
Enhanced Consensus and Dispute Resolution API Routes
Implementation of SCC Algorithm 3 and Dispute Resolution Algorithm 2 from Narayanan et al. paper
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from ...services.scc_consensus_service import scc_consensus_service
from ...services.dispute_resolution_service import dispute_resolution_service

router = APIRouter()

# === PYDANTIC MODELS ===

# SCC Consensus Models
class TransactionData(BaseModel):
    tx_id: Optional[str] = Field(None, description="Transaction ID (auto-generated if not provided)")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Recipient address")
    product_id: str = Field(..., description="Product ID")
    transaction_type: str = Field(..., description="Type: manufacture, transfer, purchase, deliver")
    value: float = Field(..., description="Transaction value in ETH")
    metadata: Dict = Field(default_factory=dict, description="Additional transaction metadata")
    timestamp: str = Field(..., description="Transaction timestamp (ISO format)")
    chain_id: int = Field(..., description="Blockchain chain ID")

class BatchCreationRequest(BaseModel):
    proposer_address: str = Field(..., description="Secondary Node address proposing the batch")
    transactions: List[TransactionData] = Field(..., description="List of transactions to batch")
    nft_references: Optional[List[str]] = Field(None, description="Related NFT token IDs")

class ValidationVoteRequest(BaseModel):
    batch_id: str = Field(..., description="Transaction batch ID")
    validator_address: str = Field(..., description="Primary Node validator address")
    vote: bool = Field(..., description="True = approve, False = reject")
    reasoning: str = Field(..., description="Reasoning for the vote")
    nft_validation_results: Optional[Dict] = Field(None, description="NFT validation results")
    blockchain_verification: Optional[Dict] = Field(None, description="Blockchain verification results")

# Dispute Resolution Models
class DisputeEvidence(BaseModel):
    evidence_type: str = Field(..., description="Type: blockchain, nft, document, photo, video")
    content: Dict = Field(..., description="Evidence content/metadata")
    ipfs_hash: Optional[str] = Field(None, description="IPFS hash if stored on IPFS")
    blockchain_tx_hash: Optional[str] = Field(None, description="Blockchain transaction hash")
    nft_token_id: Optional[str] = Field(None, description="NFT token ID if relevant")

class DisputeInitiationRequest(BaseModel):
    dispute_type: str = Field(..., description="Type: product_quality, delivery_delay, payment_dispute, counterfeit_claim, damage_claim, contract_breach")
    involved_parties: List[str] = Field(..., description="Addresses of parties involved in dispute")
    product_id: Optional[str] = Field(None, description="Product ID if dispute is product-related")
    transaction_id: Optional[str] = Field(None, description="Transaction ID if dispute is transaction-related")
    description: str = Field(..., description="Detailed description of the dispute")
    evidence: List[DisputeEvidence] = Field(..., description="Evidence supporting the dispute")
    initiated_by: str = Field(..., description="Address of party initiating the dispute")

class ArbitratorVoteRequest(BaseModel):
    dispute_id: str = Field(..., description="Dispute ID")
    stakeholder_address: str = Field(..., description="Stakeholder address submitting vote")
    arbitrator_candidate_id: str = Field(..., description="ID of arbitrator candidate being voted for")
    reasoning: Optional[str] = Field(None, description="Reasoning for arbitrator selection")

class ArbitratorDecisionRequest(BaseModel):
    dispute_id: str = Field(..., description="Dispute ID")
    arbitrator_address: str = Field(..., description="Arbitrator address submitting decision")
    decision: Dict = Field(..., description="Arbitrator decision details")
    reasoning: str = Field(..., description="Detailed reasoning for the decision")

# === DEPENDENCY INJECTION ===

async def get_scc_service():
    """Get initialized SCC consensus service"""
    if scc_consensus_service.database is None:
        await scc_consensus_service.initialize()
    return scc_consensus_service

async def get_dispute_service():
    """Get initialized dispute resolution service"""
    if dispute_resolution_service.database is None:
        await dispute_resolution_service.initialize()
    return dispute_resolution_service

# === SCC CONSENSUS ALGORITHM ENDPOINTS ===

@router.post("/consensus/batch/create", response_model=Dict, tags=["SCC Consensus"])
async def create_transaction_batch(
    request: BatchCreationRequest,
    scc_service = Depends(get_scc_service)
):
    """
    Create transaction batch for consensus validation
    Implementation of Algorithm 3, Step 1: Transaction Batching
    """
    try:
        # Convert Pydantic models to dictionaries
        transactions_data = [tx.dict() for tx in request.transactions]
        
        result = await scc_service.create_transaction_batch(
            proposer_address=request.proposer_address,
            transactions=transactions_data,
            nft_references=request.nft_references
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Batch creation failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch creation error: {str(e)}")

@router.post("/consensus/validation/vote", response_model=Dict, tags=["SCC Consensus"])
async def submit_validation_vote(
    request: ValidationVoteRequest,
    scc_service = Depends(get_scc_service)
):
    """
    Submit validation vote for transaction batch
    Implementation of Algorithm 3, Step 3: Validation Process
    """
    try:
        result = await scc_service.submit_validation_vote(
            batch_id=request.batch_id,
            validator_address=request.validator_address,
            vote=request.vote,
            reasoning=request.reasoning,
            nft_validation_results=request.nft_validation_results,
            blockchain_verification=request.blockchain_verification
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Vote submission failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vote submission error: {str(e)}")

@router.get("/consensus/batch/{batch_id}/status", response_model=Dict, tags=["SCC Consensus"])
async def get_batch_consensus_status(
    batch_id: str,
    scc_service = Depends(get_scc_service)
):
    """Get consensus status for a transaction batch"""
    try:
        # Get batch document
        batch_doc = await scc_service.database["scc_transaction_batches"].find_one({
            "batch_id": batch_id
        })
        
        if not batch_doc:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Get consensus votes
        votes_cursor = scc_service.database["scc_validation_votes"].find({
            "batch_id": batch_id
        })
        votes = await votes_cursor.to_list(length=100)
        
        # Get consensus result if available
        consensus_result = await scc_service.database["scc_consensus_results"].find_one({
            "batch_id": batch_id
        })
        
        return {
            "batch_id": batch_id,
            "status": batch_doc["status"],
            "proposer_id": batch_doc["proposer_id"],
            "transactions_count": len(batch_doc["transactions"]),
            "created_at": batch_doc["created_at"].isoformat(),
            "validation_deadline": batch_doc.get("validation_deadline", "").replace("Z", "+00:00") if batch_doc.get("validation_deadline") else None,
            "votes_received": len(votes),
            "votes": [
                {
                    "validator_id": vote["validator_id"],
                    "vote": vote["vote"],
                    "reasoning": vote["reasoning"],
                    "timestamp": vote["timestamp"].isoformat()
                } for vote in votes
            ],
            "consensus_result": consensus_result.__dict__ if consensus_result else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch status error: {str(e)}")

@router.post("/consensus/reconciliation/perform", response_model=Dict, tags=["SCC Consensus"])
async def perform_periodic_reconciliation(
    scc_service = Depends(get_scc_service)
):
    """
    Perform periodic reconciliation across consensus nodes
    Implementation of Algorithm 3, Step 6: Periodic Reconciliation
    """
    try:
        result = await scc_service.perform_periodic_reconciliation()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconciliation error: {str(e)}")

@router.get("/consensus/nodes", response_model=Dict, tags=["SCC Consensus"])
async def get_consensus_nodes(
    node_type: Optional[str] = Query(None, description="Filter by node type: primary, secondary"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    scc_service = Depends(get_scc_service)
):
    """Get consensus network nodes"""
    try:
        # Build filter
        filter_query = {}
        if node_type:
            filter_query["node_type"] = node_type
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        # Get nodes
        nodes_cursor = scc_service.database["scc_nodes"].find(filter_query)
        nodes = await nodes_cursor.to_list(length=100)
        
        return {
            "nodes": [
                {
                    "node_id": node["node_id"],
                    "address": node["address"],
                    "node_type": node["node_type"],
                    "role": node["role"],
                    "stake_amount": node["stake_amount"],
                    "trust_score": node["trust_score"],
                    "reputation": node["reputation"],
                    "chain_id": node["chain_id"],
                    "is_active": node["is_active"],
                    "last_activity": node["last_activity"].isoformat()
                } for node in nodes
            ],
            "count": len(nodes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nodes retrieval error: {str(e)}")

# === DISPUTE RESOLUTION ALGORITHM ENDPOINTS ===

@router.post("/disputes/initiate", response_model=Dict, tags=["Dispute Resolution"])
async def initiate_dispute(
    request: DisputeInitiationRequest,
    dispute_service = Depends(get_dispute_service)
):
    """
    Initiate dispute resolution process
    Implementation of Algorithm 2, Step 1: Dispute Initiation
    """
    try:
        # Convert evidence to dictionaries
        evidence_data = [evidence.dict() for evidence in request.evidence]
        
        result = await dispute_service.initiate_dispute(
            dispute_type=request.dispute_type,
            involved_parties=request.involved_parties,
            product_id=request.product_id,
            transaction_id=request.transaction_id,
            description=request.description,
            evidence=evidence_data,
            initiated_by=request.initiated_by
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Dispute initiation failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dispute initiation error: {str(e)}")

@router.post("/disputes/arbitrator/vote", response_model=Dict, tags=["Dispute Resolution"])
async def vote_for_arbitrator(
    request: ArbitratorVoteRequest,
    dispute_service = Depends(get_dispute_service)
):
    """
    Submit vote for arbitrator selection
    Implementation of Algorithm 2, Step 3: Stakeholder Voting
    """
    try:
        result = await dispute_service.submit_arbitrator_vote(
            dispute_id=request.dispute_id,
            stakeholder_address=request.stakeholder_address,
            arbitrator_candidate_id=request.arbitrator_candidate_id,
            reasoning=request.reasoning
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Arbitrator vote failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arbitrator vote error: {str(e)}")

@router.post("/disputes/arbitrator/decision", response_model=Dict, tags=["Dispute Resolution"])
async def submit_arbitrator_decision(
    request: ArbitratorDecisionRequest,
    dispute_service = Depends(get_dispute_service)
):
    """
    Submit arbitrator decision for dispute
    Implementation of Algorithm 2, Step 6: Arbitrator Decision
    """
    try:
        result = await dispute_service.submit_arbitrator_decision(
            dispute_id=request.dispute_id,
            arbitrator_address=request.arbitrator_address,
            decision=request.decision,
            reasoning=request.reasoning
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Decision submission failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision submission error: {str(e)}")

@router.get("/disputes/{dispute_id}/status", response_model=Dict, tags=["Dispute Resolution"])
async def get_dispute_status(
    dispute_id: str,
    dispute_service = Depends(get_dispute_service)
):
    """Get detailed status of a dispute"""
    try:
        # Get dispute record
        dispute_doc = await dispute_service.database["dispute_records"].find_one({
            "dispute_id": dispute_id
        })
        
        if not dispute_doc:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        # Get arbitrator votes if in voting phase
        votes_cursor = dispute_service.database["arbitrator_votes"].find({
            "dispute_id": dispute_id
        })
        arbitrator_votes = await votes_cursor.to_list(length=100)
        
        # Get evidence
        evidence_cursor = dispute_service.database["dispute_evidence"].find({
            "dispute_id": dispute_id
        })
        evidence = await evidence_cursor.to_list(length=100)
        
        # Get resolution outcome if resolved
        resolution_outcome = await dispute_service.database["resolution_outcomes"].find_one({
            "dispute_id": dispute_id
        })
        
        return {
            "dispute_id": dispute_id,
            "dispute_type": dispute_doc["dispute_type"],
            "status": dispute_doc["status"],
            "involved_parties": dispute_doc["involved_parties"],
            "description": dispute_doc["description"],
            "product_id": dispute_doc.get("product_id"),
            "transaction_id": dispute_doc.get("transaction_id"),
            "selected_arbitrator": dispute_doc.get("selected_arbitrator"),
            "created_at": dispute_doc["created_at"].isoformat(),
            "deadline": dispute_doc["deadline"].isoformat(),
            "resolved_at": dispute_doc.get("resolved_at").isoformat() if dispute_doc.get("resolved_at") else None,
            "arbitrator_candidates": dispute_doc["arbitrator_candidates"],
            "arbitrator_votes": [
                {
                    "stakeholder_id": vote["stakeholder_id"],
                    "arbitrator_candidate_id": vote["arbitrator_candidate_id"],
                    "vote_weight": vote["vote_weight"],
                    "reasoning": vote.get("reasoning"),
                    "timestamp": vote["timestamp"].isoformat()
                } for vote in arbitrator_votes
            ],
            "evidence_count": len(evidence),
            "resolution_outcome": resolution_outcome
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dispute status error: {str(e)}")

@router.get("/disputes", response_model=Dict, tags=["Dispute Resolution"])
async def list_disputes(
    status: Optional[str] = Query(None, description="Filter by status"),
    dispute_type: Optional[str] = Query(None, description="Filter by dispute type"),
    limit: int = Query(20, description="Number of disputes to return"),
    dispute_service = Depends(get_dispute_service)
):
    """List disputes with optional filtering"""
    try:
        # Build filter
        filter_query = {}
        if status:
            filter_query["status"] = status
        if dispute_type:
            filter_query["dispute_type"] = dispute_type
        
        # Get disputes
        disputes_cursor = dispute_service.database["dispute_records"].find(filter_query).sort(
            "created_at", -1
        ).limit(limit)
        
        disputes = await disputes_cursor.to_list(length=limit)
        
        return {
            "disputes": [
                {
                    "dispute_id": dispute["dispute_id"],
                    "dispute_type": dispute["dispute_type"],
                    "status": dispute["status"],
                    "involved_parties_count": len(dispute["involved_parties"]),
                    "product_id": dispute.get("product_id"),
                    "selected_arbitrator": dispute.get("selected_arbitrator"),
                    "created_at": dispute["created_at"].isoformat(),
                    "resolved_at": dispute.get("resolved_at").isoformat() if dispute.get("resolved_at") else None
                } for dispute in disputes
            ],
            "count": len(disputes),
            "filter": filter_query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disputes listing error: {str(e)}")

@router.get("/arbitrators", response_model=Dict, tags=["Dispute Resolution"])
async def get_arbitrator_candidates(
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    expertise_area: Optional[str] = Query(None, description="Filter by expertise area"),
    dispute_service = Depends(get_dispute_service)
):
    """Get arbitrator candidates"""
    try:
        # Build filter
        filter_query = {}
        if is_available is not None:
            filter_query["is_available"] = is_available
        if expertise_area:
            filter_query["expertise_areas"] = {"$in": [expertise_area]}
        
        # Get arbitrators
        arbitrators_cursor = dispute_service.database["arbitrator_candidates"].find(filter_query).sort(
            "reputation_score", -1
        )
        
        arbitrators = await arbitrators_cursor.to_list(length=100)
        
        return {
            "arbitrators": [
                {
                    "arbitrator_id": arb["arbitrator_id"],
                    "name": arb["name"],
                    "expertise_areas": arb["expertise_areas"],
                    "reputation_score": arb["reputation_score"],
                    "resolution_success_rate": arb["resolution_success_rate"],
                    "total_cases_handled": arb["total_cases_handled"],
                    "neutrality_score": arb["neutrality_score"],
                    "is_available": arb["is_available"],
                    "chain_id": arb["chain_id"]
                } for arb in arbitrators
            ],
            "count": len(arbitrators)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arbitrators retrieval error: {str(e)}")

# === HEALTH AND STATUS ENDPOINTS ===

@router.get("/health", response_model=Dict, tags=["Health"])
async def health_check():
    """Health check for enhanced consensus and dispute resolution services"""
    try:
        # Test SCC service
        scc_service = await get_scc_service()
        await scc_service.database["scc_nodes"].find_one()
        scc_status = "healthy"
        
        # Test dispute service
        dispute_service = await get_dispute_service()
        await dispute_service.database["arbitrator_candidates"].find_one()
        dispute_status = "healthy"
        
        return {
            "status": "healthy",
            "services": {
                "scc_consensus": scc_status,
                "dispute_resolution": dispute_status
            },
            "algorithms_implemented": [
                "Algorithm 3: Supply Chain Consensus (SCC)",
                "Algorithm 2: Dispute Resolution and Voting Mechanism"
            ],
            "features": [
                "Primary/Secondary node classification",
                "Supermajority consensus validation", 
                "Weighted stakeholder voting",
                "Neutral arbitrator selection",
                "Blockchain and NFT evidence review",
                "Automated decision execution",
                "Periodic reconciliation",
                "Reputation-based scoring"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }