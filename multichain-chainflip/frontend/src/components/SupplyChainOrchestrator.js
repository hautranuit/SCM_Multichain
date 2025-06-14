import React, { useState, useEffect } from 'react';
import { 
  ShoppingCart, 
  Truck, 
  MapPin, 
  Users, 
  Star, 
  Package,
  CheckCircle,
  Clock,
  AlertCircle,
  TrendingUp,
  Navigation,
  Send,
  Palette,
  Shield,
  ArrowRight,
  Eye,
  DollarSign,
  Lock,
  Unlock
} from 'lucide-react';

const SupplyChainOrchestrator = () => {
  const [activeTab, setActiveTab] = useState('purchase');
  const [purchaseRequests, setPurchaseRequests] = useState([]);
  const [transporterLeaderboard, setTransporterLeaderboard] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [nftTransfers, setNftTransfers] = useState([]);
  const [nftAnalytics, setNftAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Purchase form state
  const [purchaseForm, setPurchaseForm] = useState({
    buyer_address: '0xc6A050a538a9E857B4DCb4A33436280c202F6941',
    buyer_chain: 'optimism_sepolia',
    product_id: '',
    manufacturer_address: '0x032041b4b356fEE1496805DD4749f181bC736FFA',
    manufacturer_chain: 'base_sepolia',
    delivery_address: '',
    delivery_coordinates: ['', ''],
    manufacturer_coordinates: ['37.7749', '-122.4194'], // Default San Francisco
    purchase_amount: ''
  });
  
  // Shipping form state
  const [shippingForm, setShippingForm] = useState({
    request_id: '',
    manufacturer_address: '0x032041b4b356fEE1496805DD4749f181bC736FFA',
    estimated_delivery_time: '',
    package_details: {
      weight: '',
      dimensions: '',
      description: ''
    },
    special_instructions: ''
  });

  // NFT transfer form state
  const [nftForm, setNftForm] = useState({
    purchase_request_id: '',
    product_id: '',
    manufacturer_address: '0x032041b4b356fEE1496805DD4749f181bC736FFA',
    transporter_addresses: ['0x28918ecf013F32fAf45e05d62B4D9b207FCae784'],
    buyer_address: '0xc6A050a538a9E857B4DCb4A33436280c202F6941',
    purchase_amount: '0.1'
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadPurchaseRequests(),
        loadTransporterLeaderboard(),
        loadAnalytics(),
        loadNftTransfers(),
        loadNftAnalytics()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPurchaseRequests = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/supply-chain/purchase/list?limit=50`);
      const data = await response.json();
      setPurchaseRequests(data.requests || []);
    } catch (error) {
      console.error('Error loading purchase requests:', error);
    }
  };

  const loadTransporterLeaderboard = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/supply-chain/transporters/leaderboard?limit=20`);
      const data = await response.json();
      setTransporterLeaderboard(data || []);
    } catch (error) {
      console.error('Error loading transporter leaderboard:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/supply-chain/analytics/dashboard`);
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const loadNftTransfers = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/supply-chain/nft/transfers/list?limit=50`);
      const data = await response.json();
      setNftTransfers(data.transfers || []);
    } catch (error) {
      console.error('Error loading NFT transfers:', error);
    }
  };

  const loadNftAnalytics = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/supply-chain/nft/analytics/dashboard`);
      const data = await response.json();
      setNftAnalytics(data);
    } catch (error) {
      console.error('Error loading NFT analytics:', error);
    }
  };

  const handlePurchaseSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const requestData = {
        ...purchaseForm,
        delivery_coordinates: [
          parseFloat(purchaseForm.delivery_coordinates[0]),
          parseFloat(purchaseForm.delivery_coordinates[1])
        ],
        manufacturer_coordinates: [
          parseFloat(purchaseForm.manufacturer_coordinates[0]),
          parseFloat(purchaseForm.manufacturer_coordinates[1])
        ],
        purchase_amount: parseFloat(purchaseForm.purchase_amount)
      };

      const response = await fetch(`${BACKEND_URL}/api/supply-chain/purchase/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        alert(`Purchase initiated successfully! Request ID: ${result.request_id}`);
        setPurchaseForm({
          ...purchaseForm,
          product_id: '',
          delivery_address: '',
          delivery_coordinates: ['', ''],
          purchase_amount: ''
        });
        await loadPurchaseRequests();
      } else {
        alert(`Purchase failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Purchase initiation error:', error);
      alert(`Purchase failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleShippingSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/supply-chain/shipping/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...shippingForm,
          estimated_delivery_time: parseInt(shippingForm.estimated_delivery_time)
        })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        alert('Shipping initiated successfully! NFT transfer flow automatically started.');
        setShippingForm({
          ...shippingForm,
          request_id: '',
          estimated_delivery_time: '',
          package_details: { weight: '', dimensions: '', description: '' },
          special_instructions: ''
        });
        await Promise.all([loadPurchaseRequests(), loadNftTransfers()]);
      } else {
        alert(`Shipping failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Shipping initiation error:', error);
      alert(`Shipping failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNftSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const requestData = {
        ...nftForm,
        purchase_amount: parseFloat(nftForm.purchase_amount),
        product_metadata: {
          name: `Product ${nftForm.product_id}`,
          description: `Supply chain product for purchase ${nftForm.purchase_request_id}`,
          product_id: nftForm.product_id,
          purchase_request_id: nftForm.purchase_request_id,
          created_at: new Date().toISOString()
        }
      };

      const response = await fetch(`${BACKEND_URL}/api/supply-chain/nft/initiate-transfer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        alert(`NFT transfer initiated! Transfer ID: ${result.transfer_id}`);
        setNftForm({
          ...nftForm,
          purchase_request_id: '',
          product_id: ''
        });
        await loadNftTransfers();
      } else {
        alert(`NFT transfer failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('NFT transfer error:', error);
      alert(`NFT transfer failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const executeNextNftStep = async (transferId) => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/supply-chain/nft/execute-step`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transfer_id: transferId,
          executor_address: '0x28918ecf013F32fAf45e05d62B4D9b207FCae784'
        })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        alert('Transfer step executed successfully!');
        await loadNftTransfers();
      } else {
        alert(`Step execution failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Step execution error:', error);
      alert(`Step execution failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending_hub_coordination': 'text-yellow-600 bg-yellow-100',
      'hub_coordinated': 'text-blue-600 bg-blue-100',
      'shipping_initiated': 'text-purple-600 bg-purple-100',
      'in_transit': 'text-orange-600 bg-orange-100',
      'delivered': 'text-green-600 bg-green-100',
      'cancelled': 'text-red-600 bg-red-100',
      'minted': 'text-indigo-600 bg-indigo-100',
      'escrowed': 'text-blue-600 bg-blue-100',
      'failed': 'text-red-600 bg-red-100'
    };
    return colors[status] || 'text-gray-600 bg-gray-100';
  };

  const getChainDisplay = (chain) => {
    const chainNames = {
      'optimism_sepolia': 'Optimism Sepolia',
      'base_sepolia': 'Base Sepolia',
      'arbitrum_sepolia': 'Arbitrum Sepolia',
      'polygon_amoy': 'Polygon Amoy'
    };
    return chainNames[chain] || chain;
  };

  const calculateDistance = (coord1, coord2) => {
    // Simple distance calculation for display
    const lat1 = parseFloat(coord1[0]);
    const lon1 = parseFloat(coord1[1]);
    const lat2 = parseFloat(coord2[0]);
    const lon2 = parseFloat(coord2[1]);
    
    const R = 3959; // Earth's radius in miles
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c;
    
    return Math.round(distance);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg">
        <h1 className="text-3xl font-bold mb-2">Supply Chain Orchestrator</h1>
        <p className="text-blue-100">Cross-chain purchase coordination with NFT transfers and escrow management</p>
      </div>

      {/* Analytics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {analytics && (
          <>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Requests</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.total_requests}</p>
                </div>
                <ShoppingCart className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Requests</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.active_requests}</p>
                </div>
                <Clock className="h-8 w-8 text-yellow-600" />
              </div>
            </div>
          </>
        )}
        
        {nftAnalytics && (
          <>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">NFT Transfers</p>
                  <p className="text-2xl font-bold text-gray-900">{nftAnalytics.total_transfers}</p>
                </div>
                <Palette className="h-8 w-8 text-purple-600" />
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Escrow Value</p>
                  <p className="text-2xl font-bold text-gray-900">{nftAnalytics.total_escrow_value_eth.toFixed(2)} ETH</p>
                </div>
                <Shield className="h-8 w-8 text-green-600" />
              </div>
            </div>
          </>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'purchase', label: 'Initiate Purchase', icon: ShoppingCart },
              { id: 'shipping', label: 'Start Shipping', icon: Send },
              { id: 'nft', label: 'NFT Transfers', icon: Palette },
              { id: 'tracking', label: 'Track Orders', icon: Package },
              { id: 'transporters', label: 'Transporters', icon: Users }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5 mr-2" />
                {label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Purchase Initiation Tab */}
          {activeTab === 'purchase' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Initiate Cross-Chain Purchase</h2>
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Process Flow</h3>
                <div className="flex items-center space-x-4 text-sm text-blue-700">
                  <span className="flex items-center"><ShoppingCart className="h-4 w-4 mr-1" />Buyer (OP Sepolia)</span>
                  <span>→</span>
                  <span className="flex items-center"><Navigation className="h-4 w-4 mr-1" />Hub (Polygon Amoy)</span>
                  <span>→</span>
                  <span className="flex items-center"><Package className="h-4 w-4 mr-1" />Manufacturer (Base Sepolia)</span>
                </div>
              </div>
              
              <form onSubmit={handlePurchaseSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Product ID</label>
                  <input
                    type="text"
                    value={purchaseForm.product_id}
                    onChange={(e) => setPurchaseForm({...purchaseForm, product_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter product identifier"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Purchase Amount (ETH)</label>
                  <input
                    type="number"
                    step="0.001"
                    value={purchaseForm.purchase_amount}
                    onChange={(e) => setPurchaseForm({...purchaseForm, purchase_amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.01"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Delivery Address</label>
                  <input
                    type="text"
                    value={purchaseForm.delivery_address}
                    onChange={(e) => setPurchaseForm({...purchaseForm, delivery_address: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Full delivery address"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Buyer Chain</label>
                  <select
                    value={purchaseForm.buyer_chain}
                    onChange={(e) => setPurchaseForm({...purchaseForm, buyer_chain: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="optimism_sepolia">Optimism Sepolia (Buyer)</option>
                    <option value="arbitrum_sepolia">Arbitrum Sepolia</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Delivery Coordinates</label>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="number"
                      step="any"
                      value={purchaseForm.delivery_coordinates[0]}
                      onChange={(e) => setPurchaseForm({
                        ...purchaseForm, 
                        delivery_coordinates: [e.target.value, purchaseForm.delivery_coordinates[1]]
                      })}
                      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Latitude"
                      required
                    />
                    <input
                      type="number"
                      step="any"
                      value={purchaseForm.delivery_coordinates[1]}
                      onChange={(e) => setPurchaseForm({
                        ...purchaseForm, 
                        delivery_coordinates: [purchaseForm.delivery_coordinates[0], e.target.value]
                      })}
                      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Longitude"
                      required
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Manufacturer Coordinates</label>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="number"
                      step="any"
                      value={purchaseForm.manufacturer_coordinates[0]}
                      onChange={(e) => setPurchaseForm({
                        ...purchaseForm, 
                        manufacturer_coordinates: [e.target.value, purchaseForm.manufacturer_coordinates[1]]
                      })}
                      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Latitude"
                      required
                    />
                    <input
                      type="number"
                      step="any"
                      value={purchaseForm.manufacturer_coordinates[1]}
                      onChange={(e) => setPurchaseForm({
                        ...purchaseForm, 
                        manufacturer_coordinates: [purchaseForm.manufacturer_coordinates[0], e.target.value]
                      })}
                      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Longitude"
                      required
                    />
                  </div>
                </div>
                
                <div className="md:col-span-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Processing...
                      </>
                    ) : (
                      <>
                        <ShoppingCart className="h-4 w-4 mr-2" />
                        Initiate Purchase
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Shipping Initiation Tab */}
          {activeTab === 'shipping' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Start Shipping Process</h2>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-green-700">
                  This step is performed by manufacturers after receiving cross-chain purchase notifications from the Hub. 
                  <span className="font-medium"> NFT transfer flow will be automatically initiated when shipping starts.</span>
                </p>
              </div>
              
              <form onSubmit={handleShippingSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Purchase Request ID</label>
                  <input
                    type="text"
                    value={shippingForm.request_id}
                    onChange={(e) => setShippingForm({...shippingForm, request_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="PURCHASE-xxx-xxx"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Estimated Delivery Time (hours)</label>
                  <input
                    type="number"
                    value={shippingForm.estimated_delivery_time}
                    onChange={(e) => setShippingForm({...shippingForm, estimated_delivery_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="24"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Package Weight (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={shippingForm.package_details.weight}
                    onChange={(e) => setShippingForm({
                      ...shippingForm, 
                      package_details: {...shippingForm.package_details, weight: e.target.value}
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="1.5"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Package Dimensions</label>
                  <input
                    type="text"
                    value={shippingForm.package_details.dimensions}
                    onChange={(e) => setShippingForm({
                      ...shippingForm, 
                      package_details: {...shippingForm.package_details, dimensions: e.target.value}
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="20x15x10 cm"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Package Description</label>
                  <input
                    type="text"
                    value={shippingForm.package_details.description}
                    onChange={(e) => setShippingForm({
                      ...shippingForm, 
                      package_details: {...shippingForm.package_details, description: e.target.value}
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Product description"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Special Instructions</label>
                  <textarea
                    value={shippingForm.special_instructions}
                    onChange={(e) => setShippingForm({...shippingForm, special_instructions: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                    placeholder="Any special delivery instructions..."
                  />
                </div>
                
                <div className="md:col-span-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center justify-center"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Processing...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4 mr-2" />
                        Start Shipping & NFT Transfer
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* NFT Transfers Tab */}
          {activeTab === 'nft' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">NFT Transfer Management</h2>
                <button
                  onClick={loadNftTransfers}
                  className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 flex items-center"
                >
                  <Palette className="h-4 w-4 mr-2" />
                  Refresh NFTs
                </button>
              </div>

              {/* Manual NFT Initiation Form */}
              <div className="bg-purple-50 p-4 rounded-lg">
                <h3 className="font-medium text-purple-900 mb-3">Manual NFT Transfer Initiation</h3>
                <p className="text-sm text-purple-700 mb-4">
                  NFT transfers are automatically initiated when shipping starts. Use this form for manual testing only.
                </p>
                
                <form onSubmit={handleNftSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <input
                      type="text"
                      value={nftForm.purchase_request_id}
                      onChange={(e) => setNftForm({...nftForm, purchase_request_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="Purchase Request ID"
                      required
                    />
                  </div>
                  <div>
                    <input
                      type="text"
                      value={nftForm.product_id}
                      onChange={(e) => setNftForm({...nftForm, product_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="Product ID"
                      required
                    />
                  </div>
                  <div>
                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center"
                    >
                      {loading ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      ) : (
                        <Palette className="h-4 w-4 mr-2" />
                      )}
                      Create NFT Transfer
                    </button>
                  </div>
                </form>
              </div>
              
              {/* NFT Transfers List */}
              <div className="space-y-4">
                {nftTransfers.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Palette className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No NFT transfers found</p>
                  </div>
                ) : (
                  nftTransfers.map((transfer) => (
                    <div key={transfer.transfer_id} className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-lg border border-purple-200">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="font-medium text-gray-900 flex items-center">
                            <Palette className="h-4 w-4 mr-2 text-purple-600" />
                            {transfer.transfer_id}
                          </h3>
                          <p className="text-sm text-gray-600">Token ID: {transfer.token_id}</p>
                          <p className="text-sm text-gray-600">Product: {transfer.product_id}</p>
                        </div>
                        <div className="text-right">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(transfer.status)}`}>
                            {transfer.status.replace(/_/g, ' ').toUpperCase()}
                          </span>
                          <p className="text-sm text-gray-500 mt-1">{transfer.progress_percentage.toFixed(0)}% Complete</p>
                        </div>
                      </div>
                      
                      {/* Transfer Progress Bar */}
                      <div className="mb-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium text-gray-700">Transfer Progress</span>
                          <span className="text-sm text-gray-500">{transfer.current_step}/{transfer.total_steps} steps</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-gradient-to-r from-purple-500 to-indigo-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${transfer.progress_percentage}%` }}
                          ></div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="font-medium text-gray-700 flex items-center">
                            <Users className="h-4 w-4 mr-1" />
                            Manufacturer
                          </p>
                          <p className="text-gray-600">{transfer.manufacturer_address.slice(0, 8)}...</p>
                        </div>
                        <div>
                          <p className="font-medium text-gray-700 flex items-center">
                            <Truck className="h-4 w-4 mr-1" />
                            Transporters
                          </p>
                          <p className="text-gray-600">{transfer.transporter_count} assigned</p>
                        </div>
                        <div>
                          <p className="font-medium text-gray-700 flex items-center">
                            <ShoppingCart className="h-4 w-4 mr-1" />
                            Buyer
                          </p>
                          <p className="text-gray-600">{transfer.buyer_address.slice(0, 8)}...</p>
                        </div>
                        <div>
                          <p className="font-medium text-gray-700 flex items-center">
                            <Shield className="h-4 w-4 mr-1" />
                            Escrow
                          </p>
                          <p className="text-gray-600">{transfer.purchase_amount} ETH</p>
                          <p className="text-gray-500">{transfer.escrow_id.slice(0, 8)}...</p>
                        </div>
                      </div>
                      
                      <div className="mt-4 pt-4 border-t border-purple-200 flex justify-between items-center">
                        <span className="text-sm text-gray-500">
                          Created: {new Date(transfer.created_at).toLocaleString()}
                        </span>
                        {transfer.status === 'in_transit' && (
                          <button
                            onClick={() => executeNextNftStep(transfer.transfer_id)}
                            disabled={loading}
                            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center text-sm"
                          >
                            <ArrowRight className="h-4 w-4 mr-1" />
                            Execute Next Step
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Order Tracking Tab */}
          {activeTab === 'tracking' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Purchase Requests</h2>
                <button
                  onClick={loadPurchaseRequests}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
                >
                  <Clock className="h-4 w-4 mr-2" />
                  Refresh
                </button>
              </div>
              
              <div className="space-y-4">
                {purchaseRequests.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No purchase requests found</p>
                  </div>
                ) : (
                  purchaseRequests.map((request) => (
                    <div key={request.request_id} className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="font-medium text-gray-900">{request.request_id}</h3>
                          <p className="text-sm text-gray-600">Product: {request.product_id}</p>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                          {request.status.replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="font-medium text-gray-700">Buyer</p>
                          <p className="text-gray-600">{request.buyer_address.slice(0, 8)}...</p>
                          <p className="text-gray-500">{getChainDisplay(request.buyer_chain)}</p>
                        </div>
                        <div>
                          <p className="font-medium text-gray-700">Manufacturer</p>
                          <p className="text-gray-600">{request.manufacturer_address.slice(0, 8)}...</p>
                          <p className="text-gray-500">{getChainDisplay(request.manufacturer_chain)}</p>
                        </div>
                        <div>
                          <p className="font-medium text-gray-700">Delivery Details</p>
                          <p className="text-gray-600">{request.distance_miles} miles</p>
                          <p className="text-gray-500">{request.transporters_required} transporters needed</p>
                        </div>
                      </div>
                      
                      <div className="mt-3 pt-3 border-t border-gray-200 flex justify-between items-center">
                        <span className="text-sm text-gray-600">
                          Amount: {request.purchase_amount} ETH
                        </span>
                        <span className="text-sm text-gray-500">
                          {new Date(request.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Transporters Tab */}
          {activeTab === 'transporters' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Transporter Leaderboard</h2>
                <button
                  onClick={loadTransporterLeaderboard}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
                >
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Refresh
                </button>
              </div>
              
              <div className="bg-white overflow-hidden shadow rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Rank
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Transporter
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Reputation
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Deliveries
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Success Rate
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {transporterLeaderboard.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                          No transporters found
                        </td>
                      </tr>
                    ) : (
                      transporterLeaderboard.map((transporter) => (
                        <tr key={transporter.address}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            #{transporter.rank}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {transporter.address.slice(0, 8)}...
                            </div>
                            <div className="text-sm text-gray-500">
                              {transporter.address.slice(-8)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <Star className="h-4 w-4 text-yellow-400 mr-1" />
                              <span className="text-sm font-medium text-gray-900">
                                {transporter.reputation_score.toFixed(3)}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {transporter.total_deliveries}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {transporter.success_rate.toFixed(1)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              transporter.status === 'available' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {transporter.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SupplyChainOrchestrator;