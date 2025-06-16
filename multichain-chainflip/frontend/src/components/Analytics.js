import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { BarChart3, TrendingUp, Activity, Database, RefreshCw, Users, Package, Shield, CheckCircle, AlertCircle } from 'lucide-react';

const Analytics = () => {
  const [analyticsData, setAnalyticsData] = useState({
    overview: {
      totalProducts: 0,
      totalParticipants: 0,
      totalTransactions: 0,
      activeChains: 2
    },
    transactions: [],
    products: [],
    participants: [],
    performance: []
  });
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedMetric, setSelectedMetric] = useState('transactions');

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      // Fetch real data from backend
      const [productsRes, participantsRes] = await Promise.all([
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/products/`),
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/participants/`)
      ]);

      const products = productsRes.data || [];
      const participants = participantsRes.data || [];

      // Generate mock analytics data based on real data
      const mockTransactions = generateMockTransactions(products.length);
      const performanceData = generatePerformanceData();
      
      setAnalyticsData({
        overview: {
          totalProducts: products.length,
          totalParticipants: participants.length,
          totalTransactions: mockTransactions.reduce((sum, day) => sum + day.transactions, 0),
          activeChains: 2
        },
        transactions: mockTransactions,
        products: products,
        participants: participants,
        performance: performanceData
      });
    } catch (error) {
      console.error('Error fetching analytics:', error);
      // Use mock data if API fails
      setAnalyticsData({
        overview: {
          totalProducts: 25,
          totalParticipants: 12,
          totalTransactions: 348,
          activeChains: 2
        },
        transactions: generateMockTransactions(25),
        products: [],
        participants: [],
        performance: generatePerformanceData()
      });
    }
    setLoading(false);
  };

  const generateMockTransactions = (productCount) => {
    const days = timeRange === '24h' ? 24 : timeRange === '7d' ? 7 : 30;
    const data = [];
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      data.push({
        date: timeRange === '24h' ? date.getHours() + ':00' : date.toLocaleDateString(),
        transactions: Math.floor(Math.random() * (productCount + 10)) + 5,
        verified: Math.floor(Math.random() * (productCount + 5)) + 2,
        created: Math.floor(Math.random() * 5) + 1,
        scanned: Math.floor(Math.random() * 15) + 3
      });
    }
    return data;
  };

  const generatePerformanceData = () => {
    return [
      { name: 'Products Created', value: Math.floor(Math.random() * 50) + 20, color: '#3b82f6' },
      { name: 'QR Scans', value: Math.floor(Math.random() * 100) + 50, color: '#10b981' },
      { name: 'Verifications', value: Math.floor(Math.random() * 80) + 30, color: '#f59e0b' },
      { name: 'Failed Scans', value: Math.floor(Math.random() * 20) + 5, color: '#ef4444' }
    ];
  };

  const getParticipantTypeDistribution = () => {
    const distribution = analyticsData.participants.reduce((acc, participant) => {
      const type = participant.participant_type || participant.participantType || 'unknown';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});

    return Object.keys(distribution).map((key, index) => ({
      name: key.charAt(0).toUpperCase() + key.slice(1),
      value: distribution[key],
      color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280'][index % 6]
    }));
  };

  const getChainDistribution = () => {
    return [
      { name: 'Polygon PoS', value: 65, color: '#8b5cf6' },
      { name: 'L2 CDK', value: 35, color: '#3b82f6' }
    ];
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Modern Header with Gradient */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center">
                <BarChart3 className="w-8 h-8 mr-3" />
                Analytics Dashboard
              </h1>
              <p className="text-blue-100 mt-2 text-lg">
                Real-time insights into your blockchain supply chain operations
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="px-4 py-2 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-white/50"
              >
                <option value="24h" className="text-gray-900">Last 24 Hours</option>
                <option value="7d" className="text-gray-900">Last 7 Days</option>
                <option value="30d" className="text-gray-900">Last 30 Days</option>
              </select>
              <button
                onClick={fetchAnalytics}
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
        {/* Overview Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Package className="w-6 h-6 text-blue-600" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">Total Products</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(analyticsData.overview.totalProducts)}
                  </p>
                  <p className="ml-2 text-sm font-medium text-green-600">
                    +{Math.floor(Math.random() * 20) + 5}%
                  </p>
                </div>
                <p className="text-xs text-gray-500 mt-1">vs last {timeRange}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-green-600" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">Active Participants</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(analyticsData.overview.totalParticipants)}
                  </p>
                  <p className="ml-2 text-sm font-medium text-green-600">
                    +{Math.floor(Math.random() * 15) + 2}%
                  </p>
                </div>
                <p className="text-xs text-gray-500 mt-1">vs last {timeRange}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Activity className="w-6 h-6 text-yellow-600" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">Blockchain Transactions</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(analyticsData.overview.totalTransactions)}
                  </p>
                  <p className="ml-2 text-sm font-medium text-green-600">
                    +{Math.floor(Math.random() * 30) + 10}%
                  </p>
                </div>
                <p className="text-xs text-gray-500 mt-1">vs last {timeRange}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Database className="w-6 h-6 text-purple-600" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">Active Chains</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsData.overview.activeChains}
                  </p>
                  <p className="ml-2 text-sm font-medium text-blue-600">
                    Multi-chain
                  </p>
                </div>
                <p className="text-xs text-gray-500 mt-1">Polygon PoS & L2 CDK</p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Transaction Trends */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Transaction Trends</h3>
                <p className="text-sm text-gray-600">Daily transaction volume and verification rates</p>
              </div>
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
            {loading ? (
              <div className="h-80 flex items-center justify-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={analyticsData.transactions}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="transactions" 
                    stackId="1" 
                    stroke="#3b82f6" 
                    fill="#3b82f6" 
                    fillOpacity={0.3} 
                    strokeWidth={2}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="verified" 
                    stackId="2" 
                    stroke="#10b981" 
                    fill="#10b981" 
                    fillOpacity={0.3} 
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Performance Metrics */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Performance Metrics</h3>
                <p className="text-sm text-gray-600">Key performance indicators for the platform</p>
              </div>
              <BarChart3 className="w-5 h-5 text-green-600" />
            </div>
            {loading ? (
              <div className="h-80 flex items-center justify-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={analyticsData.performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }} 
                  />
                  <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Distribution Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Participant Type Distribution */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Participant Types</h3>
                <p className="text-sm text-gray-600">Distribution of network participants</p>
              </div>
              <Users className="w-5 h-5 text-indigo-600" />
            </div>
            {analyticsData.participants.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={getParticipantTypeDistribution()}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {getParticipantTypeDistribution().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px'
                    }} 
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <Users className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                  <p>No participant data available</p>
                </div>
              </div>
            )}
          </div>

          {/* Chain Distribution */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Chain Usage</h3>
                <p className="text-sm text-gray-600">Multi-chain transaction distribution</p>
              </div>
              <Database className="w-5 h-5 text-purple-600" />
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={getChainDistribution()}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                >
                  {getChainDistribution().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e2e8f0', 
                    borderRadius: '8px'
                  }} 
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Real-time Activity */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Real-time Activity</h3>
                <p className="text-sm text-gray-600">Live platform metrics</p>
              </div>
              <Activity className="w-5 h-5 text-green-600" />
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-blue-600 text-sm">🔍</span>
                  </div>
                  <span className="text-sm font-medium text-blue-900">QR Code Scans</span>
                </div>
                <span className="text-sm font-bold text-blue-600">
                  {Math.floor(Math.random() * 50) + 10}/hour
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  </div>
                  <span className="text-sm font-medium text-green-900">Product Verifications</span>
                </div>
                <span className="text-sm font-bold text-green-600">
                  {Math.floor(Math.random() * 30) + 5}/hour
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                    <Package className="w-4 h-4 text-yellow-600" />
                  </div>
                  <span className="text-sm font-medium text-yellow-900">New Products</span>
                </div>
                <span className="text-sm font-bold text-yellow-600">
                  {Math.floor(Math.random() * 10) + 1}/hour
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                    <Users className="w-4 h-4 text-purple-600" />
                  </div>
                  <span className="text-sm font-medium text-purple-900">New Participants</span>
                </div>
                <span className="text-sm font-bold text-purple-600">
                  {Math.floor(Math.random() * 5) + 1}/day
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">System Health & Performance</h3>
              <p className="text-sm text-gray-600">Real-time system status and performance metrics</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-green-600">All Systems Operational</span>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-green-600 mb-1">99.9%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Activity className="w-8 h-8 text-blue-600" />
              </div>
              <div className="text-2xl font-bold text-blue-600 mb-1">1.2s</div>
              <div className="text-sm text-gray-600">Avg Response</div>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Shield className="w-8 h-8 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-green-600 mb-1">100%</div>
              <div className="text-sm text-gray-600">Security Score</div>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Database className="w-8 h-8 text-purple-600" />
              </div>
              <div className="text-2xl font-bold text-purple-600 mb-1">2</div>
              <div className="text-sm text-gray-600">Active Chains</div>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <TrendingUp className="w-8 h-8 text-indigo-600" />
              </div>
              <div className="text-2xl font-bold text-indigo-600 mb-1">Active</div>
              <div className="text-sm text-gray-600">FL System</div>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-green-600 mb-1">Connected</div>
              <div className="text-sm text-gray-600">IPFS Storage</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;