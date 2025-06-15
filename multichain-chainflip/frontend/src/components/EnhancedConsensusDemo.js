import React, { useState, useEffect } from 'react';
import axios from 'axios';

const EnhancedConsensusDemo = () => {
  const [activeTab, setActiveTab] = useState('consensus');
  const [consensusNodes, setConsensusNodes] = useState([]);
  const [arbitrators, setArbitrators] = useState([]);
  const [loading, setLoading] = useState(false);

  // API base URL
  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchConsensusNodes();
    fetchArbitrators();
  }, []);

  const fetchConsensusNodes = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/enhanced-consensus/consensus/nodes`);
      setConsensusNodes(response.data.nodes || []);
    } catch (error) {
      console.error('Error fetching consensus nodes:', error);
    }
  };

  const fetchArbitrators = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/enhanced-consensus/arbitrators`);
      setArbitrators(response.data.arbitrators || []);
    } catch (error) {
      console.error('Error fetching arbitrators:', error);
    }
  };

  const createSampleBatch = async () => {
    setLoading(true);
    try {
      const sampleBatch = {
        proposer_address: "0x032041b4b356fEE1496805DD4749f181bC736FFA",
        transactions: [
          {
            from_address: "0x032041b4b356fEE1496805DD4749f181bC736FFA",
            to_address: "0x742d35Cc8A8E3c8c4e3bB2C4a2f5e1a2C3d4E5F6",
            product_id: "PROD-001",
            transaction_type: "transfer",
            value: 1.5,
            metadata: { "quality_score": 0.95 },
            timestamp: new Date().toISOString(),
            chain_id: 84532
          }
        ],
        nft_references: ["NFT-001", "NFT-002"]
      };

      const response = await axios.post(`${API_BASE}/api/enhanced-consensus/consensus/batch/create`, sampleBatch);
      alert(`✅ Batch created successfully!\nBatch ID: ${response.data.batch_id}\nTransactions: ${response.data.transactions_count}`);
    } catch (error) {
      console.error('Error creating batch:', error);
      alert(`❌ Error creating batch: ${error.response?.data?.detail || error.message}`);
    }
    setLoading(false);
  };

  const initiateSampleDispute = async () => {
    setLoading(true);
    try {
      const sampleDispute = {
        dispute_type: "product_quality",
        involved_parties: [
          "0x032041b4b356fEE1496805DD4749f181bC736FFA",
          "0x742d35Cc8A8E3c8c4e3bB2C4a2f5e1a2C3d4E5F6"
        ],
        product_id: "PROD-001",
        description: "Product quality does not match specifications. Expected high-grade material but received substandard quality.",
        evidence: [
          {
            evidence_type: "photo",
            content: { "description": "Photo showing product defects", "file_size": "2.5MB" },
            ipfs_hash: "QmSamplePhotoHash123"
          }
        ],
        initiated_by: "0x742d35Cc8A8E3c8c4e3bB2C4a2f5e1a2C3d4E5F6"
      };

      const response = await axios.post(`${API_BASE}/api/enhanced-consensus/disputes/initiate`, sampleDispute);
      alert(`✅ Dispute initiated successfully!\nDispute ID: ${response.data.dispute_id}\nStakeholders: ${response.data.stakeholders_count}\nArbitrator Candidates: ${response.data.arbitrator_candidates_count}`);
    } catch (error) {
      console.error('Error initiating dispute:', error);
      alert(`❌ Error initiating dispute: ${error.response?.data?.detail || error.message}`);
    }
    setLoading(false);
  };

  const getNodeTypeColor = (nodeType) => {
    return nodeType === 'primary' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800';
  };

  const getReputationColor = (score) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.8) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Enhanced Consensus & Dispute Resolution
          </h1>
          <p className="text-gray-600">
            Implementation of Narayanan et al. Algorithms 2 & 3 for Supply Chain Management
          </p>
        </div>

        {/* Algorithm Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-blue-500">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              🔗 Algorithm 3: Supply Chain Consensus (SCC)
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              Primary/Secondary node classification with supermajority validation
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Primary Nodes:</span>
                <span className="font-medium">{consensusNodes.filter(n => n.node_type === 'primary').length}</span>
              </div>
              <div className="flex justify-between">
                <span>Secondary Nodes:</span>
                <span className="font-medium">{consensusNodes.filter(n => n.node_type === 'secondary').length}</span>
              </div>
              <div className="flex justify-between">
                <span>Supermajority Threshold:</span>
                <span className="font-medium">67%</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-purple-500">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              ⚖️ Algorithm 2: Dispute Resolution & Voting
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              Stakeholder-driven arbitrator selection with weighted voting
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Available Arbitrators:</span>
                <span className="font-medium">{arbitrators.filter(a => a.is_available).length}</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Success Rate:</span>
                <span className="font-medium">
                  {arbitrators.length > 0 ? 
                    Math.round(arbitrators.reduce((sum, a) => sum + a.resolution_success_rate, 0) / arbitrators.length * 100) 
                    : 0}%
                </span>
              </div>
              <div className="flex justify-between">
                <span>Total Cases Handled:</span>
                <span className="font-medium">
                  {arbitrators.reduce((sum, a) => sum + a.total_cases_handled, 0)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-lg">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('consensus')}
                className={`py-4 px-6 border-b-2 font-medium text-sm ${
                  activeTab === 'consensus'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                SCC Consensus Nodes
              </button>
              <button
                onClick={() => setActiveTab('arbitrators')}
                className={`py-4 px-6 border-b-2 font-medium text-sm ${
                  activeTab === 'arbitrators'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Arbitrator Network
              </button>
              <button
                onClick={() => setActiveTab('demo')}
                className={`py-4 px-6 border-b-2 font-medium text-sm ${
                  activeTab === 'demo'
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Live Demo
              </button>
            </nav>
          </div>

          <div className="p-6">
            {/* Consensus Nodes Tab */}
            {activeTab === 'consensus' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Consensus Network Nodes</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {consensusNodes.map((node) => (
                    <div key={node.node_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium text-gray-900">{node.node_id}</h4>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getNodeTypeColor(node.node_type)}`}>
                          {node.node_type.toUpperCase()}
                        </span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Role:</span>
                          <span className="font-medium">{node.role}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Stake:</span>
                          <span className="font-medium">{node.stake_amount} ETH</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Trust Score:</span>
                          <span className={`font-medium ${getReputationColor(node.trust_score)}`}>
                            {(node.trust_score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Reputation:</span>
                          <span className={`font-medium ${getReputationColor(node.reputation)}`}>
                            {(node.reputation * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Arbitrators Tab */}
            {activeTab === 'arbitrators' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Dispute Resolution Arbitrators</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {arbitrators.map((arbitrator) => (
                    <div key={arbitrator.arbitrator_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium text-gray-900">{arbitrator.name}</h4>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          arbitrator.is_available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {arbitrator.is_available ? 'AVAILABLE' : 'BUSY'}
                        </span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-gray-500">Expertise:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {arbitrator.expertise_areas.map((area, index) => (
                              <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                {area.replace('_', ' ')}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Success Rate:</span>
                          <span className={`font-medium ${getReputationColor(arbitrator.resolution_success_rate)}`}>
                            {(arbitrator.resolution_success_rate * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Cases Handled:</span>
                          <span className="font-medium">{arbitrator.total_cases_handled}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Neutrality Score:</span>
                          <span className={`font-medium ${getReputationColor(arbitrator.neutrality_score)}`}>
                            {(arbitrator.neutrality_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Demo Tab */}
            {activeTab === 'demo' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Live Algorithm Demonstration</h3>
                <div className="space-y-6">
                  {/* SCC Algorithm Demo */}
                  <div className="border rounded-lg p-6 bg-blue-50">
                    <h4 className="text-lg font-medium text-blue-900 mb-3">
                      🔗 Algorithm 3: Supply Chain Consensus Demo
                    </h4>
                    <p className="text-blue-700 mb-4">
                      Test the SCC algorithm by creating a transaction batch for Primary Node validation.
                    </p>
                    <button
                      onClick={createSampleBatch}
                      disabled={loading}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Creating Batch...' : 'Create Sample Transaction Batch'}
                    </button>
                    <div className="mt-4 text-sm text-blue-600">
                      <p><strong>Process:</strong> Secondary Node creates batch → Primary Nodes validate → Supermajority consensus → Commit/Reject</p>
                    </div>
                  </div>

                  {/* Dispute Resolution Demo */}
                  <div className="border rounded-lg p-6 bg-purple-50">
                    <h4 className="text-lg font-medium text-purple-900 mb-3">
                      ⚖️ Algorithm 2: Dispute Resolution Demo
                    </h4>
                    <p className="text-purple-700 mb-4">
                      Test the dispute resolution algorithm by initiating a sample product quality dispute.
                    </p>
                    <button
                      onClick={initiateSampleDispute}
                      disabled={loading}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Initiating Dispute...' : 'Initiate Sample Product Quality Dispute'}
                    </button>
                    <div className="mt-4 text-sm text-purple-600">
                      <p><strong>Process:</strong> Dispute arises → Stakeholder voting → Arbitrator selection → Evidence review → Decision execution</p>
                    </div>
                  </div>

                  {/* Algorithm Features */}
                  <div className="border rounded-lg p-6 bg-green-50">
                    <h4 className="text-lg font-medium text-green-900 mb-3">
                      ✨ Enhanced Features from Narayanan et al. Paper
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <h5 className="font-medium text-green-800 mb-2">SCC Algorithm Features:</h5>
                        <ul className="space-y-1 text-green-700">
                          <li>• Primary/Secondary node classification</li>
                          <li>• Stake and trust-based validation</li>
                          <li>• Supermajority threshold (67%)</li>
                          <li>• NFT and blockchain verification</li>
                          <li>• Automated rewards and penalties</li>
                          <li>• Periodic reconciliation</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-green-800 mb-2">Dispute Resolution Features:</h5>
                        <ul className="space-y-1 text-green-700">
                          <li>• Weighted stakeholder voting</li>
                          <li>• Neutral arbitrator requirement</li>
                          <li>• Expertise-based arbitrator selection</li>
                          <li>• Multi-type evidence support</li>
                          <li>• Automated decision execution</li>
                          <li>• Reputation-based scoring</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedConsensusDemo;