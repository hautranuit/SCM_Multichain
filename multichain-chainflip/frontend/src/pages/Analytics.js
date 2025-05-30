import React, { useState, useEffect } from 'react';
import { useNotification } from '../contexts/NotificationContext';

export const Analytics = () => {
  const { showError } = useNotification();
  
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/dashboard`);
      
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      showError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const MetricCard = ({ title, value, change, icon, color = 'blue' }) => (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change > 0 ? '↗' : '↘'} {Math.abs(change)}% from last period
            </p>
          )}
        </div>
        <div className={`p-3 bg-${color}-100 rounded-lg`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
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
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Performance metrics and insights</p>
        </div>
        
        <div className="flex space-x-3">
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="select-field"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          <button onClick={fetchAnalytics} className="btn-secondary">
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Products"
          value={analytics?.overview?.total_products || 0}
          change={12}
          icon="📦"
          color="blue"
        />
        <MetricCard
          title="Active Participants"
          value={analytics?.overview?.total_participants || 0}
          change={8}
          icon="👥"
          color="green"
        />
        <MetricCard
          title="Transactions"
          value={analytics?.overview?.total_transactions || 0}
          change={15}
          icon="🔄"
          color="purple"
        />
        <MetricCard
          title="Security Score"
          value="98.5%"
          change={2}
          icon="🛡️"
          color="emerald"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Supply Chain Flow */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Supply Chain Flow</h3>
          </div>
          
          <div className="space-y-4">
            {[
              { status: 'Manufactured', count: 45, color: 'bg-blue-500' },
              { status: 'In Transit', count: 23, color: 'bg-yellow-500' },
              { status: 'Delivered', count: 67, color: 'bg-green-500' },
              { status: 'Sold', count: 89, color: 'bg-gray-500' }
            ].map((item) => (
              <div key={item.status} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                  <span className="text-sm font-medium text-gray-900">{item.status}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${item.color}`}
                      style={{ width: `${Math.min(item.count, 100)}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-bold text-gray-900">{item.count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Network Performance */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Network Performance</h3>
          </div>
          
          <div className="grid grid-cols-2 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {analytics?.network_status?.polygon_pos?.latest_block || 0}
              </div>
              <div className="text-sm text-gray-600">Polygon PoS Block</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">99.9%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">0.8s</div>
              <div className="text-sm text-gray-600">Avg Response</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">1.2M</div>
              <div className="text-sm text-gray-600">Gas Used</div>
            </div>
          </div>
        </div>
      </div>

      {/* Security & FL Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security Threats */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Security Overview</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-red-600 text-sm">⚠️</span>
                </div>
                <div>
                  <div className="font-medium text-gray-900">Anomalies Detected</div>
                  <div className="text-sm text-gray-500">Last 7 days</div>
                </div>
              </div>
              <div className="text-2xl font-bold text-red-600">
                {analytics?.security?.anomalies_last_24h || 0}
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                  <span className="text-orange-600 text-sm">🛡️</span>
                </div>
                <div>
                  <div className="font-medium text-gray-900">Counterfeit Alerts</div>
                  <div className="text-sm text-gray-500">Total detected</div>
                </div>
              </div>
              <div className="text-2xl font-bold text-orange-600">
                {analytics?.security?.total_counterfeits || 0}
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 text-sm">✅</span>
                </div>
                <div>
                  <div className="font-medium text-gray-900">Verified Products</div>
                  <div className="text-sm text-gray-500">Authenticity confirmed</div>
                </div>
              </div>
              <div className="text-2xl font-bold text-green-600">98.7%</div>
            </div>
          </div>
        </div>

        {/* FL Performance */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Federated Learning</h3>
          </div>
          
          <div className="space-y-4">
            <div className="text-center py-4">
              <div className="text-4xl font-bold text-blue-600 mb-2">96.3%</div>
              <div className="text-sm text-gray-600">Model Accuracy</div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">15</div>
                <div className="text-xs text-gray-600">Training Rounds</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">8</div>
                <div className="text-xs text-gray-600">Active Nodes</div>
              </div>
            </div>
            
            <div className="pt-4 border-t">
              <div className="text-sm text-gray-600 mb-2">Recent Training Activity</div>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span>Anomaly Detection</span>
                  <span className="text-green-600">✅ Completed</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Counterfeit Detection</span>
                  <span className="text-blue-600">🔄 In Progress</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Participant Activity */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">Top Participants</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Participant
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Products
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reputation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Chain
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {[
                { address: '0x742d35Cc...8C0d', type: 'Manufacturer', products: 45, reputation: 98, chain: 'Polygon PoS' },
                { address: '0x1234567...89ab', type: 'Distributor', products: 32, reputation: 95, chain: 'L2 CDK' },
                { address: '0xabcdef1...2345', type: 'Retailer', products: 28, reputation: 92, chain: 'Polygon PoS' }
              ].map((participant, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {participant.address}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {participant.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {participant.products}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <span className="mr-2">{participant.reputation}</span>
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full" 
                          style={{ width: `${participant.reputation}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {participant.chain}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
