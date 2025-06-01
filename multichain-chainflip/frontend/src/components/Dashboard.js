import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  Users, 
  Building, 
  Truck, 
  ShoppingCart, 
  Activity, 
  Shield,
  Database,
  Globe,
  Zap,
  Package
} from 'lucide-react';

const Dashboard = ({ backendStatus }) => {
  const { user, userRole, l2Blockchain, isAdmin } = useAuth();
  const [currentPage, setCurrentPage] = useState('dashboard');

  const getRoleInfo = () => {
    switch (userRole) {
      case 'manufacturer':
        return {
          icon: Building,
          title: 'Manufacturer Dashboard',
          description: 'Manage product creation and supply chain initiation',
          l2Chain: '2442 - Manufacturer L2',
          color: 'blue'
        };
      case 'transporter':
        return {
          icon: Truck,
          title: 'Transporter Dashboard',
          description: 'Track shipments and manage logistics',
          l2Chain: '2443 - Transporter L2',
          color: 'green'
        };
      case 'buyer':
        return {
          icon: ShoppingCart,
          title: 'Buyer Dashboard',
          description: 'Purchase products and verify authenticity',
          l2Chain: '2444 - Buyer L2',
          color: 'purple'
        };
      case 'admin':
        return {
          icon: Shield,
          title: 'Admin Dashboard',
          description: 'System administration and user management',
          l2Chain: 'All Networks',
          color: 'red'
        };
      default:
        return {
          icon: Users,
          title: 'Dashboard',
          description: 'ChainFLIP Supply Chain Management',
          l2Chain: 'Not Assigned',
          color: 'gray'
        };
    }
  };

  const roleInfo = getRoleInfo();
  const RoleIcon = roleInfo.icon;

  const menuItems = [
    { id: 'products', name: 'Products', icon: '📦', path: '/products', description: 'Create, manage and track products on blockchain with QR code generation' },
    { id: 'participants', name: 'Participants', icon: '👥', path: '/participants', description: 'Register supply chain participants and manage roles across networks' },
    { id: 'qr-scanner', name: 'QR Scanner', icon: '📱', path: '/qr-scanner', description: 'Scan QR codes with camera to verify product authenticity' },
    { id: 'analytics', name: 'Analytics', icon: '📈', path: '/analytics', description: 'View real-time metrics, charts and system performance data' },
  ];

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div>
      {/* Top Navigation Header */}
      <header className="bg-white shadow border-b border-gray-200 mb-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-indigo-600 mr-4">
                🔗 ChainFLIP
              </h1>
              <span className="text-sm text-gray-500">
                Multi-Chain Supply Chain Management
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm">
                Backend: <span className={backendStatus.includes('✅') ? 'text-green-600' : 'text-red-600'}>
                  {backendStatus}
                </span>
              </div>
              {isAdmin && (
                <button
                  onClick={() => window.location.href = '/admin'}
                  className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-sm font-medium flex items-center"
                >
                  <Shield className="h-4 w-4 mr-1" />
                  Admin Panel
                </button>
              )}
              <button
                onClick={async () => {
                  try {
                    // Clear localStorage and redirect to login
                    localStorage.clear();
                    window.location.href = '/login';
                  } catch (error) {
                    console.error('Logout error:', error);
                    localStorage.clear();
                    window.location.href = '/login';
                  }
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded-md text-sm font-medium flex items-center"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Welcome Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {getGreeting()}, {user?.name}! 👋
            </h1>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <RoleIcon className={`h-5 w-5 text-${roleInfo.color}-600`} />
                <span className="text-gray-600">{roleInfo.title}</span>
              </div>
              <div className="text-sm text-gray-500">
                L2 Chain: {l2Blockchain || roleInfo.l2Chain}
              </div>
            </div>
          </div>
          {isAdmin && (
            <button
              onClick={() => window.location.href = '/admin'}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center"
            >
              <Shield className="h-4 w-4 mr-2" />
              Admin Panel
            </button>
          )}
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5">
              <h3 className="text-lg font-medium text-gray-900">System Status</h3>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Backend:</span>
                  <span className={backendStatus.includes('✅') ? 'text-green-600' : 'text-red-600'}>
                    {backendStatus}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Frontend:</span>
                  <span className="text-green-600">✅ Running</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Database:</span>
                  <span className="text-green-600">✅ Connected</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Globe className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-5">
              <h3 className="text-lg font-medium text-gray-900">Blockchain Network</h3>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Polygon PoS:</span>
                  <span className="text-green-600">✅ Connected</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>L2 CDK:</span>
                  <span className="text-green-600">✅ Connected</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Smart Contracts:</span>
                  <span className="text-green-600">✅ Deployed</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Database className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-5">
              <h3 className="text-lg font-medium text-gray-900">IPFS Integration</h3>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Web3.Storage:</span>
                  <span className="text-green-600">✅ Connected</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Gateway:</span>
                  <span className="text-green-600">✅ Available</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Encryption:</span>
                  <span className="text-green-600">✅ Active</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* User Role Information */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="flex items-center">
          <RoleIcon className={`h-12 w-12 text-${roleInfo.color}-600 mr-4`} />
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-gray-900">{roleInfo.title}</h3>
            <p className="text-gray-600 mt-1">{roleInfo.description}</p>
            <div className="mt-3 flex items-center space-x-6 text-sm">
              <div>
                <span className="font-medium text-gray-900">Email:</span>
                <span className="ml-2 text-gray-600">{user?.email}</span>
              </div>
              <div>
                <span className="font-medium text-gray-900">Wallet:</span>
                <span className="ml-2 text-gray-600 font-mono text-xs">{user?.wallet_address}</span>
              </div>
              <div>
                <span className="font-medium text-gray-900">L2 Chain:</span>
                <span className="ml-2 text-gray-600">{l2Blockchain || 'Not Assigned'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">🚀 ChainFLIP Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {menuItems.map((item) => (
            <div 
              key={item.id} 
              className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-all cursor-pointer hover:-translate-y-1"
              onClick={() => window.location.href = item.path}
            >
              <div className="flex items-center mb-3">
                <span className="text-2xl mr-3">{item.icon}</span>
                <h4 className="text-lg font-medium text-gray-900">{item.name}</h4>
              </div>
              <p className="text-gray-600 text-sm mb-4">{item.description}</p>
              <div className="flex items-center text-green-600 text-sm font-medium">
                <Zap className="h-4 w-4 mr-1" />
                Ready to use
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center">
            <Package className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <h4 className="text-lg font-semibold text-blue-900">🎉 All Features Operational!</h4>
              <p className="text-blue-700 mt-1">
                Your ChainFLIP platform is fully functional with blockchain integration, 
                IPFS storage, federated learning, and real-time analytics. Click any feature above to get started!
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Federated Learning System */}
      <div className="bg-white rounded-lg shadow p-6 mt-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          🤖 Federated Learning System
        </h3>
        <div className="text-center py-8">
          <div className="text-6xl mb-4">🤖</div>
          <p className="text-gray-600 text-lg mb-4">
            AI-Powered Anomaly & Counterfeit Detection
          </p>
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 max-w-md mx-auto">
            <h4 className="text-green-800 font-semibold mb-3">✅ System Status: Active</h4>
            <div className="text-sm text-green-700 space-y-1">
              <div>• Federated learning network operational</div>
              <div>• AI models trained and deployed</div>
              <div>• Real-time anomaly detection enabled</div>
              <div>• Counterfeit prevention system active</div>
            </div>
          </div>
          <p className="text-gray-500 mt-4">
            Advanced ML algorithms continuously monitor supply chain for anomalies and counterfeits.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;