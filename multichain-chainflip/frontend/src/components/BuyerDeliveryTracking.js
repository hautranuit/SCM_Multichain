import React, { useState, useEffect } from 'react';
import { 
  Package, 
  Truck, 
  MapPin, 
  Clock, 
  CheckCircle, 
  Bell,
  RefreshCw,
  Route,
  Eye,
  AlertCircle,
  Info
} from 'lucide-react';

const BuyerDeliveryTracking = ({ buyerAddress }) => {
  const [notifications, setNotifications] = useState([]);
  const [deliveryTracking, setDeliveryTracking] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedDelivery, setSelectedDelivery] = useState(null);
  const [activeTab, setActiveTab] = useState('notifications');

  // Use provided buyer address or fallback
  const currentBuyerAddress = buyerAddress || "0x90F79bf6EB2c4f870365E785982E1f101E93b906";

  useEffect(() => {
    loadBuyerData();
  }, [currentBuyerAddress]);

  const loadBuyerData = async () => {
    setLoading(true);
    try {
      // Load delivery notifications
      const notificationsResponse = await fetch(
        `http://localhost:8001/api/blockchain/delivery/buyer/notifications/${currentBuyerAddress}`
      );
      if (notificationsResponse.ok) {
        const notificationsData = await notificationsResponse.json();
        setNotifications(notificationsData.notifications || []);
        
        // Load tracking details for each delivery
        const trackingPromises = notificationsData.notifications.map(async (notification) => {
          try {
            const trackingResponse = await fetch(
              `http://localhost:8001/api/blockchain/delivery/tracking/${notification.delivery_request_id}`
            );
            if (trackingResponse.ok) {
              const trackingData = await trackingResponse.json();
              return {
                deliveryId: notification.delivery_request_id,
                tracking: trackingData
              };
            }
          } catch (error) {
            console.error(`Error loading tracking for ${notification.delivery_request_id}:`, error);
          }
          return null;
        });

        const trackingResults = await Promise.all(trackingPromises);
        const trackingMap = {};
        trackingResults.forEach(result => {
          if (result) {
            trackingMap[result.deliveryId] = result.tracking;
          }
        });
        setDeliveryTracking(trackingMap);
      }
    } catch (error) {
      console.error('Error loading buyer data:', error);
    }
    setLoading(false);
  };

  const getDeliveryStatus = (tracking) => {
    if (!tracking || !tracking.stage_updates) return 'unknown';
    
    const stages = tracking.stage_updates;
    if (stages.length === 0) return 'assigned';
    
    const latestStage = stages[stages.length - 1];
    return latestStage.is_final_stage ? 'delivered' : 'in_transit';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'assigned': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'in_transit': return <Truck className="w-4 h-4 text-blue-500" />;
      case 'delivered': return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleString();
  };

  const renderNotifications = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Delivery Notifications</h3>
        <button
          onClick={loadBuyerData}
          className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {notifications.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Bell className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No delivery notifications</p>
          <p className="text-sm">You'll receive notifications when your orders are delivered</p>
        </div>
      ) : (
        <div className="space-y-4">
          {notifications.map((notification) => {
            const tracking = deliveryTracking[notification.delivery_request_id];
            const status = getDeliveryStatus(tracking);
            
            return (
              <div key={notification.notification_id} className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-medium text-gray-900">
                      Delivery #{notification.delivery_request_id}
                    </h4>
                    <p className="text-sm text-gray-600">
                      Product: {notification.product_id}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(status)}
                    <span className="text-sm font-medium capitalize">
                      {status.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">Delivery Completed</span>
                  </div>
                  <p className="text-sm text-green-700">
                    {notification.message_for_buyer || 'Your product has been delivered successfully!'}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    Delivered on: {formatTimestamp(notification.completion_timestamp)}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                  <div>
                    <span className="font-medium">Final Transporter:</span>
                    <p className="truncate">{notification.transporter_address}</p>
                  </div>
                  <div>
                    <span className="font-medium">Notification Time:</span>
                    <p>{formatTimestamp(notification.notification_timestamp)}</p>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedDelivery(notification.delivery_request_id)}
                    className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                  >
                    <Route className="w-4 h-4" />
                    <span>Track Delivery</span>
                  </button>
                  <button
                    onClick={() => alert('Encryption keys access coming soon!')}
                    className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                  >
                    <Eye className="w-4 h-4" />
                    <span>Access Keys</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  const renderDeliveryTracking = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Delivery Tracking</h3>
      
      {Object.keys(deliveryTracking).length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No delivery tracking data available</p>
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(deliveryTracking).map(([deliveryId, tracking]) => {
            const status = getDeliveryStatus(tracking);
            const stages = tracking.stage_updates || [];
            
            return (
              <div key={deliveryId} className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="font-medium text-gray-900">Delivery #{deliveryId}</h4>
                    <p className="text-sm text-gray-600">Product: {tracking.product_id}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(status)}
                    <span className="text-sm font-medium capitalize">
                      {status.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                {/* Progress Timeline */}
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-gray-700 mb-3">Delivery Progress</h5>
                  <div className="space-y-3">
                    {stages.map((stage, index) => (
                      <div key={stage.stage_update_id} className="flex items-start space-x-3">
                        <div className={`w-4 h-4 rounded-full mt-0.5 ${
                          stage.is_final_stage ? 'bg-green-500' : 
                          index === stages.length - 1 ? 'bg-blue-500' : 'bg-gray-400'
                        }`}></div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                Stage {stage.stage_number} of {stage.total_stages}
                              </p>
                              <p className="text-sm text-gray-600">
                                {stage.current_location} → {stage.next_location}
                              </p>
                              <p className="text-xs text-gray-500 truncate">
                                Transporter: {stage.transporter_address}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-gray-500">
                                {formatTimestamp(stage.update_timestamp)}
                              </p>
                              {stage.estimated_completion && (
                                <p className="text-xs text-gray-500">
                                  ETA: {stage.estimated_completion}
                                </p>
                              )}
                            </div>
                          </div>
                          {stage.is_final_stage && (
                            <div className="mt-2 p-2 bg-green-50 rounded text-xs text-green-700">
                              🎉 Delivery completed! Your product has been delivered.
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Route Information */}
                {tracking.route_locations && (
                  <div className="border-t pt-4">
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Delivery Route</h5>
                    <div className="text-sm text-gray-600">
                      {tracking.route_locations.join(' → ')}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Delivery Tracking</h1>
          <p className="text-gray-600">Track your orders and view delivery notifications</p>
        </div>
        <div className="text-sm text-gray-600">
          <Package className="w-4 h-4 inline mr-1" />
          Buyer: {currentBuyerAddress.slice(0, 8)}...{currentBuyerAddress.slice(-6)}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Deliveries</p>
              <p className="text-2xl font-bold text-gray-900">
                {notifications.length}
              </p>
            </div>
            <Package className="w-8 h-8 text-gray-500" />
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">In Transit</p>
              <p className="text-2xl font-bold text-blue-600">
                {Object.values(deliveryTracking).filter(t => getDeliveryStatus(t) === 'in_transit').length}
              </p>
            </div>
            <Truck className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-green-600">
                {Object.values(deliveryTracking).filter(t => getDeliveryStatus(t) === 'delivered').length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-gray-50 border rounded-lg p-1 mb-6">
        <div className="flex space-x-1">
          <button
            onClick={() => setActiveTab('notifications')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'notifications'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Bell className="w-4 h-4" />
            <span>Notifications</span>
          </button>
          <button
            onClick={() => setActiveTab('tracking')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'tracking'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Route className="w-4 h-4" />
            <span>Tracking</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'notifications' && renderNotifications()}
        {activeTab === 'tracking' && renderDeliveryTracking()}
      </div>

      {/* Detailed Tracking Modal */}
      {selectedDelivery && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Detailed Tracking</h2>
                <button
                  onClick={() => setSelectedDelivery(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              {deliveryTracking[selectedDelivery] && (
                <div className="space-y-6">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Info className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-blue-800">Delivery Information</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Delivery ID:</span>
                        <p>{selectedDelivery}</p>
                      </div>
                      <div>
                        <span className="font-medium">Product ID:</span>
                        <p>{deliveryTracking[selectedDelivery].product_id}</p>
                      </div>
                      <div>
                        <span className="font-medium">Status:</span>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(getDeliveryStatus(deliveryTracking[selectedDelivery]))}
                          <span className="capitalize">
                            {getDeliveryStatus(deliveryTracking[selectedDelivery]).replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Total Stages:</span>
                        <p>{deliveryTracking[selectedDelivery].total_stages || 'N/A'}</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-4">Delivery Timeline</h3>
                    <div className="space-y-4">
                      {(deliveryTracking[selectedDelivery].stage_updates || []).map((stage, index) => (
                        <div key={stage.stage_update_id} className="flex items-start space-x-4 p-4 border rounded-lg">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                            stage.is_final_stage ? 'bg-green-500' : 
                            index === (deliveryTracking[selectedDelivery].stage_updates || []).length - 1 ? 'bg-blue-500' : 'bg-gray-400'
                          }`}>
                            {stage.stage_number}
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-medium">
                                Stage {stage.stage_number} of {stage.total_stages}
                              </h4>
                              <span className="text-sm text-gray-500">
                                {formatTimestamp(stage.update_timestamp)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">
                              <MapPin className="w-4 h-4 inline mr-1" />
                              {stage.current_location} → {stage.next_location}
                            </p>
                            <p className="text-sm text-gray-500 mb-2">
                              <Truck className="w-4 h-4 inline mr-1" />
                              Transporter: {stage.transporter_address}
                            </p>
                            {stage.estimated_completion && (
                              <p className="text-sm text-gray-500">
                                <Clock className="w-4 h-4 inline mr-1" />
                                ETA: {stage.estimated_completion}
                              </p>
                            )}
                            {stage.is_final_stage && (
                              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded">
                                <div className="flex items-center space-x-2">
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                  <span className="text-sm font-medium text-green-800">
                                    Delivery Completed Successfully!
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {deliveryTracking[selectedDelivery].route_locations && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Complete Route</h3>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                          <Route className="w-4 h-4" />
                          <span>{deliveryTracking[selectedDelivery].route_locations.join(' → ')}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BuyerDeliveryTracking;
