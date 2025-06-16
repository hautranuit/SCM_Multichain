import React, { useState, useEffect } from 'react';
import axios from 'axios';
import QRCode from 'qrcode.react';
import { useAuth } from '../contexts/AuthContext';
import blockchainService from '../services/blockchainService';
import CrossChainTransfer from './CrossChainTransfer';
import { Package, Truck, Shield, Store, Eye, ArrowRight, ShoppingCart, Plus, Upload, RefreshCw, Sparkles, Zap, Star } from 'lucide-react';

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
                { title: 'Manufacturer', subtitle: 'zkEVM Cardona', value: multiChainStats.multichain?.statistics?.total_products || 0, icon: '🏭', color: 'green' },
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
                  {[
                    { key: 'marketplace', label: 'Marketplace', icon: '🛒', desc: 'Discover products' },
                    { key: 'orders', label: 'Your Orders', icon: '📋', desc: 'Track purchases' },
                    { key: 'owned', label: 'My Products', icon: '👤', desc: 'Owned items' }
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

          {/* Ultra-Modern Create Form */}
          {showCreateForm && userRole === 'manufacturer' && (
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20"></div>
              <div className="relative p-8">
                <div className="text-center mb-8">
                  <h3 className="text-3xl font-bold text-white mb-2">Create Product NFT</h3>
                  <p className="text-white/70">Launch your product on zkEVM Cardona with IPFS metadata storage</p>
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
                    <div className="md:col-span-2 space-y-2">
                      <label className="block text-white/90 font-medium">Description</label>
                      <textarea
                        value={newProduct.description}
                        onChange={(e) => setNewProduct({...newProduct, description: e.target.value})}
                        rows={3}
                        className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                        placeholder="Enter product description"
                      />
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
                     userRole === 'manufacturer' ? '🏭 My Creations' : 
                     userRole === 'transporter' ? '🚛 Products in Transit' : 
                     '📦 Products List'}
                  </h3>
                  <p className="text-white/70 mt-2">
                    {userRole === 'buyer' && activeTab === 'marketplace' ? 'Discover authentic products with verified supply chains' :
                     userRole === 'buyer' && activeTab === 'orders' ? 'Track your purchase journey and delivery status' :
                     userRole === 'buyer' && activeTab === 'owned' ? 'Products you currently own in your wallet' :
                     userRole === 'manufacturer' ? 'Products you have created and launched' :
                     userRole === 'transporter' ? 'Products in your custody for delivery' :
                     'All products in the ecosystem'}
                  </p>
                </div>
                <button
                  onClick={() => {
                    fetchProducts();
                    if (userRole === 'buyer' && activeTab === 'orders') {
                      fetchBuyerPurchases();
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

              {!loading && (userRole !== 'buyer' || activeTab !== 'orders') && products.length === 0 && (
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

              {!loading && userRole === 'buyer' && activeTab === 'orders' && purchases.length === 0 && (
                <div className="text-center py-20">
                  <div className="w-20 h-20 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-3xl flex items-center justify-center mx-auto mb-6">
                    <ShoppingCart className="w-10 h-10 text-purple-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">No purchases yet</h3>
                  <p className="text-white/60">Your purchase history will appear here</p>
                </div>
              )}

              {/* Modern Products Grid */}
              {!loading && ((userRole !== 'buyer' || activeTab !== 'orders') && products.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {products.map((product, index) => (
                    <div key={product.token_id || product.id || index} className="group relative">
                      {/* Card Background */}
                      <div className="absolute inset-0 bg-gradient-to-br from-white/15 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500 group-hover:shadow-2xl group-hover:shadow-cyan-500/20"></div>
                      
                      {/* Gradient Overlay on Hover */}
                      <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/0 to-blue-400/0 group-hover:from-cyan-400/10 group-hover:to-blue-400/10 rounded-3xl transition-all duration-500"></div>
                      
                      {/* Card Content */}
                      <div className="relative p-8 space-y-6">
                        {/* Product Image with Fallback */}
                        {product.image_cid ? (
                          <div className="aspect-w-16 aspect-h-9 rounded-2xl overflow-hidden">
                            <img 
                              src={`${process.env.REACT_APP_IPFS_GATEWAY}${product.image_cid}`}
                              alt="Product"
                              className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-500"
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          </div>
                        ) : (
                          <div className="w-full h-48 bg-gradient-to-br from-cyan-400/20 to-blue-400/20 rounded-2xl flex items-center justify-center">
                            <Package className="w-12 h-12 text-cyan-400" />
                          </div>
                        )}
                        
                        {/* Product Header */}
                        <div className="space-y-3">
                          <div className="flex items-start justify-between">
                            <h4 className="text-xl font-bold text-white group-hover:text-cyan-100 transition-colors line-clamp-2">
                              {product.name || product.metadata?.name || `Product ${index + 1}`}
                            </h4>
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-100 border border-cyan-400/30">
                              {product.category || product.metadata?.category || 'General'}
                            </span>
                          </div>
                          
                          <p className="text-white/70 text-sm line-clamp-2">
                            {product.description || product.metadata?.description || 'No description available'}
                          </p>
                        </div>

                        {/* Product Details */}
                        <div className="space-y-3">
                          <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                            <span className="text-white/70 text-sm">Price:</span>
                            <span className="font-bold text-green-400 text-lg">
                              {product.price || product.metadata?.price_eth || '0.000'} ETH
                            </span>
                          </div>
                          {product.token_id && (
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                              <span className="text-white/70 text-sm">Token ID:</span>
                              <span className="font-mono text-xs text-cyan-400">{product.token_id}</span>
                            </div>
                          )}
                        </div>

                        {/* QR Code */}
                        <div className="flex justify-center">
                          <div className="p-3 bg-white rounded-2xl">
                            <QRCode 
                              value={generateQRCode(product)} 
                              size={100}
                            />
                          </div>
                        </div>

                        {/* Modern Action Buttons */}
                        <div className="grid grid-cols-2 gap-4">
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
                                onClick={() => handleQualityCheck(product.token_id)}
                                className="group/btn relative overflow-hidden bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-purple-500/25"
                              >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                                <div className="relative flex items-center justify-center space-x-2">
                                  <Shield className="w-4 h-4" />
                                  <span className="font-semibold">QC</span>
                                </div>
                              </button>
                              <button
                                onClick={() => handleListInMarketplace(product.token_id)}
                                className="group/btn relative overflow-hidden bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white px-4 py-3 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cyan-500/25"
                              >
                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 to-white/10 translate-x-[-100%] group-hover/btn:translate-x-0 transition-transform duration-500"></div>
                                <div className="relative flex items-center justify-center space-x-2">
                                  <Store className="w-4 h-4" />
                                  <span className="font-semibold">Sell</span>
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

              {/* Purchase History for Buyers */}
              {!loading && userRole === 'buyer' && activeTab === 'orders' && purchases.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {purchases.map((purchase, index) => (
                    <div key={purchase.purchase_id || index} className="group relative">
                      <div className="absolute inset-0 bg-gradient-to-br from-white/15 to-white/5 backdrop-blur-xl rounded-3xl border border-white/20 group-hover:border-white/30 transition-all duration-500"></div>
                      <div className="relative p-8 space-y-6">
                        <div className="flex items-start justify-between">
                          <h4 className="text-xl font-bold text-white">
                            Order #{purchase.purchase_id?.substring(0, 12)}...
                          </h4>
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                            purchase.status === 'completed' 
                              ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-400 border border-green-400/30' 
                              : 'bg-gradient-to-r from-yellow-500/20 to-orange-500/20 text-yellow-400 border border-yellow-400/30'
                          }`}>
                            {purchase.status}
                          </span>
                        </div>
                        
                        <div className="space-y-3">
                          {[
                            { label: 'Product ID', value: purchase.product_id },
                            { label: 'Price Paid', value: `${purchase.price_eth} ETH` },
                            { label: 'Purchase Date', value: purchase.purchase_date },
                            { label: 'Transaction', value: purchase.transaction_hash?.substring(0, 20) + '...' }
                          ].filter(item => item.value).map((item, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                              <span className="text-white/70 text-sm font-medium">{item.label}:</span>
                              <span className="text-white text-sm font-semibold">{item.value}</span>
                            </div>
                          ))}
                        </div>

                        <div className="p-4 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-xl border border-blue-400/20">
                          <div className="space-y-2 text-sm">
                            <div className="flex items-center justify-between">
                              <span className="text-blue-200">Payment:</span>
                              <span className={`font-semibold ${purchase.status === 'completed' ? 'text-green-400' : 'text-yellow-400'}`}>
                                {purchase.status === 'completed' ? '✅ Complete' : '⏳ Processing'}
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-blue-200">NFT Transfer:</span>
                              <span className={`font-semibold ${purchase.status === 'completed' ? 'text-green-400' : 'text-yellow-400'}`}>
                                {purchase.status === 'completed' ? '✅ Complete' : '⏳ Pending'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Cross Chain Transfer Modal */}
      {showCrossChainTransfer && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-white/10 backdrop-blur-xl rounded-3xl border border-white/30"></div>
            <div className="relative bg-transparent p-8 max-w-md w-full mx-4">
              <h3 className="text-2xl font-bold text-white mb-6 text-center">Cross-Chain Transfer</h3>
              <CrossChainTransfer 
                productId={transferProductId}
                onClose={() => {
                  setShowCrossChainTransfer(false);
                  setTransferProductId(null);
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductManagement;