import React, { useState, useEffect } from 'react';
import axios from 'axios';
import QRCode from 'qrcode.react';
import { useAuth } from '../contexts/AuthContext';
import blockchainService from '../services/blockchainService';
import CrossChainTransfer from './CrossChainTransfer';
import { Package, Truck, Shield, Store, Eye, ArrowRight } from 'lucide-react';

const ProductManagement = () => {
  const { user, userRole } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showCrossChainTransfer, setShowCrossChainTransfer] = useState(false);
  const [transferProductId, setTransferProductId] = useState(null);
  const [showVerificationForm, setShowVerificationForm] = useState(false);
  const [verificationProductId, setVerificationProductId] = useState(null);
  const [multiChainStats, setMultiChainStats] = useState(null);
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    manufacturer: '',
    batchNumber: '',
    category: '',
    price: '',
    location: '',
    manufacturingDate: '',
    expirationDate: '',
    uniqueProductID: ''
  });

  useEffect(() => {
    fetchProducts();
    loadMultiChainStats();
  }, []);

  const loadMultiChainStats = async () => {
    try {
      const stats = await blockchainService.getAllChainStats();
      setMultiChainStats(stats);
    } catch (error) {
      console.error('Error loading multi-chain stats:', error);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/products/`);
      setProducts(response.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
      setProducts([]);
    }
    setLoading(false);
  };

  const createProduct = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Prepare metadata for cross-chain minting
      const metadata = {
        name: newProduct.name,
        description: newProduct.description,
        category: newProduct.category,
        batchNumber: newProduct.batchNumber || `BATCH-${Date.now()}`,
        price: newProduct.price,
        location: newProduct.location,
        manufacturingDate: newProduct.manufacturingDate || new Date().toISOString().split('T')[0],
        expirationDate: newProduct.expirationDate,
        uniqueProductID: newProduct.uniqueProductID || `PROD-${Date.now()}`,
        productType: newProduct.category || 'General'
      };

      console.log('Creating product with enhanced blockchain service:', metadata);

      // Use the enhanced blockchain service for cross-chain minting
      const result = await blockchainService.mintProduct({
        manufacturer: newProduct.manufacturer || user?.wallet_address || "0x032041b4b356fEE1496805DD4749f181bC736FFA",
        metadata: metadata
      });
      
      console.log('Product created successfully with cross-chain integration:', result);
      
      // Show success message with enhanced details
      alert(`✅ Product created successfully on blockchain!\n\n🆔 Token ID: ${result.token_id}\n📁 Metadata CID: ${result.metadata_cid}\n🔗 Transaction: ${result.transaction_hash}\n🔐 QR Hash: ${result.qr_hash}`);
      
      await fetchProducts();
      await loadMultiChainStats(); // Refresh multi-chain stats
      setShowCreateForm(false);
      setNewProduct({
        name: '',
        description: '',
        manufacturer: '',
        batchNumber: '',
        category: '',
        price: '',
        location: '',
        manufacturingDate: '',
        expirationDate: '',
        uniqueProductID: ''
      });
    } catch (error) {
      console.error('Error creating product:', error);
      const errorMessage = error.message || 'Unknown error occurred';
      alert(`❌ Error creating product: ${errorMessage}`);
    }
    setLoading(false);
  };

  const generateQRCode = (product) => {
    // Use encrypted QR code if available, otherwise fallback to basic data
    if (product.encrypted_qr_code) {
      return product.encrypted_qr_code;
    }
    
    // Fallback QR data
    const qrData = {
      productId: product.token_id || product.id || product._id,
      name: product.name || product.metadata?.name,
      manufacturer: product.manufacturer,
      blockchain: 'polygon',
      contractAddress: process.env.REACT_APP_CONTRACT_ADDRESS || '0x60C466cF52cb9705974a89b72DeA045c45cb7572'
    };
    return JSON.stringify(qrData);
  };

  // Cross-chain operations
  const handleCrossChainTransfer = (productTokenId) => {
    setTransferProductId(productTokenId);
    setShowCrossChainTransfer(true);
  };

  const handleVerifyProduct = async (productTokenId) => {
    try {
      setLoading(true);
      const product = products.find(p => p.token_id === productTokenId);
      if (!product) {
        alert('Product not found');
        return;
      }

      // Use Algorithm 4: Product Authenticity Verification
      const result = await blockchainService.verifyProductAuthenticity({
        product_id: productTokenId,
        qr_data: generateQRCode(product),
        current_owner: user?.wallet_address || product.current_owner
      });

      alert(`🔍 Product Verification Result:\n\n✅ Status: ${result.status}\n📅 Verified: ${new Date(result.verification_timestamp * 1000).toLocaleString()}\n🔐 QR Verified: ${result.details?.qr_verified ? '✅' : '❌'}\n👤 Owner Verified: ${result.details?.owner_verified ? '✅' : '❌'}`);
    } catch (error) {
      console.error('Verification error:', error);
      alert(`❌ Verification failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleListInMarketplace = async (productTokenId) => {
    try {
      const price = prompt('Enter price for marketplace listing:');
      if (!price || isNaN(price)) {
        alert('Please enter a valid price');
        return;
      }

      setLoading(true);

      // Use Algorithm 5: Post Supply Chain Management (Marketplace)
      const result = await blockchainService.listProductForSale({
        product_id: productTokenId,
        price: parseFloat(price),
        target_chains: [80002, 2442, 421614, 11155420] // All chains
      });

      alert(`🛒 Product listed in marketplace!\n\n💰 Price: $${price}\n📅 Listed: ${new Date(result.listing_timestamp * 1000).toLocaleString()}\n🌐 Available on ${result.listed_on_chains.length} chains`);
      
      await fetchProducts();
    } catch (error) {
      console.error('Marketplace listing error:', error);
      alert(`❌ Failed to list in marketplace: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleQualityCheck = async (productTokenId) => {
    try {
      const score = prompt('Enter quality score (0-100):');
      if (!score || isNaN(score) || score < 0 || score > 100) {
        alert('Please enter a valid score between 0 and 100');
        return;
      }

      const passed = parseInt(score) >= 70;
      
      setLoading(true);

      // Perform quality check (manufacturer chain operation)
      const result = await blockchainService.performQualityCheck(
        productTokenId,
        user?.wallet_address || 'inspector',
        passed,
        parseInt(score)
      );

      alert(`🔍 Quality Check ${passed ? 'PASSED' : 'FAILED'}!\n\n📊 Score: ${score}/100\n✅ Status: ${result.status}\n📅 Checked: ${new Date().toLocaleString()}`);
      
      await fetchProducts();
    } catch (error) {
      console.error('Quality check error:', error);
      alert(`❌ Quality check failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentDate = () => {
    return new Date().toISOString().split('T')[0];
  };

  const getExpirationDate = () => {
    const date = new Date();
    date.setFullYear(date.getFullYear() + 1); // 1 year from now
    return date.toISOString().split('T')[0];
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <div>
          <h2 style={{ fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>📦 Cross-Chain Product Management</h2>
          <p style={{ color: '#6b7280', margin: '5px 0' }}>Multi-chain product lifecycle with blockchain verification</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={loadMultiChainStats}
            className="btn"
            style={{ 
              background: '#6b7280', 
              color: 'white', 
              border: 'none', 
              padding: '10px 20px', 
              borderRadius: '6px',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            🔄 Refresh Stats
          </button>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn"
            style={{ 
              background: '#3b82f6', 
              color: 'white', 
              border: 'none', 
              padding: '12px 24px', 
              borderRadius: '8px',
              fontSize: '16px',
              cursor: 'pointer'
            }}
          >
            {showCreateForm ? 'Cancel' : '+ Create Product'}
          </button>
        </div>
      </div>

      {/* Multi-Chain Stats */}
      {multiChainStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-800 mb-2">🏛️ Hub Chain</h3>
            <div className="text-sm text-blue-700">
              <div>Status: {multiChainStats.multichain?.polygon_pos_hub?.connected ? '✅ Connected' : '❌ Disconnected'}</div>
              <div>Products: {multiChainStats.multichain?.statistics?.total_products || 0}</div>
            </div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-800 mb-2">🏭 Manufacturer</h3>
            <div className="text-sm text-green-700">
              <div>Chain: zkEVM Cardona</div>
              <div>Products: {multiChainStats.multichain?.statistics?.total_products || 0}</div>
            </div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="font-semibold text-yellow-800 mb-2">🚛 Transporter</h3>
            <div className="text-sm text-yellow-700">
              <div>Chain: Arbitrum Sepolia</div>
              <div>Shipments: {multiChainStats.multichain?.statistics?.total_transactions || 0}</div>
            </div>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 className="font-semibold text-purple-800 mb-2">🛒 Buyer</h3>
            <div className="text-sm text-purple-700">
              <div>Chain: Optimism Sepolia</div>
              <div>Purchases: {multiChainStats.multichain?.statistics?.total_disputes || 0}</div>
            </div>
          </div>
        </div>
      )}

      {/* Create Product Form */}
      {showCreateForm && (
        <div className="card" style={{ marginBottom: '30px', padding: '20px' }}>
          <h3 style={{ marginBottom: '20px' }}>Create New Product (NFTCore Contract)</h3>
          <form onSubmit={createProduct}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Product Name *</label>
                <input
                  type="text"
                  required
                  value={newProduct.name}
                  onChange={(e) => setNewProduct({...newProduct, name: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="Enter product name"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Unique Product ID</label>
                <input
                  type="text"
                  value={newProduct.uniqueProductID}
                  onChange={(e) => setNewProduct({...newProduct, uniqueProductID: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="Auto-generated if empty"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Category/Product Type</label>
                <select
                  value={newProduct.category}
                  onChange={(e) => setNewProduct({...newProduct, category: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                >
                  <option value="">Select category</option>
                  <option value="Electronics">Electronics</option>
                  <option value="Food & Beverage">Food & Beverage</option>
                  <option value="Pharmaceuticals">Pharmaceuticals</option>
                  <option value="Textiles">Textiles</option>
                  <option value="Automotive">Automotive</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Batch Number</label>
                <input
                  type="text"
                  value={newProduct.batchNumber}
                  onChange={(e) => setNewProduct({...newProduct, batchNumber: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="Auto-generated if empty"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Manufacturing Date</label>
                <input
                  type="date"
                  value={newProduct.manufacturingDate}
                  onChange={(e) => setNewProduct({...newProduct, manufacturingDate: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  defaultValue={getCurrentDate()}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Expiration Date</label>
                <input
                  type="date"
                  value={newProduct.expirationDate}
                  onChange={(e) => setNewProduct({...newProduct, expirationDate: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="Optional"
                />
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Description</label>
                <textarea
                  value={newProduct.description}
                  onChange={(e) => setNewProduct({...newProduct, description: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px',
                    minHeight: '80px'
                  }}
                  placeholder="Enter product description"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Price (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newProduct.price}
                  onChange={(e) => setNewProduct({...newProduct, price: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="0.00"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Manufacturing Location</label>
                <input
                  type="text"
                  value={newProduct.location}
                  onChange={(e) => setNewProduct({...newProduct, location: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="Manufacturing location"
                />
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Manufacturer Address</label>
                <input
                  type="text"
                  value={newProduct.manufacturer}
                  onChange={(e) => setNewProduct({...newProduct, manufacturer: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="0x... (defaults to demo address if empty)"
                />
              </div>
            </div>
            <div style={{ marginTop: '20px' }}>
              <button
                type="submit"
                disabled={loading}
                className="btn"
                style={{ 
                  background: loading ? '#9ca3af' : '#10b981', 
                  color: 'white', 
                  border: 'none', 
                  padding: '12px 24px', 
                  borderRadius: '8px',
                  fontSize: '16px',
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Creating Product NFT...' : 'Create Product on Blockchain'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Products List */}
      <div className="card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>Products List</h3>
          <button
            onClick={fetchProducts}
            className="btn"
            style={{ 
              background: '#6b7280', 
              color: 'white', 
              border: 'none', 
              padding: '8px 16px', 
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            🔄 Refresh
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '18px', color: '#6b7280' }}>Loading products...</div>
          </div>
        )}

        {!loading && products.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '18px', color: '#6b7280', marginBottom: '10px' }}>No products found</div>
            <div style={{ fontSize: '14px', color: '#9ca3af' }}>Create your first product to get started</div>
          </div>
        )}

        {!loading && products.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
            {products.map((product, index) => (
              <div key={product.token_id || product.id || index} className="card" style={{ border: '1px solid #e5e7eb', padding: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
                    {product.name || product.metadata?.name || `Product ${index + 1}`}
                  </h4>
                  <span style={{ 
                    background: '#dbeafe', 
                    color: '#1e40af', 
                    padding: '2px 8px', 
                    borderRadius: '12px',
                    fontSize: '12px'
                  }}>
                    {product.category || product.metadata?.category || 'General'}
                  </span>
                </div>
                
                <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '10px' }}>
                  <div><strong>Description:</strong> {product.description || product.metadata?.description || 'No description'}</div>
                  <div><strong>Batch:</strong> {product.batchNumber || product.metadata?.batchNumber || 'N/A'}</div>
                  <div><strong>Price:</strong> ${product.price || product.metadata?.price || '0.00'}</div>
                  {product.token_id && <div><strong>Token ID:</strong> {product.token_id}</div>}
                  {product.metadata_cid && <div><strong>IPFS CID:</strong> {product.metadata_cid.substring(0, 20)}...</div>}
                  {product.manufacturer && (
                    <div><strong>Manufacturer:</strong> {product.manufacturer.substring(0, 10)}...</div>
                  )}
                  {product.qr_hash && (
                    <div><strong>QR Hash:</strong> {product.qr_hash.substring(0, 16)}...</div>
                  )}
                </div>

                <div style={{ marginTop: '15px' }}>
                  <div style={{ marginBottom: '10px', textAlign: 'center' }}>
                    <QRCode 
                      value={generateQRCode(product)} 
                      size={100}
                      style={{ border: '1px solid #e5e7eb', padding: '5px' }}
                    />
                  </div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '10px', textAlign: 'center' }}>
                    {product.encrypted_qr_code ? '🔐 Encrypted QR Code' : '📱 Basic QR Code'}
                  </div>
                  
                  {/* Cross-Chain Operations */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginBottom: '10px' }}>
                    <button
                      onClick={() => handleCrossChainTransfer(product.token_id)}
                      className="btn"
                      style={{ 
                        background: '#10b981', 
                        color: 'white', 
                        border: 'none', 
                        padding: '6px 8px', 
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      title="Transfer to another chain"
                    >
                      <Truck className="w-3 h-3 mr-1" />
                      Ship
                    </button>
                    
                    <button
                      onClick={() => handleVerifyProduct(product.token_id)}
                      className="btn"
                      style={{ 
                        background: '#8b5cf6', 
                        color: 'white', 
                        border: 'none', 
                        padding: '6px 8px', 
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      title="Verify authenticity using Algorithm 4"
                    >
                      <Shield className="w-3 h-3 mr-1" />
                      Verify
                    </button>
                    
                    {userRole === 'manufacturer' && (
                      <button
                        onClick={() => handleQualityCheck(product.token_id)}
                        className="btn"
                        style={{ 
                          background: '#f59e0b', 
                          color: 'white', 
                          border: 'none', 
                          padding: '6px 8px', 
                          borderRadius: '4px',
                          fontSize: '12px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                        title="Perform quality check"
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        QC
                      </button>
                    )}
                    
                    <button
                      onClick={() => handleListInMarketplace(product.token_id)}
                      className="btn"
                      style={{ 
                        background: '#ec4899', 
                        color: 'white', 
                        border: 'none', 
                        padding: '6px 8px', 
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      title="List in marketplace using Algorithm 5"
                    >
                      <Store className="w-3 h-3 mr-1" />
                      Sell
                    </button>
                  </div>
                  
                  <button
                    onClick={() => setSelectedProduct(selectedProduct?.token_id === product.token_id ? null : product)}
                    className="btn"
                    style={{ 
                      background: '#3b82f6', 
                      color: 'white', 
                      border: 'none', 
                      padding: '8px 12px', 
                      borderRadius: '4px',
                      fontSize: '14px',
                      cursor: 'pointer',
                      width: '100%'
                    }}
                  >
                    {selectedProduct?.token_id === product.token_id ? 'Hide Details' : 'View Details'}
                  </button>
                </div>

                {selectedProduct?.token_id === product.token_id && (
                  <div style={{ 
                    marginTop: '15px', 
                    padding: '10px', 
                    background: '#f9fafb', 
                    borderRadius: '6px',
                    fontSize: '12px'
                  }}>
                    <div><strong>Token ID:</strong> {product.token_id || 'N/A'}</div>
                    <div><strong>Created:</strong> {product.created_at ? new Date(product.created_at * 1000).toLocaleDateString() : 'N/A'}</div>
                    <div><strong>Status:</strong> {product.status || 'Active'}</div>
                    <div><strong>Chain ID:</strong> {product.chain_id || 'N/A'}</div>
                    {product.transaction_hash && (
                      <div><strong>Tx Hash:</strong> {product.transaction_hash.substring(0, 20)}...</div>
                    )}
                    {product.mint_params && (
                      <div style={{ marginTop: '8px' }}>
                        <strong>NFT Parameters:</strong>
                        <div style={{ marginLeft: '10px', fontSize: '11px' }}>
                          <div>Unique ID: {product.mint_params.uniqueProductID}</div>
                          <div>Manufacturing Date: {product.mint_params.manufacturingDate}</div>
                          <div>Product Type: {product.mint_params.productType}</div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Cross-Chain Transfer Modal */}
      {showCrossChainTransfer && transferProductId && (
        <CrossChainTransfer
          productTokenId={transferProductId}
          onClose={() => {
            setShowCrossChainTransfer(false);
            setTransferProductId(null);
            fetchProducts(); // Refresh products after transfer
          }}
        />
      )}
    </div>
  );
};

export default ProductManagement;
