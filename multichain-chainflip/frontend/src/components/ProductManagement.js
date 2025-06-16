import React, { useState, useEffect } from 'react';
import axios from 'axios';
import QRCode from 'qrcode.react';
import { useAuth } from '../contexts/AuthContext';
import blockchainService from '../services/blockchainService';
import CrossChainTransfer from './CrossChainTransfer';
import { Package, Truck, Shield, Store, Eye, ArrowRight, ShoppingCart, Plus, Upload, RefreshCw } from 'lucide-react';

const ProductManagement = () => {
  const { user, userRole } = useAuth();
  const [products, setProducts] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showCrossChainTransfer, setShowCrossChainTransfer] = useState(false);
  const [transferProductId, setTransferProductId] = useState(null);
  const [showVerificationForm, setShowVerificationForm] = useState(false);
  const [verificationProductId, setVerificationProductId] = useState(null);
  const [multiChainStats, setMultiChainStats] = useState(null);
  const [productImage, setProductImage] = useState(null);
  const [productVideo, setProductVideo] = useState(null);
  const [activeTab, setActiveTab] = useState('marketplace'); // For buyer tabs: marketplace, orders, owned
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
    if (userRole === 'buyer' && activeTab === 'orders') {
      fetchBuyerPurchases();
    }
  }, [activeTab]);

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
      // Build API URL with role-based filtering following Algorithm 5
      let apiUrl = `${process.env.REACT_APP_BACKEND_URL}/api/products/`;
      
      // Add role-based filtering parameters if user is authenticated
      if (userRole && user?.wallet_address) {
        const params = new URLSearchParams({
          user_role: userRole,
          wallet_address: user.wallet_address,
          view_type: activeTab  // marketplace, owned, created
        });
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
      }
      
    } catch (error) {
      console.error('❌ Error fetching products:', error);
      setProducts([]);
    }
    setLoading(false);
  };

  const fetchBuyerPurchases = async () => {
    if (userRole !== 'buyer' || !user?.wallet_address) return;
    
    setLoading(true);
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/products/buyer/${user.wallet_address}/purchases`
      );
      console.log('✅ Fetched buyer purchases:', response.data);
      setPurchases(response.data.purchases || []);
    } catch (error) {
      console.error('❌ Error fetching purchases:', error);
      setPurchases([]);
    }
    setLoading(false);
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
      return response.data.cid;
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
        imageCid = await uploadFileToIPFS(
          productImage.data,
          `product_image_${Date.now()}.${productImage.file.name.split('.').pop()}`,
          productImage.file.type
        );
        console.log('Image uploaded, CID:', imageCid);
      }

      // Upload video if selected
      if (productVideo) {
        console.log('Uploading video to IPFS...');
        videoCid = await uploadFileToIPFS(
          productVideo.data,
          `product_video_${Date.now()}.${productVideo.file.name.split('.').pop()}`,
          productVideo.file.type
        );
        console.log('Video uploaded, CID:', videoCid);
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
      const price = prompt('Enter price in ETH for marketplace listing:');
      if (!price || isNaN(price)) {
        alert('Please enter a valid price in ETH');
        return;
      }

      setLoading(true);

      // Use Algorithm 5: Post Supply Chain Management (Marketplace)
      const result = await blockchainService.listProductForSale({
        product_id: productTokenId,
        price: parseFloat(price),
        target_chains: [80002, 2442, 421614, 11155420] // All chains
      });

      alert(`🛒 Product listed in marketplace!\n\n💰 Price: ${price} ETH\n📅 Listed: ${new Date(result.listing_timestamp * 1000).toLocaleString()}\n🌐 Available on ${result.listed_on_chains.length} chains`);
      
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

  const handleCompleteShipping = async (productTokenId) => {
    try {
      const confirmation = window.confirm('Mark this product as delivered and complete shipping?\n\nThis will require consensus validation.');
      if (!confirmation) return;

      setLoading(true);

      // ALGORITHM 3: Supply Chain Consensus Validation
      const consensusValidation = await performConsensusValidation(productTokenId);
      
      if (!consensusValidation.approved) {
        alert(`❌ Consensus Validation Failed!\n\n${consensusValidation.reason}\n\nShipping cannot be completed without consensus approval.`);
        return;
      }

      // Complete shipping operation (transporter chain operation)
      const result = await blockchainService.completeShipping({
        product_id: productTokenId,
        transporter: user?.wallet_address,
        delivery_confirmation: true,
        delivery_timestamp: Date.now(),
        consensus_approval: consensusValidation.consensus_id
      });

      alert(`✅ Shipping Completed with Consensus!\n\n📦 Product: ${productTokenId}\n🚛 Delivered by: ${user?.wallet_address}\n📅 Completed: ${new Date().toLocaleString()}\n🔗 Transaction: ${result.transaction_hash || 'N/A'}\n⚡ Consensus ID: ${consensusValidation.consensus_id}`);
      
      await fetchProducts();
    } catch (error) {
      console.error('Complete shipping error:', error);
      alert(`❌ Failed to complete shipping: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const performConsensusValidation = async (productTokenId) => {
    try {
      // Algorithm 3: Supply Chain Consensus
      const shipmentData = {
        shipment_id: `SHIP-${Date.now()}-${productTokenId}`,
        product_id: productTokenId,
        transporter: user?.wallet_address,
        start_location: 'Current Location',
        end_location: 'Delivery Address',
        distance: Math.floor(Math.random() * 1000) + 100, // Mock distance
        transport_fee: Math.floor(Math.random() * 100) + 50, // Mock fee
        timestamp: Date.now()
      };

      // Simulate consensus voting process
      const consensusResult = await simulateConsensusVoting(shipmentData);
      
      return {
        approved: consensusResult.votes_for >= consensusResult.required_votes,
        consensus_id: consensusResult.consensus_id,
        votes_for: consensusResult.votes_for,
        votes_against: consensusResult.votes_against,
        required_votes: consensusResult.required_votes,
        reason: consensusResult.approved 
          ? `Consensus reached: ${consensusResult.votes_for}/${consensusResult.required_votes} votes`
          : `Insufficient votes: ${consensusResult.votes_for}/${consensusResult.required_votes} required`
      };
    } catch (error) {
      console.error('Consensus validation error:', error);
      return {
        approved: false,
        reason: `Consensus validation failed: ${error.message}`
      };
    }
  };

  const simulateConsensusVoting = async (shipmentData) => {
    // Algorithm 3: Simplified consensus simulation
    const required_votes = 3; // Minimum votes required
    const votes_for = Math.floor(Math.random() * 5) + 1; // Random votes (1-5)
    const votes_against = Math.floor(Math.random() * 2); // Random opposing votes (0-1)
    const consensus_id = `CONSENSUS-${Date.now()}`;

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    return {
      consensus_id,
      votes_for,
      votes_against,
      required_votes,
      approved: votes_for >= required_votes,
      participants: [
        { role: 'manufacturer', vote: 'approve', reason: 'Quality standards met' },
        { role: 'inspector', vote: 'approve', reason: 'Documentation complete' },
        { role: 'network_node', vote: votes_for >= 3 ? 'approve' : 'reject', reason: 'Network validation' }
      ]
    };
  };

  const handleBuyProduct = async (productTokenId) => {
    try {
      const product = products.find(p => p.token_id === productTokenId);
      if (!product) {
        alert('Product not found');
        return;
      }

      // Direct purchase without mandatory verification
      // (Verification is available separately via the "Verify" button)
      const price = product.price || product.metadata?.price_eth || '0.001';
      const confirmation = window.confirm(
        `🛒 Cross-Chain Product Purchase\n\n` +
        `📦 Product: ${product.name || 'Product'}\n` +
        `💰 Purchase for ${price} ETH?\n\n` +
        `🔗 Cross-Chain Flow:\n` +
        `   1️⃣ Optimism Sepolia (Buyer Chain)\n` +
        `   2️⃣ → LayerZero Bridge →\n` +
        `   3️⃣ Polygon PoS (Hub Chain)\n` +
        `   4️⃣ → fxPortal Bridge →\n` +
        `   5️⃣ zkEVM Cardona (Manufacturer Chain)\n\n` +
        `⏱️ Processing time: 3-7 minutes\n` +
        `🔐 Escrow protection included\n` +
        `🎁 Transporter incentives enabled\n\n` +
        `ℹ️ Use the "Verify" button to check authenticity separately`
      );
      if (!confirmation) return;

      setLoading(true);

      // Algorithm 5 + Algorithm 1: Cross-Chain Purchase
      const result = await blockchainService.buyProduct({
        product_id: productTokenId,
        buyer: user?.wallet_address,
        price: parseFloat(price),
        payment_method: 'ETH'
      });

      // Payment processing complete
      if (result.success) {
        const crossChainDetails = result.cross_chain_details || {};
        alert(
          `🎉 Cross-Chain Purchase Successful!\n\n` +
          `✅ ${result.status}\n` +
          `📦 Product: ${product.name || 'Product'}\n` +
          `💰 Paid: ${price} ETH\n` +
          `📅 Date: ${new Date().toLocaleString()}\n\n` +
          `🔗 Cross-Chain Transaction Details:\n` +
          `   🔹 Purchase ID: ${result.purchase_id}\n` +
          `   🔹 LayerZero TX: ${crossChainDetails.layerzero_tx || 'Processing...'}\n` +
          `   🔹 fxPortal TX: ${crossChainDetails.fxportal_tx || 'Processing...'}\n` +
          `   🔹 Escrow ID: ${crossChainDetails.escrow_id || 'N/A'}\n\n` +
          `🌉 Bridges Used: LayerZero + fxPortal\n` +
          `⛓️ Chains: Optimism → Polygon → zkEVM\n` +
          `🎯 Algorithms: Algorithm 1 + Algorithm 5\n\n` +
          `🔄 NFT ownership transferred to your wallet\n` +
          `💳 Payment processing with escrow protection`
        );
        
        // Refresh data
        await fetchProducts();
        if (activeTab === 'orders') {
          await fetchBuyerPurchases();
        }
      }

    } catch (error) {
      console.error('❌ Cross-chain buy product error:', error);
      
      // Enhanced error handling for cross-chain issues
      let errorMessage = error.message;
      if (errorMessage.includes('authenticity')) {
        errorMessage = 'Product authenticity verification failed. This may be due to QR code issues or IPFS connectivity.';
      } else if (errorMessage.includes('cross-chain')) {
        errorMessage = 'Cross-chain communication failed. Please check bridge connectivity and try again.';
      } else if (errorMessage.includes('escrow')) {
        errorMessage = 'Escrow creation failed. Your funds are safe and no payment was processed.';
      } else if (errorMessage.includes('LayerZero')) {
        errorMessage = 'LayerZero bridge communication failed. Please try again in a few minutes.';
      } else if (errorMessage.includes('fxPortal')) {
        errorMessage = 'fxPortal bridge communication failed. Cross-chain transfer may be delayed.';
      }
      
      alert(`❌ Cross-Chain Purchase Failed!\n\n${errorMessage}\n\nNo payment was processed. Please try again.`);
    } finally {
      setLoading(false);
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
        `   📥 To: Manufacturer's chain (zkEVM Cardona)\n` +
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

  const getExpirationDate = () => {
    const date = new Date();
    date.setFullYear(date.getFullYear() + 1); // 1 year from now
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Modern Header with Gradient */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">
                📦 {userRole === 'manufacturer' ? 'Product Creation Studio' : 
                     userRole === 'transporter' ? 'Shipping Dashboard' :
                     userRole === 'buyer' ? 'Product Marketplace' : 
                     'Product Management'}
              </h1>
              <p className="text-blue-100 mt-2 text-lg">
                {userRole === 'manufacturer' 
                  ? 'Create and manage NFT products with blockchain verification' 
                  : userRole === 'transporter'
                  ? 'Handle shipments and complete delivery processes with consensus'
                  : userRole === 'buyer'
                  ? 'Discover and purchase verified products from trusted manufacturers'
                  : `Comprehensive product management for ${userRole} role`
                }
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={loadMultiChainStats}
                className="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-md shadow-sm text-sm font-medium text-white hover:bg-white/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </button>
              {/* Only show Create Product NFT button for manufacturers */}
              {userRole === 'manufacturer' && (
                <button
                  onClick={() => setShowCreateForm(!showCreateForm)}
                  className="inline-flex items-center px-6 py-2 bg-white text-blue-600 rounded-md shadow-sm text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {showCreateForm ? 'Cancel' : 'Create Product NFT'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Multi-Chain Stats Cards */}
        {multiChainStats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-xl">🏛️</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-600">Hub Chain</h3>
                  <div className="text-sm text-gray-500 mt-1">
                    <div>Status: {multiChainStats.multichain?.polygon_pos_hub?.connected ? '✅ Connected' : '❌ Disconnected'}</div>
                    <div className="text-2xl font-bold text-blue-600">{multiChainStats.multichain?.statistics?.total_products || 0}</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-xl">🏭</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-600">Manufacturer</h3>
                  <div className="text-sm text-gray-500 mt-1">
                    <div>zkEVM Cardona</div>
                    <div className="text-2xl font-bold text-green-600">{multiChainStats.multichain?.statistics?.total_products || 0}</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <span className="text-xl">🚛</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-600">Transporter</h3>
                  <div className="text-sm text-gray-500 mt-1">
                    <div>Arbitrum Sepolia</div>
                    <div className="text-2xl font-bold text-yellow-600">{multiChainStats.multichain?.statistics?.total_transactions || 0}</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-xl">🛒</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-600">Buyer</h3>
                  <div className="text-sm text-gray-500 mt-1">
                    <div>Optimism Sepolia</div>
                    <div className="text-2xl font-bold text-purple-600">{multiChainStats.multichain?.statistics?.total_disputes || 0}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Buyer Tabs */}
        {userRole === 'buyer' && (
          <div className="mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1">
              <nav className="flex space-x-1">
                <button
                  onClick={() => setActiveTab('marketplace')}
                  className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === 'marketplace'
                      ? 'bg-blue-500 text-white shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  🛒 Marketplace
                </button>
                <button
                  onClick={() => setActiveTab('orders')}
                  className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === 'orders'
                      ? 'bg-blue-500 text-white shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  📋 Your Orders
                </button>
                <button
                  onClick={() => setActiveTab('owned')}
                  className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === 'owned'
                      ? 'bg-blue-500 text-white shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  👤 My Products
                </button>
              </nav>
            </div>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              {activeTab === 'marketplace' && (
                <div className="text-sm text-blue-800">
                  <strong>🛒 Marketplace:</strong> Browse and purchase products with authenticity verification and secure payments.
                </div>
              )}
              {activeTab === 'orders' && (
                <div className="text-sm text-blue-800">
                  <strong>📋 Purchase History:</strong> Track your order status and payment processing with NFT ownership transfers and cross-chain transactions.
                </div>
              )}
              {activeTab === 'owned' && (
                <div className="text-sm text-blue-800">
                  <strong>👤 Owned Products:</strong> Products you currently own after successful purchases transferred to your wallet address.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Create Product Form - Only for Manufacturers */}
        {showCreateForm && userRole === 'manufacturer' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
            <div className="border-b border-gray-200 pb-4 mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Create Product NFT</h3>
              <p className="text-sm text-gray-600 mt-1">Create a new product NFT on zkEVM Cardona with IPFS metadata storage</p>
            </div>
            <form onSubmit={createProduct}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Product Name *</label>
                  <input
                    type="text"
                    required
                    value={newProduct.name}
                    onChange={(e) => setNewProduct({...newProduct, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter product name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select
                    value={newProduct.category}
                    onChange={(e) => setNewProduct({...newProduct, category: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                  <textarea
                    value={newProduct.description}
                    onChange={(e) => setNewProduct({...newProduct, description: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter product description"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Price (ETH)</label>
                  <input
                    type="number"
                    step="0.001"
                    value={newProduct.price}
                    onChange={(e) => setNewProduct({...newProduct, price: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0.000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Manufacturing Location</label>
                  <input
                    type="text"
                    value={newProduct.location}
                    onChange={(e) => setNewProduct({...newProduct, location: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Manufacturing location"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Product Image</label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  {productImage && (
                    <div className="mt-2 text-sm text-green-600">
                      ✅ {productImage.file.name} selected
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Product Video</label>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleVideoUpload}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  {productVideo && (
                    <div className="mt-2 text-sm text-green-600">
                      ✅ {productVideo.file.name} selected
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-6 pt-6 border-t border-gray-200">
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center px-6 py-3 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating Product NFT...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Create Product NFT on zkEVM Cardona
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Products Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {userRole === 'buyer' && activeTab === 'marketplace' ? 'Available Products' :
                   userRole === 'buyer' && activeTab === 'orders' ? 'Your Purchase History' :
                   userRole === 'buyer' && activeTab === 'owned' ? 'Products You Own' :
                   userRole === 'manufacturer' ? 'My Products' : 
                   userRole === 'transporter' ? 'Products in Transit' : 
                   'Products List'}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {userRole === 'buyer' && activeTab === 'marketplace' ? 'Products available for purchase with verification' :
                   userRole === 'buyer' && activeTab === 'orders' ? 'Your order history and delivery status' :
                   userRole === 'buyer' && activeTab === 'owned' ? 'Products you currently own' :
                   userRole === 'manufacturer' ? 'Products you have created' :
                   userRole === 'transporter' ? 'Products in your custody' :
                   'All products in the system'}
                </p>
              </div>
              <button
                onClick={() => {
                  fetchProducts();
                  if (userRole === 'buyer' && activeTab === 'orders') {
                    fetchBuyerPurchases();
                  }
                }}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>

          <div className="p-6">
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">Loading products...</p>
              </div>
            )}

            {!loading && (userRole !== 'buyer' || activeTab !== 'orders') && products.length === 0 && (
              <div className="text-center py-12">
                <Package className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No products found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {userRole === 'manufacturer' ? 'Create your first product to get started' : 'No products available yet'}
                </p>
              </div>
            )}

            {!loading && userRole === 'buyer' && activeTab === 'orders' && purchases.length === 0 && (
              <div className="text-center py-12">
                <ShoppingCart className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No purchases yet</h3>
                <p className="mt-1 text-sm text-gray-500">Your purchase history will appear here</p>
              </div>
            )}

            {/* Products Grid */}
            {!loading && ((userRole !== 'buyer' || activeTab !== 'orders') && products.length > 0) && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map((product, index) => (
                  <div key={product.token_id || product.id || index} className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
                    {/* Product Image */}
                    {product.image_cid && (
                      <div className="aspect-w-16 aspect-h-9">
                        <img 
                          src={`${process.env.REACT_APP_IPFS_GATEWAY}${product.image_cid}`}
                          alt="Product"
                          className="w-full h-48 object-cover"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      </div>
                    )}
                    
                    <div className="p-6">
                      {/* Product Header */}
                      <div className="flex items-start justify-between mb-4">
                        <h4 className="text-lg font-semibold text-gray-900 truncate">
                          {product.name || product.metadata?.name || `Product ${index + 1}`}
                        </h4>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {product.category || product.metadata?.category || 'General'}
                        </span>
                      </div>

                      {/* Product Details */}
                      <div className="space-y-2 mb-4">
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {product.description || product.metadata?.description || 'No description available'}
                        </p>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">Price:</span>
                          <span className="font-semibold text-green-600">
                            {product.price || product.metadata?.price_eth || '0.000'} ETH
                          </span>
                        </div>
                        {product.token_id && (
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-500">Token ID:</span>
                            <span className="font-mono text-xs text-gray-900">{product.token_id}</span>
                          </div>
                        )}
                      </div>

                      {/* QR Code */}
                      <div className="flex justify-center mb-4">
                        <QRCode 
                          value={generateQRCode(product)} 
                          size={80}
                          className="border border-gray-200 rounded p-1"
                        />
                      </div>

                      {/* Action Buttons */}
                      <div className="grid grid-cols-2 gap-2">
                        {userRole === 'buyer' && activeTab === 'marketplace' && (
                          <>
                            <button
                              onClick={() => handleBuyProduct(product.token_id)}
                              className="inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <ShoppingCart className="w-4 h-4 mr-1" />
                              Buy
                            </button>
                            <button
                              onClick={() => handleVerifyProduct(product.token_id)}
                              className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <Shield className="w-4 h-4 mr-1" />
                              Verify
                            </button>
                          </>
                        )}
                        
                        {userRole === 'transporter' && (
                          <>
                            <button
                              onClick={() => handleCrossChainTransfer(product.token_id)}
                              className="inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                            >
                              <Truck className="w-4 h-4 mr-1" />
                              Ship
                            </button>
                            <button
                              onClick={() => handleCompleteShipping(product.token_id)}
                              className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <Package className="w-4 h-4 mr-1" />
                              Complete
                            </button>
                          </>
                        )}
                        
                        {userRole === 'manufacturer' && (
                          <>
                            <button
                              onClick={() => handleQualityCheck(product.token_id)}
                              className="inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                            >
                              <Shield className="w-4 h-4 mr-1" />
                              QC
                            </button>
                            <button
                              onClick={() => handleListInMarketplace(product.token_id)}
                              className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <Store className="w-4 h-4 mr-1" />
                              Sell
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Purchase History for Buyers */}
            {!loading && userRole === 'buyer' && activeTab === 'orders' && purchases.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {purchases.map((purchase, index) => (
                  <div key={purchase.purchase_id || index} className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6">
                    <div className="flex items-start justify-between mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">
                        Order #{purchase.purchase_id?.substring(0, 12)}...
                      </h4>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        purchase.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {purchase.status}
                      </span>
                    </div>
                    
                    <div className="space-y-2 text-sm text-gray-600">
                      <div><strong>Product ID:</strong> {purchase.product_id}</div>
                      <div><strong>Price Paid:</strong> {purchase.price_eth} ETH</div>
                      <div><strong>Purchase Date:</strong> {purchase.purchase_date}</div>
                      {purchase.transaction_hash && (
                        <div><strong>Transaction:</strong> {purchase.transaction_hash.substring(0, 20)}...</div>
                      )}
                    </div>

                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <div className="text-xs text-blue-800">
                        <div><strong>🔄 Payment:</strong> {purchase.status === 'completed' ? '✅ Complete' : '⏳ Processing'}</div>
                        <div><strong>🛒 NFT Transfer:</strong> {purchase.status === 'completed' ? '✅ Complete' : '⏳ Pending'}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Cross Chain Transfer Modal */}
      {showCrossChainTransfer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Cross-Chain Transfer</h3>
            <CrossChainTransfer 
              productId={transferProductId}
              onClose={() => {
                setShowCrossChainTransfer(false);
                setTransferProductId(null);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductManagement;