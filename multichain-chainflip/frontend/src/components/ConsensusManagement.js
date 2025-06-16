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
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {shipments.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Truck className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No shipments found</h3>
          <p className="text-sm text-gray-500">
            Create a shipment from the Product Management page to start consensus voting.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="divide-y divide-gray-200">
            {shipments.map((shipment) => (
              <div key={shipment.shipment_id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                      <Package className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-blue-600">
                        {shipment.shipment_id}
                      </p>
                      <p className="text-sm text-gray-500">
                        {shipment.start_location} → {shipment.end_location}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getShipmentStatusColor(shipment.status)}`}>
                      {shipment.status || 'pending'}
                    </span>
                    {shipment.status !== 'approved' && shipment.status !== 'rejected' && (
                      <button
                        onClick={() => openVoteModal(shipment)}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        <Vote className="w-4 h-4 mr-2" />
                        Vote
                      </button>
                    )}
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Distance:</span>
                    <span className="ml-2 font-medium">{shipment.distance || 0} km</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Transport Fee:</span>
                    <span className="ml-2 font-medium">${shipment.transport_fee || 0}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Votes:</span>
                    <span className="ml-2 font-medium">{shipment.consensus_votes?.length || 0}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderBatchProcessingTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Batch Processing ({userRole === 'admin' ? 'Primary Node' : 'Secondary Node'})
          </h3>
          <p className="text-sm text-gray-600">
            Process transaction batches for consensus validation
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={addTransactionToBatch}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Transaction
          </button>
          <button
            onClick={handleCreateBatch}
            disabled={batchTransactions.length === 0 || loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            <Layers className="w-4 h-4 mr-2" />
            {userRole === 'admin' ? 'Validate Batch' : 'Propose Batch'}
          </button>
        </div>
      </div>

      {/* Current Batch */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
          <Target className="w-5 h-5 mr-2" />
          Current Batch ({batchTransactions.length} transactions)
        </h4>
        {batchTransactions.length === 0 ? (
          <div className="text-center py-8">
            <Layers className="mx-auto h-10 w-10 text-gray-300 mb-3" />
            <p className="text-gray-500">No transactions in current batch.</p>
            <p className="text-sm text-gray-400 mt-1">Click "Add Transaction" to start building a batch.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {batchTransactions.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{tx.type}: {tx.product_id}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    From: {tx.from.substring(0, 10)}... → To: {tx.to.substring(0, 10)}...
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(tx.timestamp).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => removeTransactionFromBatch(tx.id)}
                  className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Batches */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
          <Clock className="w-5 h-5 mr-2" />
          Recent Batches
        </h4>
        {batches.length === 0 ? (
          <div className="text-center py-8">
            <Layers className="mx-auto h-10 w-10 text-gray-300 mb-3" />
            <p className="text-gray-500">No batches found.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {batches.slice(0, 10).map((batch) => (
              <div key={batch.batch_id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    batch.consensus_reached ? 'bg-green-500' : 
                    batch.status === 'proposed' ? 'bg-yellow-500' : 'bg-gray-500'
                  }`}></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{batch.batch_id}</p>
                    <p className="text-xs text-gray-500">
                      {batch.transactions?.length || 0} transactions • {batch.node_type} node
                    </p>
                  </div>
                </div>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                  batch.consensus_reached ? 'bg-green-100 text-green-800' : 
                  batch.status === 'proposed' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {batch.consensus_reached ? 'Approved' : batch.status}
                </span>
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
                Algorithm 3: Supply Chain Consensus
              </h1>
              <p className="text-indigo-100 mt-2 text-lg">
                Batch processing with federated learning validation for supply chain transactions
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg">
                <div className="text-sm font-medium">Node Type</div>
                <div className="text-lg font-bold">
                  {userRole === 'admin' ? 'Primary' : 'Secondary'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'overview', name: 'Overview', icon: BarChart3 },
              { id: 'shipments', name: 'Consensus Voting', icon: Vote },
              { id: 'batches', name: 'Batch Processing', icon: Layers }
            ].map((tab) => {
              const IconComponent = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <IconComponent className="w-4 h-4 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        {loading && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-4"></div>
            <p className="text-gray-600">Loading consensus data...</p>
          </div>
        )}

        {!loading && (
          <>
            {activeTab === 'overview' && renderOverviewTab()}
            {activeTab === 'shipments' && renderShipmentsTab()}
            {activeTab === 'batches' && renderBatchProcessingTab()}
          </>
        )}
      </div>

      {/* Vote Modal */}
      {showVoteModal && selectedShipment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <Vote className="w-6 h-6 text-indigo-600 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">
                Vote on Shipment
              </h3>
            </div>
            
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-900 mb-2">
                {selectedShipment.shipment_id}
              </p>
              <p className="text-sm text-gray-600 mb-1">
                <strong>Route:</strong> {selectedShipment.start_location} → {selectedShipment.end_location}
              </p>
              <p className="text-sm text-gray-600">
                <strong>Distance:</strong> {selectedShipment.distance} km
              </p>
            </div>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason for your vote:
              </label>
              <textarea
                value={voteReason}
                onChange={(e) => setVoteReason(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Explain your reasoning for approving or rejecting this shipment..."
              />
            </div>
            
            <div className="flex space-x-3 mb-4">
              <button
                onClick={() => handleVoteSubmission(selectedShipment.shipment_id, true)}
                disabled={loading || !voteReason.trim()}
                className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Approve
              </button>
              <button
                onClick={() => handleVoteSubmission(selectedShipment.shipment_id, false)}
                disabled={loading || !voteReason.trim()}
                className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
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