import React, { useState, useEffect } from 'react';
import { useBlockchain } from '../contexts/BlockchainContext';
import { useNotification } from '../contexts/NotificationContext';

export const FederatedLearning = () => {
  const { isConnected, account } = useBlockchain();
  const { showSuccess, showError } = useNotification();
  
  const [flStatus, setFlStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [trainingInProgress, setTrainingInProgress] = useState(false);

  useEffect(() => {
    fetchFLStatus();
    
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchFLStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchFLStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/federated-learning/status`);
      
      if (response.ok) {
        const data = await response.json();
        setFlStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch FL status:', error);
      showError('Failed to load FL status');
    } finally {
      setLoading(false);
    }
  };

  const startTraining = async (modelType) => {
    if (!isConnected) {
      showError('Please connect your wallet first');
      return;
    }

    try {
      setTrainingInProgress(true);
      
      // Generate sample training data (in real implementation, this would come from actual supply chain data)
      const sampleData = generateSampleTrainingData(modelType);
      
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/federated-learning/train/${modelType}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            participant_address: account,
            training_data: sampleData,
            model_type: modelType
          })
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        showSuccess(`${modelType} training completed successfully!`);
        fetchFLStatus(); // Refresh status
      } else {
        const error = await response.json();
        showError(`Training failed: ${error.error}`);
      }
    } catch (error) {
      console.error('Training error:', error);
      showError('Failed to start training');
    } finally {
      setTrainingInProgress(false);
    }
  };

  const aggregateModels = async (modelType) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/federated-learning/aggregate/${modelType}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        showSuccess(`${modelType} models aggregated successfully!`);
        fetchFLStatus(); // Refresh status
      } else {
        const error = await response.json();
        showError(`Aggregation failed: ${error.error}`);
      }
    } catch (error) {
      console.error('Aggregation error:', error);
      showError('Failed to aggregate models');
    }
  };

  const generateSampleTrainingData = (modelType) => {
    if (modelType === 'anomaly') {
      return Array.from({ length: 50 }, (_, i) => ({
        transport_duration: Math.random() * 72 * 3600, // 0-72 hours in seconds
        temperature_readings: Array.from({ length: 10 }, () => 20 + Math.random() * 10),
        humidity_readings: Array.from({ length: 10 }, () => 40 + Math.random() * 20),
        location_jumps: Math.floor(Math.random() * 5),
        participant_reputation: 70 + Math.random() * 30,
        product_age_days: Math.random() * 365,
        handover_frequency: Math.random() * 3
      }));
    } else if (modelType === 'counterfeit') {
      return Array.from({ length: 50 }, (_, i) => ({
        qr_code_complexity: Math.random(),
        metadata_consistency: 0.8 + Math.random() * 0.2,
        participant_verification_score: 0.7 + Math.random() * 0.3,
        product_history_length: 1 + Math.floor(Math.random() * 10),
        cryptographic_signature_strength: 0.8 + Math.random() * 0.2,
        ipfs_metadata_integrity: 0.9 + Math.random() * 0.1,
        transport_chain_consistency: 0.8 + Math.random() * 0.2,
        is_counterfeit: Math.random() < 0.1 ? 1 : 0 // 10% counterfeit rate
      }));
    }
    return [];
  };

  const ModelCard = ({ modelType, modelInfo, title, description, icon }) => (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">{icon}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-600">{description}</p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-bold text-primary-600">
            {modelInfo?.training_rounds || 0}
          </div>
          <div className="text-xs text-gray-500">Training Rounds</div>
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Active Participants:</span>
          <span className="font-medium">{modelInfo?.active_participants || 0}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Last Updated:</span>
          <span className="font-medium text-sm">
            {modelInfo?.last_updated ? 
              new Date(modelInfo.last_updated).toLocaleDateString() : 
              'Never'
            }
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Features:</span>
          <span className="font-medium">{modelInfo?.features?.length || 0}</span>
        </div>
      </div>
      
      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => startTraining(modelType)}
          disabled={!isConnected || trainingInProgress}
          className="btn-primary text-sm flex-1"
        >
          {trainingInProgress ? '⏳ Training...' : '🚀 Train Model'}
        </button>
        <button
          onClick={() => aggregateModels(modelType)}
          disabled={trainingInProgress || (modelInfo?.training_rounds || 0) === 0}
          className="btn-secondary text-sm flex-1"
        >
          🔄 Aggregate
        </button>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Federated Learning</h1>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="card">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Federated Learning</h1>
          <p className="text-gray-600">Collaborative AI training for supply chain security</p>
        </div>
        
        <div className="flex space-x-3">
          <button 
            onClick={fetchFLStatus}
            className="btn-secondary"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Connection Warning */}
      {!isConnected && (
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
          <div className="flex">
            <span className="text-warning-600 text-xl mr-3">⚠️</span>
            <div>
              <h3 className="text-sm font-medium text-warning-800">
                Wallet Not Connected
              </h3>
              <p className="mt-1 text-sm text-warning-700">
                Connect your wallet to participate in federated learning training.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* FL Models */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ModelCard
          modelType="anomaly"
          modelInfo={flStatus?.models?.anomaly_detection}
          title="Anomaly Detection"
          description="Detect unusual patterns in supply chain operations"
          icon="🔍"
        />
        
        <ModelCard
          modelType="counterfeit"
          modelInfo={flStatus?.models?.counterfeit_detection}
          title="Counterfeit Detection"
          description="Identify potentially counterfeit products"
          icon="🛡️"
        />
      </div>

      {/* Detection Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">🚨 Recent Anomalies</h3>
          </div>
          
          <div className="text-center py-8">
            <div className="text-4xl font-bold text-red-600 mb-2">
              {flStatus?.detections?.anomalies_detected || 0}
            </div>
            <div className="text-sm text-gray-600">Anomalies Detected</div>
            {(flStatus?.detections?.anomalies_detected || 0) > 0 && (
              <button className="mt-4 btn-secondary text-sm">
                View Details
              </button>
            )}
          </div>
        </div>
        
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">🛡️ Counterfeit Alerts</h3>
          </div>
          
          <div className="text-center py-8">
            <div className="text-4xl font-bold text-orange-600 mb-2">
              {flStatus?.detections?.counterfeits_detected || 0}
            </div>
            <div className="text-sm text-gray-600">Counterfeits Found</div>
            {(flStatus?.detections?.counterfeits_detected || 0) > 0 && (
              <button className="mt-4 btn-secondary text-sm">
                View Details
              </button>
            )}
          </div>
        </div>
      </div>

      {/* FL Process Information */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">🤖 How Federated Learning Works</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4">
            <div className="text-3xl mb-3">📊</div>
            <h4 className="font-semibold text-gray-900 mb-2">Local Training</h4>
            <p className="text-sm text-gray-600">
              Each participant trains models on their local supply chain data
            </p>
          </div>
          
          <div className="text-center p-4">
            <div className="text-3xl mb-3">🔄</div>
            <h4 className="font-semibold text-gray-900 mb-2">Model Aggregation</h4>
            <p className="text-sm text-gray-600">
              Local models are aggregated to create improved global models
            </p>
          </div>
          
          <div className="text-center p-4">
            <div className="text-3xl mb-3">🛡️</div>
            <h4 className="font-semibold text-gray-900 mb-2">Privacy Preserved</h4>
            <p className="text-sm text-gray-600">
              Raw data never leaves participants' systems, ensuring privacy
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
