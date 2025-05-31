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
    location: ''
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
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/blockchain/products/mint`, {
        manufacturer: newProduct.manufacturer || "0x032041b4b356fEE1496805DD4749f181bC736FFA",
        metadata: {
          name: newProduct.name,
          description: newProduct.description,
          category: newProduct.category,
          batchNumber: newProduct.batchNumber,
          price: newProduct.price,
          location: newProduct.location
        }
      });
      
      console.log('Product created:', response.data);
      await fetchProducts();
      setShowCreateForm(false);
      setNewProduct({
        name: '',
        description: '',
        manufacturer: '',
        batchNumber: '',
        category: '',
        price: '',
        location: ''
      });
    } catch (error) {
      console.error('Error creating product:', error);
      alert('Error creating product: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const generateQRCode = (product) => {
    const qrData = {
      productId: product.id || product._id,
      name: product.name || product.metadata?.name,
      manufacturer: product.manufacturer,
      blockchain: 'polygon',
      contractAddress: process.env.REACT_APP_CONTRACT_ADDRESS
    };
    return JSON.stringify(qrData);
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
          <h3 style={{ marginBottom: '20px' }}>Create New Product</h3>
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
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Category</label>
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
                  placeholder="BATCH-001"
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
                  placeholder="0x..."
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Location</label>
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
                {loading ? 'Creating...' : 'Create Product on Blockchain'}
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {products.map((product, index) => (
              <div key={product.id || index} className="card" style={{ border: '1px solid #e5e7eb', padding: '15px' }}>
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
                  {product.tokenId && <div><strong>Token ID:</strong> {product.tokenId}</div>}
                  {product.manufacturer && (
                    <div><strong>Manufacturer:</strong> {product.manufacturer.substring(0, 10)}...</div>
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
                  <button
                    onClick={() => setSelectedProduct(selectedProduct?.id === product.id ? null : product)}
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
                    {selectedProduct?.id === product.id ? 'Hide Details' : 'View Details'}
                  </button>
                </div>

                {selectedProduct?.id === product.id && (
                  <div style={{ 
                    marginTop: '15px', 
                    padding: '10px', 
                    background: '#f9fafb', 
                    borderRadius: '6px',
                    fontSize: '12px'
                  }}>
                    <div><strong>Product ID:</strong> {product.id || 'N/A'}</div>
                    <div><strong>Created:</strong> {product.createdAt ? new Date(product.createdAt).toLocaleDateString() : 'N/A'}</div>
                    <div><strong>Status:</strong> Active</div>
                    {product.transactionHash && (
                      <div><strong>Tx Hash:</strong> {product.transactionHash.substring(0, 20)}...</div>
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