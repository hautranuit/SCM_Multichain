import React, { useState, useEffect } from 'react';
import { 
  Truck, 
  MapPin, 
  Clock, 
  CheckCircle, 
  Package, 
  Navigation,
  RefreshCw,
  Camera,
  AlertCircle,
  Route,
  Play
} from 'lucide-react';

const TransporterDashboard = () => {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [updateStatus, setUpdateStatus] = useState({});
  const [currentLocation, setCurrentLocation] = useState('');
  const [proofImage, setProofImage] = useState(null);

  // Transporter address - in production this would come from wallet connection
  const transporterAddress = "0x8C1d7fCD3ec5ce7d3a2AEa73D22CE0C6D5Bb84c4"; // Transporter 1

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8001/api/blockchain/delivery/transporter/assignments/${transporterAddress}`);
      if (response.ok) {
        const data = await response.json();
        setAssignments(data.assignments || []);
      } else {
        console.error('Failed to load assignments');
      }
    } catch (error) {
      console.error('Error loading assignments:', error);
    }
    setLoading(false);
  };

  const updateDeliveryStage = async (deliveryRequestId, stageNumber) => {
    if (!currentLocation.trim()) {
      alert('Please enter your current location');
      return;
    }

    setLoading(true);
    setUpdateStatus(prev => ({ ...prev, [deliveryRequestId]: 'updating' }));

    try {
      const response = await fetch('http://localhost:8001/api/blockchain/delivery/transporter/update-stage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          delivery_request_id: deliveryRequestId,
          transporter_address: transporterAddress,
          stage_number: stageNumber,
          current_location: currentLocation,
          proof_image: proofImage?.data || null,
          notes: `Stage ${stageNumber} update from transporter`
        })
      });

      if (response.ok) {
        const result = await response.json();
        setUpdateStatus(prev => ({ ...prev, [deliveryRequestId]: 'success' }));
        alert('Stage update sent successfully!');
        setCurrentLocation('');
        setProofImage(null);
        loadAssignments(); // Refresh assignments
      } else {
        const error = await response.json();
        setUpdateStatus(prev => ({ ...prev, [deliveryRequestId]: 'error' }));
        alert(`Failed to update stage: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error updating stage:', error);
      setUpdateStatus(prev => ({ ...prev, [deliveryRequestId]: 'error' }));
      alert('Error updating delivery stage');
    }
    setLoading(false);
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setCurrentLocation(`${latitude.toFixed(6)}, ${longitude.toFixed(6)}`);
          setLoading(false);
        },
        (error) => {
          console.error('Geolocation error:', error);
          setLoading(false);
          alert('Failed to get current location');
        }
      );
    } else {
      alert('Geolocation is not supported by this browser');
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setProofImage({
          file: file,
          data: reader.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'assigned': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'in_transit': return <Truck className="w-4 h-4 text-blue-500" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return <Package className="w-4 h-4 text-gray-500" />;
    }
  };

  const getUpdateStatusIcon = (deliveryId) => {
    const status = updateStatus[deliveryId];
    switch (status) {
      case 'updating': return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Play className="w-4 h-4" />;
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transporter Dashboard</h1>
          <p className="text-gray-600">Manage your delivery assignments and update status</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={loadAssignments}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <div className="text-sm text-gray-600">
            <Truck className="w-4 h-4 inline mr-1" />
            {transporterAddress.slice(0, 8)}...{transporterAddress.slice(-6)}
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Assignments</p>
              <p className="text-2xl font-bold text-blue-600">
                {assignments.filter(a => a.status !== 'completed').length}
              </p>
            </div>
            <Truck className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">In Transit</p>
              <p className="text-2xl font-bold text-yellow-600">
                {assignments.filter(a => a.status === 'in_transit').length}
              </p>
            </div>
            <Navigation className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-green-600">
                {assignments.filter(a => a.status === 'completed').length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
      </div>

      {/* Assignments List */}
      <div className="bg-white border rounded-lg shadow-sm">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Your Delivery Assignments</h2>
        </div>

        <div className="p-4">
          {assignments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No assignments found</p>
              <p className="text-sm">Check back later for new delivery requests</p>
            </div>
          ) : (
            <div className="space-y-4">
              {assignments.map((assignment) => (
                <div key={assignment.delivery_request_id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium text-gray-900">
                        Delivery #{assignment.delivery_request_id}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Stage {assignment.stage_number} of {assignment.total_stages}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(assignment.status)}
                      <span className="text-sm font-medium capitalize">
                        {assignment.status?.replace('_', ' ')}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                    <div>
                      <span className="font-medium">Product ID:</span>
                      <p>{assignment.product_id}</p>
                    </div>
                    <div>
                      <span className="font-medium">Priority:</span>
                      <p className="capitalize">{assignment.delivery_priority || 'standard'}</p>
                    </div>
                    <div>
                      <span className="font-medium">Route:</span>
                      <p>{assignment.current_location} → {assignment.next_location}</p>
                    </div>
                    <div>
                      <span className="font-medium">ETA:</span>
                      <p>{assignment.estimated_completion || 'TBD'}</p>
                    </div>
                  </div>

                  {assignment.route_locations && (
                    <div className="mb-4">
                      <span className="text-sm font-medium text-gray-700">Full Route:</span>
                      <div className="mt-1 text-sm text-gray-600">
                        {assignment.route_locations.join(' → ')}
                      </div>
                    </div>
                  )}

                  {assignment.status !== 'completed' && (
                    <div className="border-t pt-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Update Delivery Status</h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Current Location
                          </label>
                          <div className="flex space-x-2">
                            <input
                              type="text"
                              value={currentLocation}
                              onChange={(e) => setCurrentLocation(e.target.value)}
                              placeholder="Enter current location or coordinates"
                              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
                            />
                            <button
                              onClick={getCurrentLocation}
                              className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                              disabled={loading}
                            >
                              <MapPin className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Proof Image (Optional)
                          </label>
                          <div className="flex items-center space-x-2">
                            <input
                              type="file"
                              accept="image/*"
                              onChange={handleImageUpload}
                              className="hidden"
                              id={`image-${assignment.delivery_request_id}`}
                            />
                            <label
                              htmlFor={`image-${assignment.delivery_request_id}`}
                              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer text-sm"
                            >
                              <Camera className="w-4 h-4" />
                              <span>{proofImage ? 'Image Selected' : 'Upload Image'}</span>
                            </label>
                          </div>
                        </div>
                      </div>

                      <div className="flex justify-between items-center">
                        <button
                          onClick={() => setSelectedAssignment(assignment)}
                          className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                        >
                          <Route className="w-4 h-4" />
                          <span>View Details</span>
                        </button>

                        <button
                          onClick={() => updateDeliveryStage(assignment.delivery_request_id, assignment.stage_number)}
                          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                          disabled={loading || updateStatus[assignment.delivery_request_id] === 'updating' || !currentLocation.trim()}
                        >
                          {getUpdateStatusIcon(assignment.delivery_request_id)}
                          <span>
                            {updateStatus[assignment.delivery_request_id] === 'updating' 
                              ? 'Updating...' 
                              : `Update Stage ${assignment.stage_number}`
                            }
                          </span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Assignment Details Modal */}
      {selectedAssignment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Assignment Details</h2>
                <button
                  onClick={() => setSelectedAssignment(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Delivery Request ID</label>
                  <p className="text-sm text-gray-900">{selectedAssignment.delivery_request_id}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Product ID</label>
                    <p className="text-sm text-gray-900">{selectedAssignment.product_id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Status</label>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(selectedAssignment.status)}
                      <span className="text-sm capitalize">
                        {selectedAssignment.status?.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Your Stage</label>
                    <p className="text-sm text-gray-900">
                      {selectedAssignment.stage_number} of {selectedAssignment.total_stages}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Priority</label>
                    <p className="text-sm text-gray-900 capitalize">
                      {selectedAssignment.delivery_priority || 'standard'}
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Route Segment</label>
                  <p className="text-sm text-gray-900">
                    {selectedAssignment.current_location} → {selectedAssignment.next_location}
                  </p>
                </div>

                {selectedAssignment.route_locations && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Complete Route</label>
                    <div className="bg-gray-50 p-3 rounded text-sm">
                      {selectedAssignment.route_locations.map((location, index) => (
                        <div key={index} className={`flex items-center ${
                          index === selectedAssignment.stage_number - 1 ? 'font-bold text-blue-600' : ''
                        }`}>
                          <div className={`w-3 h-3 rounded-full mr-3 ${
                            index < selectedAssignment.stage_number - 1 ? 'bg-green-500' :
                            index === selectedAssignment.stage_number - 1 ? 'bg-blue-500' : 'bg-gray-300'
                          }`}></div>
                          {location}
                          {index === selectedAssignment.stage_number - 1 && (
                            <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              YOUR STAGE
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700">Estimated Completion</label>
                  <p className="text-sm text-gray-900">{selectedAssignment.estimated_completion || 'TBD'}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Assignment Time</label>
                  <p className="text-sm text-gray-900">
                    {selectedAssignment.timestamp ? new Date(selectedAssignment.timestamp * 1000).toLocaleString() : 'N/A'}
                  </p>
                </div>

                {selectedAssignment.special_instructions && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Special Instructions</label>
                    <p className="text-sm text-gray-900 bg-yellow-50 p-2 rounded">
                      {selectedAssignment.special_instructions}
                    </p>
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

export default TransporterDashboard;
