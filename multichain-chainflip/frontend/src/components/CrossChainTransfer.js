/**
 * Cross-Chain Transfer Component
 * Handles product transfers across different L2 chains
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import blockchainService from '../services/blockchainService';
import { ArrowRight, Truck, Package, AlertCircle, CheckCircle } from 'lucide-react';

const CrossChainTransfer = ({ productTokenId, onClose }) => {
  const { user, userRole } = useAuth();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [product, setProduct] = useState(null);
  const [transferData, setTransferData] = useState({
    targetChain: '',
    recipient: '',
    shipmentDetails: {
      start_location: '',
      end_location: '',
      distance: 0,
      estimated_delivery_time: ''
    }
  });
  const [shipmentResult, setShipmentResult] = useState(null);

  const chains = [
    { id: 'manufacturer', name: 'Manufacturer Chain (zkEVM)', chainId: 2442, role: 'manufacturer' },
    { id: 'transporter', name: 'Transporter Chain (Arbitrum)', chainId: 421614, role: 'transporter' },
    { id: 'buyer', name: 'Buyer Chain (Optimism)', chainId: 11155420, role: 'buyer' }
  ];

  useEffect(() => {
    if (productTokenId) {
      loadProductDetails();
    }
  }, [productTokenId]);

  const loadProductDetails = async () => {
    try {
      setLoading(true);
      const productData = await blockchainService.getProduct(productTokenId);
      setProduct(productData);
    } catch (error) {
      console.error('Error loading product:', error);
      alert('Failed to load product details');
    } finally {
      setLoading(false);
    }
  };

  const handleChainSelect = (chainId) => {
    setTransferData({
      ...transferData,
      targetChain: chainId
    });
    setStep(2);
  };

  const calculateEstimatedDelivery = (distance) => {
    const baseTime = 24; // 24 hours base
    const additionalTime = Math.floor(distance / 100) * 12; // 12 hours per 100km
    const estimatedHours = baseTime + additionalTime;
    
    const deliveryDate = new Date();
    deliveryDate.setHours(deliveryDate.getHours() + estimatedHours);
    
    return deliveryDate.toISOString();
  };

  const handleCreateShipment = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Auto-calculate estimated delivery time based on distance
      const estimatedDelivery = calculateEstimatedDelivery(transferData.shipmentDetails.distance);
      
      const shipmentData = {
        product_token_id: productTokenId,
        ...transferData.shipmentDetails,
        estimated_delivery_time: estimatedDelivery
      };

      // Create shipment on transporter chain
      const result = await blockchainService.createShipment(
        user.wallet_address,
        shipmentData
      );

      setShipmentResult(result);
      setStep(3);
    } catch (error) {
      console.error('Error creating shipment:', error);
      alert(`Failed to create shipment: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !product) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg">
          <div className="text-center">Loading product details...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Cross-Chain Transfer</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ×
          </button>
        </div>

        {/* Product Info */}
        {product && (
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <h3 className="font-semibold mb-2">Product Details</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><strong>Name:</strong> {product.name || product.metadata?.name}</div>
              <div><strong>Token ID:</strong> {product.token_id}</div>
              <div><strong>Current Owner:</strong> {blockchainService.formatAddressForDisplay(product.current_owner)}</div>
              <div><strong>Status:</strong> {product.status}</div>
            </div>
          </div>
        )}

        {/* Step Progress */}
        <div className="flex items-center justify-center mb-6">
          <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${step >= 1 ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-400'}`}>
              1
            </div>
            <span className="ml-2">Select Chain</span>
          </div>
          <ArrowRight className="mx-4 text-gray-400" />
          <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${step >= 2 ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-400'}`}>
              2
            </div>
            <span className="ml-2">Shipment Details</span>
          </div>
          <ArrowRight className="mx-4 text-gray-400" />
          <div className={`flex items-center ${step >= 3 ? 'text-green-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${step >= 3 ? 'border-green-600 bg-green-600 text-white' : 'border-gray-400'}`}>
              3
            </div>
            <span className="ml-2">Complete</span>
          </div>
        </div>

        {/* Step 1: Chain Selection */}
        {step === 1 && (
          <div>
            <h3 className="text-lg font-semibold mb-4">Select Target Chain</h3>
            <div className="grid gap-4">
              {chains.map((chain) => (
                <div
                  key={chain.id}
                  onClick={() => handleChainSelect(chain.id)}
                  className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{chain.name}</h4>
                      <p className="text-sm text-gray-600">Chain ID: {chain.chainId}</p>
                      <p className="text-sm text-gray-600">Role: {chain.role}</p>
                    </div>
                    <ArrowRight className="text-blue-500" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Shipment Details */}
        {step === 2 && (
          <div>
            <h3 className="text-lg font-semibold mb-4">Shipment Details</h3>
            <form onSubmit={handleCreateShipment}>
              <div className="grid gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Recipient Address
                  </label>
                  <input
                    type="text"
                    required
                    value={transferData.recipient}
                    onChange={(e) => setTransferData({
                      ...transferData,
                      recipient: e.target.value
                    })}
                    placeholder="0x..."
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start Location
                    </label>
                    <input
                      type="text"
                      required
                      value={transferData.shipmentDetails.start_location}
                      onChange={(e) => setTransferData({
                        ...transferData,
                        shipmentDetails: {
                          ...transferData.shipmentDetails,
                          start_location: e.target.value
                        }
                      })}
                      placeholder="Origin city/address"
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Location
                    </label>
                    <input
                      type="text"
                      required
                      value={transferData.shipmentDetails.end_location}
                      onChange={(e) => setTransferData({
                        ...transferData,
                        shipmentDetails: {
                          ...transferData.shipmentDetails,
                          end_location: e.target.value
                        }
                      })}
                      placeholder="Destination city/address"
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Distance (km)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={transferData.shipmentDetails.distance}
                    onChange={(e) => setTransferData({
                      ...transferData,
                      shipmentDetails: {
                        ...transferData.shipmentDetails,
                        distance: parseInt(e.target.value) || 0
                      }
                    })}
                    placeholder="Distance in kilometers"
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  />
                </div>

                {transferData.shipmentDetails.distance > 0 && (
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Estimated Delivery:</strong> {Math.floor(24 + (transferData.shipmentDetails.distance / 100) * 12)} hours
                    </p>
                    <p className="text-xs text-blue-600 mt-1">
                      Base time: 24 hours + 12 hours per 100km
                    </p>
                  </div>
                )}
              </div>

              <div className="flex gap-4 mt-6">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center"
                >
                  {loading ? 'Creating...' : (
                    <>
                      <Truck className="w-4 h-4 mr-2" />
                      Create Shipment
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Step 3: Success */}
        {step === 3 && shipmentResult && (
          <div className="text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-green-800 mb-2">
              Shipment Created Successfully!
            </h3>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <p className="text-green-800 mb-2">
                <strong>Shipment ID:</strong> {shipmentResult.shipment_id}
              </p>
              <p className="text-sm text-green-700">
                Your product has been scheduled for cross-chain transfer. 
                The shipment is now on the Transporter Chain (Arbitrum) and awaiting consensus approval.
              </p>
            </div>
            <button
              onClick={onClose}
              className="bg-green-600 text-white py-2 px-6 rounded-lg hover:bg-green-700"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CrossChainTransfer;