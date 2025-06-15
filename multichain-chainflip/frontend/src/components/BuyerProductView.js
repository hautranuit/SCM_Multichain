import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Package, MapPin, Clock, Star, CheckCircle, Camera, AlertCircle } from 'lucide-react';

const BuyerProductView = ({ productCid, onConfirmReceipt }) => {
  const [loading, setLoading] = useState(false);
  const [productInfo, setProductInfo] = useState(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmationData, setConfirmationData] = useState({
    buyer_id: '',
    buyer_name: '',
    delivery_location: '',
    condition_rating: 5,
    quality_rating: 5,
    payment_confirmed: false,
    payment_method: 'ETH',
    feedback: '',
    proof_images: []
  });
  const [proofImage, setProofImage] = useState(null);

  useEffect(() => {
    if (productCid) {
      fetchProductInfo();
    }
  }, [productCid]);

  const fetchProductInfo = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/ipfs/buyer/product-info/${productCid}`
      );
      
      if (response.data.success) {
        setProductInfo(response.data.buyer_info);
      }
    } catch (error) {
      console.error('Error fetching product info:', error);
      alert(`❌ Failed to load product information: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setProofImage({
          file: file,
          data: reader.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadImageToIPFS = async (fileData, filename) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/ipfs/upload-file`, {
        fileData: fileData,
        filename: filename,
        mimeType: 'image/jpeg'
      });
      return response.data.cid;
    } catch (error) {
      console.error('IPFS upload error:', error);
      throw error;
    }
  };

  const handleConfirmReceipt = async () => {
    setLoading(true);
    try {
      let proofImageCid = '';
      
      // Upload proof image if provided
      if (proofImage) {
        console.log('Uploading proof image to IPFS...');
        proofImageCid = await uploadImageToIPFS(
          proofImage.data,
          `delivery_proof_${Date.now()}.jpg`
        );
      }

      // Prepare confirmation data
      const finalConfirmationData = {
        ...confirmationData,
        proof_images: proofImageCid ? [proofImageCid] : []
      };

      // Call backend API to confirm receipt
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/ipfs/buyer/confirm-receipt`,
        {
          product_id: productInfo?.product_details?.product_id,
          current_cid: productCid,
          confirmation_data: finalConfirmationData
        }
      );

      if (response.data.success) {
        alert(`✅ Receipt Confirmed Successfully!\n\nNew IPFS CID: ${response.data.new_cid}\nDelivery Status: Complete\nThank you for your feedback!`);
        
        // Call parent callback if provided
        if (onConfirmReceipt) {
          onConfirmReceipt(response.data);
        }

        setShowConfirmDialog(false);
        // Refresh product info
        await fetchProductInfo();
      }

    } catch (error) {
      console.error('Confirmation error:', error);
      alert(`❌ Failed to confirm receipt: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getStatusColor = (status) => {
    const colors = {
      'manufactured': 'bg-blue-100 text-blue-800',
      'in_transit': 'bg-yellow-100 text-yellow-800',
      'delivered': 'bg-green-100 text-green-800',
      'delayed': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading && !productInfo) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
        <span>Loading product information...</span>
      </div>
    );
  }

  if (!productInfo) {
    return (
      <div className="text-center p-8">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No product information available</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Package className="w-6 h-6 text-blue-600 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">Product Information</h2>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(productInfo.shipping_info.current_status)}`}>
          {productInfo.shipping_info.current_status}
        </span>
      </div>

      {/* Product Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <Package className="w-5 h-5 mr-2" />
            Product Details
          </h3>
          <div className="space-y-2 text-sm">
            <div><strong>Name:</strong> {productInfo.product_details.name || 'N/A'}</div>
            <div><strong>ID:</strong> {productInfo.product_details.product_id}</div>
            <div><strong>Description:</strong> {productInfo.product_details.description || 'No description'}</div>
            <div><strong>Manufacturer:</strong> {productInfo.product_details.manufacturer?.name || 'Unknown'}</div>
            <div className="flex items-center">
              <strong>Quality Score:</strong>
              <div className="flex items-center ml-2">
                <Star className="w-4 h-4 text-yellow-500 mr-1" />
                <span>{productInfo.product_details.quality_score}/5</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <MapPin className="w-5 h-5 mr-2" />
            Shipping Information
          </h3>
          <div className="space-y-2 text-sm">
            <div><strong>Current Location:</strong> {productInfo.shipping_info.current_location || 'Unknown'}</div>
            <div><strong>Estimated Delivery:</strong> {productInfo.shipping_info.estimated_delivery || 'TBD'}</div>
            <div className="flex items-center">
              <strong>Status:</strong>
              <span className={`ml-2 px-2 py-1 rounded text-xs ${getStatusColor(productInfo.shipping_info.current_status)}`}>
                {productInfo.shipping_info.current_status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Verification Status */}
      <div className="bg-green-50 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-green-900 mb-3 flex items-center">
          <CheckCircle className="w-5 h-5 mr-2" />
          Verification Status
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center">
            <span className={`w-3 h-3 rounded-full mr-2 ${productInfo.verification.authenticity_verified ? 'bg-green-500' : 'bg-red-500'}`}></span>
            <span>Authenticity {productInfo.verification.authenticity_verified ? 'Verified' : 'Failed'}</span>
          </div>
          <div className="flex items-center">
            <span className={`w-3 h-3 rounded-full mr-2 ${productInfo.verification.blockchain_verified ? 'bg-green-500' : 'bg-red-500'}`}></span>
            <span>Blockchain {productInfo.verification.blockchain_verified ? 'Verified' : 'Pending'}</span>
          </div>
          <div className="text-xs text-gray-600">
            Last Updated: {formatTimestamp(productInfo.verification.last_updated)}
          </div>
        </div>
      </div>

      {/* Shipping Timeline */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
          <Clock className="w-5 h-5 mr-2" />
          Shipping Timeline
        </h3>
        <div className="space-y-3">
          {productInfo.shipping_info.timeline.map((event, index) => (
            <div key={index} className="flex items-start">
              <div className="flex-shrink-0 w-3 h-3 bg-blue-500 rounded-full mt-2 mr-4"></div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-gray-900">{event.event.replace('_', ' ').toUpperCase()}</div>
                  <div className="text-sm text-gray-500">{formatTimestamp(event.timestamp)}</div>
                </div>
                <div className="text-sm text-gray-600">{event.location}</div>
                <div className="text-sm text-gray-500">{event.details}</div>
                {event.actor && (
                  <div className="text-xs text-gray-400">By: {event.actor}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Product Images */}
      {productInfo.product_details.images && productInfo.product_details.images.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">Product Images</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {productInfo.product_details.images.map((imageCid, index) => (
              <img
                key={index}
                src={`${process.env.REACT_APP_IPFS_GATEWAY}${imageCid}`}
                alt={`Product ${index + 1}`}
                className="w-full h-24 object-cover rounded-lg border"
              />
            ))}
          </div>
        </div>
      )}

      {/* Confirm Receipt Button */}
      {productInfo.shipping_info.current_status !== 'delivered' && (
        <div className="flex justify-center">
          <button
            onClick={() => setShowConfirmDialog(true)}
            className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 flex items-center"
          >
            <CheckCircle className="w-5 h-5 mr-2" />
            Confirm Receipt & Payment
          </button>
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Confirm Receipt & Payment</h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Buyer ID</label>
                  <input
                    type="text"
                    value={confirmationData.buyer_id}
                    onChange={(e) => setConfirmationData(prev => ({ ...prev, buyer_id: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="Your buyer ID"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Buyer Name</label>
                  <input
                    type="text"
                    value={confirmationData.buyer_name}
                    onChange={(e) => setConfirmationData(prev => ({ ...prev, buyer_name: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="Your name"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Delivery Location</label>
                <input
                  type="text"
                  value={confirmationData.delivery_location}
                  onChange={(e) => setConfirmationData(prev => ({ ...prev, delivery_location: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Where was it delivered?"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Condition Rating</label>
                  <select
                    value={confirmationData.condition_rating}
                    onChange={(e) => setConfirmationData(prev => ({ ...prev, condition_rating: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    {[1,2,3,4,5].map(rating => (
                      <option key={rating} value={rating}>{rating} Star{rating > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Quality Rating</label>
                  <select
                    value={confirmationData.quality_rating}
                    onChange={(e) => setConfirmationData(prev => ({ ...prev, quality_rating: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    {[1,2,3,4,5].map(rating => (
                      <option key={rating} value={rating}>{rating} Star{rating > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={confirmationData.payment_confirmed}
                    onChange={(e) => setConfirmationData(prev => ({ ...prev, payment_confirmed: e.target.checked }))}
                    className="mr-2"
                  />
                  I confirm payment has been processed
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Feedback</label>
                <textarea
                  value={confirmationData.feedback}
                  onChange={(e) => setConfirmationData(prev => ({ ...prev, feedback: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                  rows="3"
                  placeholder="Optional feedback about the product and delivery..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Proof Image</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="w-full px-3 py-2 border rounded-md"
                />
                {proofImage && (
                  <div className="mt-1 text-sm text-green-600">✅ {proofImage.file.name}</div>
                )}
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowConfirmDialog(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReceipt}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Confirming...' : 'Confirm Receipt'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BuyerProductView;