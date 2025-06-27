import React, { useState, useEffect } from 'react';
import { 
  Package, 
  CheckCircle, 
  AlertTriangle, 
  Eye, 
  Key,
  Truck,
  Shield,
  Coins,
  ArrowRightLeft,
  Clock,
  RefreshCw,
  Info
} from 'lucide-react';

const BuyerProductReceipt = ({ buyerAddress }) => {
  const [deliveredProducts, setDeliveredProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [confirmingProduct, setConfirmingProduct] = useState(null);
  const [verificationStep, setVerificationStep] = useState('product_check');
  const [productCondition, setProductCondition] = useState('good');
  const [authenticity, setAuthenticity] = useState('verified');
  const [notes, setNotes] = useState('');
  const [finalizing, setFinalizing] = useState(false);

  // Buyer address - in production this would come from wallet connection
  const currentBuyerAddress = buyerAddress || "0x90F79bf6EB2c4f870365E785982E1f101E93b906";

  useEffect(() => {
    loadDeliveredProducts();
  }, [currentBuyerAddress]);

  const loadDeliveredProducts = async () => {
    setLoading(true);
    try {
      // Get delivery notifications for delivered products
      const response = await fetch(`http://localhost:8001/api/blockchain/delivery/buyer/notifications/${currentBuyerAddress}`);
      if (response.ok) {
        const data = await response.json();
        // Filter for products that have been delivered but not yet confirmed by buyer
        const deliveredNotConfirmed = data.notifications?.filter(notification => 
          notification.status === 'delivered' && !notification.buyer_confirmed
        ) || [];
        setDeliveredProducts(deliveredNotConfirmed);
      }
    } catch (error) {
      console.error('Error loading delivered products:', error);
    }
    setLoading(false);
  };

  const startProductConfirmation = (product) => {
    setConfirmingProduct(product);
    setVerificationStep('product_check');
    setProductCondition('good');
    setAuthenticity('verified');
    setNotes('');
  };

  const confirmProductReceipt = async () => {
    if (!confirmingProduct) return;

    setFinalizing(true);
    try {
      // Prepare verification results
      const verificationPassed = productCondition === 'excellent' || productCondition === 'good';
      const authenticityPassed = authenticity === 'verified';
      const conditionSatisfactory = productCondition !== 'poor';
      
      // Step 1: Confirm product receipt with verification details
      const confirmResponse = await fetch('http://localhost:8001/api/blockchain/delivery/buyer/confirm-receipt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          delivery_request_id: confirmingProduct.delivery_request_id,
          buyer_address: currentBuyerAddress,
          product_verification_passed: verificationPassed,
          authenticity_check_passed: authenticityPassed,
          condition_satisfactory: conditionSatisfactory,
          notes: notes || `Product condition: ${productCondition}, Authenticity: ${authenticity}`
        })
      });

      if (confirmResponse.ok) {
        const result = await confirmResponse.json();
        
        // Show success message with transaction details including tokenURI preservation
        let message = `🎉 Product receipt confirmed successfully!\n\n`;
        
        if (result.escrow_released) {
          message += `💰 Escrow released to manufacturer ✅\n`;
        }
        
        if (result.nft_transferred) {
          message += `🎨 NFT transferred to your wallet ✅\n`;
          message += `🔗 TokenURI (IPFS) preserved for authenticity ✅\n`;
        }
        
        if (result.transaction_hashes) {
          if (result.transaction_hashes.escrow_release) {
            message += `📍 Escrow TX: ${result.transaction_hashes.escrow_release.slice(0, 20)}...\n`;
          }
          if (result.transaction_hashes.nft_burn) {
            message += `🔥 NFT Burn TX: ${result.transaction_hashes.nft_burn.slice(0, 20)}...\n`;
          }
          if (result.transaction_hashes.nft_message) {
            message += `📡 Cross-chain Message TX: ${result.transaction_hashes.nft_message.slice(0, 20)}...\n`;
          }
        }
        
        message += `\n🎯 Your product NFT now contains:\n`;
        message += `• Original IPFS metadata (tokenURI) ✅\n`;
        message += `• Proof of authenticity and ownership ✅\n`;
        message += `• Complete supply chain history ✅\n\n`;
        message += `The NFT's tokenURI (IPFS CID) has been preserved during the cross-chain transfer, ensuring authenticity and traceability.`;
        
        alert(message);
        
        // Reset state and reload
        setConfirmingProduct(null);
        setVerificationStep('product_check');
        loadDeliveredProducts();
      } else {
        const error = await confirmResponse.json();
        alert(`Failed to confirm receipt: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error confirming product receipt:', error);
      alert('Error confirming product receipt');
    }
    setFinalizing(false);
  };

  const getVerificationStepIcon = (step) => {
    switch (step) {
      case 'product_check': return <Package className="w-5 h-5" />;
      case 'authenticity': return <Shield className="w-5 h-5" />;
      case 'final_confirm': return <CheckCircle className="w-5 h-5" />;
      default: return <Info className="w-5 h-5" />;
    }
  };

  const renderProductCheck = () => (
    <div className="space-y-4">
      <div className="flex items-center space-x-2 mb-4">
        <Package className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Product Condition Check</h3>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Product Condition
        </label>
        <select
          value={productCondition}
          onChange={(e) => setProductCondition(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
        >
          <option value="excellent">Excellent - Perfect condition</option>
          <option value="good">Good - Minor wear/scratches</option>
          <option value="fair">Fair - Noticeable wear but functional</option>
          <option value="poor">Poor - Damaged or defective</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Notes (Optional)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Any observations about the product condition..."
          className="w-full border border-gray-300 rounded-lg px-3 py-2 h-20"
        />
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => setConfirmingProduct(null)}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={() => setVerificationStep('authenticity')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Next: Verify Authenticity
        </button>
      </div>
    </div>
  );

  const renderAuthenticityCheck = () => (
    <div className="space-y-4">
      <div className="flex items-center space-x-2 mb-4">
        <Shield className="w-5 h-5 text-green-600" />
        <h3 className="text-lg font-semibold">Authenticity Verification</h3>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-2">
          <Info className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-800">Verification Process</span>
        </div>
        <p className="text-sm text-blue-700">
          Use your encryption keys to verify the product's IPFS metadata matches the physical product.
          Check QR codes, serial numbers, and other identifying features.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Authenticity Status
        </label>
        <select
          value={authenticity}
          onChange={(e) => setAuthenticity(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2"
        >
          <option value="verified">✅ Verified - Product is authentic</option>
          <option value="suspicious">⚠️ Suspicious - Some concerns</option>
          <option value="counterfeit">❌ Counterfeit - Product is fake</option>
        </select>
      </div>

      {authenticity !== 'verified' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-yellow-600" />
            <span className="text-sm font-medium text-yellow-800">Authentication Issue</span>
          </div>
          <p className="text-sm text-yellow-700">
            If you suspect the product is not authentic, please provide details and consider
            contacting support before confirming receipt.
          </p>
        </div>
      )}

      <div className="flex justify-between">
        <button
          onClick={() => setVerificationStep('product_check')}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={() => setVerificationStep('final_confirm')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Next: Final Confirmation
        </button>
      </div>
    </div>
  );

  const renderFinalConfirmation = () => (
    <div className="space-y-4">
      <div className="flex items-center space-x-2 mb-4">
        <CheckCircle className="w-5 h-5 text-green-600" />
        <h3 className="text-lg font-semibold">Final Confirmation</h3>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h4 className="font-medium text-green-800 mb-2">Confirming receipt will trigger:</h4>
        <div className="space-y-2 text-sm text-green-700">
          <div className="flex items-center space-x-2">
            <Coins className="w-4 h-4" />
            <span>💰 Escrow payment released to manufacturer</span>
          </div>
          <div className="flex items-center space-x-2">
            <ArrowRightLeft className="w-4 h-4" />
            <span>🎯 NFT ownership transferred to your wallet (cross-chain)</span>
          </div>
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4" />
            <span>🔗 TokenURI (IPFS CID) preserved for authenticity verification</span>
          </div>
          <div className="flex items-center space-x-2">
            <Key className="w-4 h-4" />
            <span>🔑 Access to encryption keys for product verification</span>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-2">
          <Shield className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-800">TokenURI Preservation</span>
        </div>
        <p className="text-sm text-blue-700">
          The NFT's tokenURI (containing the IPFS CID) will be preserved during the cross-chain transfer,
          ensuring that all product metadata, authenticity proofs, and supply chain history remain intact
          and accessible on your destination chain.
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-800 mb-2">Verification Summary:</h4>
        <div className="space-y-1 text-sm text-gray-600">
          <p><span className="font-medium">Product Condition:</span> {productCondition.charAt(0).toUpperCase() + productCondition.slice(1)}</p>
          <p><span className="font-medium">Authenticity:</span> {authenticity}</p>
          {notes && <p><span className="font-medium">Notes:</span> {notes}</p>}
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-yellow-600" />
          <span className="text-sm font-medium text-yellow-800">
            This action cannot be undone
          </span>
        </div>
        <p className="text-sm text-yellow-700 mt-1">
          Once confirmed, the escrow will be released and NFT ownership will transfer.
          Make sure you've thoroughly verified the product.
        </p>
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => setVerificationStep('authenticity')}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={confirmProductReceipt}
          disabled={finalizing}
          className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {finalizing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              <span>Confirm Receipt & Transfer</span>
            </>
          )}
        </button>
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Product Receipt Confirmation</h1>
          <p className="text-gray-600">Verify delivered products and confirm receipt to complete transactions</p>
        </div>
        <div className="text-sm text-gray-600">
          <Package className="w-4 h-4 inline mr-1" />
          Buyer: {currentBuyerAddress.slice(0, 8)}...{currentBuyerAddress.slice(-6)}
        </div>
      </div>

      {/* Delivered Products List */}
      <div className="bg-white border rounded-lg shadow-sm mb-6">
        <div className="p-4 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Delivered Products Awaiting Confirmation</h2>
            <button
              onClick={loadDeliveredProducts}
              className="flex items-center space-x-2 px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <div className="p-4">
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="w-8 h-8 mx-auto mb-4 animate-spin text-blue-600" />
              <p className="text-gray-600">Loading delivered products...</p>
            </div>
          ) : deliveredProducts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Truck className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No products awaiting confirmation</p>
              <p className="text-sm">Products will appear here when delivered by transporters</p>
            </div>
          ) : (
            <div className="space-y-4">
              {deliveredProducts.map((product) => (
                <div key={product.delivery_request_id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium text-gray-900">
                        Product: {product.product_id}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Delivery: {product.delivery_request_id}
                      </p>
                      <p className="text-sm text-gray-500">
                        Delivered by: {product.transporter_address?.slice(0, 8)}...{product.transporter_address?.slice(-6)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Truck className="w-4 h-4 text-green-500" />
                      <span className="text-sm font-medium text-green-600">Delivered</span>
                    </div>
                  </div>

                  <div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
                    <p className="text-sm text-green-700">
                      📦 {product.message_for_buyer || 'Your product has been delivered successfully!'}
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      Delivered: {new Date(product.completion_timestamp * 1000).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => startProductConfirmation(product)}
                      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      <CheckCircle className="w-4 h-4" />
                      <span>Verify & Confirm Receipt</span>
                    </button>
                    <button
                      onClick={() => alert('Product details view coming soon!')}
                      className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      <Eye className="w-4 h-4" />
                      <span>View Details</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Product Verification Modal */}
      {confirmingProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">Confirm Product Receipt</h2>
                <button
                  onClick={() => setConfirmingProduct(null)}
                  className="text-gray-400 hover:text-gray-600"
                  disabled={finalizing}
                >
                  ×
                </button>
              </div>

              {/* Progress Steps */}
              <div className="flex items-center space-x-4 mb-6">
                {['product_check', 'authenticity', 'final_confirm'].map((step, index) => (
                  <div key={step} className="flex items-center">
                    <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                      verificationStep === step 
                        ? 'border-blue-600 bg-blue-600 text-white' 
                        : index < ['product_check', 'authenticity', 'final_confirm'].indexOf(verificationStep)
                        ? 'border-green-600 bg-green-600 text-white'
                        : 'border-gray-300 text-gray-400'
                    }`}>
                      {getVerificationStepIcon(step)}
                    </div>
                    {index < 2 && (
                      <div className={`w-16 h-0.5 ${
                        index < ['product_check', 'authenticity', 'final_confirm'].indexOf(verificationStep)
                          ? 'bg-green-600'
                          : 'bg-gray-300'
                      }`} />
                    )}
                  </div>
                ))}
              </div>

              {/* Step Content */}
              <div className="min-h-[300px]">
                {verificationStep === 'product_check' && renderProductCheck()}
                {verificationStep === 'authenticity' && renderAuthenticityCheck()}
                {verificationStep === 'final_confirm' && renderFinalConfirmation()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BuyerProductReceipt;
