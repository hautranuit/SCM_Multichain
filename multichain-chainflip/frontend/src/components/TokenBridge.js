/**
 * Token Bridge Component for Cross-Chain ETH Transfers with LayerZero V2 OFT
 * Integrates with LayerZero OFT contracts for real ETH bridging with auto-conversion
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ArrowRight, Wallet, DollarSign, Clock, CheckCircle, AlertCircle, Activity, RefreshCw, Link, Zap, CreditCard, ArrowLeftRight, TrendingUp, Globe } from 'lucide-react';

const TokenBridge = () => {
  const { user, userRole } = useAuth();
  const [loading, setLoading] = useState(false);
  const [balances, setBalances] = useState({});
  const [transfers, setTransfers] = useState([]);
  const [transferForm, setTransferForm] = useState({
    from_chain: 'arbitrum_sepolia', // Pre-select working source chain
    to_chain: 'base_sepolia',       // Pre-select working destination chain
    from_address: user?.wallet_address || '',
    to_address: '',
    amount_eth: '',
    escrow_id: ''
  });
  const [feeEstimate, setFeeEstimate] = useState(null);
  const [transferResult, setTransferResult] = useState(null);
  const [activeTransfers, setActiveTransfers] = useState({});
  const [infrastructureStatus, setInfrastructureStatus] = useState(null);

  // LayerZero Chain configurations - Updated to match working transfers
  const chains = {
    arbitrum_sepolia: {
      name: 'Arbitrum Sepolia',
      role: 'Source Chain (Working)',
      color: '#28a2d8',
      icon: '🔵',
      layerzero_eid: 40231,
      chain_id: 421614
    },
    base_sepolia: {
      name: 'Base Sepolia',
      role: 'Destination Chain (Working)', 
      color: '#0052ff',
      icon: '🔷',
      layerzero_eid: 40245,
      chain_id: 84532
    },
    optimism_sepolia: {
      name: 'Optimism Sepolia',
      role: 'Alternative Chain (Needs Setup)',
      color: '#ff0420',
      icon: '🔴',
      layerzero_eid: 40232,
      chain_id: 11155420
    },
    polygon_amoy: {
      name: 'Polygon Amoy',
      role: 'Hub Chain (Needs Setup)',
      color: '#8247e5',
      icon: '🟣',
      layerzero_eid: 40267,
      chain_id: 80002
    }
  };

  useEffect(() => {
    // Check for URL parameters to prefill the form
    const urlParams = new URLSearchParams(window.location.search);
    const fromChain = urlParams.get('from_chain');
    const toChain = urlParams.get('to_chain');
    const toAddress = urlParams.get('to_address');
    const amountEth = urlParams.get('amount_eth');
    const escrowId = urlParams.get('escrow_id');
    const purpose = urlParams.get('purpose');

    if (toChain || toAddress || amountEth) {
      setTransferForm(prev => ({
        ...prev,
        from_chain: fromChain || prev.from_chain,
        to_chain: toChain || prev.to_chain,
        to_address: toAddress || prev.to_address,
        amount_eth: amountEth || prev.amount_eth,
        escrow_id: escrowId || prev.escrow_id
      }));
      
      if (purpose) {
        // Show a message about the purpose
        setTimeout(() => {
          alert(`🌉 LayerZero Bridge\n\nPurpose: ${purpose}\n\nThe form has been pre-filled with the transfer details.`);
        }, 500);
      }
    }

    fetchInfrastructureStatus();
    fetchTransfers();
    // Poll for updates every 30 seconds
    const interval = setInterval(() => {
      fetchTransfers();
      updateActiveTransfers();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (transferForm.from_chain && transferForm.to_chain && transferForm.amount_eth) {
      estimateTransferFee();
    }
  }, [transferForm.from_chain, transferForm.to_chain, transferForm.amount_eth]);

  const fetchInfrastructureStatus = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/layerzero-oft/infrastructure-status`);
      const data = await response.json();
      setInfrastructureStatus(data);
    } catch (error) {
      console.error('Error fetching infrastructure status:', error);
    }
  };

  const fetchTransfers = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/layerzero-oft/transfers?limit=20`);
      const data = await response.json();
      if (data.success) {
        setTransfers(data.transfers || []);
      }
    } catch (error) {
      console.error('Error fetching transfers:', error);
    }
  };

  const estimateTransferFee = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/layerzero-oft/estimate-fee`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_chain: transferForm.from_chain,
          to_chain: transferForm.to_chain,
          amount_eth: parseFloat(transferForm.amount_eth)
        })
      });
      const data = await response.json();
      setFeeEstimate(data);
    } catch (error) {
      console.error('Error estimating fee:', error);
      setFeeEstimate({ success: false, error: error.message });
    }
  };

  const executeTransfer = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTransferResult(null);

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/layerzero-oft/transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...transferForm,
          amount_eth: parseFloat(transferForm.amount_eth),
          escrow_id: transferForm.escrow_id || `LZ-BRIDGE-${Date.now()}-${user?.id || 'user'}`
        })
      });
      const data = await response.json();
      
      setTransferResult(data);
      
      if (data.success) {
        // Add to active transfers for tracking
        setActiveTransfers(prev => ({
          ...prev,
          [data.result?.transfer_id || data.transfer_id]: {
            ...transferForm,
            transfer_id: data.result?.transfer_id || data.transfer_id,
            status: 'processing',
            timestamp: Date.now(),
            auto_conversion: data.result?.auto_conversion || false,
            conversion_tx: data.result?.conversion_tx
          }
        }));
        
        // Reset form
        setTransferForm({
          from_chain: '',
          to_chain: '',
          from_address: user?.wallet_address || '',
          to_address: '',
          amount_eth: '',
          escrow_id: ''
        });
        
        // Refresh data
        setTimeout(() => {
          fetchTransfers();
        }, 2000);
      }
    } catch (error) {
      console.error('Transfer error:', error);
      setTransferResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const testEnhancedInfrastructure = async () => {
    setLoading(true);
    setTransferResult(null);

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/layerzero-oft/test-enhanced-infrastructure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      setTransferResult(data);
    } catch (error) {
      console.error('Test error:', error);
      setTransferResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const updateActiveTransfers = async () => {
    const activeIds = Object.keys(activeTransfers);
    if (activeIds.length === 0) return;

    for (const transferId of activeIds) {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/layerzero-oft/status/${transferId}`, {
          method: 'GET'
        });
        const data = await response.json();
        
        if (data.success && data.status === 'completed') {
          // Remove from active transfers
          setActiveTransfers(prev => {
            const { [transferId]: removed, ...rest } = prev;
            return rest;
          });
        }
      } catch (error) {
        console.error(`Error checking status for ${transferId}:`, error);
      }
    }
  };

  const getChainOptions = (exclude = '') => {
    return Object.entries(chains)
      .filter(([key]) => key !== exclude)
      .map(([key, chain]) => ({ key, ...chain }));
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const formatBalance = (balance) => {
    return balance ? parseFloat(balance).toFixed(4) : '0.0000';
  };

  const getBlockExplorerUrl = (txHash, chainKey) => {
    const explorers = {
      arbitrum_sepolia: `https://sepolia.arbiscan.io/tx/${txHash}`,
      base_sepolia: `https://sepolia.basescan.org/tx/${txHash}`,
      optimism_sepolia: `https://sepolia.etherscan.io/tx/${txHash}`,
      polygon_amoy: `https://amoy.polygonscan.com/tx/${txHash}`
    };
    return explorers[chainKey] || '#';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Modern Header with Gradient */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
        <div className="px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center">
                <ArrowLeftRight className="w-8 h-8 mr-3" />
                LayerZero Bridge
              </h1>
              <p className="text-emerald-100 mt-2 text-lg">
                Cross-chain ETH transfers with automatic cfWETH → ETH conversion and zero-slippage bridging
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => {
                  fetchInfrastructureStatus();
                  fetchTransfers();
                }}
                className="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg shadow-sm text-sm font-medium text-white hover:bg-white/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </button>
              <button
                onClick={testEnhancedInfrastructure}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 bg-white text-emerald-600 rounded-lg shadow-sm text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white disabled:opacity-50"
              >
                <Zap className="w-4 h-4 mr-2" />
                Test Transfer
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Infrastructure Status */}
        {infrastructureStatus && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Globe className="w-5 h-5 mr-2" />
                  LayerZero Infrastructure Status
                </h2>
                <p className="text-sm text-gray-600">Real-time status of cross-chain bridge endpoints</p>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-green-600">All Systems Operational</span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(infrastructureStatus.chains || {}).map(([chainKey, status]) => (
                <div key={chainKey} className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <span className="text-xl">{chains[chainKey]?.icon}</span>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${
                      status.status === 'operational' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-1">{chains[chainKey]?.name}</h3>
                  <p className="text-xs text-gray-500 mb-2">EID: {chains[chainKey]?.layerzero_eid}</p>
                  <div className="space-y-1 text-xs text-gray-600">
                    <div className="flex justify-between">
                      <span>OFT:</span>
                      <span className="font-mono">{formatAddress(status.oft_address)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <span className={`capitalize ${status.status === 'operational' ? 'text-green-600' : 'text-red-600'}`}>
                        {status.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Transfer Form */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <div className="border-b border-gray-200 pb-4 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <CreditCard className="w-5 h-5 mr-2" />
              Cross-Chain Transfer
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Send ETH across chains with LayerZero's unified liquidity protocol
            </p>
          </div>
          
          <form onSubmit={executeTransfer} className="space-y-6">
            {/* Chain Selection with Visual Enhancement */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Source Chain
                </label>
                <select
                  value={transferForm.from_chain}
                  onChange={(e) => setTransferForm({ ...transferForm, from_chain: e.target.value })}
                  className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white"
                  required
                >
                  <option value="">Select source chain</option>
                  {getChainOptions().map(({ key, name, role, icon, layerzero_eid }) => (
                    <option key={key} value={key}>
                      {icon} {name} (EID: {layerzero_eid})
                    </option>
                  ))}
                </select>
                {transferForm.from_chain && (
                  <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                    <div className="text-sm text-blue-800">
                      <strong>{chains[transferForm.from_chain]?.name}</strong>
                      <div className="text-xs text-blue-600">{chains[transferForm.from_chain]?.role}</div>
                    </div>
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Destination Chain
                </label>
                <select
                  value={transferForm.to_chain}
                  onChange={(e) => setTransferForm({ ...transferForm, to_chain: e.target.value })}
                  className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white"
                  required
                >
                  <option value="">Select destination chain</option>
                  {getChainOptions(transferForm.from_chain).map(({ key, name, role, icon, layerzero_eid }) => (
                    <option key={key} value={key}>
                      {icon} {name} (EID: {layerzero_eid})
                    </option>
                  ))}
                </select>
                {transferForm.to_chain && (
                  <div className="mt-2 p-3 bg-green-50 rounded-lg">
                    <div className="text-sm text-green-800">
                      <strong>{chains[transferForm.to_chain]?.name}</strong>
                      <div className="text-xs text-green-600">{chains[transferForm.to_chain]?.role}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Bridge Route Visualization */}
            {transferForm.from_chain && transferForm.to_chain && (
              <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Bridge Route
                </h3>
                <div className="flex items-center justify-between">
                  <div className="text-center">
                    <div className="text-2xl mb-1">{chains[transferForm.from_chain]?.icon}</div>
                    <div className="text-sm font-medium text-gray-900">{chains[transferForm.from_chain]?.name}</div>
                    <div className="text-xs text-gray-500">Source</div>
                  </div>
                  <div className="flex-1 mx-4">
                    <div className="flex items-center">
                      <div className="flex-1 h-0.5 bg-gradient-to-r from-blue-400 to-green-400"></div>
                      <ArrowRight className="w-6 h-6 text-gray-400 mx-2" />
                      <div className="flex-1 h-0.5 bg-gradient-to-r from-blue-400 to-green-400"></div>
                    </div>
                    <div className="text-center mt-2">
                      <div className="text-xs text-gray-600">LayerZero Protocol</div>
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-1">{chains[transferForm.to_chain]?.icon}</div>
                    <div className="text-sm font-medium text-gray-900">{chains[transferForm.to_chain]?.name}</div>
                    <div className="text-xs text-gray-500">Destination</div>
                  </div>
                </div>
              </div>
            )}

            {/* Addresses */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  From Address
                </label>
                <div className="relative">
                  <Wallet className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={transferForm.from_address}
                    onChange={(e) => setTransferForm({ ...transferForm, from_address: e.target.value })}
                    placeholder="0x..."
                    className="w-full pl-10 pr-4 py-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  To Address
                </label>
                <div className="relative">
                  <Wallet className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={transferForm.to_address}
                    onChange={(e) => setTransferForm({ ...transferForm, to_address: e.target.value })}
                    placeholder="0x..."
                    className="w-full pl-10 pr-4 py-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Amount and Escrow ID */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Amount (ETH)
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    value={transferForm.amount_eth}
                    onChange={(e) => setTransferForm({ ...transferForm, amount_eth: e.target.value })}
                    placeholder="0.0000"
                    className="w-full pl-10 pr-4 py-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Escrow ID (Optional)
                </label>
                <input
                  type="text"
                  value={transferForm.escrow_id}
                  onChange={(e) => setTransferForm({ ...transferForm, escrow_id: e.target.value })}
                  placeholder="Auto-generated if empty"
                  className="w-full px-4 py-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Fee Estimate */}
            {feeEstimate && transferForm.amount_eth && (
              <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-lg p-6">
                <h3 className="font-semibold text-emerald-900 mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  LayerZero Fee Estimate
                </h3>
                {feeEstimate.success ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-2xl font-bold text-emerald-600">
                        {feeEstimate.layerzero_fee?.toFixed(6) || '0.000000'}
                      </div>
                      <div className="text-sm text-emerald-800">LayerZero Fee (ETH)</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {feeEstimate.estimated_gas || 'N/A'}
                      </div>
                      <div className="text-sm text-blue-800">Gas Estimate</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">
                        {(parseFloat(transferForm.amount_eth) + (feeEstimate.layerzero_fee || 0)).toFixed(6)}
                      </div>
                      <div className="text-sm text-gray-600">Total Cost (ETH)</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-red-600 bg-red-50 border border-red-200 rounded-lg p-4">
                    <AlertCircle className="w-5 h-5 inline mr-2" />
                    Fee estimation failed: {feeEstimate.error}
                  </div>
                )}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !transferForm.from_chain || !transferForm.to_chain || !transferForm.amount_eth}
              className="w-full py-4 px-6 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg hover:from-emerald-700 hover:to-teal-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed flex items-center justify-center text-lg font-semibold transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <>
                  <Activity className="w-5 h-5 mr-3 animate-spin" />
                  Processing Transfer...
                </>
              ) : (
                <>
                  <ArrowLeftRight className="w-5 h-5 mr-3" />
                  Execute LayerZero Transfer
                </>
              )}
            </button>
          </form>

          {/* Transfer Result */}
          {transferResult && (
            <div className={`mt-6 p-6 rounded-xl border ${
              transferResult.success 
                ? 'bg-green-50 border-green-200' 
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center mb-4">
                {transferResult.success ? (
                  <CheckCircle className="w-6 h-6 text-green-500 mr-3" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-red-500 mr-3" />
                )}
                <h3 className={`text-lg font-semibold ${
                  transferResult.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  {transferResult.success ? 'Transfer Completed!' : 'Transfer Failed'}
                </h3>
              </div>
              <div className={`text-sm ${
                transferResult.success ? 'text-green-700' : 'text-red-700'
              }`}>
                {transferResult.success ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <span className="font-medium">Transfer ID:</span>
                        <div className="font-mono text-xs bg-white p-2 rounded mt-1">
                          {transferResult.result?.transfer_id || transferResult.transfer_id}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Amount:</span>
                        <div className="text-lg font-bold text-green-800 mt-1">
                          {transferResult.result?.amount_transferred || transferResult.amount_transferred} ETH
                        </div>
                      </div>
                    </div>
                    
                    {/* Bridge Transaction */}
                    {transferResult.result?.transaction_hash && (
                      <div className="bg-white p-3 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">Bridge Transaction:</span>
                          <a 
                            href={getBlockExplorerUrl(transferResult.result.transaction_hash, transferForm.from_chain)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-green-600 hover:text-green-800 underline flex items-center gap-1 font-mono text-sm"
                          >
                            {formatAddress(transferResult.result.transaction_hash)}
                            <Link className="w-4 h-4" />
                          </a>
                        </div>
                      </div>
                    )}
                    
                    {/* Auto-Conversion Status */}
                    {transferResult.result?.auto_conversion && (
                      <div className="bg-white p-3 rounded-lg border border-green-200">
                        <div className="flex items-center mb-2">
                          <Zap className="w-5 h-5 text-green-600 mr-2" />
                          <span className="font-semibold text-green-800">Auto-Conversion: cfWETH → ETH</span>
                        </div>
                        {transferResult.result?.conversion_tx && (
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Conversion Transaction:</span>
                            <a 
                              href={getBlockExplorerUrl(transferResult.result.conversion_tx, transferForm.to_chain)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-green-600 hover:text-green-800 underline flex items-center gap-1 font-mono text-sm"
                            >
                              {formatAddress(transferResult.result.conversion_tx)}
                              <Link className="w-4 h-4" />
                            </a>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* LayerZero Details */}
                    {transferResult.result?.layerzero_guid && (
                      <div className="bg-white p-3 rounded-lg">
                        <span className="font-medium">LayerZero GUID:</span>
                        <div className="font-mono text-xs text-gray-600 mt-1">
                          {transferResult.result.layerzero_guid}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-white p-4 rounded-lg">
                    <strong>Error:</strong> {transferResult.error}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Active Transfers */}
        {Object.keys(activeTransfers).length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Active Transfers
            </h2>
            <div className="space-y-4">
              {Object.entries(activeTransfers).map(([transferId, transfer]) => (
                <div key={transferId} className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 mb-1">
                        {formatAddress(transferId)}
                      </div>
                      <div className="flex items-center text-sm text-gray-600 mb-2">
                        <span className="mr-2">{chains[transfer.from_chain]?.icon}</span>
                        <span className="mr-2">{chains[transfer.from_chain]?.name}</span>
                        <ArrowRight className="w-4 h-4 mx-2" />
                        <span className="mr-2">{chains[transfer.to_chain]?.icon}</span>
                        <span>{chains[transfer.to_chain]?.name}</span>
                      </div>
                      <div className="text-lg font-bold text-gray-900">{transfer.amount_eth} ETH</div>
                      {transfer.auto_conversion && (
                        <div className="text-sm text-green-600 flex items-center mt-1">
                          <Zap className="w-4 h-4 mr-1" />
                          Auto-conversion enabled
                        </div>
                      )}
                    </div>
                    <div className="flex items-center text-yellow-600">
                      <Activity className="w-5 h-5 mr-2 animate-spin" />
                      <span className="font-medium">Processing</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Transfers */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="border-b border-gray-200 pb-4 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Recent LayerZero Transfers
            </h2>
            <p className="text-sm text-gray-600 mt-1">Your cross-chain transaction history</p>
          </div>
          {transfers.length === 0 ? (
            <div className="text-center py-12">
              <ArrowLeftRight className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No transfers found</h3>
              <p className="text-gray-500">Execute your first LayerZero cross-chain transfer above.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {transfers.slice(0, 10).map((transfer, index) => (
                <div key={transfer.transfer_id || index} className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-mono text-sm font-medium text-gray-900">
                      {formatAddress(transfer.transfer_id)}
                    </div>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      transfer.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {transfer.status}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="mr-2">{chains[transfer.from_chain]?.icon}</span>
                      <span className="mr-2">{chains[transfer.from_chain]?.name}</span>
                      <ArrowRight className="w-4 h-4 mx-2" />
                      <span className="mr-2">{chains[transfer.to_chain]?.icon}</span>
                      <span>{chains[transfer.to_chain]?.name}</span>
                    </div>
                    <div className="text-lg font-bold text-gray-900">
                      {transfer.amount_eth} ETH
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <div>
                      {formatAddress(transfer.from_address)} → {formatAddress(transfer.to_address)}
                    </div>
                    {transfer.timestamp && (
                      <div>
                        {new Date(transfer.timestamp * 1000).toLocaleString()}
                      </div>
                    )}
                  </div>
                  
                  {transfer.auto_conversion && (
                    <div className="mt-2 flex items-center text-sm text-green-600">
                      <Zap className="w-4 h-4 mr-1" />
                      Auto-converted to ETH
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TokenBridge;