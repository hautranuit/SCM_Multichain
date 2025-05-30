import React from 'react';
import { useBlockchain } from '../../contexts/BlockchainContext';
import { useNotification } from '../../contexts/NotificationContext';

export const Header = () => {
  const { account, isConnected, isConnecting, connectWallet, disconnectWallet, chainId, networkStatus } = useBlockchain();
  const { showSuccess, showError } = useNotification();

  const handleConnect = async () => {
    try {
      await connectWallet();
      showSuccess('Wallet connected successfully!');
    } catch (error) {
      showError('Failed to connect wallet');
    }
  };

  const handleDisconnect = () => {
    disconnectWallet();
    showSuccess('Wallet disconnected');
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const getChainName = (chainId) => {
    switch (chainId) {
      case 80002:
        return 'Polygon Amoy';
      case 1001:
        return 'L2 CDK';
      default:
        return 'Unknown Network';
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">CF</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900">ChainFLIP</h1>
            </div>
            <div className="text-sm text-gray-500">Multi-Chain Supply Chain</div>
          </div>

          {/* Network Status */}
          <div className="flex items-center space-x-4">
            {/* Polygon PoS Status */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${networkStatus.polygonPos.connected ? 'network-indicator-online' : 'network-indicator-offline'}`}></div>
              <span className="text-sm text-gray-600">Polygon PoS</span>
            </div>

            {/* L2 CDK Status */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${networkStatus.l2Cdk.connected ? 'network-indicator-online' : 'network-indicator-offline'}`}></div>
              <span className="text-sm text-gray-600">L2 CDK</span>
            </div>

            {/* Wallet Connection */}
            <div className="flex items-center space-x-3">
              {isConnected ? (
                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {formatAddress(account)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {getChainName(chainId)}
                    </div>
                  </div>
                  <button
                    onClick={handleDisconnect}
                    className="btn-secondary text-sm"
                  >
                    Disconnect
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleConnect}
                  disabled={isConnecting}
                  className="btn-primary"
                >
                  {isConnecting ? (
                    <div className="flex items-center space-x-2">
                      <div className="loading-spinner w-4 h-4"></div>
                      <span>Connecting...</span>
                    </div>
                  ) : (
                    'Connect Wallet'
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
