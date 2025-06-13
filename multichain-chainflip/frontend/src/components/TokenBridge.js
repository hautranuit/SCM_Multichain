/**
 * Token Bridge Component for Cross-Chain ETH Transfers with LayerZero V2 OFT
 * Integrates with LayerZero OFT contracts for real ETH bridging with auto-conversion
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ArrowRight, Wallet, DollarSign, Clock, CheckCircle, AlertCircle, Activity, RefreshCw, Link, Zap } from 'lucide-react';

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
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🌉 LayerZero Bridge</h1>
            <p className="text-gray-600 mt-1">
              Cross-chain ETH transfers with automatic cfWETH → ETH conversion
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                fetchInfrastructureStatus();
                fetchTransfers();
              }}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={testEnhancedInfrastructure}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-green-50 text-green-600 rounded-lg hover:bg-green-100 disabled:opacity-50"
            >
              <Zap className="w-4 h-4" />
              Test Transfer
            </button>
          </div>
        </div>
      </div>

      {/* Infrastructure Status */}
      {infrastructureStatus && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            LayerZero Infrastructure Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(infrastructureStatus.chains || {}).map(([chainKey, status]) => (
              <div key={chainKey} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xl">{chains[chainKey]?.icon}</span>
                  <div className={`w-3 h-3 rounded-full ${
                    status.status === 'operational' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                </div>
                <h3 className="font-medium text-sm text-gray-900">{chains[chainKey]?.name}</h3>
                <p className="text-xs text-gray-500 mb-2">EID: {chains[chainKey]?.layerzero_eid}</p>
                <div className="text-xs text-gray-600">
                  <div>OFT: {formatAddress(status.oft_address)}</div>
                  <div>Status: {status.status}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transfer Form */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <ArrowRight className="w-5 h-5 mr-2" />
          Cross-Chain Transfer
        </h2>
        
        <form onSubmit={executeTransfer} className="space-y-4">
          {/* Chain Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From Chain
              </label>
              <select
                value={transferForm.from_chain}
                onChange={(e) => setTransferForm({ ...transferForm, from_chain: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg"
                required
              >
                <option value="">Select source chain</option>
                {getChainOptions().map(({ key, name, role, icon, layerzero_eid }) => (
                  <option key={key} value={key}>
                    {icon} {name} (EID: {layerzero_eid})
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                To Chain
              </label>
              <select
                value={transferForm.to_chain}
                onChange={(e) => setTransferForm({ ...transferForm, to_chain: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg"
                required
              >
                <option value="">Select destination chain</option>
                {getChainOptions(transferForm.from_chain).map(({ key, name, role, icon, layerzero_eid }) => (
                  <option key={key} value={key}>
                    {icon} {name} (EID: {layerzero_eid})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Addresses */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From Address
              </label>
              <input
                type="text"
                value={transferForm.from_address}
                onChange={(e) => setTransferForm({ ...transferForm, from_address: e.target.value })}
                placeholder="0x..."
                className="w-full p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                To Address
              </label>
              <input
                type="text"
                value={transferForm.to_address}
                onChange={(e) => setTransferForm({ ...transferForm, to_address: e.target.value })}
                placeholder="0x..."
                className="w-full p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
          </div>

          {/* Amount and Escrow ID */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Amount (ETH)
              </label>
              <input
                type="number"
                step="0.0001"
                min="0.0001"
                value={transferForm.amount_eth}
                onChange={(e) => setTransferForm({ ...transferForm, amount_eth: e.target.value })}
                placeholder="0.0000"
                className="w-full p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Escrow ID (Optional)
              </label>
              <input
                type="text"
                value={transferForm.escrow_id}
                onChange={(e) => setTransferForm({ ...transferForm, escrow_id: e.target.value })}
                placeholder="Auto-generated if empty"
                className="w-full p-3 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          {/* Fee Estimate */}
          {feeEstimate && transferForm.amount_eth && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 mb-2">LayerZero Fee Estimate</h3>
              {feeEstimate.success ? (
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>LayerZero Fee:</span>
                    <span>{feeEstimate.layerzero_fee?.toFixed(6) || '0.000000'} ETH</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Gas Estimate:</span>
                    <span>{feeEstimate.estimated_gas || 'N/A'}</span>
                  </div>
                  <div className="text-xs text-blue-600">
                    Total Cost: {(parseFloat(transferForm.amount_eth) + (feeEstimate.layerzero_fee || 0)).toFixed(6)} ETH
                  </div>
                </div>
              ) : (
                <div className="text-red-600 text-sm">
                  Fee estimation failed: {feeEstimate.error}
                </div>
              )}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !transferForm.from_chain || !transferForm.to_chain || !transferForm.amount_eth}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <>
                <Activity className="w-4 h-4 mr-2 animate-spin" />
                Processing Transfer...
              </>
            ) : (
              <>
                <ArrowRight className="w-4 h-4 mr-2" />
                Execute LayerZero Transfer
              </>
            )}
          </button>
        </form>

        {/* Transfer Result */}
        {transferResult && (
          <div className={`mt-4 p-4 rounded-lg border ${
            transferResult.success 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center">
              {transferResult.success ? (
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              )}
              <h3 className={`font-medium ${
                transferResult.success ? 'text-green-800' : 'text-red-800'
              }`}>
                {transferResult.success ? 'Transfer Completed!' : 'Transfer Failed'}
              </h3>
            </div>
            <div className={`mt-2 text-sm ${
              transferResult.success ? 'text-green-700' : 'text-red-700'
            }`}>
              {transferResult.success ? (
                <div className="space-y-2">
                  <div>Transfer ID: {transferResult.result?.transfer_id || transferResult.transfer_id}</div>
                  <div>Amount: {transferResult.result?.amount_transferred || transferResult.amount_transferred} ETH</div>
                  
                  {/* Bridge Transaction */}
                  {transferResult.result?.transaction_hash && (
                    <div className="flex items-center gap-2">
                      <span>Bridge TX:</span>
                      <a 
                        href={getBlockExplorerUrl(transferResult.result.transaction_hash, transferForm.from_chain)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-green-600 hover:text-green-800 underline flex items-center gap-1"
                      >
                        {formatAddress(transferResult.result.transaction_hash)}
                        <Link className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                  
                  {/* Auto-Conversion Status */}
                  {transferResult.result?.auto_conversion && (
                    <>
                      <div className="font-medium text-green-800 mt-3">
                        ✅ Auto-Conversion: cfWETH → ETH
                      </div>
                      {transferResult.result?.conversion_tx && (
                        <div className="flex items-center gap-2">
                          <span>Conversion TX:</span>
                          <a 
                            href={getBlockExplorerUrl(transferResult.result.conversion_tx, transferForm.to_chain)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-green-600 hover:text-green-800 underline flex items-center gap-1"
                          >
                            {formatAddress(transferResult.result.conversion_tx)}
                            <Link className="w-3 h-3" />
                          </a>
                        </div>
                      )}
                    </>
                  )}
                  
                  {/* LayerZero Details */}
                  {transferResult.result?.layerzero_guid && (
                    <div className="text-xs text-green-600 mt-2">
                      LayerZero GUID: {transferResult.result.layerzero_guid}
                    </div>
                  )}
                  
                  <div className="text-xs text-green-600 mt-2">
                    {transferResult.result?.message || transferResult.message}
                  </div>
                </div>
              ) : (
                <div>Error: {transferResult.error}</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Active Transfers */}
      {Object.keys(activeTransfers).length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Active Transfers
          </h2>
          <div className="space-y-3">
            {Object.entries(activeTransfers).map(([transferId, transfer]) => (
              <div key={transferId} className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div>
                  <div className="font-medium">{formatAddress(transferId)}</div>
                  <div className="text-sm text-gray-600">
                    {chains[transfer.from_chain]?.icon} {chains[transfer.from_chain]?.name} → 
                    {chains[transfer.to_chain]?.icon} {chains[transfer.to_chain]?.name}
                  </div>
                  <div className="text-sm text-gray-600">{transfer.amount_eth} ETH</div>
                  {transfer.auto_conversion && (
                    <div className="text-xs text-green-600">Auto-conversion enabled</div>
                  )}
                </div>
                <div className="flex items-center text-yellow-600">
                  <Activity className="w-4 h-4 mr-1 animate-spin" />
                  Processing
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Transfers */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Activity className="w-5 h-5 mr-2" />
          Recent LayerZero Transfers
        </h2>
        {transfers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No transfers found. Execute your first LayerZero cross-chain transfer above.
          </div>
        ) : (
          <div className="space-y-3">
            {transfers.slice(0, 10).map((transfer, index) => (
              <div key={transfer.transfer_id || index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{formatAddress(transfer.transfer_id)}</div>
                    <div className={`text-sm px-2 py-1 rounded ${
                      transfer.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {transfer.status}
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {chains[transfer.from_chain]?.icon} {chains[transfer.from_chain]?.name} → 
                    {chains[transfer.to_chain]?.icon} {chains[transfer.to_chain]?.name}
                  </div>
                  <div className="text-sm text-gray-600">
                    {transfer.amount_eth} ETH • {formatAddress(transfer.from_address)} → {formatAddress(transfer.to_address)}
                  </div>
                  {transfer.auto_conversion && (
                    <div className="text-xs text-green-600 flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Auto-converted to ETH
                    </div>
                  )}
                  {transfer.timestamp && (
                    <div className="text-xs text-gray-500">
                      {new Date(transfer.timestamp * 1000).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TokenBridge;