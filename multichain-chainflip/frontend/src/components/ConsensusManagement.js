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
  Layers
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
      case 'approved': return 'text-green-600 bg-green-100';
      case 'rejected': return 'text-red-600 bg-red-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Layers className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Total Batches</p>
              <p className="text-2xl font-bold text-gray-900">{consensusStats?.total_batches || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Approved Batches</p>
              <p className="text-2xl font-bold text-gray-900">{consensusStats?.approved_batches || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Truck className="h-8 w-8 text-purple-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Total Shipments</p>
              <p className="text-2xl font-bold text-gray-900">{consensusStats?.total_shipments || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Vote className="h-8 w-8 text-indigo-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Consensus Votes</p>
              <p className="text-2xl font-bold text-gray-900">{consensusStats?.consensus_votes || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Approval Rate */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">📊 Consensus Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Batch Approval Rate</span>
              <span className="text-sm text-gray-900">{(consensusStats?.approval_rate || 0).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-600 h-2 rounded-full" 
                style={{ width: `${consensusStats?.approval_rate || 0}%` }}
              ></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Avg Votes per Shipment</span>
              <span className="text-sm text-gray-900">{(consensusStats?.average_votes_per_shipment || 0).toFixed(1)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full" 
                style={{ width: `${Math.min((consensusStats?.average_votes_per_shipment || 0) * 20, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderShipmentsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">🚛 Shipments Requiring Consensus</h3>
        <button
          onClick={loadConsensusData}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {shipments.length === 0 ? (
        <div className="text-center py-12">
          <Truck className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No shipments found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Create a shipment from the Product Management page to start consensus voting.
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {shipments.map((shipment) => (
              <li key={shipment.shipment_id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Package className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-indigo-600">
                          {shipment.shipment_id}
                        </p>
                        <p className="text-sm text-gray-500">
                          {shipment.start_location} → {shipment.end_location}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getShipmentStatusColor(shipment.status)}`}>
                        {shipment.status || 'pending'}
                      </span>
                      {shipment.status !== 'approved' && shipment.status !== 'rejected' && (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => openVoteModal(shipment)}
                            className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                          >
                            <Vote className="h-3 w-3 mr-1" />
                            Vote
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 text-sm text-gray-700">
                    <p><strong>Distance:</strong> {shipment.distance || 0} km</p>
                    <p><strong>Transport Fee:</strong> ${shipment.transport_fee || 0}</p>
                    <p><strong>Votes:</strong> {shipment.consensus_votes?.length || 0}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  const renderBatchProcessingTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">⚡ Batch Processing ({userRole === 'admin' ? 'Primary Node' : 'Secondary Node'})</h3>
        <div className="flex space-x-2">
          <button
            onClick={addTransactionToBatch}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
          >
            Add Transaction
          </button>
          <button
            onClick={handleCreateBatch}
            disabled={batchTransactions.length === 0 || loading}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
          >
            {userRole === 'admin' ? 'Validate Batch' : 'Propose Batch'}
          </button>
        </div>
      </div>

      {/* Current Batch */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Current Batch ({batchTransactions.length} transactions)</h4>
        {batchTransactions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No transactions in current batch. Click "Add Transaction" to start.</p>
        ) : (
          <div className="space-y-2">
            {batchTransactions.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium">{tx.type}: {tx.product_id}</p>
                  <p className="text-xs text-gray-500">{tx.from.substring(0, 10)}... → {tx.to.substring(0, 10)}...</p>
                </div>
                <button
                  onClick={() => removeTransactionFromBatch(tx.id)}
                  className="text-red-600 hover:text-red-800"
                >
                  <XCircle className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Batches */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Recent Batches</h4>
        {batches.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No batches found.</p>
        ) : (
          <div className="space-y-3">
            {batches.slice(0, 10).map((batch) => (
              <div key={batch.batch_id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{batch.batch_id}</p>
                  <p className="text-xs text-gray-500">
                    {batch.transactions?.length || 0} transactions • {batch.node_type} node
                  </p>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  batch.consensus_reached ? 'text-green-600 bg-green-100' : 
                  batch.status === 'proposed' ? 'text-yellow-600 bg-yellow-100' : 'text-gray-600 bg-gray-100'
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
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          ⚡ Algorithm 3: Supply Chain Consensus
        </h1>
        <p className="text-gray-600">
          Batch processing with federated learning validation for supply chain transactions
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
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
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <IconComponent className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <p className="mt-2 text-gray-600">Loading consensus data...</p>
        </div>
      )}

      {!loading && (
        <>
          {activeTab === 'overview' && renderOverviewTab()}
          {activeTab === 'shipments' && renderShipmentsTab()}
          {activeTab === 'batches' && renderBatchProcessingTab()}
        </>
      )}

      {/* Vote Modal */}
      {showVoteModal && selectedShipment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Vote on Shipment: {selectedShipment.shipment_id}
            </h3>
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                <strong>Route:</strong> {selectedShipment.start_location} → {selectedShipment.end_location}
              </p>
              <p className="text-sm text-gray-600">
                <strong>Distance:</strong> {selectedShipment.distance} km
              </p>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason for your vote:
              </label>
              <textarea
                value={voteReason}
                onChange={(e) => setVoteReason(e.target.value)}
                rows={3}
                className="w-full p-3 border border-gray-300 rounded-lg"
                placeholder="Explain your reasoning for approving or rejecting this shipment..."
              />
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => handleVoteSubmission(selectedShipment.shipment_id, true)}
                disabled={loading || !voteReason.trim()}
                className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Approve
              </button>
              <button
                onClick={() => handleVoteSubmission(selectedShipment.shipment_id, false)}
                disabled={loading || !voteReason.trim()}
                className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400"
              >
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </button>
            </div>
            <button
              onClick={() => {
                setShowVoteModal(false);
                setSelectedShipment(null);
                setVoteReason('');
              }}
              className="w-full mt-3 inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
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