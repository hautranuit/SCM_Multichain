import React, { useState, useEffect } from 'react';
import { useBlockchain } from '../contexts/BlockchainContext';
import { useNotification } from '../contexts/NotificationContext';

export const Dashboard = () => {
  const { isConnected, networkStatus } = useBlockchain();
  const { showError } = useNotification();
  
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [flStats, setFlStats] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch system statistics
      const statsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/dashboard`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }
      
      // Fetch FL statistics
      const flResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/federated-learning/status`);
      if (flResponse.ok) {
        const flData = await flResponse.json();
        setFlStats(flData);
      }
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      showError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, subtitle, icon, color = 'primary' }) => (
    <div className="card">
      <div className="flex items-center">
        <div className={`flex-shrink-0 p-3 bg-${color}-100 rounded-lg`}>
          <span className="text-2xl">{icon}</span>
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
      </div>
    </div>
  );

  const NetworkStatusCard = () => (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold text-gray-900">Network Status</h3>
      </div>
      
      <div className="space-y-4">
        {/* Polygon PoS */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${networkStatus.polygonPos.connected ? 'bg-green-400' : 'bg-red-400'}`}></div>
            <div>
              <div className="font-medium text-gray-900">Polygon PoS Hub</div>
              <div className="text-sm text-gray-500">Chain ID: {networkStatus.polygonPos.chainId}</div>
            </div>
          </div>
          <span className={`badge ${networkStatus.polygonPos.connected ? 'badge-success' : 'badge-danger'}`}>
            {networkStatus.polygonPos.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* L2 CDK */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${networkStatus.l2Cdk.connected ? 'bg-green-400' : 'bg-gray-400'}`}></div>
            <div>
              <div className="font-medium text-gray-900">L2 CDK Participants</div>
              <div className="text-sm text-gray-500">Chain ID: {networkStatus.l2Cdk.chainId}</div>
            </div>
          </div>
          <span className={`badge ${networkStatus.l2Cdk.connected ? 'badge-success' : 'badge-gray'}`}>
            {networkStatus.l2Cdk.connected ? 'Connected' : 'Not Configured'}
          </span>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">ChainFLIP Multi-Chain Supply Chain Management</p>
        </div>
        <button 
          onClick={fetchDashboardData}
          className="btn-secondary"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Connection Warning */}
      {!isConnected && (
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-warning-600 text-xl">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-warning-800">
                Wallet Not Connected
              </h3>
              <div className="mt-2 text-sm text-warning-700">
                <p>Connect your wallet to interact with the ChainFLIP network and view real-time data.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Products"
          value={stats?.overview?.total_products || 0}
          subtitle={`+${stats?.overview?.products_last_7_days || 0} this week`}
          icon="📦"
          color="primary"
        />
        <StatCard
          title="Active Participants"
          value={stats?.overview?.total_participants || 0}
          subtitle="Network nodes"
          icon="👥"
          color="success"
        />
        <StatCard
          title="Transactions"
          value={stats?.overview?.total_transactions || 0}
          subtitle="Multi-chain"
          icon="🔄"
          color="warning"
        />
        <StatCard
          title="FL Models"
          value={flStats?.models?.anomaly_detection?.training_rounds || 0}
          subtitle="Training rounds"
          icon="🤖"
          color="purple"
        />
      </div>

      {/* Network and FL Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <NetworkStatusCard />
        
        {/* FL Status Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Federated Learning Status</h3>
          </div>
          
          {flStats ? (
            <div className="space-y-4">
              {/* Anomaly Detection */}
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div>
                  <div className="font-medium text-gray-900">Anomaly Detection</div>
                  <div className="text-sm text-gray-500">
                    Round {flStats.models?.anomaly_detection?.training_rounds || 0} • 
                    {flStats.models?.anomaly_detection?.active_participants || 0} participants
                  </div>
                </div>
                <span className="badge badge-info">Active</span>
              </div>

              {/* Counterfeit Detection */}
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <div>
                  <div className="font-medium text-gray-900">Counterfeit Detection</div>
                  <div className="text-sm text-gray-500">
                    Round {flStats.models?.counterfeit_detection?.training_rounds || 0} • 
                    {flStats.models?.counterfeit_detection?.active_participants || 0} participants
                  </div>
                </div>
                <span className="badge badge-info">Active</span>
              </div>

              {/* Detection Stats */}
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{flStats.detections?.anomalies_detected || 0}</div>
                  <div className="text-sm text-gray-500">Anomalies Detected</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{flStats.detections?.counterfeits_detected || 0}</div>
                  <div className="text-sm text-gray-500">Counterfeits Found</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-2xl mb-2">🤖</div>
              <p>Loading FL status...</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
        </div>
        
        <div className="space-y-3">
          {stats?.recent_activity ? (
            stats.recent_activity.map((activity, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-600 text-sm">🔄</span>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                  <p className="text-xs text-gray-500">{activity.timestamp}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-2xl mb-2">📊</div>
              <p>No recent activity</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
