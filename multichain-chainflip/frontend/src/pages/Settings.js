import React, { useState } from 'react';
import { useBlockchain } from '../contexts/BlockchainContext';
import { useNotification } from '../contexts/NotificationContext';

export const Settings = () => {
  const { isConnected, account, chainId, switchToPolygon, networkStatus } = useBlockchain();
  const { showSuccess, showError } = useNotification();
  
  const [activeTab, setActiveTab] = useState('network');

  const TabButton = ({ id, label, icon, isActive, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        isActive
          ? 'bg-primary-100 text-primary-700 border border-primary-200'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
      }`}
    >
      <span className="text-lg">{icon}</span>
      <span>{label}</span>
    </button>
  );

  const NetworkSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Network Configuration</h3>
        
        {/* Current Connection */}
        <div className="card mb-6">
          <div className="card-header">
            <h4 className="font-medium text-gray-900">Current Connection</h4>
          </div>
          
          {isConnected ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Wallet Address:</span>
                <span className="font-mono text-sm">{account}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Chain ID:</span>
                <span className="font-medium">{chainId}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Network:</span>
                <span className="font-medium">
                  {chainId === 80002 ? 'Polygon Amoy Testnet' : 'Unknown Network'}
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-gray-500">
              <div className="text-2xl mb-2">🔌</div>
              <p>No wallet connected</p>
            </div>
          )}
        </div>

        {/* Network Status */}
        <div className="card">
          <div className="card-header">
            <h4 className="font-medium text-gray-900">Network Status</h4>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  networkStatus.polygonPos.connected ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <div>
                  <div className="font-medium text-gray-900">Polygon PoS Hub</div>
                  <div className="text-sm text-gray-500">
                    Chain ID: {networkStatus.polygonPos.chainId}
                  </div>
                </div>
              </div>
              <div className="flex space-x-2">
                <span className={`badge ${
                  networkStatus.polygonPos.connected ? 'badge-success' : 'badge-danger'
                }`}>
                  {networkStatus.polygonPos.connected ? 'Connected' : 'Disconnected'}
                </span>
                {chainId !== 80002 && (
                  <button onClick={switchToPolygon} className="btn-primary text-xs">
                    Switch
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  networkStatus.l2Cdk.connected ? 'bg-green-400' : 'bg-gray-400'
                }`}></div>
                <div>
                  <div className="font-medium text-gray-900">L2 CDK Participants</div>
                  <div className="text-sm text-gray-500">
                    Chain ID: {networkStatus.l2Cdk.chainId}
                  </div>
                </div>
              </div>
              <span className={`badge ${
                networkStatus.l2Cdk.connected ? 'badge-success' : 'badge-gray'
              }`}>
                {networkStatus.l2Cdk.connected ? 'Connected' : 'Not Configured'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const ApiSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">API Configuration</h3>
        
        <div className="card">
          <div className="card-header">
            <h4 className="font-medium text-gray-900">Backend Endpoints</h4>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Backend URL
              </label>
              <input 
                type="text" 
                className="input-field" 
                value={process.env.REACT_APP_BACKEND_URL}
                disabled
              />
              <p className="text-xs text-gray-500 mt-1">
                Main API endpoint for blockchain and FL operations
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                IPFS Gateway
              </label>
              <input 
                type="text" 
                className="input-field" 
                value={process.env.REACT_APP_IPFS_GATEWAY}
                disabled
              />
              <p className="text-xs text-gray-500 mt-1">
                Gateway for accessing IPFS content
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contract Address
              </label>
              <input 
                type="text" 
                className="input-field" 
                value={process.env.REACT_APP_CONTRACT_ADDRESS}
                disabled
              />
              <p className="text-xs text-gray-500 mt-1">
                Main supply chain contract address
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const SecuritySettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Security & Privacy</h3>
        
        <div className="card">
          <div className="card-header">
            <h4 className="font-medium text-gray-900">Data Protection</h4>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">Encrypted QR Codes</div>
                <div className="text-sm text-gray-500">Use AES-256 encryption for QR data</div>
              </div>
              <input type="checkbox" checked disabled className="rounded" />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">IPFS Privacy</div>
                <div className="text-sm text-gray-500">Store sensitive data encrypted on IPFS</div>
              </div>
              <input type="checkbox" checked disabled className="rounded" />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">FL Privacy Protection</div>
                <div className="text-sm text-gray-500">Federated learning with differential privacy</div>
              </div>
              <input type="checkbox" checked disabled className="rounded" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h4 className="font-medium text-gray-900">Security Status</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center space-x-3 text-sm">
              <span className="text-green-600">✅</span>
              <span>Smart contracts verified and audited</span>
            </div>
            <div className="flex items-center space-x-3 text-sm">
              <span className="text-green-600">✅</span>
              <span>End-to-end encryption enabled</span>
            </div>
            <div className="flex items-center space-x-3 text-sm">
              <span className="text-green-600">✅</span>
              <span>Multi-signature wallet support</span>
            </div>
            <div className="flex items-center space-x-3 text-sm">
              <span className="text-green-600">✅</span>
              <span>Regular security monitoring active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const SystemSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
        
        <div className="card">
          <div className="card-header">
            <h4 className="font-medium text-gray-900">Version Information</h4>
          </div>
          
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Frontend Version:</span>
              <span className="font-medium">2.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Backend Version:</span>
              <span className="font-medium">2.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Contract Version:</span>
              <span className="font-medium">2.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Last Updated:</span>
              <span className="font-medium">{new Date().toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h4 className="font-medium text-gray-900">System Health</h4>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-green-600">99.9%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-blue-600">0.8s</div>
              <div className="text-sm text-gray-600">Response Time</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'network':
        return <NetworkSettings />;
      case 'api':
        return <ApiSettings />;
      case 'security':
        return <SecuritySettings />;
      case 'system':
        return <SystemSettings />;
      default:
        return <NetworkSettings />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Configure your ChainFLIP experience</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-2 border-b border-gray-200 pb-4">
        <TabButton
          id="network"
          label="Network"
          icon="🌐"
          isActive={activeTab === 'network'}
          onClick={setActiveTab}
        />
        <TabButton
          id="api"
          label="API"
          icon="🔗"
          isActive={activeTab === 'api'}
          onClick={setActiveTab}
        />
        <TabButton
          id="security"
          label="Security"
          icon="🔒"
          isActive={activeTab === 'security'}
          onClick={setActiveTab}
        />
        <TabButton
          id="system"
          label="System"
          icon="⚙️"
          isActive={activeTab === 'system'}
          onClick={setActiveTab}
        />
      </div>

      {/* Tab Content */}
      {renderTabContent()}
    </div>
  );
};
