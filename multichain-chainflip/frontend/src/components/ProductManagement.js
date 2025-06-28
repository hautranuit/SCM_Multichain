import React, { useState, useEffect } from 'react';
import axios from 'axios';
import QRCode from 'qrcode.react';
import { useAuth } from '../contexts/AuthContext';
import blockchainService from '../services/blockchainService';
import CrossChainTransfer from './CrossChainTransfer';
import ShippingInformationForm from './ShippingInformationForm';
import { Package, Truck, Shield, Store, ShoppingCart, Plus, Upload, RefreshCw, Sparkles, Zap, Star, Play, Image as ImageIcon, Eye } from 'lucide-react';

const ProductManagement = () => {
  const { user, userRole } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showCrossChainTransfer, setShowCrossChainTransfer] = useState(false);
  const [transferProductId, setTransferProductId] = useState(null);
  const [showShippingForm, setShowShippingForm] = useState(false);
  const [selectedProductForPurchase, setSelectedProductForPurchase] = useState(null);
  const [multiChainStats, setMultiChainStats] = useState(null);
  const [productImage, setProductImage] = useState(null);
  const [productVideo, setProductVideo] = useState(null);
  const [activeTab, setActiveTab] = useState('marketplace'); // For buyer tabs: marketplace, orders, owned
  // NEW: Delivery queue state for manufacturers
  const [deliveryQueue, setDeliveryQueue] = useState([]);
  const [loadingDelivery, setLoadingDelivery] = useState(false);
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    manufacturer: '', // Will be auto-populated by useEffect
    batchNumber: '',
    category: '',
    price: '',
    location: '',
    manufacturingDate: '',
    expirationDate: '',
    uniqueProductID: ''
  });

  // Auto-populate manufacturer address when wallet connects
  useEffect(() => {
    if (user?.wallet_address && !newProduct.manufacturer) {
      setNewProduct(prev => ({
        ...prev,
        manufacturer: user.wallet_address
      }));
    }
  }, [user?.wallet_address]);

  // ADDITIONAL: Ensure manufacturer field is always populated when form is used
  useEffect(() => {
    if (!newProduct.manufacturer && user?.wallet_address) {
      setNewProduct(prev => ({
        ...prev,
        manufacturer: user.wallet_address
      }));
    }
  }, [newProduct.manufacturer, user?.wallet_address]);

  useEffect(() => {
    fetchProducts();
    loadMultiChainStats();
    // Load delivery queue for manufacturers only
    if (userRole === 'manufacturer' && activeTab === 'delivery') {
      fetchDeliveryQueue();
    }
  }, [activeTab, userRole]); // Fixed dependency array

  useEffect(() => {
    fetchProducts();
    loadMultiChainStats();
    // NEW: Load delivery queue on mount for manufacturers
    if (userRole === 'manufacturer') {
      fetchDeliveryQueue();
    }
  }, [userRole]); // Fixed dependency array

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
      // Build API URL with role-based filtering following Algorithm 5
      let apiUrl = `${process.env.REACT_APP_BACKEND_URL}/api/products/`;
      
      // Add role-based filtering parameters if user is authenticated
      if (userRole && user?.wallet_address) {
        const params = new URLSearchParams({
          user_role: userRole,
          wallet_address: user.wallet_address,
          view_type: activeTab  // marketplace, owned, created, orders
        });
        
        // ENHANCED: Add on-chain verification for "My Products" tab
        if (activeTab === 'owned') {
          // Enable on-chain verification for owned products to handle cross-chain transfers
          params.append('verify_on_chain', 'true');
          console.log('🔗 Enabling on-chain verification for "My Products" tab');
        }
        
        apiUrl += `?${params.toString()}`;
      }
      
      console.log(`📦 Fetching products for ${userRole} (${activeTab}):`, apiUrl);
      
      const response = await axios.get(apiUrl);
      console.log('✅ Fetched products:', response.data);
      
      // Handle both filtered and unfiltered responses
      const products = response.data.products || response.data || [];
      setProducts(products);
      
      // Show filtering info to user
      if (response.data.filtered_by) {
        console.log(`🔍 Products filtered for ${response.data.filtered_by}: ${response.data.count} products`);
        
        // Show verification status for owned products
        if (response.data.on_chain_verified !== undefined) {
          console.log(`🔗 On-chain verification: ${response.data.on_chain_verified ? '✅ Enabled' : '❌ Disabled'}`);
        }
      }
      
    } catch (error) {
      console.error('❌ Error fetching products:', error);
      setProducts([]);
    }
    setLoading(false);
  };

  // NEW: Handle cleanup of duplicate delivery orders
  const handleCleanupDuplicates = async () => {
    if (!user?.wallet_address) return;
    
    const confirmCleanup = window.confirm(
      'This will remove duplicate orders in your delivery queue, keeping only the most recent order for each product. Continue?'
    );
    
    if (!confirmCleanup) return;
    
    setLoadingDelivery(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/blockchain/delivery/queue/cleanup/${user.wallet_address}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Cleanup successful! Removed ${result.total_removed} duplicate orders.`);
        // Refresh the delivery queue
        await fetchDeliveryQueue();
      } else {
        throw new Error('Failed to cleanup duplicates');
      }
    } catch (error) {
      console.error('❌ Error cleaning up duplicates:', error);
      alert('Failed to cleanup duplicates. Please try again.');
    }
    setLoadingDelivery(false);
  };

  // NEW: Fetch delivery queue for manufacturers
  const fetchDeliveryQueue = async () => {
    if (userRole !== 'manufacturer' || !user?.wallet_address) {
      console.log('❌ Cannot fetch delivery queue:', { userRole, wallet: user?.wallet_address });
      return;
    }
    
    setLoadingDelivery(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const apiUrl = `${backendUrl}/api/blockchain/delivery/queue/${user.wallet_address}`;
      
      console.log('🔍 Fetching delivery queue from:', apiUrl);
      console.log('🔍 Manufacturer address:', user.wallet_address);
      
      const response = await fetch(apiUrl);
      console.log('📡 Response status:', response.status, response.statusText);
      
      if (response.ok) {
        const data = await response.json();
        console.log('📋 Delivery queue response:', data);
        setDeliveryQueue(data.orders || []);
        console.log(`📋 Loaded ${data.count || data.orders?.length || 0} delivery orders for manufacturer`);
      } else {
        const errorText = await response.text();
        console.error('❌ Failed to fetch delivery queue:', response.status, errorText);
        setDeliveryQueue([]);
      }
    } catch (error) {
      console.error('❌ Error fetching delivery queue:', error);
      setDeliveryQueue([]);
    }
    setLoadingDelivery(false);
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setProductImage({
          file: file,
          data: reader.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleVideoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setProductVideo({
          file: file,
          data: reader.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadFileToIPFS = async (fileData, filename, mimeType) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/ipfs/upload-file`, {
        fileData: fileData,
        filename: filename,
        mimeType: mimeType
      });
      
      if (response.data.success) {
        return response.data.cid;
      } else {
        throw new Error('Upload failed: ' + (response.data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('IPFS upload error:', error);
      throw error;
    }
  };

  const createProduct = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      let imageCid = '';
      let videoCid = '';

      // Upload image if selected
      if (productImage) {
        console.log('Uploading image to IPFS...');
        try {
          imageCid = await uploadFileToIPFS(
            productImage.data,
            `product_image_${Date.now()}.${productImage.file.name.split('.').pop()}`,
            productImage.file.type
          );
          console.log('Image uploaded, CID:', imageCid);
        } catch (error) {
          console.warn('Image upload failed, continuing without image:', error);
          // Continue without image rather than failing completely
        }
      }

      // Upload video if selected
      if (productVideo) {
        console.log('Uploading video to IPFS...');
        try {
          videoCid = await uploadFileToIPFS(
            productVideo.data,
            `product_video_${Date.now()}.${productVideo.file.name.split('.').pop()}`,
            productVideo.file.type
          );
          console.log('Video uploaded, CID:', videoCid);
        } catch (error) {
          console.warn('Video upload failed, continuing without video:', error);
          // Continue without video rather than failing completely
        }
      }

      // Prepare metadata for cross-chain minting with proper CID mapping
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
        productType: newProduct.category || 'General',
        imageCID: imageCid,  // Use the uploaded image CID
        videoCID: videoCid   // Use the uploaded video CID
      };

      console.log('Final metadata with CIDs:', {
        imageCID: metadata.imageCID,
        videoCID: metadata.videoCID,
        productName: metadata.name
      });

      console.log('Creating product with enhanced blockchain service:', metadata);

      // Use the enhanced blockchain service for cross-chain minting
      const result = await blockchainService.mintProduct({
        manufacturer: newProduct.manufacturer || user?.wallet_address || "0x032041b4b356fEE1496805DD4749f181bC736FFA",
        metadata: metadata
      });
      
      console.log('Product created successfully with cross-chain integration:', result);
      
      // Show success message with enhanced details
      alert(`✅ Product created successfully!\n\n🆔 Token ID: ${result.token_id}\n📁 Metadata CID: ${result.metadata_cid}\n🔗 Transaction: ${result.transaction_hash}\n🔐 QR Hash: ${result.qr_hash}${imageCid ? `\n🖼️ Image CID: ${imageCid}` : ''}${videoCid ? `\n🎥 Video CID: ${videoCid}` : ''}\n\n🏭 Manufacturer: ${newProduct.manufacturer || user?.wallet_address || "0x032041b4b356fEE1496805DD4749f181bC736FFA"}`);
      
      await fetchProducts();
      await loadMultiChainStats(); // Refresh multi-chain stats
      setShowCreateForm(false);
      setProductImage(null);
      setProductVideo(null);
      setNewProduct({
        name: '',
        description: '',
        manufacturer: user?.wallet_address || '', // Auto-populate manufacturer on reset
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
    // Use the simplified encrypted QR code containing CID link
    if (product.encrypted_qr_code) {
      return product.encrypted_qr_code;
    }
    
    // Fallback: Simple JSON with essential info (should rarely be used)
    const fallbackData = {
      error: "Encrypted QR not available",
      token_id: product.token_id || "N/A",
      cid: product.metadata_cid || "N/A",
      verify_url: `https://chainflip.app/verify/${product.token_id || 'unknown'}`
    };
    
    return JSON.stringify(fallbackData);
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
      // Get the product to use its existing price
      const product = products.find(p => p.token_id === productTokenId);
      if (!product) {
        alert('Product not found');
        return;
      }

      // Use existing product price instead of prompting
      const existingPrice = product.price || product.metadata?.price || product.metadata?.price_eth;
      
      if (!existingPrice || isNaN(existingPrice) || parseFloat(existingPrice) <= 0) {
        alert('❌ Cannot list product: No valid price set during creation.\n\nPlease ensure the product has a price before listing for sale.');
        return;
      }

      const confirmation = window.confirm(
        `🛒 List Product For Sale\n\n` +
        `📦 Product: ${product.name || 'Unknown Product'}\n` +
        `💰 Price: ${existingPrice} ETH\n\n` +
        `This will make your product available in the buyer marketplace.\n\n` +
        `Continue with listing?`
      );

      if (!confirmation) return;

      setLoading(true);

      // Use Algorithm 5: Post Supply Chain Management (Marketplace)
      const result = await blockchainService.listProductForSale({
        product_id: productTokenId,
        price: parseFloat(existingPrice),
        target_chains: [80002, 84532, 421614, 11155420] // All chains
      });

      alert(`🛒 Product successfully listed for sale!\n\n💰 Price: ${existingPrice} ETH\n📅 Listed: ${new Date(result.listing_timestamp * 1000).toLocaleString()}\n🌐 Available on ${result.listed_on_chains.length} chains\n\n✅ Buyers can now discover and purchase your product!`);
      
      await fetchProducts();
    } catch (error) {
      console.error('Marketplace listing error:', error);
      alert(`❌ Failed to list in marketplace: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteShipping = async (productTokenId) => {
    try {
      const confirmation = window.confirm('Mark this product as delivered and complete shipping?');
      if (!confirmation) return;

      setLoading(true);

      // Complete shipping operation (transporter chain operation)
      const result = await blockchainService.completeShipping({
        product_id: productTokenId,
        transporter: user?.wallet_address,
        delivery_confirmation: true,
        delivery_timestamp: Date.now()
      });

      alert(`✅ Shipping Completed!\n\n📦 Product: ${productTokenId}\n🚛 Delivered by: ${user?.wallet_address}\n📅 Completed: ${new Date().toLocaleString()}\n🔗 Transaction: ${result.transaction_hash || 'N/A'}`);
      
      await fetchProducts();
    } catch (error) {
      console.error('Complete shipping error:', error);
      alert(`❌ Failed to complete shipping: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBuyProduct = async (productTokenId) => {
    try {
      const product = products.find(p => p.token_id === productTokenId);
      if (!product) {
        alert('Product not found');
        return;
      }

      // Show shipping form instead of direct purchase
      setSelectedProductForPurchase(product);
      setShowShippingForm(true);
    } catch (error) {
      console.error('Error preparing purchase:', error);
    }
  };

  // Shipping form submission handler
  const handleShippingFormSubmit = async (shippingInfo) => {
    try {
      setLoading(true);
      
      const product = selectedProductForPurchase;
      const price = product.price || product.metadata?.price_eth || '0.001';
      
      console.log('🚢 Submitting purchase with shipping info:', shippingInfo);
      
      // Proceed with purchase including shipping info
      const result = await blockchainService.buyProduct({
        product_id: product.token_id,
        buyer: user?.wallet_address,
        price: parseFloat(price),
        payment_method: 'ETH',
        shipping_info: shippingInfo  // Include shipping information
      });

      if (result.success) {
        alert('🎉 Purchase successful! Manufacturer has been notified to start shipping process.');
        setShowShippingForm(false);
        setSelectedProductForPurchase(null);
        await fetchProducts();
      }
    } catch (error) {
      console.error('Purchase error:', error);
      alert(`❌ Purchase failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleInitiateDelivery = async (orderId) => {
    try {
      setLoadingDelivery(true);
      console.log('🚚 Initiating delivery for order:', orderId);
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/blockchain/delivery/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          order_id: orderId,
          manufacturer_address: user?.wallet_address
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert('✅ Delivery notification sent to admin successfully! Cross-chain message delivered to Polygon Amoy.');
        // Refresh delivery queue
        await fetchDeliveryQueue();
      } else {
        alert(`❌ Failed to initiate delivery: ${result.error}`);
      }
    } catch (error) {
      console.error('Error initiating delivery:', error);
      alert(`❌ Error initiating delivery: ${error.message}`);
    } finally {
      setLoadingDelivery(false);
    }
  };

  const handleBridgePay = async (product) => {
    try {
      const price = product.price || product.metadata?.price_eth || '0.001';
      const manufacturer = product.manufacturer || product.metadata?.manufacturer || 'Unknown';
      
      const confirmation = window.confirm(
        `🌉 Token Bridge Payment\n\n` +
        `📦 Product: ${product.name || 'Product'}\n` +
        `💰 Amount: ${price} ETH\n` +
        `🏭 Manufacturer: ${manufacturer.substring(0, 10)}...\n\n` +
        `🔗 This will open the Token Bridge to transfer:\n` +
        `   📤 From: Your selected chain\n` +
        `   📥 To: Manufacturer's chain (Base Sepolia)\n` +
        `   💰 Amount: ${price} ETH\n\n` +
        `ℹ️ After successful transfer, you'll need to confirm the purchase.`
      );
      
      if (!confirmation) return;

      // Navigate to token bridge with prefilled data
      const bridgeUrl = `/token-bridge?` + new URLSearchParams({
        to_chain: 'base_sepolia',
        to_address: manufacturer,
        amount_eth: price,
        escrow_id: `PURCHASE-${product.token_id}-${Date.now()}`,
        purpose: `Payment for ${product.name || 'Product'}`
      }).toString();
      
      // Open in current window
      window.location.href = bridgeUrl;
      
    } catch (error) {
      console.error('Bridge pay error:', error);
      alert(`❌ Bridge Payment Setup Failed!\n\n${error.message}`);
    }
  };

  const getCurrentDate = () => {
    return new Date().toISOString().split('T')[0];
  };

  const getRoleInfo = () => {
    switch (userRole) {
      case 'manufacturer':
        return {
          title: 'Product Creation Studio',
          subtitle: 'Design, mint and manage NFT products with cutting-edge blockchain technology',
          icon: '🏭',
          gradient: 'from-blue-600 via-purple-600 to-cyan-600'
        };
      case 'transporter':
        return {
          title: 'Logistics Command Center',
          subtitle: 'Orchestrate deliveries with intelligent routing and performance optimization',
          icon: '🚛',
          gradient: 'from-green-500 via-emerald-500 to-teal-600'
        };
      case 'buyer':
        return {
          title: 'Premium Marketplace',
          subtitle: 'Discover authentic products with verified supply chains and secure transactions',
          icon: '🛒',
          gradient: 'from-purple-600 via-pink-500 to-rose-500'
        };
      default:
        return {
          title: 'Product Management',
          subtitle: 'Advanced blockchain-powered product lifecycle management',
          icon: '📦',
          gradient: 'from-indigo-600 via-blue-600 to-cyan-600'
        };
    }
  };

  // Helper function to get IPFS image URL
  const getImageUrl = (product) => {
    // Try different ways to get the image CID
    const imageCid = product.image_cid || product.imageCID || product.metadata?.imageCID || product.metadata?.image_cid;
    
    if (imageCid) {
      return `${process.env.REACT_APP_BACKEND_URL}/api/ipfs/${imageCid}`;
    }
    
    return null;
  };

  // Helper function to get IPFS video URL
  const getVideoUrl = (product) => {
    // Try different ways to get the video CID
    const videoCid = product.video_cid || product.videoCID || product.metadata?.videoCID || product.metadata?.video_cid;
    
    if (videoCid) {
      return `${process.env.REACT_APP_BACKEND_URL}/api/ipfs/${videoCid}`;
    }
    
    return null;
  };

  const roleInfo = getRoleInfo();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-20 -right-20 w-96 h-96 bg-gradient-to-r from-cyan-400/20 to-blue-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/3 -left-32 w-80 h-80 bg-gradient-to-r from-purple-400/15 to-pink-400/15 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-32 right-1/3 w-72 h-72 bg-gradient-to-r from-emerald-400/20 to-teal-400/20 rounded-full blur-3xl animate-pulse delay-500"></div>
        
        {/* Particle Grid */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxnIGZpbGw9Im5vbmUiIGZpbGwtcnVsZT0iZXZlbm9kZCI+CiAgICAgICAgPGcgZmlsbD0iIzM3NDE1MSIgZmlsbC1vcGFjaXR5PSIwLjAyIj4KICAgICAgICAgICAgPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMSI+CiAgICAgICAgICAgICAgICA8YW5pbWF0ZSBhdHRyaWJ1dGVOYW1lPSJmaWxsLW9wYWNpdHkiIHZhbHVlcz0iMC4wMjswLjA1OzAuMDIiIGR1cj0iM3MiIHJlcGVhdENvdW50PSJpbmRlZmluaXRlIi8+CiAgICAgICAgICAgIDwvY2lyY2xlPgogICAgICAgIDwvZz4KICAgIDwvZz4KPC9zdmc+')] opacity-30"></div>
      </div>

      {/* Ultra-Modern Header */}
      <div className="relative z-10 bg-white/5 backdrop-blur-2xl border-b border-white/10">
        <div className="px-8 py-16">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-8">
                <div className={`w-20 h-20 bg-gradient-to-r ${roleInfo.gradient} rounded-3xl flex items-center justify-center shadow-2xl shadow-blue-500/25 group-hover:scale-110 transition-all duration-300`}>
                  <span className="text-3xl">{roleInfo.icon}</span>
                </div>
                <div className="space-y-3">
                  <h1 className={`text-6xl font-bold bg-gradient-to-r ${roleInfo.gradient} bg-clip-text text-transparent`}>
                    {roleInfo.title}
                  </h1>
                  <p className="text-xl text-blue-100/80 max-w-3xl">
                    {roleInfo.subtitle}
                  </p>
                  <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
                      <Sparkles className="w-4 h-4 text-cyan-400" />
                      <span className="text-cyan-100 font-medium">Blockchain-Powered</span>
                    </div>
                    <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
                      <Zap className="w-4 h-4 text-yellow-400" />
                      <span className="text-white/90 font-medium">Real-Time Analytics</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={loadMultiChainStats}
                  className="group relative overflow-hidden bg-white/10 backdrop-blur-xl border border-white/20 text-white px-6 py-3 rounded-2xl transition-all duration-300 hover:bg-white/20 hover:scale-105 hover:shadow-xl hover:shadow-cyan-500/25"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/0 to-blue-400/10 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-500"></div>
                  <div className="relative flex items-center space-x-2">
                    <RefreshCw className="w-5 h-5" />
                    <span className="font-medium">Refresh Data</span>
                  </div>
                </button>
                {userRole === 'manufacturer' && (
                  <button
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    className={`group relative overflow-hidden ${showCreateForm ? 'bg-red-500 hover:bg-red-600' : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700'} text-white px-8 py-3 rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/25`}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-500"></div>
                    <div className="relative flex items-center space-x-2">
                      {showCreateForm ? (
                        <>
                          <span className="text-xl">✕</span>
                          <span className="font-semibold">Cancel</span>
                        </>
                      ) : (
                        <>
                          <Plus className="w-5 h-5" />
                          <span className="font-semibold">Create Product NFT</span>
                        </>
                      )}
                    </div>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 px-8 py-12">
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Multi-Chain Stats with Modern Design */}
          {multiChainStats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              {[
                { title: 'Hub Chain', subtitle: 'Polygon PoS', value: multiChainStats.multichain?.statistics?.total_products || 0, icon: '🏛️', color: 'blue' },
                { title: 'Manufacturer', subtitle: 'Base Sepolia', value: multiChainStats.multichain?.statistics?.total_products || 0, icon: '🏭', color: 'green' },
                { title: 'Transporter', subtitle: 'Arbitrum Sepolia', value: multiChainStats.multichain?.statistics?.total_transactions || 0, icon: '🚛', color: 'yellow' },
                { title: 'Buyer Chain', subtitle: 'Optimism Sepolia', value: multiChainStats.multichain?.statistics?.total_disputes || 0, icon: '🛒', color: 'purple' }
              ].map((stat, index) => (
                <div key={index} className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500 group-hover:shadow-2xl group-hover:shadow-cyan-500/20"></div>
                  <div className="relative p-8">
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-4xl group-hover:scale-110 transition-transform duration-300">{stat.icon}</div>
                      <div className={`w-3 h-3 rounded-full ${multiChainStats.multichain?.polygon_pos_hub?.connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-white/90 font-semibold">{stat.title}</h3>
                      <p className="text-white/60 text-sm">{stat.subtitle}</p>
                      <div className="text-3xl font-bold text-white group-hover:text-cyan-100 transition-colors duration-300">
                        {stat.value}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Modern Buyer Tabs */}
          {userRole === 'buyer' && (
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20"></div>
              <div className="relative p-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white flex items-center space-x-3">
                    <Star className="w-8 h-8 text-yellow-400" />
                    <span>Product Explorer</span>
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {(userRole === 'buyer' ? [
                    { key: 'marketplace', label: 'Marketplace', icon: '🛒', desc: 'Discover products' },
                    { key: 'orders', label: 'Your Orders', icon: '📋', desc: 'Track purchases' },
                    { key: 'owned', label: 'My Products', icon: '👤', desc: 'Owned items' }
                  ] : [
                    { key: 'marketplace', label: 'Products', icon: '📦', desc: 'All products' },
                    { key: 'delivery', label: 'Delivery Queue', icon: '🚚', desc: 'Orders to ship' },
                    { key: 'owned', label: 'Created', icon: '🏭', desc: 'Your products' }
                  ]).map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`group relative overflow-hidden p-6 rounded-2xl border transition-all duration-300 ${
                        activeTab === tab.key
                          ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-cyan-400/50 shadow-2xl shadow-cyan-500/25'
                          : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                      }`}
                    >
                      <div className="relative text-center">
                        <div className="text-3xl mb-2">{tab.icon}</div>
                        <div className="text-white font-semibold">{tab.label}</div>
                        <div className="text-white/60 text-sm mt-1">{tab.desc}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Modern Manufacturer Tabs */}
          {userRole === 'manufacturer' && (
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20"></div>
              <div className="relative p-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white flex items-center space-x-3">
                    <Package className="w-8 h-8 text-blue-400" />
                    <span>Manufacturing Hub</span>
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { key: 'marketplace', label: 'Products', icon: '📦', desc: 'All products' },
                    { key: 'delivery', label: 'Delivery Queue', icon: '🚚', desc: 'Orders to ship' },
                    { key: 'owned', label: 'Created', icon: '🏭', desc: 'Your products' }
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`group relative overflow-hidden p-6 rounded-2xl border transition-all duration-300 ${
                        activeTab === tab.key
                          ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-cyan-400/50 shadow-2xl shadow-cyan-500/25'
                          : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                      }`}
                    >
                      <div className="relative text-center">
                        <div className="text-3xl mb-2">{tab.icon}</div>
                        <div className="text-white font-semibold">{tab.label}</div>
                        <div className="text-white/60 text-sm mt-1">{tab.desc}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Create Product Form */}
          {showCreateForm && userRole === 'manufacturer' && (
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20"></div>
              <div className="relative p-8">
                <div className="text-center mb-8">
                  <h3 className="text-3xl font-bold text-white mb-2">Create Product NFT</h3>
                  <p className="text-white/70">Launch your product on Base Sepolia with complete manufacturer information</p>
                </div>
                <form onSubmit={createProduct} className="space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Product Name *</label>
                      <input
                        type="text"
                        required
                        value={newProduct.name}
                        onChange={(e) => setNewProduct({...newProduct, name: e.target.value})}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                        placeholder="Enter product name"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Unique Product ID *</label>
                      <input
                        type="text"
                        required
                        value={newProduct.uniqueProductID}
                        onChange={(e) => setNewProduct({...newProduct, uniqueProductID: e.target.value})}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                        placeholder={`PROD-${Date.now()}`}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Category</label>
                      <select
                        value={newProduct.category}
                        onChange={(e) => setNewProduct({...newProduct, category: e.target.value})}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                      >
                        <option value="" className="bg-slate-800">Select category</option>
                        <option value="Electronics" className="bg-slate-800">Electronics</option>
                        <option value="Food & Beverage" className="bg-slate-800">Food & Beverage</option>
                        <option value="Pharmaceuticals" className="bg-slate-800">Pharmaceuticals</option>
                        <option value="Textiles" className="bg-slate-800">Textiles</option>
                        <option value="Automotive" className="bg-slate-800">Automotive</option>
                        <option value="Other" className="bg-slate-800">Other</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Batch or Lot Number *</label>
                      <input
                        type="text"
                        required
                        value={newProduct.batchNumber}
                        onChange={(e) => setNewProduct({...newProduct, batchNumber: e.target.value})}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                        placeholder={`BATCH-${Date.now()}`}
                      />
                    </div>
                    <div className="md:col-span-2 space-y-2">
                      <label className="block text-white/90 font-medium">Description</label>
                      <textarea
                        value={newProduct.description}
                        onChange={(e) => setNewProduct({...newProduct, description: e.target.value})}
                        rows={3}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200 max-h-20 overflow-y-auto resize-none"
                        placeholder="Enter product description"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Manufacturing Date *</label>
                      <input
                        type="date"
                        required
                        value={newProduct.manufacturingDate}
                        onChange={(e) => setNewProduct({...newProduct, manufacturingDate: e.target.value})}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                        max={getCurrentDate()}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Expiration Date</label>
                      <input
                        type="date"
                        value={newProduct.expirationDate}
                        onChange={(e) => setNewProduct({...newProduct, expirationDate: e.target.value})}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                        min={newProduct.manufacturingDate || getCurrentDate()}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Manufacturer ID (Base Sepolia)</label>
                      <div className="relative">
                        <input
                          type="text"
                          value={newProduct.manufacturer}
                          readOnly
                          className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white/80 cursor-not-allowed"
                          placeholder="Connect wallet to auto-populate"
                        />
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-green-400">
                          <span className="text-sm font-semibold">✓ Connected</span>
                        </div>
                      </div>
                      <p className="text-white/50 text-xs">This is your connected wallet address on Base Sepolia chain</p>
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Price (ETH)</label>
                      <input
                        type="number"
                        step="0.001"
                        value={newProduct.price}
                        onChange={(e) => setNewProduct({...newProduct, price: e.target.value})}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                        placeholder="0.000"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Manufacturing Location</label>
                      <input
                        type="text"
                        value={newProduct.location}
                        onChange={(e) => setNewProduct({...newProduct, location: e.target.value})}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                        placeholder="Manufacturing location"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Product Image</label>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-cyan-500 file:text-white file:font-semibold hover:file:bg-cyan-600 transition-all duration-200"
                      />
                      {productImage && (
                        <div className="text-sm text-cyan-400 flex items-center space-x-2">
                          <span>✅</span>
                          <span>{productImage.file.name} selected</span>
                        </div>
                      )}
                    </div>
                    <div className="space-y-2">
                      <label className="block text-white/90 font-medium">Product Video</label>
                      <input
                        type="file"
                        accept="video/*"
                        onChange={handleVideoUpload}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-purple-500 file:text-white file:font-semibold hover:file:bg-purple-600 transition-all duration-200"
                      />
                      {productVideo && (
                        <div className="text-sm text-purple-400 flex items-center space-x-2">
                          <span>✅</span>
                          <span>{productVideo.file.name} selected</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-center">
                    <button
                      type="submit"
                      disabled={loading}
                      className="group relative overflow-hidden bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 disabled:from-gray-500 disabled:to-gray-600 text-white px-12 py-4 rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/25 disabled:cursor-not-allowed disabled:hover:scale-100"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-500"></div>
                      <div className="relative flex items-center space-x-3">
                        {loading ? (
                          <>
                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                            <span className="text-lg font-semibold">Creating Product NFT...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="w-6 h-6" />
                            <span className="text-lg font-semibold">Create Product NFT on Base Sepolia</span>
                          </>
                        )}
                      </div>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Modern Products Section */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20"></div>
            <div className="relative p-8">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-3xl font-bold text-white">
                    {userRole === 'buyer' && activeTab === 'marketplace' ? '🛒 Marketplace Collection' :
                     userRole === 'buyer' && activeTab === 'orders' ? '📋 Purchase History' :
                     userRole === 'buyer' && activeTab === 'owned' ? '👤 Your Products' :
                     userRole === 'manufacturer' && activeTab === 'delivery' ? '🚚 Delivery Queue' :
                     userRole === 'manufacturer' ? '🏭 My Creations' : 
                     userRole === 'transporter' ? '🚛 Products in Transit' : 
                     '📦 Products List'}
                  </h3>
                  <p className="text-white/70 mt-2">
                    {userRole === 'buyer' && activeTab === 'marketplace' ? 'Discover authentic products with verified supply chains' :
                     userRole === 'buyer' && activeTab === 'orders' ? 'Track your purchase journey and delivery status' :
                     userRole === 'buyer' && activeTab === 'owned' ? 'Products you currently own in your wallet' :
                     userRole === 'manufacturer' && activeTab === 'delivery' ? 'Orders waiting for delivery initiation - click Start Delivery to transfer NFT and release payment' :
                     userRole === 'manufacturer' ? 'Products you have created and launched' :
                     userRole === 'transporter' ? 'Products in your custody for delivery' :
                     'All products in the ecosystem'}
                  </p>
                </div>
                <button
                  onClick={() => {
                    fetchProducts();
                    if (userRole === 'manufacturer' && activeTab === 'delivery') {
                      fetchDeliveryQueue();
                    }
                  }}
                  className="group relative overflow-hidden bg-white/10 backdrop-blur-xl border border-white/20 text-white px-6 py-3 rounded-2xl transition-all duration-300 hover:bg-white/20 hover:scale-105 hover:shadow-xl hover:shadow-cyan-500/25"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/0 to-blue-400/10 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-500"></div>
                  <div className="relative flex items-center space-x-2">
                    <RefreshCw className="w-5 h-5" />
                    <span className="font-medium">Refresh</span>
                  </div>
                </button>
              </div>

              {loading && (
                <div className="text-center py-20">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400 mb-4"></div>
                  <p className="text-white/70 text-lg">Loading products...</p>
                </div>
              )}

              {!loading && (userRole !== 'buyer' || activeTab !== 'orders') && (userRole !== 'manufacturer' || activeTab !== 'delivery') && products.length === 0 && (
                <div className="text-center py-20">
                  <div className="w-20 h-20 bg-gradient-to-r from-cyan-400/20 to-blue-400/20 rounded-3xl flex items-center justify-center mx-auto mb-6">
                    <Package className="w-10 h-10 text-cyan-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">No products found</h3>
                  <p className="text-white/60">
                    {userRole === 'manufacturer' ? 'Create your first product to get started' : 'No products available yet'}
                  </p>
                </div>
              )}

              {!loading && userRole === 'buyer' && activeTab === 'orders' && products.length === 0 && (
                <div className="text-center py-20">
                  <div className="w-20 h-20 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-3xl flex items-center justify-center mx-auto mb-6">
                    <ShoppingCart className="w-10 h-10 text-purple-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">No purchases yet</h3>
                  <p className="text-white/60">Your purchase history will appear here</p>
                </div>
              )}

              {/* Modern Products Grid with Fixed Heights */}
              {!loading && ((userRole !== 'buyer' || activeTab !== 'orders') && (userRole !== 'manufacturer' || activeTab !== 'delivery') && products.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {products.map((product, index) => (
                    <div key={product.token_id || product.id || index} className="group relative h-[700px] flex flex-col">
                      {/* Card Background */}
                      <div className="absolute inset-0 bg-gradient-to-br from-white/15 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500 group-hover:shadow-2xl group-hover:shadow-cyan-500/20"></div>
                      
                      {/* Gradient Overlay on Hover */}
                      <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/0 to-blue-400/0 group-hover:from-cyan-400/10 group-hover:to-blue-400/10 rounded-3xl transition-all duration-500"></div>
                      
                      {/* Card Content */}
                      <div className="relative p-8 flex flex-col h-full">
                        {/* Product Image/Video Section - Fixed Height */}
                        <div className="h-48 mb-6">
                          {getImageUrl(product) ? (
                            <div className="relative h-full rounded-2xl overflow-hidden group/media">
                              <img 
                                src={getImageUrl(product)}
                                alt="Product"
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'flex';
                                }}
                              />
                              <div className="hidden w-full h-full bg-gradient-to-br from-cyan-400/20 to-blue-400/20 rounded-2xl items-center justify-center">
                                <ImageIcon className="w-12 h-12 text-cyan-400" />
                              </div>
                              {/* Video overlay if video exists */}
                              {getVideoUrl(product) && (
                                <div className="absolute top-4 right-4 bg-black/50 backdrop-blur-sm rounded-full p-2">
                                  <Play className="w-4 h-4 text-white" />
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="w-full h-full bg-gradient-to-br from-cyan-400/20 to-blue-400/20 rounded-2xl flex items-center justify-center">
                              <Package className="w-12 h-12 text-cyan-400" />
                            </div>
                          )}
                        </div>
                        
                        {/* Product Header - Fixed Height */}
                        <div className="h-24 mb-4">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="text-xl font-bold text-white group-hover:text-cyan-100 transition-colors line-clamp-2 flex-1 mr-2">
                              {product.name || product.metadata?.name || `Product ${index + 1}`}
                            </h4>
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-100 border border-cyan-400/30 whitespace-nowrap">
                              {product.category || product.metadata?.category || 'General'}
                            </span>
                          </div>
                          
                          <p className="text-white/70 text-sm line-clamp-2 max-h-10 overflow-y-auto">
                            {product.description || product.metadata?.description || 'No description available'}
                          </p>
                        </div>

                        {/* Enhanced Product Details - Expandable */}
                        <div className="mb-4 space-y-2">
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div className="p-2 bg-white/5 rounded-lg">
                              <span className="text-white/70 block">Price:</span>
                              <span className="font-bold text-green-400">
                                {product.price || product.metadata?.price_eth || '0.000'} ETH
                              </span>
                            </div>
                            <div className="p-2 bg-white/5 rounded-lg">
                              <span className="text-white/70 block">Token ID:</span>
                              <span className="font-mono text-xs text-cyan-400 truncate">{product.token_id}</span>
                            </div>
                          </div>
                          
                          {/* New Fields Display */}
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {(product.metadata?.uniqueProductID || product.uniqueProductID) && (
                              <div className="p-2 bg-white/5 rounded-lg">
                                <span className="text-white/70 block">Product ID:</span>
                                <span className="font-mono text-xs text-cyan-400 truncate">{product.metadata?.uniqueProductID || product.uniqueProductID}</span>
                              </div>
                            )}
                            {(product.metadata?.batchNumber || product.batchNumber) && (
                              <div className="p-2 bg-white/5 rounded-lg">
                                <span className="text-white/70 block">Batch:</span>
                                <span className="font-mono text-xs text-cyan-400 truncate">{product.metadata?.batchNumber || product.batchNumber}</span>
                              </div>
                            )}
                          </div>

                          {/* Manufacturing Details */}
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {(product.metadata?.manufacturingDate || product.manufacturingDate) && (
                              <div className="p-2 bg-white/5 rounded-lg">
                                <span className="text-white/70 block">Mfg Date:</span>
                                <span className="text-white text-xs">{product.metadata?.manufacturingDate || product.manufacturingDate}</span>
                              </div>
                            )}
                            {(product.metadata?.expirationDate || product.expirationDate) && (
                              <div className="p-2 bg-white/5 rounded-lg">
                                <span className="text-white/70 block">Exp Date:</span>
                                <span className="text-white text-xs">{product.metadata?.expirationDate || product.expirationDate}</span>
                              </div>
                            )}
                          </div>

                          {/* Manufacturer Info */}
                          {(product.manufacturer || product.metadata?.manufacturerID) && (
                            <div className="p-2 bg-white/5 rounded-lg text-sm">
                              <span className="text-white/70 block">Manufacturer:</span>
                              <span className="font-mono text-xs text-cyan-400 truncate">
                                {(product.manufacturer || product.metadata?.manufacturerID)?.substring(0, 20)}...
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Compact QR Code - No longer covering info */}
                        <div className="flex justify-center mb-4">
                          <div className="p-2 bg-white rounded-xl">
                            <QRCode 
                              value={generateQRCode(product)} 
                              size={60}
                            />
                          </div>
                        </div>

                        {/* Modern Action Buttons - Bottom */}
                        <div className="grid grid-cols-2 gap-4 mt-auto">
                          {userRole === 'buyer' && activeTab === 'marketplace' && (
                            <>
                              <button
                                onClick={() => handleBuyProduct(product.token_id)}
                                className="group/btn relative overflow-hidden bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-emerald-500/25"
                              >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                                <div className="relative flex items-center justify-center space-x-2">
                                  <ShoppingCart className="w-4 h-4" />
                                  <span className="font-semibold">Buy</span>
                                </div>
                              </button>
                              <button
                                onClick={() => handleVerifyProduct(product.token_id)}
                                className="group/btn relative overflow-hidden bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-blue-500/25"
                              >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                                <div className="relative flex items-center justify-center space-x-2">
                                  <Shield className="w-4 h-4" />
                                  <span className="font-semibold">Verify</span>
                                </div>
                              </button>
                            </>
                          )}
                          
                          {userRole === 'transporter' && (
                            <>
                              <button
                                onClick={() => handleCrossChainTransfer(product.token_id)}
                                className="group/btn relative overflow-hidden bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-green-500/25"
                              >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                                <div className="relative flex items-center justify-center space-x-2">
                                  <Truck className="w-4 h-4" />
                                  <span className="font-semibold">Ship</span>
                                </div>
                              </button>
                              <button
                                onClick={() => handleCompleteShipping(product.token_id)}
                                className="group/btn relative overflow-hidden bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-purple-500/25"
                              >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                                <div className="relative flex items-center justify-center space-x-2">
                                  <Package className="w-4 h-4" />
                                  <span className="font-semibold">Complete</span>
                                </div>
                              </button>
                            </>
                          )}
                          
                          {userRole === 'manufacturer' && (
                            <>
                              <button
                                onClick={() => handleListInMarketplace(product.token_id)}
                                className="col-span-2 group/btn relative overflow-hidden bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cyan-500/25"
                              >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                                <div className="relative flex items-center justify-center space-x-2">
                                  <Store className="w-4 h-4" />
                                  <span className="font-semibold">List For Sale</span>
                                </div>
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Purchase History for Buyers - NOW USING PRODUCTS STATE */}
              {!loading && userRole === 'buyer' && activeTab === 'orders' && products.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {products.map((product, index) => (
                    <div key={product.token_id || index} className="group relative h-[500px]">
                      <div className="absolute inset-0 bg-gradient-to-br from-white/15 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500"></div>
                      <div className="relative p-8 h-full flex flex-col">
                        <div className="flex items-start justify-between mb-6">
                          <h4 className="text-xl font-bold text-white">
                            {product.name || `Product ${product.token_id}`}
                          </h4>
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                            product.status === 'order_pending' 
                              ? 'bg-yellow-500/20 text-yellow-100 border border-yellow-400/30' 
                              : product.status === 'shipped' 
                              ? 'bg-blue-500/20 text-blue-100 border border-blue-400/30' 
                              : product.status === 'delivered' 
                              ? 'bg-green-500/20 text-green-100 border border-green-400/30' 
                              : 'bg-gray-500/20 text-gray-100 border border-gray-400/30'
                          }`}>
                            {product.status === 'order_pending' 
                              ? 'Order Pending'
                              : product.status === 'shipped' 
                              ? 'Shipped' 
                              : product.status === 'delivered' 
                              ? 'Delivered' 
                              : product.status || 'Processing'}
                          </span>
                        </div>
                        
                        <div className="space-y-4 flex-1">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="p-3 bg-white/5 rounded-lg">
                              <span className="text-white/70 block">Product:</span>
                              <span className="font-semibold text-white">{product.name || 'Unknown Product'}</span>
                            </div>
                            <div className="p-3 bg-white/5 rounded-lg">
                              <span className="text-white/70 block">Price:</span>
                              <span className="font-bold text-green-400">{product.price || product.mint_params?.price || '0.000'} ETH</span>
                            </div>
                            <div className="p-3 bg-white/5 rounded-lg">
                              <span className="text-white/70 block">Order Date:</span>
                              <span className="text-white text-xs">{product.purchase_date ? new Date(product.purchase_date * 1000).toLocaleDateString() : 'N/A'}</span>
                            </div>
                            <div className="p-3 bg-white/5 rounded-lg">
                              <span className="text-white/70 block">Token ID:</span>
                              <span className="text-cyan-400 text-xs">{product.token_id}</span>
                            </div>
                          </div>
                          
                          {product.manufacturer && (
                            <div className="p-3 bg-white/5 rounded-lg">
                              <span className="text-white/70 block mb-2">Manufacturer:</span>
                              <div className="text-xs text-white/80">
                                <p>{product.manufacturer?.substring(0, 16)}...</p>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <div className="mt-6 grid grid-cols-2 gap-4">
                          <button
                            onClick={() => handleVerifyProduct(product.token_id)}
                            className="group/btn relative overflow-hidden bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-blue-500/25"
                          >
                            <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                            <div className="relative flex items-center justify-center space-x-2">
                              <Shield className="w-4 h-4" />
                              <span className="font-semibold">Verify</span>
                            </div>
                          </button>
                          <button
                            onClick={() => {
                              const details = `Order Details:\n\nProduct: ${product.name || `Product ${product.token_id}`}\nToken ID: ${product.token_id}\nPrice: ${product.metadata?.price_eth || 'N/A'} ETH\nStatus: ${product.status || 'Processing'}\nManufacturer: ${product.manufacturer || 'N/A'}\nListed Date: ${product.listing_timestamp ? new Date(product.listing_timestamp * 1000).toLocaleString() : 'N/A'}`;
                              alert(details);
                            }}
                            className="group/btn relative overflow-hidden bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-purple-500/25"
                          >
                            <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                            <div className="relative flex items-center justify-center space-x-2">
                              <Eye className="w-4 h-4" />
                              <span className="font-semibold">Details</span>
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* NEW: Delivery Queue for Manufacturers */}
          {!loading && userRole === 'manufacturer' && activeTab === 'delivery' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-white">🚚 Delivery Queue</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={fetchDeliveryQueue}
                    disabled={loadingDelivery}
                    className="group relative overflow-hidden bg-white/10 backdrop-blur-xl border border-white/20 text-white px-4 py-2 rounded-xl transition-all duration-300 hover:bg-white/20 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${loadingDelivery ? 'animate-spin' : ''}`} />
                  </button>
                  <button
                    onClick={handleCleanupDuplicates}
                    disabled={loadingDelivery}
                    className="group relative overflow-hidden bg-red-500/20 backdrop-blur-xl border border-red-400/30 text-white px-4 py-2 rounded-xl transition-all duration-300 hover:bg-red-500/30 disabled:opacity-50 text-sm"
                  >
                    🧹 Cleanup Duplicates
                  </button>
                </div>
              </div>

              {loadingDelivery && (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mb-4"></div>
                  <p className="text-white/70">Loading delivery orders...</p>
                </div>
              )}

              {!loadingDelivery && deliveryQueue.length === 0 && (
                <div className="text-center py-20">
                  <div className="w-20 h-20 bg-gradient-to-r from-green-400/20 to-blue-400/20 rounded-3xl flex items-center justify-center mx-auto mb-6">
                    <Truck className="w-10 h-10 text-green-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">No delivery orders</h3>
                  <p className="text-white/60">Orders waiting for delivery will appear here</p>
                </div>
              )}

              {!loadingDelivery && deliveryQueue.length > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {(() => {
                    // Group orders by product_id to avoid duplicates
                    const uniqueProducts = new Map();
                    
                    deliveryQueue.forEach(order => {
                      const productId = order.product_id;
                      if (!uniqueProducts.has(productId)) {
                        // Keep the most recent order for each product
                        uniqueProducts.set(productId, order);
                      } else {
                        // Replace with more recent order if found
                        const existing = uniqueProducts.get(productId);
                        if (order.order_timestamp > existing.order_timestamp) {
                          uniqueProducts.set(productId, order);
                        }
                      }
                    });
                    
                    // Get count of orders for each product
                    const orderCounts = new Map();
                    deliveryQueue.forEach(order => {
                      const productId = order.product_id;
                      orderCounts.set(productId, (orderCounts.get(productId) || 0) + 1);
                    });
                    
                    return Array.from(uniqueProducts.values()).map((order, index) => {
                      const orderCount = orderCounts.get(order.product_id) || 1;
                      
                      return (
                        <div key={order.product_id || index} className="group relative">
                          <div className="absolute inset-0 bg-gradient-to-br from-white/15 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-green-400/30 transition-all duration-500"></div>
                          
                          <div className="relative p-6">
                            <div className="flex items-start justify-between mb-4">
                              <div>
                                <h4 className="text-xl font-bold text-white mb-1">
                                  {order.product_details?.name || `Product #${order.product_id?.slice(-8)}`}
                                </h4>
                                <p className="text-white/60 text-sm">
                                  {orderCount > 1 ? `${orderCount} orders pending` : 'Latest order:'} {new Date(order.order_timestamp * 1000).toLocaleDateString()}
                                </p>
                              </div>
                              <div className="bg-yellow-400/20 px-3 py-1 rounded-full">
                                <span className="text-yellow-400 text-xs font-semibold">
                                  {orderCount > 1 ? `${orderCount} WAITING` : 'WAITING'}
                                </span>
                              </div>
                            </div>

                            <div className="space-y-3 mb-6">
                              <div className="flex items-center justify-between">
                                <span className="text-white/70">Product ID:</span>
                                <span className="text-white font-mono text-sm">
                                  {order.product_id}
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-white/70">Latest Buyer:</span>
                                <span className="text-white font-mono text-sm">
                                  {order.buyer?.slice(0, 6)}...{order.buyer?.slice(-4)}
                                </span>
                              </div>
                              
                              {/* NEW: Shipping Information */}
                              {(order.buyer_name || order.shipping_info?.name) && (
                                <div className="border-t border-white/10 pt-3 mt-3">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-white/70">Customer:</span>
                                    <span className="text-white font-semibold">
                                      {order.buyer_name || order.shipping_info?.name || 'Tran Ngoc Hau'}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-white/70">Phone:</span>
                                    <span className="text-white">
                                      {order.buyer_phone || order.shipping_info?.phone || '0868009253'}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-white/70">Email:</span>
                                    <span className="text-white text-sm">
                                      {order.buyer_email || order.shipping_info?.email || 'hautn030204@gmail.com'}
                                    </span>
                                  </div>
                                  <div className="flex items-start justify-between">
                                    <span className="text-white/70">Address:</span>
                                    <div className="text-white text-sm text-right max-w-xs">
                                      {order.delivery_address ? (
                                        <>
                                          {order.delivery_address.street}<br/>
                                          {order.delivery_address.city}, {order.delivery_address.state}<br/>
                                          {order.delivery_address.zip_code}, {order.delivery_address.country}
                                        </>
                                      ) : (
                                        <>
                                          123 Nguyen Van Linh Street<br/>
                                          Ho Chi Minh City, Ho Chi Minh<br/>
                                          70000, Vietnam
                                        </>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              )}
                              
                              <div className="border-t border-white/10 pt-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-white/70">Price Each:</span>
                                  <span className="text-white font-bold">{order.price_eth || order.price || '0.001'} ETH</span>
                                </div>
                              </div>
                              
                              {orderCount > 1 && (
                                <div className="flex items-center justify-between">
                                  <span className="text-white/70">Total Value:</span>
                                  <span className="text-white font-bold">{((order.price_eth || order.price || 0.001) * orderCount).toFixed(4)} ETH</span>
                                </div>
                              )}
                              <div className="flex items-center justify-between">
                                <span className="text-white/70">Escrow:</span>
                                <span className="text-green-400 text-sm">✅ All Secured</span>
                              </div>
                            </div>

                            <button
                              onClick={() => {
                                // Handle multiple orders for the same product
                                if (orderCount > 1) {
                                  // Show confirmation dialog for multiple orders
                                  if (window.confirm(`This will initiate delivery for all ${orderCount} orders of this product. Continue?`)) {
                                    // Get all order IDs for this product
                                    const allOrderIds = deliveryQueue
                                      .filter(o => o.product_id === order.product_id)
                                      .map(o => o.order_id);
                                    
                                    // For now, start with the most recent order
                                    handleInitiateDelivery(order.order_id);
                                  }
                                } else {
                                  handleInitiateDelivery(order.order_id);
                                }
                              }}
                              disabled={loadingDelivery}
                              className="w-full group relative overflow-hidden bg-gradient-to-r from-green-500/20 to-green-600/20 backdrop-blur-xl border border-green-400/30 text-white py-3 rounded-2xl transition-all duration-300 hover:from-green-500/30 hover:to-green-600/30 hover:scale-105 hover:shadow-lg hover:shadow-green-500/25 disabled:opacity-50"
                            >
                              <div className="absolute inset-0 bg-gradient-to-r from-green-400/0 to-green-500/10 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-500"></div>
                              <div className="relative flex items-center justify-center space-x-2">
                                <Truck className="w-5 h-5" />
                                <span className="font-semibold">
                                  {orderCount > 1 ? `Start Delivery (${orderCount} orders)` : 'Start Delivery'}
                                </span>
                              </div>
                            </button>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Cross-Chain Transfer Modal */}
      {showCrossChainTransfer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-slate-800 p-8 rounded-3xl border border-white/20 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Cross-Chain Transfer</h2>
              <button
                onClick={() => setShowCrossChainTransfer(false)}
                className="text-white/60 hover:text-white transition-colors"
              >
                <span className="text-2xl">✕</span>
              </button>
            </div>
            
            <CrossChainTransfer 
              productId={transferProductId}
              onClose={() => setShowCrossChainTransfer(false)}
              onSuccess={() => {
                setShowCrossChainTransfer(false);
                fetchProducts();
              }}
            />
          </div>
        </div>
      )}

      {/* Shipping Information Form */}
      {showShippingForm && selectedProductForPurchase && (
        <ShippingInformationForm
          productName={selectedProductForPurchase.name || 'Product'}
          productPrice={selectedProductForPurchase.price || selectedProductForPurchase.metadata?.price_eth || '0.001'}
          loading={loading}
          onSubmit={handleShippingFormSubmit}
          onCancel={() => {
            setShowShippingForm(false);
            setSelectedProductForPurchase(null);
          }}
        />
      )}
    </div>
  );
};

export default ProductManagement;