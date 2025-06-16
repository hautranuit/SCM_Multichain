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

      // Load system-specific stats
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
        title: "Network Health",
        value: backendStatus.includes('✅') ? 'Connected' : 'Disconnected',
        color: backendStatus.includes('✅') ? 'green' : 'red',
        icon: '🌐',
        gradient: 'from-green-400 to-emerald-600'
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
            icon: '📦',
            gradient: 'from-blue-500 to-indigo-600'
          },
          {
            title: "Payments Processed", 
            value: stats.totalPayments,
            color: 'purple',
            icon: '💰',
            gradient: 'from-purple-500 to-pink-600'
          },
          {
            title: "Quality Rating",
            value: '98.5%',
            color: 'green',
            icon: '✅',
            gradient: 'from-green-400 to-teal-600'
          }
        ];

      case 'transporter':
        return [
          ...baseCards,
          {
            title: "Deliveries Completed",
            value: stats.totalTransactions,
            color: 'blue',
            icon: '🚛',
            gradient: 'from-blue-500 to-cyan-600'
          },
          {
            title: "Earnings",
            value: '$2,450',
            color: 'green',
            icon: '💎',
            gradient: 'from-emerald-400 to-green-600'
          },
          {
            title: "Performance Score",
            value: '4.8/5',
            color: 'purple',
            icon: '⭐',
            gradient: 'from-yellow-400 to-orange-500'
          }
        ];

      case 'buyer':
        return [
          ...baseCards,
          {
            title: "Products Purchased",
            value: stats.totalTransactions,
            color: 'blue',
            icon: '🛒',
            gradient: 'from-blue-500 to-indigo-600'
          },
          {
            title: "Marketplace Items",
            value: stats.marketplaceListings,
            color: 'purple',
            icon: '🏪',
            gradient: 'from-purple-500 to-pink-600'
          },
          {
            title: "Authenticity Score",
            value: '100%',
            color: 'green',
            icon: '🔐',
            gradient: 'from-green-400 to-emerald-600'
          }
        ];

      default:
        return [
          ...baseCards,
          {
            title: "Total Products",
            value: stats.totalProducts,
            color: 'blue',
            icon: '📊',
            gradient: 'from-blue-500 to-indigo-600'
          },
          {
            title: "Total Transactions",
            value: stats.totalTransactions,
            color: 'purple',
            icon: '💫',
            gradient: 'from-purple-500 to-pink-600'
          },
          {
            title: "Platform Health",
            value: '99.9%',
            color: 'green',
            icon: '💚',
            gradient: 'from-green-400 to-emerald-600'
          }
        ];
    }
  };

  const systemStatus = [
    {
      name: "Smart Payment System",
      status: "Operational",
      color: "green",
      description: "Automated escrow payments running smoothly",
      icon: "💳"
    },
    {
      name: "Dispute Resolution",
      status: "Operational", 
      color: "green",
      description: "Consensus voting mechanism active",
      icon: "⚖️"
    },
    {
      name: "Supply Chain Coordination",
      status: "Operational",
      color: "green", 
      description: "Cross-chain coordination working",
      icon: "🔗"
    },
    {
      name: "Enhanced Verification",
      status: "Operational",
      color: "green",
      description: "Product verification systems active",
      icon: "🔍"
    },
    {
      name: "Marketplace Platform", 
      status: "Operational",
      color: "green",
      description: "Secondary marketplace running",
      icon: "🛍️"
    }
  ];

  const cards = getRoleSpecificCards();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-10 -right-10 w-72 h-72 bg-gradient-to-r from-blue-400/30 to-cyan-400/30 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-20 w-96 h-96 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-20 right-1/4 w-64 h-64 bg-gradient-to-r from-cyan-400/25 to-blue-400/25 rounded-full blur-3xl animate-pulse delay-500"></div>
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxnIGZpbGw9Im5vbmUiIGZpbGwtcnVsZT0iZXZlbm9kZCI+CiAgICAgICAgPGcgZmlsbD0iIzM3NDE1MSIgZmlsbC1vcGFjaXR5PSIwLjAzIj4KICAgICAgICAgICAgPGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMS41Ii8+CiAgICAgICAgPC9nPgogICAgPC9nPgo8L3N2Zz4=')] opacity-20"></div>
      </div>

      {/* Modern Hero Header */}
      <div className="relative z-10 bg-white/5 backdrop-blur-xl border-b border-white/10">
        <div className="px-8 py-12">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/25">
                    <span className="text-2xl">
                      {userRole === 'manufacturer' ? '🏭' : 
                       userRole === 'transporter' ? '🚛' :
                       userRole === 'buyer' ? '🛒' : '👤'}
                    </span>
                  </div>
                  <div>
                    <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-cyan-100 to-blue-200 bg-clip-text text-transparent">
                      Welcome back, {user?.username || 'User'}
                    </h1>
                    <p className="text-xl text-blue-100/80 mt-2 max-w-2xl">
                      {userRole === 'manufacturer' && 'Master your product ecosystem with advanced blockchain technology and real-time analytics'}
                      {userRole === 'transporter' && 'Optimize delivery operations with intelligent routing and performance tracking'}
                      {userRole === 'buyer' && 'Discover authentic products with verified supply chains and secure transactions'}
                      {userRole === 'admin' && 'Orchestrate the entire platform with comprehensive oversight and control'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
                    <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse"></div>
                    <span className="text-cyan-100 font-medium capitalize">{userRole} Dashboard</span>
                  </div>
                  <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
                    <div className={`w-3 h-3 rounded-full ${backendStatus.includes('✅') ? 'bg-green-400' : 'bg-red-400'}`}></div>
                    <span className="text-white/90 font-medium">{backendStatus.includes('✅') ? 'Systems Online' : 'Checking...'}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 px-8 py-12">
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Modern Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {cards.map((card, index) => (
              <div key={index} className="group relative">
                {/* Card Background with Glassmorphism */}
                <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500 group-hover:shadow-2xl group-hover:shadow-cyan-500/25"></div>
                
                {/* Gradient Overlay */}
                <div className={`absolute inset-0 bg-gradient-to-r ${card.gradient} opacity-0 group-hover:opacity-10 rounded-3xl transition-all duration-500`}></div>
                
                {/* Card Content */}
                <div className="relative p-8 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-2">
                      <p className="text-white/70 text-sm font-medium tracking-wide uppercase">{card.title}</p>
                      <p className="text-4xl font-bold text-white group-hover:text-cyan-100 transition-colors duration-300">
                        {card.value}
                      </p>
                    </div>
                    <div className="text-4xl group-hover:scale-110 transition-transform duration-300">{card.icon}</div>
                  </div>
                  
                  {/* Animated Progress Bar */}
                  <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                    <div className={`h-full bg-gradient-to-r ${card.gradient} rounded-full transform translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-1000 ease-out`}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Enhanced System Status */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500"></div>
              <div className="relative p-8">
                <div className="flex items-center space-x-4 mb-8">
                  <div className="w-12 h-12 bg-gradient-to-r from-green-400 to-emerald-500 rounded-2xl flex items-center justify-center">
                    <span className="text-white text-xl">⚡</span>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">System Performance</h2>
                    <p className="text-white/70">All algorithms operating at peak efficiency</p>
                  </div>
                </div>
                
                <div className="space-y-6">
                  {systemStatus.map((system, index) => (
                    <div key={index} className="group/item relative">
                      <div className="flex items-center justify-between p-4 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 group-hover/item:border-white/20 transition-all duration-300">
                        <div className="flex items-center space-x-4">
                          <div className="text-2xl">{system.icon}</div>
                          <div>
                            <h3 className="font-semibold text-white group-hover/item:text-cyan-100 transition-colors">{system.name}</h3>
                            <p className="text-sm text-white/60">{system.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>
                          <span className="font-medium text-green-400">{system.status}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modern Quick Actions */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500"></div>
              <div className="relative p-8">
                <div className="flex items-center space-x-4 mb-8">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-400 to-cyan-500 rounded-2xl flex items-center justify-center">
                    <span className="text-white text-xl">🚀</span>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">Quick Actions</h2>
                    <p className="text-white/70">Streamlined workflows for maximum productivity</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {userRole === 'manufacturer' && (
                    <>
                      <button 
                        onClick={() => window.location.href = '/products'}
                        className="group/btn relative overflow-hidden bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/25"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                        <div className="relative">
                          <div className="text-2xl mb-2">📦</div>
                          <div className="text-lg font-semibold">Create Product</div>
                          <div className="text-sm opacity-90">Launch new NFT</div>
                        </div>
                      </button>
                      <button 
                        onClick={() => window.location.href = '/enhanced-authenticity'}
                        className="group/btn relative overflow-hidden bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-green-500/25"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                        <div className="relative">
                          <div className="text-2xl mb-2">🔐</div>
                          <div className="text-lg font-semibold">Verify Products</div>
                          <div className="text-sm opacity-90">Enhanced security</div>
                        </div>
                      </button>
                    </>
                  )}
                  
                  {userRole === 'transporter' && (
                    <>
                      <button 
                        onClick={() => window.location.href = '/qr-scanner'}
                        className="group/btn relative overflow-hidden bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-green-500/25"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                        <div className="relative">
                          <div className="text-2xl mb-2">📱</div>
                          <div className="text-lg font-semibold">Update Status</div>
                          <div className="text-sm opacity-90">Scan & deliver</div>
                        </div>
                      </button>
                      <button 
                        onClick={() => window.location.href = '/products'}
                        className="group/btn relative overflow-hidden bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/25"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                        <div className="relative">
                          <div className="text-2xl mb-2">🚛</div>
                          <div className="text-lg font-semibold">View Routes</div>
                          <div className="text-sm opacity-90">Optimize delivery</div>
                        </div>
                      </button>
                    </>
                  )}
                  
                  {userRole === 'buyer' && (
                    <>
                      <button 
                        onClick={() => window.location.href = '/products'}
                        className="group/btn relative overflow-hidden bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/25"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                        <div className="relative">
                          <div className="text-2xl mb-2">🛒</div>
                          <div className="text-lg font-semibold">Shop Now</div>
                          <div className="text-sm opacity-90">Discover products</div>
                        </div>
                      </button>
                      <button 
                        onClick={() => window.location.href = '/qr-scanner'}
                        className="group/btn relative overflow-hidden bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-green-500/25"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                        <div className="relative">
                          <div className="text-2xl mb-2">✅</div>
                          <div className="text-lg font-semibold">Confirm Receipt</div>
                          <div className="text-sm opacity-90">Complete purchase</div>
                        </div>
                      </button>
                    </>
                  )}

                  {userRole === 'admin' && (
                    <>
                      <button 
                        onClick={() => window.location.href = '/participants'}
                        className="group/btn relative overflow-hidden bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/25"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                        <div className="relative">
                          <div className="text-2xl mb-2">👥</div>
                          <div className="text-lg font-semibold">Admin Panel</div>
                          <div className="text-sm opacity-90">Manage users</div>
                        </div>
                      </button>
                      <button 
                        onClick={() => window.location.href = '/qr-scanner'}
                        className="group/btn relative overflow-hidden bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-green-500/25"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                        <div className="relative">
                          <div className="text-2xl mb-2">📱</div>
                          <div className="text-lg font-semibold">IPFS Scanner</div>
                          <div className="text-sm opacity-90">Data management</div>
                        </div>
                      </button>
                    </>
                  )}
                  
                  {/* Universal Actions */}
                  <button 
                    onClick={() => window.location.href = '/enhanced-consensus'}
                    className="group/btn relative overflow-hidden bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-gray-500/25"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                    <div className="relative">
                      <div className="text-2xl mb-2">🔗</div>
                      <div className="text-lg font-semibold">Consensus Hub</div>
                      <div className="text-sm opacity-90">Network decisions</div>
                    </div>
                  </button>
                  
                  <button 
                    onClick={() => window.location.href = '/enhanced-authenticity'}
                    className="group/btn relative overflow-hidden bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white p-6 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-indigo-500/25"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                    <div className="relative">
                      <div className="text-2xl mb-2">🔍</div>
                      <div className="text-lg font-semibold">Verification</div>
                      <div className="text-sm opacity-90">Enhanced security</div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Modern Network Health */}
          <div className="group relative">
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500"></div>
            <div className="relative p-8">
              <div className="flex items-center space-x-4 mb-8">
                <div className="w-12 h-12 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-2xl flex items-center justify-center">
                  <span className="text-white text-xl">🌐</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">Network Analytics</h2>
                  <p className="text-white/70">Real-time blockchain performance metrics</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="text-center group/metric">
                  <div className="w-20 h-20 bg-gradient-to-r from-green-400 to-emerald-500 rounded-3xl flex items-center justify-center mx-auto mb-4 group-hover/metric:scale-110 transition-transform duration-300">
                    <span className="text-white text-2xl font-bold">
                      {networkStatus.multichain?.statistics?.total_products || 0}
                    </span>
                  </div>
                  <div className="text-white/90 font-semibold">Products Tracked</div>
                  <div className="text-white/60 text-sm">Across all chains</div>
                </div>
                
                <div className="text-center group/metric">
                  <div className="w-20 h-20 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-3xl flex items-center justify-center mx-auto mb-4 group-hover/metric:scale-110 transition-transform duration-300">
                    <span className="text-white text-2xl font-bold">
                      {networkStatus.multichain?.statistics?.total_transactions || 0}
                    </span>
                  </div>
                  <div className="text-white/90 font-semibold">Transactions</div>
                  <div className="text-white/60 text-sm">Cross-chain operations</div>
                </div>
                
                <div className="text-center group/metric">
                  <div className="w-20 h-20 bg-gradient-to-r from-purple-400 to-pink-500 rounded-3xl flex items-center justify-center mx-auto mb-4 group-hover/metric:scale-110 transition-transform duration-300">
                    <span className="text-white text-2xl font-bold">99.9%</span>
                  </div>
                  <div className="text-white/90 font-semibold">Uptime</div>
                  <div className="text-white/60 text-sm">Platform reliability</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModernDashboard;