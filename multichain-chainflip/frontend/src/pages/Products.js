import React, { useState, useEffect } from 'react';
import { useBlockchain } from '../contexts/BlockchainContext';
import { useNotification } from '../contexts/NotificationContext';

export const Products = () => {
  const { isConnected, account } = useBlockchain();
  const { showSuccess, showError } = useNotification();
  
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showMintModal, setShowMintModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/products/`);
      
      if (response.ok) {
        const data = await response.json();
        setProducts(data.products || []);
      }
    } catch (error) {
      console.error('Failed to fetch products:', error);
      showError('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeProduct = async (product) => {
    try {
      setSelectedProduct(product);
      setShowAnalysisModal(true);
      
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/products/${product.token_id}/analyze`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            token_id: product.token_id,
            analysis_type: 'full'
          })
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        setAnalysisResult(result);
        showSuccess('Product analysis completed');
      } else {
        showError('Failed to analyze product');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      showError('Failed to analyze product');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'manufactured':
        return 'badge-info';
      case 'in_transit':
        return 'badge-warning';
      case 'delivered':
        return 'badge-success';
      case 'sold':
        return 'badge-gray';
      default:
        return 'badge-gray';
    }
  };

  const ProductCard = ({ product }) => (
    <div className="card hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              Product #{product.token_id}
            </h3>
            <span className={`badge ${getStatusColor(product.status)}`}>
              {product.status}
            </span>
          </div>
          
          <div className="space-y-2 text-sm text-gray-600">
            <div><strong>Manufacturer:</strong> {product.manufacturer?.slice(0, 10)}...</div>
            <div><strong>Current Owner:</strong> {product.current_owner?.slice(0, 10)}...</div>
            <div><strong>Chain:</strong> {product.chain_id === 80002 ? 'Polygon PoS' : 'L2 CDK'}</div>
            {product.created_at && (
              <div><strong>Created:</strong> {new Date(product.created_at * 1000).toLocaleDateString()}</div>
            )}
          </div>
        </div>
        
        <div className="flex flex-col space-y-2">
          <button
            onClick={() => handleAnalyzeProduct(product)}
            className="btn-primary text-sm"
          >
            🔍 Analyze
          </button>
          <button
            onClick={() => setSelectedProduct(product)}
            className="btn-secondary text-sm"
          >
            📄 Details
          </button>
        </div>
      </div>
      
      {/* Anomaly/Counterfeit Indicators */}
      <div className="mt-4 flex space-x-2">
        {product.last_anomaly_check?.is_anomaly && (
          <span className="badge badge-danger text-xs">⚠️ Anomaly Detected</span>
        )}
        {product.last_counterfeit_check?.is_counterfeit && (
          <span className="badge badge-danger text-xs">🚨 Counterfeit Risk</span>
        )}
      </div>
    </div>
  );

  const MintProductModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Mint New Product</h2>
        
        <form onSubmit={(e) => {
          e.preventDefault();
          // Handle minting logic
          setShowMintModal(false);
          showSuccess('Product minting initiated');
        }}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Product Name
              </label>
              <input type="text" className="input-field" placeholder="Enter product name" required />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Batch Number
              </label>
              <input type="text" className="input-field" placeholder="Enter batch number" required />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Manufacturing Date
              </label>
              <input type="date" className="input-field" required />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Product Type
              </label>
              <select className="select-field" required>
                <option value="">Select type</option>
                <option value="electronics">Electronics</option>
                <option value="pharmaceutical">Pharmaceutical</option>
                <option value="food">Food & Beverage</option>
                <option value="clothing">Clothing</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          
          <div className="flex space-x-3 mt-6">
            <button type="submit" className="btn-primary flex-1">
              Mint Product
            </button>
            <button 
              type="button" 
              onClick={() => setShowMintModal(false)}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const AnalysisModal = () => (
    showAnalysisModal && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">
              Analysis Results - Product #{selectedProduct?.token_id}
            </h2>
            <button 
              onClick={() => {
                setShowAnalysisModal(false);
                setAnalysisResult(null);
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          
          {analysisResult ? (
            <div className="space-y-6">
              {/* Anomaly Detection Results */}
              {analysisResult.anomaly_detection && (
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">🔍 Anomaly Detection</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm text-gray-600">Status:</span>
                      <div className={`badge ${analysisResult.anomaly_detection.is_anomaly ? 'badge-danger' : 'badge-success'} ml-2`}>
                        {analysisResult.anomaly_detection.is_anomaly ? 'Anomaly Detected' : 'Normal'}
                      </div>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Confidence:</span>
                      <span className="ml-2 font-medium">
                        {(analysisResult.anomaly_detection.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-2">
                    <span className="text-sm text-gray-600">Score:</span>
                    <span className="ml-2 font-mono text-sm">
                      {analysisResult.anomaly_detection.anomaly_score?.toFixed(4)}
                    </span>
                  </div>
                </div>
              )}

              {/* Counterfeit Detection Results */}
              {analysisResult.counterfeit_detection && (
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">🛡️ Counterfeit Detection</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm text-gray-600">Status:</span>
                      <div className={`badge ${analysisResult.counterfeit_detection.is_counterfeit ? 'badge-danger' : 'badge-success'} ml-2`}>
                        {analysisResult.counterfeit_detection.is_counterfeit ? 'Counterfeit Risk' : 'Authentic'}
                      </div>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Confidence:</span>
                      <span className="ml-2 font-medium">
                        {(analysisResult.counterfeit_detection.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-2">
                    <span className="text-sm text-gray-600">Probability:</span>
                    <span className="ml-2 font-mono text-sm">
                      {(analysisResult.counterfeit_detection.counterfeit_probability * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="loading-spinner mx-auto mb-4"></div>
              <p className="text-gray-600">Analyzing product...</p>
            </div>
          )}
        </div>
      </div>
    )
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-600">Manage and track products across the supply chain</p>
        </div>
        
        <div className="flex space-x-3">
          <button 
            onClick={fetchProducts}
            className="btn-secondary"
          >
            🔄 Refresh
          </button>
          {isConnected && (
            <button 
              onClick={() => setShowMintModal(true)}
              className="btn-primary"
            >
              ➕ Mint Product
            </button>
          )}
        </div>
      </div>

      {/* Connection Warning */}
      {!isConnected && (
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
          <div className="flex">
            <span className="text-warning-600 text-xl mr-3">⚠️</span>
            <div>
              <h3 className="text-sm font-medium text-warning-800">
                Wallet Not Connected
              </h3>
              <p className="mt-1 text-sm text-warning-700">
                Connect your wallet to mint products and perform transactions.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Products Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      ) : products.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((product) => (
            <ProductCard key={product.token_id || product._id} product={product} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📦</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Products Found</h3>
          <p className="text-gray-600 mb-6">Get started by minting your first product.</p>
          {isConnected && (
            <button 
              onClick={() => setShowMintModal(true)}
              className="btn-primary"
            >
              ➕ Mint Your First Product
            </button>
          )}
        </div>
      )}

      {/* Modals */}
      {showMintModal && <MintProductModal />}
      <AnalysisModal />
    </div>
  );
};
