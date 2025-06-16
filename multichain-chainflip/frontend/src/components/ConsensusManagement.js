/**
 * Algorithm 3: Supply Chain Consensus Management Component
 * Implements batch processing and consensus voting UI for ChainFLIP
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import blockchainService from '../services/blockchainService';
import { 
  Vote, 
  Package, 
  Truck, 
  Users, 
  CheckCircle, 
  XCircle,
  Clock,
  BarChart3,
  RefreshCw,
  AlertCircle,
  Target,
  Layers,
  Plus,
  Trash2,
  Award,
  Shield
} from 'lucide-react';

const ConsensusManagement = () => {
  const { user, userRole } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [consensusStats, setConsensusStats] = useState(null);
  const [shipments, setShipments] = useState([]);
  const [batches, setBatches] = useState([]);
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [voteReason, setVoteReason] = useState('');
  const [showVoteModal, setShowVoteModal] = useState(false);
  const [batchTransactions, setBatchTransactions] = useState([]);

  useEffect(() => {
    loadConsensusData();
  }, []);

  const loadConsensusData = async () => {
    try {
      setLoading(true);
      // Mock data for Algorithm 3 demonstration
      const mockStats = {
        total_batches: 15,
        approved_batches: 12,
        approval_rate: 80,
        total_shipments: 28,
        consensus_votes: 45,
        average_votes_per_shipment: 1.6
      };
      
      const mockShipments = [
        {
          shipment_id: 'SHIP-1701234567-1234',
          start_location: 'Shanghai Factory',
          end_location: 'Los Angeles Port',
          distance: 11000,
          transport_fee: 1200,
          status: 'pending',
          consensus_votes: []
        },
        {
          shipment_id: 'SHIP-1701234568-5678',
          start_location: 'Berlin Warehouse',
          end_location: 'Frankfurt Distribution',
          distance: 550,
          transport_fee: 150,
          status: 'approved',
          consensus_votes: [1, 2, 3]
        }
      ];

      const mockBatches = [
        {
          batch_id: 'BATCH-1701234567',
          transactions: [{}, {}, {}],
          node_type: 'secondary',
          status: 'proposed',
          consensus_reached: false
        },
        {
          batch_id: 'BATCH-1701234566',
          transactions: [{}, {}],
          node_type: 'primary',
          status: 'validated',
          consensus_reached: true
        }
      ];
      
      setConsensusStats(mockStats);
      setShipments(mockShipments);
      setBatches(mockBatches);
    } catch (error) {
      console.error('Error loading consensus data:', error);
      alert(`Error loading data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleVoteSubmission = async (shipmentId, approve) => {
    if (!voteReason.trim()) {
      alert('Please provide a reason for your vote');
      return;
    }

    try {
      setLoading(true);
      
      // Mock vote submission
      alert(`✅ Vote submitted successfully!\n\nShipment: ${shipmentId}\nDecision: ${approve ? 'APPROVED' : 'REJECTED'}\nReason: ${voteReason}`);
      
      await loadConsensusData();
      setShowVoteModal(false);
      setVoteReason('');
      setSelectedShipment(null);
    } catch (error) {
      console.error('Voting error:', error);
      alert(`❌ Voting error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBatch = async () => {
    if (batchTransactions.length === 0) {
      alert('Please add at least one transaction to the batch');
      return;
    }

    try {
      setLoading(true);
      
      const batchId = `BATCH-${Date.now()}`;
      alert(`✅ Batch ${userRole === 'admin' ? 'validated' : 'proposed'}!\n\nBatch ID: ${batchId}\nTransactions: ${batchTransactions.length}\nNode Type: ${userRole === 'admin' ? 'Primary' : 'Secondary'}`);
      
      await loadConsensusData();
      setBatchTransactions([]);
    } catch (error) {
      console.error('Batch processing error:', error);
      alert(`❌ Batch processing error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const openVoteModal = (shipment) => {
    setSelectedShipment(shipment);
    setShowVoteModal(true);
    setVoteReason('');
  };

  const addTransactionToBatch = () => {
    const newTransaction = {
      id: `tx_${Date.now()}`,
      type: 'shipment',
      product_id: `PROD_${Math.floor(Math.random() * 10000)}`,
      from: user?.wallet_address || 'unknown',
      to: '0x' + Math.random().toString(16).substring(2, 42),
      timestamp: Date.now()
    };
    setBatchTransactions([...batchTransactions, newTransaction]);
  };

  const removeTransactionFromBatch = (txId) => {
    setBatchTransactions(batchTransactions.filter(tx => tx.id !== txId));
  };

  const getShipmentStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const renderOverviewTab = () => (
    <div className="space-y-8">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Layers className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Batches</p>
              <p className="text-2xl font-bold text-gray-900">{consensusStats?.total_batches || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Approved Batches</p>
              <p className="text-2xl font-bold text-gray-900">{consensusStats?.approved_batches || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Truck className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Shipments</p>
              <p className="text-2xl font-bold text-gray-900">{consensusStats?.total_shipments || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                <Vote className="w-6 h-6 text-indigo-600" />
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Consensus Votes</p>
              <p className="text-2xl font-bold text-gray-900">{consensusStats?.consensus_votes || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2" />
          Consensus Performance
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium text-gray-600">Batch Approval Rate</span>
              <span className="text-sm font-bold text-gray-900">{(consensusStats?.approval_rate || 0).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full transition-all duration-500" 
                style={{ width: `${consensusStats?.approval_rate || 0}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-2">Higher approval rates indicate efficient consensus</p>
          </div>
          <div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium text-gray-600">Avg Votes per Shipment</span>
              <span className="text-sm font-bold text-gray-900">{(consensusStats?.average_votes_per_shipment || 0).toFixed(1)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-blue-400 to-blue-600 h-3 rounded-full transition-all duration-500" 
                style={{ width: `${Math.min((consensusStats?.average_votes_per_shipment || 0) * 20, 100)}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-2">More votes indicate active network participation</p>
          </div>
        </div>
      </div>

      {/* Network Health */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
          <Shield className="w-5 h-5 mr-2" />
          Network Health Status
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <div className="text-lg font-bold text-green-600 mb-1">Operational</div>
            <div className="text-sm text-green-700">Consensus Engine</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <Users className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <div className="text-lg font-bold text-blue-600 mb-1">Active</div>
            <div className="text-sm text-blue-700">Federated Learning</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <Award className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <div className="text-lg font-bold text-purple-600 mb-1">Validated</div>
            <div className="text-sm text-purple-700">Supply Chain Integrity</div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderShipmentsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Shipments Requiring Consensus</h3>
          <p className="text-sm text-gray-600">Vote on shipments to validate supply chain operations</p>
        </div>
        <button
          onClick={loadConsensusData}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        {shipments.length === 0 ? (
          <div className="text-center py-8">
            <Package className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No shipments</h3>
            <p className="mt-1 text-sm text-gray-500">No shipments requiring consensus at this time</p>
          </div>
        ) : (
          <div className="space-y-4">
            {shipments.map((shipment, index) => (
              <div key={shipment.shipment_id || index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-medium text-gray-900">{shipment.shipment_id}</div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getShipmentStatusColor(shipment.status)}`}>
                    {shipment.status}
                  </span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <span className="text-sm text-gray-500">From:</span>
                    <div className="font-medium">{shipment.start_location}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">To:</span>
                    <div className="font-medium">{shipment.end_location}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Fee:</span>
                    <div className="font-medium">${shipment.transport_fee}</div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Distance: {shipment.distance} km | Votes: {shipment.consensus_votes?.length || 0}
                  </div>
                  
                  {shipment.status === 'pending' && (
                    <button
                      onClick={() => openVoteModal(shipment)}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <Vote className="w-4 h-4 mr-1" />
                      Vote
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderBatchesTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Transaction Batch Processing</h3>
          <p className="text-sm text-gray-600">Create and validate transaction batches</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={addTransactionToBatch}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Transaction
          </button>
          <button
            onClick={handleCreateBatch}
            disabled={batchTransactions.length === 0 || loading}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            <Target className="w-4 h-4 mr-2" />
            {userRole === 'admin' ? 'Validate Batch' : 'Propose Batch'}
          </button>
        </div>
      </div>

      {/* Pending Batch */}
      {batchTransactions.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Pending Batch ({batchTransactions.length} transactions)
          </h4>
          
          <div className="space-y-3 mb-6">
            {batchTransactions.map((tx, index) => (
              <div key={tx.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{tx.type} - {tx.product_id}</div>
                  <div className="text-sm text-gray-500">{tx.from.substring(0, 10)}... → {tx.to.substring(0, 10)}...</div>
                </div>
                <button
                  onClick={() => removeTransactionFromBatch(tx.id)}
                  className="text-red-600 hover:text-red-800"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm text-blue-800">
              <strong>Node Type:</strong> {userRole === 'admin' ? 'Primary Node (Can validate directly)' : 'Secondary Node (Requires approval)'}
            </div>
          </div>
        </div>
      )}

      {/* Existing Batches */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Recent Batches</h4>
        
        {batches.length === 0 ? (
          <div className="text-center py-8">
            <Layers className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No batches</h3>
            <p className="mt-1 text-sm text-gray-500">No transaction batches created yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {batches.map((batch, index) => (
              <div key={batch.batch_id || index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-medium text-gray-900">{batch.batch_id}</div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      batch.status === 'validated' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {batch.status}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      batch.node_type === 'primary' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {batch.node_type}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <div>Transactions: {batch.transactions?.length || 0}</div>
                  <div className="flex items-center">
                    {batch.consensus_reached ? (
                      <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500 mr-1" />
                    )}
                    Consensus: {batch.consensus_reached ? 'Reached' : 'Pending'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Modern Header with Gradient */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div className="px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center">
                <Vote className="w-8 h-8 mr-3" />
                Consensus Management
              </h1>
              <p className="text-indigo-100 mt-2 text-lg">
                Supply chain consensus voting and batch transaction processing with federated learning
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={loadConsensusData}
                className="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg shadow-sm text-sm font-medium text-white hover:bg-white/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Navigation Tabs */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1">
            <nav className="flex space-x-1">
              <button
                onClick={() => setActiveTab('overview')}
                className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === 'overview'
                    ? 'bg-indigo-500 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                📊 Overview
              </button>
              <button
                onClick={() => setActiveTab('shipments')}
                className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === 'shipments'
                    ? 'bg-indigo-500 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                🚛 Shipments
              </button>
              <button
                onClick={() => setActiveTab('batches')}
                className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === 'batches'
                    ? 'bg-indigo-500 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                📦 Batches
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <p className="mt-2 text-gray-600">Loading consensus data...</p>
          </div>
        )}

        {!loading && activeTab === 'overview' && renderOverviewTab()}
        {!loading && activeTab === 'shipments' && renderShipmentsTab()}
        {!loading && activeTab === 'batches' && renderBatchesTab()}
      </div>

      {/* Vote Modal */}
      {showVoteModal && selectedShipment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Vote on Shipment: {selectedShipment.shipment_id}
            </h3>
            
            <div className="mb-4">
              <div className="text-sm text-gray-600 space-y-1">
                <div><strong>From:</strong> {selectedShipment.start_location}</div>
                <div><strong>To:</strong> {selectedShipment.end_location}</div>
                <div><strong>Distance:</strong> {selectedShipment.distance} km</div>
                <div><strong>Fee:</strong> ${selectedShipment.transport_fee}</div>
              </div>
            </div>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason for your vote:
              </label>
              <textarea
                value={voteReason}
                onChange={(e) => setVoteReason(e.target.value)}
                rows={3}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter your reasoning..."
              />
            </div>
            
            <div className="grid grid-cols-2 gap-3 mb-4">
              <button
                onClick={() => handleVoteSubmission(selectedShipment.shipment_id, true)}
                disabled={loading || !voteReason.trim()}
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Approve
              </button>
              <button
                onClick={() => handleVoteSubmission(selectedShipment.shipment_id, false)}
                disabled={loading || !voteReason.trim()}
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                <XCircle className="w-4 h-4 mr-2" />
                Reject
              </button>
            </div>
            
            <button
              onClick={() => {
                setShowVoteModal(false);
                setSelectedShipment(null);
                setVoteReason('');
              }}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConsensusManagement;