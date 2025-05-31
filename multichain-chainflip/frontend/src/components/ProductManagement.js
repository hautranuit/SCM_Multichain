import React, { useState, useEffect } from 'react';
import axios from 'axios';
import QRCode from 'qrcode.react';

const ProductManagement = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
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
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/products`);
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
      // Prepare metadata for NFTCore contract
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

      console.log('Creating product with metadata:', metadata);

      // Send to backend (backend will handle IPFS upload & encryption)
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/blockchain/products/mint`, {
        manufacturer: newProduct.manufacturer || "0x032041b4b356fEE1496805DD4749f181bC736FFA",
        metadata: metadata
      });
      
      console.log('Product created successfully:', response.data);
      
      // Show success message with details
      alert(`Product created successfully!\n\nToken ID: ${response.data.token_id}\nMetadata CID: ${response.data.metadata_cid}\nTransaction: ${response.data.transaction_hash}`);
      
      await fetchProducts();
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
      console.error('Error creating product:', error.response?.data || error.message);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      alert(`Error creating product: ${errorMessage}`);
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

  const getCurrentDate = () => {
    return new Date().toISOString().split('T')[0];
  };

  const getExpirationDate = () => {
    const date = new Date();
    date.setFullYear(date.getFullYear() + 1); // 1 year from now
    return date.toISOString().split('T')[0];
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>📦 Products Management</h2>
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

                <div style={{ marginTop: '15px', textAlign: 'center' }}>
                  <div style={{ marginBottom: '10px' }}>
                    <QRCode 
                      value={generateQRCode(product)} 
                      size={120}
                      style={{ border: '1px solid #e5e7eb', padding: '5px' }}
                    />
                  </div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '10px' }}>
                    {product.encrypted_qr_code ? '🔐 Encrypted QR Code' : '📱 Basic QR Code'}
                  </div>
                  <button
                    onClick={() => setSelectedProduct(selectedProduct?.token_id === product.token_id ? null : product)}
                    className="btn"
                    style={{ 
                      background: '#3b82f6', 
                      color: 'white', 
                      border: 'none', 
                      padding: '6px 12px', 
                      borderRadius: '4px',
                      fontSize: '14px',
                      cursor: 'pointer'
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
    </div>
  );
};

export default ProductManagement;
