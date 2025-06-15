import React, { useState, useEffect } from 'react';
import axios from 'axios';

const EnhancedAuthenticity = () => {
  const [verificationMethod, setVerificationMethod] = useState('single');
  const [singleProduct, setSingleProduct] = useState({ productId: '', signature: '' });
  const [batchProducts, setBatchProducts] = useState([]);
  const [verificationResults, setVerificationResults] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/enhanced-authenticity/analytics/performance`);
      if (response.data.success) {
        setAnalytics(response.data);
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  const handleSingleVerification = async () => {
    if (!singleProduct.productId || !singleProduct.signature) {
      alert('Please provide both Product ID and Signature');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/enhanced-authenticity/verify`, {
        product_id: singleProduct.productId,
        signature: singleProduct.signature,
        verification_level: 'enhanced'
      });

      setVerificationResults(response.data);
    } catch (error) {
      console.error('Verification failed:', error);
      alert('Verification failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleBatchVerification = async () => {
    if (batchProducts.length === 0) {
      alert('Please add at least one product for batch verification');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/enhanced-authenticity/batch-verify`, {
        products: batchProducts.map(p => ({
          product_id: p.productId,
          signature: p.signature
        }))
      });

      setVerificationResults(response.data);
    } catch (error) {
      console.error('Batch verification failed:', error);
      alert('Batch verification failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoading(false);
    }
  };

  const addBatchProduct = () => {
    setBatchProducts([...batchProducts, { productId: '', signature: '', id: Date.now() }]);
  };

  const updateBatchProduct = (id, field, value) => {
    setBatchProducts(products => 
      products.map(p => p.id === id ? { ...p, [field]: value } : p)
    );
  };

  const removeBatchProduct = (id) => {
    setBatchProducts(products => products.filter(p => p.id !== id));
  };

  const generateMockSignature = () => {
    return '0x' + Array.from({length: 128}, () => Math.floor(Math.random() * 16).toString(16)).join('');
  };

  const generateMockProductId = () => {
    return 'PROD_' + Math.random().toString(36).substr(2, 9).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Enhanced Authenticity Verification</h1>
          <p className="text-gray-600">Algorithm 4 - Advanced product verification with batch processing and analytics</p>
        </div>

        {/* Analytics Dashboard */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Verifications</p>
                  <p className="text-2xl font-bold text-blue-600">{analytics.total_verifications || 0}</p>
                </div>
                <div className="text-3xl">🔍</div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold text-green-600">{analytics.success_rate || '0%'}</p>
                </div>
                <div className="text-3xl">✅</div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Batch Verifications</p>
                  <p className="text-2xl font-bold text-purple-600">{analytics.batch_verifications || 0}</p>
                </div>
                <div className="text-3xl">📦</div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
                  <p className="text-2xl font-bold text-orange-600">{analytics.avg_response_time || '0ms'}</p>
                </div>
                <div className="text-3xl">⚡</div>
              </div>
            </div>
          </div>
        )}

        {/* Verification Method Selection */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Verification Method</h2>
          <div className="flex space-x-4">
            <button
              onClick={() => setVerificationMethod('single')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                verificationMethod === 'single'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Single Product Verification
            </button>
            <button
              onClick={() => setVerificationMethod('batch')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                verificationMethod === 'batch'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Batch Verification (up to 50 products)
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Verification Input */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">
              {verificationMethod === 'single' ? 'Single Product Verification' : 'Batch Verification'}
            </h2>

            {verificationMethod === 'single' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Product ID</label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={singleProduct.productId}
                      onChange={(e) => setSingleProduct({...singleProduct, productId: e.target.value})}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter product ID"
                    />
                    <button
                      onClick={() => setSingleProduct({...singleProduct, productId: generateMockProductId()})}
                      className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
                    >
                      Generate
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Signature</label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={singleProduct.signature}
                      onChange={(e) => setSingleProduct({...singleProduct, signature: e.target.value})}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter signature"
                    />
                    <button
                      onClick={() => setSingleProduct({...singleProduct, signature: generateMockSignature()})}
                      className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
                    >
                      Generate
                    </button>
                  </div>
                </div>
                <button
                  onClick={handleSingleVerification}
                  disabled={isLoading}
                  className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
                >
                  {isLoading ? 'Verifying...' : 'Verify Product'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{batchProducts.length} products added</span>
                  <button
                    onClick={addBatchProduct}
                    className="px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
                  >
                    Add Product
                  </button>
                </div>
                
                <div className="max-h-80 overflow-y-auto space-y-3">
                  {batchProducts.map((product) => (
                    <div key={product.id} className="border border-gray-200 rounded-md p-3">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-sm font-medium text-gray-700">Product {batchProducts.indexOf(product) + 1}</span>
                        <button
                          onClick={() => removeBatchProduct(product.id)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          Remove
                        </button>
                      </div>
                      <div className="space-y-2">
                        <div className="flex space-x-2">
                          <input
                            type="text"
                            value={product.productId}
                            onChange={(e) => updateBatchProduct(product.id, 'productId', e.target.value)}
                            className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                            placeholder="Product ID"
                          />
                          <button
                            onClick={() => updateBatchProduct(product.id, 'productId', generateMockProductId())}
                            className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                          >
                            Gen ID
                          </button>
                        </div>
                        <div className="flex space-x-2">
                          <input
                            type="text"
                            value={product.signature}
                            onChange={(e) => updateBatchProduct(product.id, 'signature', e.target.value)}
                            className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                            placeholder="Signature"
                          />
                          <button
                            onClick={() => updateBatchProduct(product.id, 'signature', generateMockSignature())}
                            className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                          >
                            Gen Sig
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <button
                  onClick={handleBatchVerification}
                  disabled={isLoading || batchProducts.length === 0}
                  className="w-full bg-purple-600 text-white py-3 rounded-md hover:bg-purple-700 disabled:opacity-50 font-medium"
                >
                  {isLoading ? 'Processing...' : `Verify ${batchProducts.length} Products`}
                </button>
              </div>
            )}
          </div>

          {/* Verification Results */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Verification Results</h2>
            
            {!verificationResults ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">🔍</div>
                <p>Run a verification to see results here</p>
              </div>
            ) : (
              <div className="space-y-4">
                {verificationMethod === 'single' ? (
                  <div className="space-y-4">
                    <div className={`p-4 rounded-lg ${
                      verificationResults.verified ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                    }`}>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-2xl">{verificationResults.verified ? '✅' : '❌'}</span>
                        <span className={`font-semibold ${verificationResults.verified ? 'text-green-700' : 'text-red-700'}`}>
                          {verificationResults.verified ? 'Verification Successful' : 'Verification Failed'}
                        </span>
                      </div>
                      <div className="text-sm space-y-1">
                        <p><span className="font-medium">Product ID:</span> {verificationResults.product_id}</p>
                        <p><span className="font-medium">Confidence Score:</span> {verificationResults.confidence_score || 'N/A'}</p>
                        <p><span className="font-medium">Response Time:</span> {verificationResults.processing_time_ms}ms</p>
                      </div>
                    </div>
                    
                    {verificationResults.verification_details && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-2">Verification Details</h4>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p><span className="font-medium">Signature Valid:</span> {verificationResults.verification_details.signature_valid ? 'Yes' : 'No'}</p>
                          <p><span className="font-medium">Blockchain Confirmed:</span> {verificationResults.verification_details.blockchain_confirmed ? 'Yes' : 'No'}</p>
                          <p><span className="font-medium">Metadata Valid:</span> {verificationResults.verification_details.metadata_valid ? 'Yes' : 'No'}</p>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-2xl">📊</span>
                        <span className="font-semibold text-blue-700">Batch Verification Complete</span>
                      </div>
                      <div className="text-sm space-y-1">
                        <p><span className="font-medium">Total Products:</span> {verificationResults.batch_summary?.total_products || 0}</p>
                        <p><span className="font-medium">Verified:</span> {verificationResults.batch_summary?.verified_count || 0}</p>
                        <p><span className="font-medium">Failed:</span> {verificationResults.batch_summary?.failed_count || 0}</p>
                        <p><span className="font-medium">Processing Time:</span> {verificationResults.batch_summary?.total_processing_time_ms}ms</p>
                      </div>
                    </div>

                    <div className="max-h-60 overflow-y-auto space-y-2">
                      {verificationResults.results?.map((result, index) => (
                        <div key={index} className={`p-3 rounded border ${
                          result.verified ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                        }`}>
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-sm">{result.product_id}</span>
                            <span className={`text-sm ${result.verified ? 'text-green-600' : 'text-red-600'}`}>
                              {result.verified ? '✅ Verified' : '❌ Failed'}
                            </span>
                          </div>
                          {result.error && (
                            <p className="text-xs text-red-600 mt-1">{result.error}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedAuthenticity;