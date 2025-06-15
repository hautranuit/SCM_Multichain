import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const ModernDashboard = ({ backendStatus }) => {
  const { userRole, user } = useAuth();
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalTransactions: 0,
    totalDisputes: 0,
    totalPayments: 0,
    marketplaceListings: 0
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [networkStatus, setNetworkStatus] = useState({});

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load network status
      const networkResponse = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/network-status`);
      setNetworkStatus(networkResponse.data);

      // Load algorithm-specific stats
      const promises = [
        loadPaymentStats(),
        loadConsensusStats(), 
        loadSupplyChainStats(),
        loadAuthenticityStats(),
        loadMarketplaceStats()
      ];

      await Promise.all(promises);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  const loadPaymentStats = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/payment/analytics/platform`);
      if (response.data.success) {
        setStats(prev => ({
          ...prev,
          totalPayments: response.data.total_payments || 0
        }));
      }
    } catch (error) {
      console.log('Payment stats not available');
    }
  };

  const loadConsensusStats = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/enhanced-consensus/analytics/summary`);
      if (response.data.success) {
        setStats(prev => ({
          ...prev,
          totalDisputes: response.data.total_disputes || 0
        }));
      }
    } catch (error) {
      console.log('Consensus stats not available');
    }
  };

  const loadSupplyChainStats = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/supply-chain/analytics/summary`);
      if (response.data.success) {
        setStats(prev => ({
          ...prev,
          totalProducts: response.data.total_products || 0,
          totalTransactions: response.data.total_deliveries || 0
        }));
      }
    } catch (error) {
      console.log('Supply chain stats not available');
    }
  };

  const loadAuthenticityStats = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/enhanced-authenticity/analytics/performance`);
      if (response.data.success) {
        // Add authenticity-specific stats if needed
      }
    } catch (error) {
      console.log('Authenticity stats not available');
    }
  };

  const loadMarketplaceStats = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/post-supply-chain/marketplace/analytics`);
      if (response.data.success) {
        setStats(prev => ({
          ...prev,
          marketplaceListings: response.data.total_listings || 0
        }));
      }
    } catch (error) {
      console.log('Marketplace stats not available');
    }
  };

  const getRoleSpecificCards = () => {
    const baseCards = [
      {
        title: "Network Status",
        value: backendStatus.includes('✅') ? 'Connected' : 'Disconnected',
        color: backendStatus.includes('✅') ? 'green' : 'red',
        icon: '🌐'
      }
    ];

    switch (userRole) {
      case 'manufacturer':
        return [
          ...baseCards,
          {
            title: "Products Created",
            value: stats.totalProducts,
            color: 'blue',
            icon: '📦'
          },
          {
            title: "Payments Processed", 
            value: stats.totalPayments,
            color: 'purple',
            icon: '💰'
          },
          {
            title: "Active Verifications",
            value: '98.5%',
            color: 'green',
            icon: '✅'
          }
        ];

      case 'transporter':
        return [
          ...baseCards,
          {
            title: "Deliveries Completed",
            value: stats.totalTransactions,
            color: 'blue',
            icon: '🚛'
          },
          {
            title: "Incentives Earned",
            value: '$2,450',
            color: 'green',
            icon: '💎'
          },
          {
            title: "Performance Score",
            value: '4.8/5',
            color: 'purple',
            icon: '⭐'
          }
        ];

      case 'buyer':
        return [
          ...baseCards,
          {
            title: "Products Purchased",
            value: stats.totalTransactions,
            color: 'blue',
            icon: '🛒'
          },
          {
            title: "Marketplace Listings",
            value: stats.marketplaceListings,
            color: 'purple',
            icon: '🏪'
          },
          {
            title: "Verified Authenticity",
            value: '100%',
            color: 'green',
            icon: '🔐'
          }
        ];

      default:
        return [
          ...baseCards,
          {
            title: "Total Products",
            value: stats.totalProducts,
            color: 'blue',
            icon: '📊'
          },
          {
            title: "Total Transactions",
            value: stats.totalTransactions,
            color: 'purple',
            icon: '💫'
          },
          {
            title: "Platform Health",
            value: '99.9%',
            color: 'green',
            icon: '💚'
          }
        ];
    }
  };

  const algorithmStatus = [
    {
      name: "Payment & Incentive System",
      status: "Operational",
      color: "green",
      description: "Smart escrow payments running smoothly"
    },
    {
      name: "Dispute Resolution",
      status: "Operational", 
      color: "green",
      description: "Consensus voting mechanism active"
    },
    {
      name: "Supply Chain Consensus",
      status: "Operational",
      color: "green", 
      description: "Cross-chain coordination working"
    },
    {
      name: "Enhanced Authenticity",
      status: "Operational",
      color: "green",
      description: "Verification algorithms active"
    },
    {
      name: "Marketplace Management", 
      status: "Operational",
      color: "green",
      description: "Secondary marketplace running"
    }
  ];

  const cards = getRoleSpecificCards();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Welcome back, {user?.username || 'User'}
              </h1>
              <p className="text-gray-600 mt-1">
                {userRole === 'manufacturer' && 'Manage your product lifecycle and track supply chain operations'}
                {userRole === 'transporter' && 'Monitor deliveries and optimize your transportation routes'}
                {userRole === 'buyer' && 'Explore products and manage your purchases with confidence'}
                {userRole === 'admin' && 'Oversee platform operations and manage all stakeholders'}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Current Role</div>
              <div className="text-xl font-semibold text-blue-600 capitalize">{userRole}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {cards.map((card, index) => (
            <div key={index} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <p className={`text-2xl font-bold ${
                    card.color === 'green' ? 'text-green-600' :
                    card.color === 'blue' ? 'text-blue-600' :
                    card.color === 'purple' ? 'text-purple-600' :
                    card.color === 'red' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {card.value}
                  </p>
                </div>
                <div className="text-3xl">{card.icon}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Algorithm Status */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Algorithm Status</h2>
            <div className="space-y-4">
              {algorithmStatus.map((algorithm, index) => (
                <div key={index} className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{algorithm.name}</h3>
                    <p className="text-sm text-gray-600">{algorithm.description}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      algorithm.color === 'green' ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <span className={`font-medium ${
                      algorithm.color === 'green' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {algorithm.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {userRole === 'manufacturer' && (
                <>
                  <button 
                    onClick={() => window.location.href = '/products'}
                    className="bg-blue-600 text-white p-4 rounded-lg hover:bg-blue-700 transition-colors text-left"
                  >
                    <div className="text-lg font-semibold">Create Product</div>
                    <div className="text-sm opacity-90">Start new product lifecycle</div>
                  </button>
                  <button 
                    onClick={() => window.location.href = '/enhanced-authenticity'}
                    className="bg-green-600 text-white p-4 rounded-lg hover:bg-green-700 transition-colors text-left"
                  >
                    <div className="text-lg font-semibold">Verify Products</div>
                    <div className="text-sm opacity-90">Enhanced verification tools</div>
                  </button>
                </>
              )}
              
              {userRole === 'transporter' && (
                <>
                  <button 
                    onClick={() => window.location.href = '/qr-scanner'}
                    className="bg-green-600 text-white p-4 rounded-lg hover:bg-green-700 transition-colors text-left"
                  >
                    <div className="text-lg font-semibold">Scan QR Code</div>
                    <div className="text-sm opacity-90">Update delivery status</div>
                  </button>
                  <button 
                    onClick={() => window.location.href = '/products'}
                    className="bg-blue-600 text-white p-4 rounded-lg hover:bg-blue-700 transition-colors text-left"
                  >
                    <div className="text-lg font-semibold">View Shipments</div>
                    <div className="text-sm opacity-90">Manage deliveries</div>
                  </button>
                </>
              )}
              
              {userRole === 'buyer' && (
                <>
                  <button 
                    onClick={() => window.location.href = '/products'}
                    className="bg-blue-600 text-white p-4 rounded-lg hover:bg-blue-700 transition-colors text-left"
                  >
                    <div className="text-lg font-semibold">Browse Products</div>
                    <div className="text-sm opacity-90">Explore marketplace</div>
                  </button>
                  <button 
                    onClick={() => window.location.href = '/marketplace'}
                    className="bg-purple-600 text-white p-4 rounded-lg hover:bg-purple-700 transition-colors text-left"
                  >
                    <div className="text-lg font-semibold">Marketplace</div>
                    <div className="text-sm opacity-90">Secondary market & resales</div>
                  </button>
                </>
              )}
              
              {/* Algorithm 4 & 5 Feature Access for All Users */}
              <button 
                onClick={() => window.location.href = '/enhanced-authenticity'}
                className="bg-indigo-600 text-white p-4 rounded-lg hover:bg-indigo-700 transition-colors text-left"
              >
                <div className="text-lg font-semibold">Enhanced Verification</div>
                <div className="text-sm opacity-90">Algorithm 4 - Batch verification</div>
              </button>
              
              <button 
                onClick={() => window.location.href = '/marketplace'}
                className="bg-teal-600 text-white p-4 rounded-lg hover:bg-teal-700 transition-colors text-left"
              >
                <div className="text-lg font-semibold">Secondary Market</div>
                <div className="text-sm opacity-90">Algorithm 5 - Product marketplace</div>
              </button>
              
              <button 
                onClick={() => window.location.href = '/enhanced-consensus'}
                className="bg-gray-600 text-white p-4 rounded-lg hover:bg-gray-700 transition-colors text-left"
              >
                <div className="text-lg font-semibold">Consensus Hub</div>
                <div className="text-sm opacity-90">Participate in decisions</div>
              </button>
              
              <button 
                onClick={() => window.location.href = '/participants'}
                className="bg-cyan-600 text-white p-4 rounded-lg hover:bg-cyan-700 transition-colors text-left"
              >
                <div className="text-lg font-semibold">Network</div>
                <div className="text-sm opacity-90">View participants</div>
              </button>
            </div>
          </div>
        </div>

        {/* Network Health */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Network Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {networkStatus.multichain?.statistics?.total_products || 0}
              </div>
              <div className="text-gray-600">Products Tracked</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {networkStatus.multichain?.statistics?.total_transactions || 0}
              </div>
              <div className="text-gray-600">Transactions</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">99.9%</div>
              <div className="text-gray-600">Uptime</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModernDashboard;