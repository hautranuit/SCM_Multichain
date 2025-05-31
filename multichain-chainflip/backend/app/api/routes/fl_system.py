"""
Federated Learning API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
from pydantic import BaseModel

from app.services.fl_service import FederatedLearningService

router = APIRouter()

# Pydantic models
class TrainingData(BaseModel):
    participant_address: str
    training_data: List[Dict[str, Any]]
    model_type: str  # "anomaly_detection" or "counterfeit_detection"

class AnomalyDetection(BaseModel):
    product_data: Dict[str, Any]

class CounterfeitDetection(BaseModel):
    product_data: Dict[str, Any]

# Dependency to get FL service
async def get_fl_service():
    service = FederatedLearningService()
    await service.initialize()
    return service

@router.get("/status")
async def get_fl_status(
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Get federated learning system status and statistics"""
    return await fl_service.get_fl_statistics()

@router.post("/train/anomaly")
async def train_anomaly_model(
    training_data: TrainingData,
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Train local anomaly detection model"""
    try:
        result = await fl_service.train_local_anomaly_model(
            training_data.participant_address,
            training_data.training_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/train/counterfeit")
async def train_counterfeit_model(
    training_data: TrainingData,
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Train local counterfeit detection model"""
    try:
        result = await fl_service.train_local_counterfeit_model(
            training_data.participant_address,
            training_data.training_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/aggregate/anomaly")
async def aggregate_anomaly_models(
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Aggregate local anomaly detection models"""
    try:
        result = await fl_service.aggregate_anomaly_models()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/aggregate/counterfeit")
async def aggregate_counterfeit_models(
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Aggregate local counterfeit detection models"""
    try:
        result = await fl_service.aggregate_counterfeit_models()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/detect/anomaly")
async def detect_anomaly(
    detection_data: AnomalyDetection,
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Detect anomalies in product transport/handling"""
    try:
        result = await fl_service.detect_anomaly(detection_data.product_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/detect/counterfeit")
async def detect_counterfeit(
    detection_data: CounterfeitDetection,
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Detect if a product is potentially counterfeit"""
    try:
        result = await fl_service.detect_counterfeit(detection_data.product_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/models/anomaly/global")
async def get_global_anomaly_model(
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Get global anomaly detection model information"""
    try:
        model_info = fl_service.global_models.get('anomaly_detection', {})
        return {
            "model_type": "anomaly_detection",
            "features": model_info.get('features', []),
            "training_rounds": model_info.get('training_rounds', 0),
            "last_updated": model_info.get('last_updated', '').isoformat() if model_info.get('last_updated') else '',
            "participants_contributed": len(model_info.get('participants_contributed', []))
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/models/counterfeit/global")
async def get_global_counterfeit_model(
    fl_service: FederatedLearningService = Depends(get_fl_service)
):
    """Get global counterfeit detection model information"""
    try:
        model_info = fl_service.global_models.get('counterfeit_detection', {})
        return {
            "model_type": "counterfeit_detection",
            "features": model_info.get('features', []),
            "training_rounds": model_info.get('training_rounds', 0),
            "last_updated": model_info.get('last_updated', '').isoformat() if model_info.get('last_updated') else '',
            "participants_contributed": len(model_info.get('participants_contributed', []))
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
