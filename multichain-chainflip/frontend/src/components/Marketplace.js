import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const Marketplace = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('browse');
  const [listings, setListings] = useState([]);
  const [userActivity, setUserActivity] = useState([]);
  const [marketplaceStats, setMarketplaceStats] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  
  // New listing form
  const [newListing, setNewListing] = useState({
    product_id: '',
    asking_price: '',
    condition: 'excellent',
    description: ''
  });

  // Transfer form
  const [transferForm, setTransferForm] = useState({
    listing_id: '',
    buyer_address: '',
    transfer_price: ''
  });

  useEffect(() => {
    loadMarketplaceData();
  }, []);

  const loadMarketplaceData = async () => {
    try {
      await Promise.all([
        loadListings(),
        loadUserActivity(),
        loadMarketplaceStats()
      ]);
    } catch (error) {
      console.error('Failed to load marketplace data:', error);
    }
  };

  const loadListings = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/post-supply-chain/marketplace/listings`, {
        params: {
          status: 'active',
          limit: 50
        }
      });
      
      if (response.data.success) {
        setListings(response.data.listings || []);
      }
    } catch (error) {
      console.error('Failed to load listings:', error);
    }
  };

  const loadUserActivity = async () => {
    if (!user?.wallet_address) return;
    
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/post-supply-chain/marketplace/user/${user.wallet_address}/activity`
      );
      
      if (response.data.success) {
        setUserActivity(response.data.activities || []);
      }
    } catch (error) {
      console.error('Failed to load user activity:', error);
    }
  };

  const loadMarketplaceStats = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/post-supply-chain/marketplace/analytics`);
      
      if (response.data.success) {
        setMarketplaceStats(response.data);
      }
    } catch (error) {
      console.error('Failed to load marketplace stats:', error);
    }
  };

  const handleCreateListing = async () => {
    if (!newListing.product_id || !newListing.asking_price) {
      alert('Please provide product ID and asking price');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/post-supply-chain/marketplace/list`, {
        product_id: newListing.product_id,
        seller_address: user?.wallet_address || '0x1234567890abcdef',
        asking_price: parseFloat(newListing.asking_price),
        condition: newListing.condition,
        description: newListing.description || 'No description provided'
      });

      if (response.data.success) {
        alert('Product listed successfully!');
        setNewListing({ product_id: '', asking_price: '', condition: 'excellent', description: '' });
        loadListings();
      }
    } catch (error) {
      console.error('Failed to create listing:', error);
      alert('Failed to create listing: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleTransfer = async (listing) => {
    const buyerAddress = prompt('Enter buyer address:');
    if (!buyerAddress) return;

    setIsLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/post-supply-chain/marketplace/transfer`, {
        listing_id: listing.listing_id,
        buyer_address: buyerAddress,
        transfer_price: listing.asking_price,
        verification_required: true
      });

      if (response.data.success) {
        alert('Transfer initiated successfully!');
        loadListings();
        loadUserActivity();
      }
    } catch (error) {
      console.error('Failed to initiate transfer:', error);
      alert('Failed to initiate transfer: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoading(false);
    }
  };

  const getConditionColor = (condition) => {
    switch (condition) {
      case 'excellent': return 'text-green-600 bg-green-100';
      case 'good': return 'text-blue-600 bg-blue-100';
      case 'fair': return 'text-yellow-600 bg-yellow-100';
      case 'poor': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const generateMockProductId = () => {
    return 'PROD_' + Math.random().toString(36).substr(2, 9).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Marketplace</h1>
          <p className="text-gray-600">Algorithm 5 - Secondary marketplace for verified products with ownership transfers</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Listings</p>
                <p className="text-2xl font-bold text-blue-600">{marketplaceStats.total_listings || 0}</p>
              </div>
              <div className="text-3xl">🏪</div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Listings</p>
                <p className="text-2xl font-bold text-green-600">{marketplaceStats.active_listings || 0}</p>
              </div>
              <div className="text-3xl">✅</div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Volume</p>
                <p className="text-2xl font-bold text-purple-600">${marketplaceStats.total_volume || '0'}</p>
              </div>
              <div className="text-3xl">💰</div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Completed Transfers</p>
                <p className="text-2xl font-bold text-orange-600">{marketplaceStats.completed_transfers || 0}</p>
              </div>
              <div className="text-3xl">🔄</div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex space-x-4">
            <button
              onClick={() => setActiveTab('browse')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === 'browse'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Browse Listings
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === 'create'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Create Listing
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === 'activity'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              My Activity
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'browse' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings.length === 0 ? (
              <div className="col-span-full text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="text-4xl mb-4">🏪</div>
                <p className="text-gray-500">No active listings found</p>
                <button
                  onClick={loadListings}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Refresh Listings
                </button>
              </div>
            ) : (
              listings.map((listing) => (
                <div key={listing.listing_id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="font-bold text-gray-900 text-lg">{listing.product_id}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConditionColor(listing.condition)}`}>
                      {listing.condition}
                    </span>
                  </div>
                  
                  <div className="space-y-3 mb-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Price:</span>
                      <span className="font-semibold text-green-600">${listing.asking_price}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Seller:</span>
                      <span className="text-sm font-mono">{listing.seller_address?.slice(0, 10)}...</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Listed:</span>
                      <span className="text-sm">{new Date(listing.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {listing.description && (
                    <p className="text-gray-600 text-sm mb-4">{listing.description}</p>
                  )}

                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleTransfer(listing)}
                      disabled={isLoading}
                      className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
                    >
                      Purchase
                    </button>
                    <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200">
                      Details
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'create' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Create New Listing</h2>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Product ID</label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={newListing.product_id}
                      onChange={(e) => setNewListing({...newListing, product_id: e.target.value})}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter product ID"
                    />
                    <button
                      onClick={() => setNewListing({...newListing, product_id: generateMockProductId()})}
                      className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                    >
                      Generate
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Must be a delivered product you own</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Asking Price (USD)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newListing.asking_price}
                    onChange={(e) => setNewListing({...newListing, asking_price: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Condition</label>
                  <select
                    value={newListing.condition}
                    onChange={(e) => setNewListing({...newListing, condition: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="excellent">Excellent</option>
                    <option value="good">Good</option>
                    <option value="fair">Fair</option>
                    <option value="poor">Poor</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Description (Optional)</label>
                  <textarea
                    value={newListing.description}
                    onChange={(e) => setNewListing({...newListing, description: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Describe your product..."
                  />
                </div>

                <button
                  onClick={handleCreateListing}
                  disabled={isLoading}
                  className="w-full bg-green-600 text-white py-3 rounded-md hover:bg-green-700 disabled:opacity-50 font-medium"
                >
                  {isLoading ? 'Creating Listing...' : 'Create Listing'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">My Activity</h2>
            
            {userActivity.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">📋</div>
                <p>No activity found</p>
                <button
                  onClick={loadUserActivity}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Refresh Activity
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {userActivity.map((activity, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-gray-900">{activity.activity_type}</h3>
                        <p className="text-sm text-gray-600">{activity.product_id}</p>
                        <p className="text-xs text-gray-500">{new Date(activity.timestamp).toLocaleString()}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        activity.status === 'completed' ? 'bg-green-100 text-green-600' :
                        activity.status === 'pending' ? 'bg-yellow-100 text-yellow-600' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {activity.status}
                      </span>
                    </div>
                    {activity.details && (
                      <div className="mt-2 text-sm text-gray-600">
                        {activity.details}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Marketplace;