import React, { useState, useEffect, useCallback } from 'react';
import blockchainService from '../services/blockchainService';

const BuyerKeyManagement = ({ buyerAddress }) => {
  const [keys, setKeys] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedPurchase, setSelectedPurchase] = useState(null);

  useEffect(() => {
    if (buyerAddress) {
      fetchBuyerData();
    }
  }, [buyerAddress, fetchBuyerData]);

  const fetchBuyerData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch both purchases and keys
      const [purchasesResponse, keysResponse] = await Promise.all([
        blockchainService.getBuyerPurchases(buyerAddress),
        blockchainService.getBuyerEncryptionKeys(buyerAddress)
      ]);

      if (purchasesResponse.success) {
        setPurchases(purchasesResponse.purchases);
      }

      if (keysResponse.success) {
        setKeys(keysResponse.keys);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [buyerAddress]);

  const handleCopyKey = (keyValue, keyType) => {
    navigator.clipboard.writeText(keyValue);
    alert(`${keyType} copied to clipboard!`);
  };

  const handleDownloadKeys = (purchase) => {
    const purchaseKeys = keys.find(k => k.purchase_id === purchase.purchase_id);
    if (!purchaseKeys) return;

    const keyData = {
      purchase_id: purchase.purchase_id,
      product_id: purchaseKeys.product_id,
      aes_key: purchaseKeys.aes_key,
      hmac_key: purchaseKeys.hmac_key,
      timestamp: purchaseKeys.timestamp,
      instructions: "Use these keys to decrypt QR codes when you receive your product"
    };

    const dataStr = JSON.stringify(keyData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `encryption_keys_${purchase.purchase_id}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading your encryption keys...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Keys</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
            <div className="mt-4">
              <button
                onClick={fetchBuyerData}
                className="bg-red-100 hover:bg-red-200 px-3 py-2 rounded text-red-800 text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-blue-900 mb-2">🔑 Your Encryption Keys</h2>
        <p className="text-blue-800 text-sm">
          These keys allow you to decrypt QR codes on products you've purchased. 
          Keep them secure and use them when you receive your goods.
        </p>
      </div>

      {/* Purchases Overview */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <h3 className="text-md font-medium text-gray-900">Your Purchases ({purchases.length})</h3>
        </div>
        
        {purchases.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No purchases found. Make a purchase to see encryption keys here.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {purchases.map((purchase, index) => {
              const purchaseKeys = keys.find(k => k.purchase_id === purchase.purchase_id);
              
              return (
                <div key={purchase.purchase_id || index} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Purchase: {purchase.purchase_id?.substring(0, 12)}...
                          </p>
                          <p className="text-xs text-gray-500">
                            Product: {purchase.product_id} | Status: {purchase.status}
                          </p>
                          <p className="text-xs text-gray-500">
                            Date: {new Date(purchase.timestamp).toLocaleDateString()}
                          </p>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {purchase.keys_available ? (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                              🔑 Keys Available
                            </span>
                          ) : (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                              ⏳ Keys Pending
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {purchaseKeys && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setSelectedPurchase(
                            selectedPurchase === purchase.purchase_id ? null : purchase.purchase_id
                          )}
                          className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                          {selectedPurchase === purchase.purchase_id ? 'Hide Keys' : 'Show Keys'}
                        </button>
                        <button
                          onClick={() => handleDownloadKeys(purchase)}
                          className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
                        >
                          Download
                        </button>
                      </div>
                    )}
                  </div>
                  
                  {/* Expanded Keys View */}
                  {selectedPurchase === purchase.purchase_id && purchaseKeys && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Encryption Keys</h4>
                      
                      <div className="space-y-3">
                        {/* AES Key */}
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            AES Key (for decryption):
                          </label>
                          <div className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={purchaseKeys.aes_key}
                              readOnly
                              className="flex-1 text-xs bg-white border border-gray-300 rounded px-2 py-1 font-mono"
                            />
                            <button
                              onClick={() => handleCopyKey(purchaseKeys.aes_key, 'AES Key')}
                              className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
                            >
                              Copy
                            </button>
                          </div>
                        </div>
                        
                        {/* HMAC Key */}
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            HMAC Key (for verification):
                          </label>
                          <div className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={purchaseKeys.hmac_key}
                              readOnly
                              className="flex-1 text-xs bg-white border border-gray-300 rounded px-2 py-1 font-mono"
                            />
                            <button
                              onClick={() => handleCopyKey(purchaseKeys.hmac_key, 'HMAC Key')}
                              className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
                            >
                              Copy
                            </button>
                          </div>
                        </div>
                        
                        <div className="mt-3 p-3 bg-blue-50 rounded text-xs text-blue-800">
                          <p className="font-medium mb-1">📱 How to use these keys:</p>
                          <ol className="list-decimal list-inside space-y-1">
                            <li>When you receive the product, scan the QR code</li>
                            <li>Enter the AES key to decrypt the product data</li>
                            <li>Use the HMAC key to verify authenticity</li>
                            <li>This confirms the product is genuine and hasn't been tampered with</li>
                          </ol>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
      
      {/* Refresh Button */}
      <div className="flex justify-center">
        <button
          onClick={fetchBuyerData}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-2"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Refresh Keys</span>
        </button>
      </div>
    </div>
  );
};

export default BuyerKeyManagement;
