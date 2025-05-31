"""
Analytics API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.services.blockchain_service import BlockchainService

router = APIRouter()

async def get_blockchain_service():
    service = BlockchainService()
    await service.initialize()
    return service

@router.get("/dashboard")
async def get_dashboard_analytics(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get dashboard analytics data"""
    try:
        # Get basic counts
        total_products = await blockchain_service.database.products.count_documents({})
        total_participants = await blockchain_service.database.participants.count_documents({})
        total_transactions = await blockchain_service.database.transactions.count_documents({})
        
        # Get recent activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_products = await blockchain_service.database.products.count_documents({
            "created_at": {"$gte": seven_days_ago.timestamp()}
        })
        
        # Get anomalies and counterfeits
        total_anomalies = await blockchain_service.database.anomalies.count_documents({})
        total_counterfeits = await blockchain_service.database.counterfeits.count_documents({})
        
        # Recent anomalies (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_anomalies = await blockchain_service.database.anomalies.count_documents({
            "detected_at": {"$gte": yesterday}
        })
        
        return {
            "overview": {
                "total_products": total_products,
                "total_participants": total_participants,
                "total_transactions": total_transactions,
                "products_last_7_days": recent_products
            },
            "security": {
                "total_anomalies": total_anomalies,
                "total_counterfeits": total_counterfeits,
                "anomalies_last_24h": recent_anomalies
            },
            "network_status": await blockchain_service.get_network_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/supply-chain/flow")
async def get_supply_chain_flow(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get supply chain flow analytics"""
    try:
        # Aggregate products by status
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        status_distribution = []
        async for result in blockchain_service.database.products.aggregate(pipeline):
            status_distribution.append({
                "status": result["_id"],
                "count": result["count"]
            })
        
        # Get average transport time
        pipeline = [
            {"$unwind": "$transport_history"},
            {"$group": {
                "_id": None,
                "avg_transport_time": {"$avg": "$transport_history.transport_data.duration"},
                "total_transports": {"$sum": 1}
            }}
        ]
        
        transport_stats = {"avg_transport_time": 0, "total_transports": 0}
        async for result in blockchain_service.database.products.aggregate(pipeline):
            transport_stats = {
                "avg_transport_time": result.get("avg_transport_time", 0),
                "total_transports": result.get("total_transports", 0)
            }
        
        return {
            "status_distribution": status_distribution,
            "transport_statistics": transport_stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/participants/activity")
async def get_participant_activity(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get participant activity analytics"""
    try:
        # Top participants by product count
        pipeline = [
            {"$group": {"_id": "$current_owner", "product_count": {"$sum": 1}}},
            {"$sort": {"product_count": -1}},
            {"$limit": 10}
        ]
        
        top_participants = []
        async for result in blockchain_service.database.products.aggregate(pipeline):
            # Get participant info
            participant = await blockchain_service.database.participants.find_one({
                "address": result["_id"]
            })
            
            top_participants.append({
                "address": result["_id"],
                "product_count": result["product_count"],
                "participant_type": participant.get("participant_type", "unknown") if participant else "unknown",
                "reputation_score": participant.get("reputation_score", 0) if participant else 0
            })
        
        # Participant distribution by type
        pipeline = [
            {"$group": {"_id": "$participant_type", "count": {"$sum": 1}}}
        ]
        
        type_distribution = []
        async for result in blockchain_service.database.participants.aggregate(pipeline):
            type_distribution.append({
                "type": result["_id"],
                "count": result["count"]
            })
        
        return {
            "top_participants": top_participants,
            "type_distribution": type_distribution
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/security/threats")
async def get_security_analytics(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get security threat analytics"""
    try:
        # Recent anomalies trend (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Anomalies by day
        pipeline = [
            {"$match": {"detected_at": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$detected_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        anomaly_trend = []
        async for result in blockchain_service.database.anomalies.aggregate(pipeline):
            anomaly_trend.append({
                "date": result["_id"],
                "anomalies": result["count"]
            })
        
        # Counterfeit trend
        counterfeit_trend = []
        async for result in blockchain_service.database.counterfeits.aggregate(pipeline):
            counterfeit_trend.append({
                "date": result["_id"],
                "counterfeits": result["count"]
            })
        
        # Risk score by participant type
        pipeline = [
            {"$lookup": {
                "from": "participants",
                "localField": "product_id",
                "foreignField": "address",
                "as": "participant_info"
            }},
            {"$unwind": "$participant_info"},
            {"$group": {
                "_id": "$participant_info.participant_type",
                "risk_incidents": {"$sum": 1}
            }}
        ]
        
        risk_by_type = []
        async for result in blockchain_service.database.anomalies.aggregate(pipeline):
            risk_by_type.append({
                "participant_type": result["_id"],
                "risk_incidents": result["risk_incidents"]
            })
        
        return {
            "anomaly_trend": anomaly_trend,
            "counterfeit_trend": counterfeit_trend,
            "risk_by_participant_type": risk_by_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/performance/metrics")
async def get_performance_metrics(
    blockchain_service: BlockchainService = Depends(get_blockchain_service)
):
    """Get system performance metrics"""
    try:
        # Network statistics
        network_stats = await blockchain_service.get_network_stats()
        
        # Database performance
        db_stats = {
            "collections": {
                "products": await blockchain_service.database.products.count_documents({}),
                "participants": await blockchain_service.database.participants.count_documents({}),
                "transactions": await blockchain_service.database.transactions.count_documents({}),
                "fl_models": await blockchain_service.database.fl_models.count_documents({}),
                "anomalies": await blockchain_service.database.anomalies.count_documents({}),
                "counterfeits": await blockchain_service.database.counterfeits.count_documents({})
            }
        }
        
        return {
            "network": network_stats,
            "database": db_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
