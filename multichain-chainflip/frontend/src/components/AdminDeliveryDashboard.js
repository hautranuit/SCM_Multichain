import React, { useState, useEffect } from 'react';
import { 
  Package, 
  Truck, 
  MapPin, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Users, 
  Play,
  RefreshCw,
  Eye,
  Settings,
  Activity
} from 'lucide-react';

const AdminDeliveryDashboard = () => {
  const [deliveryRequests, setDeliveryRequests] = useState([]);
  const [transporters, setTransporters] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [activeTab, setActiveTab] = useState('requests');
  const [simulationStatus, setSimulationStatus] = useState({});

  // Admin address - in production this would come from wallet connection
  const adminAddress = "0x032041b4b356fEE1496805DD4749f181bC736FFA";

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load delivery requests
      const requestsResponse = await fetch('http://localhost:8001/api/blockchain/delivery/admin/requests');
      if (requestsResponse.ok) {
        const requestsData = await requestsResponse.json();
        setDeliveryRequests(requestsData.delivery_requests || []);
      }

      // Load transporters
      const transportersResponse = await fetch('http://localhost:8001/api/blockchain/delivery/admin/transporters');
      if (transportersResponse.ok) {
        const transportersData = await transportersResponse.json();
        setTransporters(transportersData.transporters || []);
      }

      // Load dashboard stats
      const dashboardResponse = await fetch('http://localhost:8001/api/blockchain/delivery/admin/dashboard');
      if (dashboardResponse.ok) {
        const dashboardData = await dashboardResponse.json();
        // Extract statistics from the response
        setDashboardStats(dashboardData.statistics || dashboardData);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
    setLoading(false);
  };

  const assignTransporters = async (deliveryRequestId, requestData = null) => {
    const currentRequest = requestData || selectedRequest;
    if (!currentRequest) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/blockchain/delivery/admin/assign-transporters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          delivery_request_id: deliveryRequestId,
          admin_address: adminAddress,
          delivery_distance_miles: currentRequest.delivery_distance_miles || 150
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        // Check the cross_chain_success flag for precise error handling
        if (result.cross_chain_success === false) {
          // Show warning message for cross-chain failures
          const warningMessage = `⚠️ Chỉ định transporter thành công (cục bộ) nhưng có lỗi cross-chain!
          
🚚 Transporter: ${result.transporter_name || 'ChainFLIP Express Delivery'}
📧 Email: ${result.transporter_email || 'hau322004hd@gmail.com'}
🏠 Address: ${result.transporter_address || '0x04351e7dF40d04B5E610c4aA033faCf435b98711'}

❌ Cross-chain message failed: ${result.warning || 'Unknown error'}
🔍 Error Type: ${result.error_type || 'Unknown'}

⚠️ Transporter đã được chỉ định trong database nhưng chưa nhận được thông báo qua blockchain.
📞 Vui lòng liên hệ trực tiếp với transporter hoặc thử lại sau.

📍 Pickup: 12 Nguyen Trai Street, District 1, Ho Chi Minh City
📍 Delivery: 45 Le Loi Street, Hai Ba Trung District, Hanoi`;

          alert(warningMessage);
        } else if (result.cross_chain_success === true && result.cross_chain_tx) {
          // Show success message for complete success
          const successMessage = `✅ Chỉ định transporter thành công!
          
🚚 Transporter: ${result.transporter_name || 'ChainFLIP Express Delivery'}
📧 Email: ${result.transporter_email || 'hau322004hd@gmail.com'}
🏠 Address: ${result.transporter_address || '0x04351e7dF40d04B5E610c4aA033faCf435b98711'}
⛓️ Chain: Arbitrum Sepolia

🌐 Cross-chain message sent successfully!
🔗 Transaction: ${result.cross_chain_tx}
💰 LayerZero Fee: ${result.layerzero_fee_paid || 'N/A'} ETH

📍 Pickup: 12 Nguyen Trai Street, District 1, Ho Chi Minh City
📍 Delivery: 45 Le Loi Street, Hai Ba Trung District, Hanoi`;

          alert(successMessage);
        } else {
          // Show partial success message for unclear status
          const partialMessage = `✅ Chỉ định transporter thành công!
          
🚚 Transporter: ${result.transporter_name || 'ChainFLIP Express Delivery'}
📧 Email: ${result.transporter_email || 'hau322004hd@gmail.com'}
🏠 Address: ${result.transporter_address || '0x04351e7dF40d04B5E610c4aA033faCf435b98711'}

⏳ Cross-chain message status: Đang xử lý...

📍 Pickup: 12 Nguyen Trai Street, District 1, Ho Chi Minh City
📍 Delivery: 45 Le Loi Street, Hai Ba Trung District, Hanoi`;

          alert(partialMessage);
        }
        
        loadDashboardData(); // Refresh data
      } else {
        const error = await response.json();
        alert(`Failed to assign transporters: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error assigning transporters:', error);
      alert('Error assigning transporters');
    }
    setLoading(false);
  };

  const simulateDelivery = async (deliveryRequestId, assignedTransporters) => {
    setLoading(true);
    setSimulationStatus(prev => ({ ...prev, [deliveryRequestId]: 'starting' }));

    try {
      const response = await fetch('http://localhost:8001/api/blockchain/delivery/admin/simulate-delivery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          delivery_request_id: deliveryRequestId,
          assigned_transporters: assignedTransporters,
          admin_address: adminAddress
        })
      });

      if (response.ok) {
        const result = await response.json();
        setSimulationStatus(prev => ({ ...prev, [deliveryRequestId]: 'completed' }));
        alert(`Delivery simulation completed!\n${result.message}`);
        loadDashboardData(); // Refresh data
      } else {
        const error = await response.json();
        setSimulationStatus(prev => ({ ...prev, [deliveryRequestId]: 'failed' }));
        alert(`Simulation failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error simulating delivery:', error);
      setSimulationStatus(prev => ({ ...prev, [deliveryRequestId]: 'failed' }));
      alert('Error simulating delivery');
    }
    setLoading(false);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending_assignment': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'assigned': return <Users className="w-4 h-4 text-blue-500" />;
      case 'delivery_in_progress': return <Truck className="w-4 h-4 text-purple-500" />;
      case 'delivered': return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSimulationStatusIcon = (deliveryId) => {
    const status = simulationStatus[deliveryId];
    switch (status) {
      case 'starting': return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Play className="w-4 h-4" />;
    }
  };

  const renderDeliveryRequests = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Delivery Management</h3>
          <p className="text-sm text-gray-600">Delivery requests and FL transporter recommendations</p>
        </div>
        <button
          onClick={loadDashboardData}
          className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {deliveryRequests.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No delivery requests found</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {deliveryRequests.map((request) => (
            <div key={request.delivery_request_id} className="bg-white border rounded-lg p-4 shadow-sm">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-medium text-gray-900">
                    {request.delivery_request_id}
                  </h4>
                  <p className="text-sm text-gray-600">
                    Product: {request.product_name || `Product #${request.product_id}`}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(request.status)}
                  <span className="text-sm font-medium capitalize">
                    {request.status?.replace('_', ' ')}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                <div>
                  <span className="font-medium">Buyer:</span>
                  <p className="truncate">{request.buyer_name || request.buyer_address || request.buyer}</p>
                </div>
                <div>
                  <span className="font-medium">Manufacturer:</span>
                  <p className="truncate">{request.manufacturer_name || request.manufacturer_address || request.manufacturer}</p>
                </div>
                <div>
                  <span className="font-medium">Distance:</span>
                  <p>{request.distance || request.delivery_distance_miles || '80 miles'}</p>
                </div>
                <div>
                  <span className="font-medium">Priority:</span>
                  <p className="capitalize">{request.delivery_priority || 'standard'}</p>
                </div>
              </div>

              {request.assigned_transporters && request.assigned_transporters.length > 0 && (
                <div className="mb-4">
                  <span className="text-sm font-medium text-gray-700">Assigned Transporters:</span>
                  <div className="mt-1 space-y-1">
                    {request.assigned_transporters.map((transporter, index) => (
                      <div key={index} className="text-xs text-gray-600 truncate">
                        Stage {index + 1}: {transporter}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* FL Recommendation Section */}
              {request.fl_recommendation && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center mb-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                    <span className="text-sm font-medium text-blue-900">🤖 FL Recommendation</span>
                    <span className="ml-auto text-xs text-blue-600 font-semibold">
                      {Math.round(request.fl_recommendation.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="text-xs text-blue-800 mb-2">{request.fl_recommendation.reasoning}</p>
                  {request.assigned_transporter && (
                    <div className="text-xs text-blue-700">
                      <p><strong>Recommended:</strong> {request.assigned_transporter.name}</p>
                      <p><strong>Address:</strong> {request.assigned_transporter.address}</p>
                      <p><strong>Specialization:</strong> {request.assigned_transporter.specialization?.join(', ')}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex space-x-2">
                {request.status === 'pending_assignment' && (
                  <button
                    onClick={() => {
                      assignTransporters(request.delivery_request_id, request);
                    }}
                    className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                    disabled={loading}
                  >
                    <Users className="w-4 h-4" />
                    <span>Accept the delivery assignment</span>
                  </button>
                )}

                {request.status === 'assigned' && request.assigned_transporters && (
                  <button
                    onClick={() => simulateDelivery(request.delivery_request_id, request.assigned_transporters)}
                    className="flex items-center space-x-2 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
                    disabled={loading || simulationStatus[request.delivery_request_id] === 'starting'}
                  >
                    {getSimulationStatusIcon(request.delivery_request_id)}
                    <span>
                      {simulationStatus[request.delivery_request_id] === 'starting' ? 'Starting...' : 'Simulate Delivery'}
                    </span>
                  </button>
                )}

                <button
                  onClick={() => setSelectedRequest(request)}
                  className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                >
                  <Eye className="w-4 h-4" />
                  <span>View Details</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderTransporters = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Available Transporters</h3>
      
      {transporters.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Truck className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No transporters available</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {transporters.map((transporter) => (
            <div key={transporter.address} className="bg-white border rounded-lg p-4 shadow-sm">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-medium text-gray-900 truncate">
                    {transporter.name || 'Transporter'}
                  </h4>
                  <p className="text-sm text-gray-600 truncate">
                    {transporter.address}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    transporter.status === 'available' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <span className="text-sm font-medium capitalize">
                    {transporter.status || 'available'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <span className="font-medium">Location:</span>
                  <p>{transporter.current_location || 'N/A'}</p>
                </div>
                <div>
                  <span className="font-medium">Capacity:</span>
                  <p>{transporter.capacity || 'Standard'}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderDashboardStats = () => (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white border rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Total Requests</p>
            <p className="text-2xl font-bold text-gray-900">
              {dashboardStats.total_requests || 0}
            </p>
          </div>
          <Package className="w-8 h-8 text-blue-500" />
        </div>
      </div>

      <div className="bg-white border rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Pending Assignment</p>
            <p className="text-2xl font-bold text-yellow-600">
              {dashboardStats.pending_assignment || 0}
            </p>
          </div>
          <Clock className="w-8 h-8 text-yellow-500" />
        </div>
      </div>

      <div className="bg-white border rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">In Transit</p>
            <p className="text-2xl font-bold text-purple-600">
              {dashboardStats.in_transit || 0}
            </p>
          </div>
          <Truck className="w-8 h-8 text-purple-500" />
        </div>
      </div>

      <div className="bg-white border rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Delivered</p>
            <p className="text-2xl font-bold text-green-600">
              {dashboardStats.delivered || 0}
            </p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-500" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Delivery Dashboard</h1>
          <p className="text-gray-600">Manage delivery requests and transporter assignments</p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Settings className="w-4 h-4" />
          <span>Admin: {adminAddress.slice(0, 8)}...{adminAddress.slice(-6)}</span>
        </div>
      </div>

      {renderDashboardStats()}

      <div className="bg-gray-50 border rounded-lg p-1 mb-6">
        <div className="flex space-x-1">
          <button
            onClick={() => setActiveTab('requests')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'requests'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Package className="w-4 h-4" />
            <span>Delivery Management</span>
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'analytics'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Analytics</span>
          </button>
        </div>
      </div>

      <div>
        {activeTab === 'requests' && renderDeliveryRequests()}
        {activeTab === 'analytics' && (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Analytics dashboard coming soon...</p>
          </div>
        )}
      </div>

      {/* Request Details Modal */}
      {selectedRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Delivery Request Details</h2>
                <button
                  onClick={() => setSelectedRequest(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Request ID</label>
                  <p className="text-sm text-gray-900">{selectedRequest.delivery_request_id}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Product</label>
                    <p className="text-sm text-gray-900">{selectedRequest.product_name || `Product #${selectedRequest.product_id}`}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Token ID</label>
                    <p className="text-sm text-gray-900">{selectedRequest.token_id || selectedRequest.product_id}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Status</label>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(selectedRequest.status)}
                      <span className="text-sm capitalize">
                        {selectedRequest.status?.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Request Time</label>
                    <p className="text-sm text-gray-900">{selectedRequest.request_time || '17:00 28/06/2025'}</p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Buyer</label>
                  <p className="text-sm text-gray-900">{selectedRequest.buyer_name || selectedRequest.buyer_address || selectedRequest.buyer}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Manufacturer</label>
                  <p className="text-sm text-gray-900">{selectedRequest.manufacturer_name || selectedRequest.manufacturer_address || selectedRequest.manufacturer}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Pickup Location</label>
                    <p className="text-sm text-gray-900">{selectedRequest.pickup_location || '12 Nguyen Trai Street, District 1, Ho Chi Minh City'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Delivery Location</label>
                    <p className="text-sm text-gray-900">{selectedRequest.delivery_location || '45 Le Loi Street, Hai Ba Trung District, Hanoi'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Distance</label>
                    <p className="text-sm text-gray-900">{selectedRequest.distance || selectedRequest.delivery_distance_miles || '80 miles'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Priority</label>
                    <p className="text-sm text-gray-900 capitalize">{selectedRequest.delivery_priority || 'standard'}</p>
                  </div>
                </div>

                {selectedRequest.assigned_transporters && selectedRequest.assigned_transporters.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Assigned Transporter</label>
                    <div className="bg-gray-50 p-3 rounded text-sm space-y-2">
                      <p><span className="font-medium">Address:</span> {selectedRequest.assigned_transporters[0]}</p>
                      {selectedRequest.assigned_transporter && (
                        <>
                          <p><span className="font-medium">Name:</span> {selectedRequest.assigned_transporter.name}</p>
                          <p><span className="font-medium">Email:</span> {selectedRequest.assigned_transporter.email}</p>
                          <p><span className="font-medium">Phone:</span> {selectedRequest.assigned_transporter.phone}</p>
                          <p><span className="font-medium">Chain:</span> {selectedRequest.assigned_transporter.chain}</p>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {selectedRequest.delivery_simulation && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Simulation Results</label>
                    <div className="bg-gray-50 p-3 rounded text-sm">
                      <p><span className="font-medium">Status:</span> {selectedRequest.delivery_simulation.final_status}</p>
                      <p><span className="font-medium">Stages Completed:</span> {selectedRequest.delivery_simulation.successful_stages}/{selectedRequest.delivery_simulation.total_stages}</p>
                      <p><span className="font-medium">Message:</span> {selectedRequest.delivery_simulation.message}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDeliveryDashboard;
