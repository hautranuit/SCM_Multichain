"""
Federated Learning Service for Supply Chain
Focus: Anomaly Detection & Counterfeit Detection
"""
import asyncio
import numpy as np
import json
import pickle
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
# import tensorflow as tf  # Commented out for simplified deployment
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
# import pandas as pd  # Commented out for simplified deployment

from app.core.config import get_settings
from app.core.database import get_database

settings = get_settings()

class FederatedLearningService:
    def __init__(self):
        self.database = None
        self.global_models = {}
        self.participant_models = {}
        self.scalers = {}
        self.model_storage_path = settings.fl_model_storage
        
    async def initialize(self):
        """Initialize FL service"""
        print("🤖 Initializing Federated Learning Service...")
        
        self.database = get_database()
        
        # Create model storage directory
        os.makedirs(self.model_storage_path, exist_ok=True)
        
        # Initialize global models
        await self.initialize_global_models()
        
        print("✅ Federated Learning Service initialized")
    
    async def initialize_global_models(self):
        """Initialize global models for anomaly detection and counterfeit detection"""
        
        # Anomaly Detection Model (Isolation Forest)
        self.global_models['anomaly_detection'] = {
            'model': IsolationForest(contamination=0.1, random_state=42),
            'scaler': StandardScaler(),
            'features': [
                'transport_duration',
                'temperature_variance',
                'humidity_variance',
                'location_jumps',
                'participant_reputation',
                'product_age',
                'handover_frequency'
            ],
            'last_updated': datetime.now(),
            'training_rounds': 0,
            'participants_contributed': []
        }
        
        # Counterfeit Detection Model (Neural Network)
        self.global_models['counterfeit_detection'] = {
            'model': self.create_counterfeit_detection_model(),
            'scaler': StandardScaler(),
            'features': [
                'qr_code_complexity',
                'metadata_consistency',
                'participant_verification_score',
                'product_history_length',
                'cryptographic_signature_strength',
                'ipfs_metadata_integrity',
                'transport_chain_consistency'
            ],
            'last_updated': datetime.now(),
            'training_rounds': 0,
            'participants_contributed': []
        }
        
        print("✅ Global FL models initialized")
    
    def create_counterfeit_detection_model(self):
        """Create simplified counterfeit detection model (without TensorFlow)"""
        # Simplified model using scikit-learn for now
        # This would be replaced with TensorFlow model when ML dependencies are available
        model_config = {
            'type': 'isolation_forest',
            'contamination': 0.1,
            'random_state': 42,
            'features': ['price_variance', 'delivery_time', 'route_deviation', 'temperature_variance']
        }
        
        return model_config
    
    async def train_local_anomaly_model(self, participant_address: str, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train local anomaly detection model for a participant"""
        
        try:
            if not training_data:
                return {"error": "No training data provided"}
            
            # Extract features for anomaly detection
            features_data = []
            for data_point in training_data:
                features = self.extract_anomaly_features(data_point)
                if features:
                    features_data.append(features)
            
            if len(features_data) < 10:  # Minimum data requirement
                return {"error": "Insufficient training data (minimum 10 samples required)"}
            
            # Convert to numpy array
            X = np.array(features_data)
            
            # Normalize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train local isolation forest model
            local_model = IsolationForest(contamination=0.1, random_state=42)
            local_model.fit(X_scaled)
            
            # Calculate model performance metrics
            anomaly_scores = local_model.decision_function(X_scaled)
            anomalies_detected = np.sum(local_model.predict(X_scaled) == -1)
            
            # Store local model
            model_data = {
                'participant_address': participant_address,
                'model_type': 'anomaly_detection',
                'model_weights': pickle.dumps(local_model),
                'scaler_params': pickle.dumps(scaler),
                'training_samples': len(features_data),
                'anomalies_detected': int(anomalies_detected),
                'mean_anomaly_score': float(np.mean(anomaly_scores)),
                'created_at': datetime.now(),
                'status': 'trained'
            }
            
            await self.database.fl_models.insert_one(model_data)
            
            return {
                "success": True,
                "model_id": str(model_data['_id']),
                "training_samples": len(features_data),
                "anomalies_detected": int(anomalies_detected),
                "ready_for_aggregation": True
            }
            
        except Exception as e:
            return {"error": f"Local anomaly model training failed: {e}"}
    
    async def train_local_counterfeit_model(self, participant_address: str, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train local counterfeit detection model for a participant"""
        
        try:
            if not training_data:
                return {"error": "No training data provided"}
            
            # Extract features and labels for counterfeit detection
            features_data = []
            labels = []
            
            for data_point in training_data:
                features = self.extract_counterfeit_features(data_point)
                label = data_point.get('is_counterfeit', 0)  # 0 = authentic, 1 = counterfeit
                
                if features:
                    features_data.append(features)
                    labels.append(label)
            
            if len(features_data) < 20:  # Minimum data requirement for neural network
                return {"error": "Insufficient training data (minimum 20 samples required)"}
            
            # Convert to numpy arrays
            X = np.array(features_data)
            y = np.array(labels)
            
            # Normalize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Create and train local model
            local_model = self.create_counterfeit_detection_model()
            
            # Train the model
            history = local_model.fit(
                X_scaled, y,
                epochs=50,
                batch_size=min(32, len(X_scaled)),
                validation_split=0.2,
                verbose=0
            )
            
            # Calculate performance metrics
            predictions = local_model.predict(X_scaled)
            accuracy = np.mean((predictions > 0.5) == y)
            
            # Store local model
            model_data = {
                'participant_address': participant_address,
                'model_type': 'counterfeit_detection',
                'model_weights': pickle.dumps(local_model.get_weights()),
                'scaler_params': pickle.dumps(scaler),
                'training_samples': len(features_data),
                'accuracy': float(accuracy),
                'loss_history': history.history['loss'][-10:],  # Last 10 epochs
                'created_at': datetime.now(),
                'status': 'trained'
            }
            
            await self.database.fl_models.insert_one(model_data)
            
            return {
                "success": True,
                "model_id": str(model_data['_id']),
                "training_samples": len(features_data),
                "accuracy": float(accuracy),
                "ready_for_aggregation": True
            }
            
        except Exception as e:
            return {"error": f"Local counterfeit model training failed: {e}"}
    
    def extract_anomaly_features(self, data_point: Dict[str, Any]) -> Optional[List[float]]:
        """Extract features for anomaly detection"""
        
        try:
            features = []
            
            # Transport duration (normalized to hours)
            transport_duration = data_point.get('transport_duration', 0) / 3600
            features.append(transport_duration)
            
            # Temperature variance during transport
            temp_data = data_point.get('temperature_readings', [20])  # Default room temp
            temp_variance = np.var(temp_data) if len(temp_data) > 1 else 0
            features.append(temp_variance)
            
            # Humidity variance
            humidity_data = data_point.get('humidity_readings', [50])  # Default 50%
            humidity_variance = np.var(humidity_data) if len(humidity_data) > 1 else 0
            features.append(humidity_variance)
            
            # Location jumps (unusual geographic movements)
            location_jumps = data_point.get('location_jumps', 0)
            features.append(location_jumps)
            
            # Participant reputation score
            participant_reputation = data_point.get('participant_reputation', 100)
            features.append(participant_reputation)
            
            # Product age (days since manufacturing)
            product_age = data_point.get('product_age_days', 0)
            features.append(product_age)
            
            # Handover frequency (transfers per day)
            handover_frequency = data_point.get('handover_frequency', 0)
            features.append(handover_frequency)
            
            return features
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def extract_counterfeit_features(self, data_point: Dict[str, Any]) -> Optional[List[float]]:
        """Extract features for counterfeit detection"""
        
        try:
            features = []
            
            # QR code complexity score
            qr_complexity = data_point.get('qr_code_complexity', 0.5)
            features.append(qr_complexity)
            
            # Metadata consistency score
            metadata_consistency = data_point.get('metadata_consistency', 1.0)
            features.append(metadata_consistency)
            
            # Participant verification score
            verification_score = data_point.get('participant_verification_score', 0.8)
            features.append(verification_score)
            
            # Product history length
            history_length = data_point.get('product_history_length', 1)
            features.append(history_length)
            
            # Cryptographic signature strength
            crypto_strength = data_point.get('cryptographic_signature_strength', 0.9)
            features.append(crypto_strength)
            
            # IPFS metadata integrity
            ipfs_integrity = data_point.get('ipfs_metadata_integrity', 1.0)
            features.append(ipfs_integrity)
            
            # Transport chain consistency
            chain_consistency = data_point.get('transport_chain_consistency', 1.0)
            features.append(chain_consistency)
            
            return features
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    async def aggregate_anomaly_models(self) -> Dict[str, Any]:
        """Aggregate local anomaly detection models using federated averaging"""
        
        try:
            # Get all trained local models for anomaly detection
            cursor = self.database.fl_models.find({
                'model_type': 'anomaly_detection',
                'status': 'trained'
            })
            
            local_models = []
            async for model_doc in cursor:
                local_models.append(model_doc)
            
            if len(local_models) < settings.fl_aggregation_threshold:
                return {
                    "error": f"Insufficient models for aggregation. Need {settings.fl_aggregation_threshold}, got {len(local_models)}"
                }
            
            # For Isolation Forest, we'll aggregate by averaging contamination parameters
            # and retraining on combined feature statistics
            
            total_samples = sum(model['training_samples'] for model in local_models)
            weighted_contamination = sum(
                model['anomalies_detected'] / model['training_samples'] 
                for model in local_models
            ) / len(local_models)
            
            # Update global model
            global_contamination = max(0.01, min(0.3, weighted_contamination))
            self.global_models['anomaly_detection']['model'] = IsolationForest(
                contamination=global_contamination,
                random_state=42
            )
            
            # Update model metadata
            self.global_models['anomaly_detection']['last_updated'] = datetime.now()
            self.global_models['anomaly_detection']['training_rounds'] += 1
            self.global_models['anomaly_detection']['participants_contributed'] = [
                model['participant_address'] for model in local_models
            ]
            
            # Mark local models as aggregated
            model_ids = [model['_id'] for model in local_models]
            await self.database.fl_models.update_many(
                {'_id': {'$in': model_ids}},
                {'$set': {'status': 'aggregated'}}
            )
            
            return {
                "success": True,
                "aggregated_models": len(local_models),
                "total_samples": total_samples,
                "global_contamination": global_contamination,
                "training_round": self.global_models['anomaly_detection']['training_rounds']
            }
            
        except Exception as e:
            return {"error": f"Anomaly model aggregation failed: {e}"}
    
    async def aggregate_counterfeit_models(self) -> Dict[str, Any]:
        """Aggregate local counterfeit detection models using federated averaging"""
        
        try:
            # Get all trained local models for counterfeit detection
            cursor = self.database.fl_models.find({
                'model_type': 'counterfeit_detection',
                'status': 'trained'
            })
            
            local_models = []
            async for model_doc in cursor:
                local_models.append(model_doc)
            
            if len(local_models) < settings.fl_aggregation_threshold:
                return {
                    "error": f"Insufficient models for aggregation. Need {settings.fl_aggregation_threshold}, got {len(local_models)}"
                }
            
            # Federated averaging of neural network weights
            global_weights = None
            total_samples = 0
            
            for model_doc in local_models:
                weights = pickle.loads(model_doc['model_weights'])
                samples = model_doc['training_samples']
                
                if global_weights is None:
                    global_weights = [w * samples for w in weights]
                else:
                    for i, w in enumerate(weights):
                        global_weights[i] += w * samples
                
                total_samples += samples
            
            # Average the weights
            global_weights = [w / total_samples for w in global_weights]
            
            # Update global model
            self.global_models['counterfeit_detection']['model'].set_weights(global_weights)
            self.global_models['counterfeit_detection']['last_updated'] = datetime.now()
            self.global_models['counterfeit_detection']['training_rounds'] += 1
            self.global_models['counterfeit_detection']['participants_contributed'] = [
                model['participant_address'] for model in local_models
            ]
            
            # Calculate average accuracy
            avg_accuracy = sum(model['accuracy'] for model in local_models) / len(local_models)
            
            # Mark local models as aggregated
            model_ids = [model['_id'] for model in local_models]
            await self.database.fl_models.update_many(
                {'_id': {'$in': model_ids}},
                {'$set': {'status': 'aggregated'}}
            )
            
            return {
                "success": True,
                "aggregated_models": len(local_models),
                "total_samples": total_samples,
                "average_accuracy": avg_accuracy,
                "training_round": self.global_models['counterfeit_detection']['training_rounds']
            }
            
        except Exception as e:
            return {"error": f"Counterfeit model aggregation failed: {e}"}
    
    async def detect_anomaly(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in product transport/handling"""
        
        try:
            features = self.extract_anomaly_features(product_data)
            if not features:
                return {"error": "Failed to extract features"}
            
            # Use global model for prediction
            model = self.global_models['anomaly_detection']['model']
            scaler = self.global_models['anomaly_detection']['scaler']
            
            # Check if model is trained
            if not hasattr(model, 'decision_function_'):
                return {"error": "Global anomaly model not trained yet"}
            
            # Normalize features
            features_scaled = scaler.transform([features])
            
            # Get anomaly score and prediction
            anomaly_score = model.decision_function(features_scaled)[0]
            is_anomaly = model.predict(features_scaled)[0] == -1
            
            # Store anomaly detection result
            anomaly_result = {
                'product_id': product_data.get('token_id'),
                'anomaly_score': float(anomaly_score),
                'is_anomaly': bool(is_anomaly),
                'features_used': self.global_models['anomaly_detection']['features'],
                'detected_at': datetime.now(),
                'model_version': self.global_models['anomaly_detection']['training_rounds']
            }
            
            if is_anomaly:
                await self.database.anomalies.insert_one(anomaly_result)
            
            return {
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": float(anomaly_score),
                "confidence": abs(float(anomaly_score)),
                "model_version": self.global_models['anomaly_detection']['training_rounds']
            }
            
        except Exception as e:
            return {"error": f"Anomaly detection failed: {e}"}
    
    async def detect_counterfeit(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if a product is potentially counterfeit"""
        
        try:
            features = self.extract_counterfeit_features(product_data)
            if not features:
                return {"error": "Failed to extract features"}
            
            # Use global model for prediction
            model = self.global_models['counterfeit_detection']['model']
            scaler = self.global_models['counterfeit_detection']['scaler']
            
            # Normalize features
            features_scaled = scaler.transform([features])
            
            # Get counterfeit probability
            counterfeit_probability = model.predict(features_scaled)[0][0]
            is_counterfeit = counterfeit_probability > 0.5
            
            # Store counterfeit detection result
            counterfeit_result = {
                'product_id': product_data.get('token_id'),
                'counterfeit_probability': float(counterfeit_probability),
                'is_counterfeit': bool(is_counterfeit),
                'features_used': self.global_models['counterfeit_detection']['features'],
                'detected_at': datetime.now(),
                'model_version': self.global_models['counterfeit_detection']['training_rounds']
            }
            
            if is_counterfeit:
                await self.database.counterfeits.insert_one(counterfeit_result)
            
            return {
                "is_counterfeit": bool(is_counterfeit),
                "counterfeit_probability": float(counterfeit_probability),
                "confidence": float(abs(counterfeit_probability - 0.5) * 2),
                "model_version": self.global_models['counterfeit_detection']['training_rounds']
            }
            
        except Exception as e:
            return {"error": f"Counterfeit detection failed: {e}"}
    
    async def get_fl_statistics(self) -> Dict[str, Any]:
        """Get federated learning system statistics"""
        
        try:
            # Count models by type and status
            anomaly_models = await self.database.fl_models.count_documents({
                'model_type': 'anomaly_detection'
            })
            counterfeit_models = await self.database.fl_models.count_documents({
                'model_type': 'counterfeit_detection'
            })
            
            # Count detections
            anomalies_detected = await self.database.anomalies.count_documents({})
            counterfeits_detected = await self.database.counterfeits.count_documents({})
            
            return {
                "models": {
                    "anomaly_detection": {
                        "total_models": anomaly_models,
                        "training_rounds": self.global_models['anomaly_detection']['training_rounds'],
                        "last_updated": self.global_models['anomaly_detection']['last_updated'].isoformat(),
                        "active_participants": len(self.global_models['anomaly_detection']['participants_contributed'])
                    },
                    "counterfeit_detection": {
                        "total_models": counterfeit_models,
                        "training_rounds": self.global_models['counterfeit_detection']['training_rounds'],
                        "last_updated": self.global_models['counterfeit_detection']['last_updated'].isoformat(),
                        "active_participants": len(self.global_models['counterfeit_detection']['participants_contributed'])
                    }
                },
                "detections": {
                    "anomalies_detected": anomalies_detected,
                    "counterfeits_detected": counterfeits_detected
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get FL statistics: {e}"}
