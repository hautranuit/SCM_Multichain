import React, { useState } from 'react';
import axios from 'axios';
import { Truck, MapPin, Camera, Clock, Save } from 'lucide-react';

const TransporterLocationUpdate = ({ productId, currentCid, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [locationData, setLocationData] = useState({
    transporter_id: '',
    transporter_name: '',
    current_location: '',
    coordinates: {
      latitude: '',
      longitude: ''
    },
    status: 'in_transit',
    estimated_delivery: '',
    notes: '',
    proof_images: []
  });
  const [proofImage, setProofImage] = useState(null);

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

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocationData(prev => ({
            ...prev,
            coordinates: {
              latitude: position.coords.latitude.toString(),
              longitude: position.coords.longitude.toString()
            }
          }));
          setLoading(false);
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Could not get current location. Please enter manually.');
          setLoading(false);
        }
      );
    } else {
      alert('Geolocation is not supported by this browser.');
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

  const handleSubmitUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let proofImageCid = '';
      
      // Upload proof image if provided
      if (proofImage) {
        console.log('Uploading proof image to IPFS...');
        proofImageCid = await uploadImageToIPFS(
          proofImage.data,
          `proof_${productId}_${Date.now()}.jpg`
        );
      }

      // Prepare location update data
      const updateData = {
        ...locationData,
        proof_images: proofImageCid ? [proofImageCid] : []
      };

      // Call backend API to update location
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/ipfs/transporter/location-update`,
        {
          product_id: productId,
          current_cid: currentCid,
          location_update: updateData
        }
      );

      if (response.data.success) {
        alert(`✅ Location Updated Successfully!\n\nNew IPFS CID: ${response.data.new_cid}\nLocation: ${locationData.current_location}\nStatus: ${locationData.status}`);
        
        // Call parent callback if provided
        if (onUpdate) {
          onUpdate(response.data);
        }

        // Reset form
        setLocationData({
          transporter_id: '',
          transporter_name: '',
          current_location: '',
          coordinates: { latitude: '', longitude: '' },
          status: 'in_transit',
          estimated_delivery: '',
          notes: '',
          proof_images: []
        });
        setProofImage(null);
      }

    } catch (error) {
      console.error('Location update error:', error);
      alert(`❌ Failed to update location: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <div className="flex items-center mb-6">
        <Truck className="w-6 h-6 text-green-600 mr-3" />
        <h3 className="text-xl font-semibold text-gray-900">Update Location</h3>
      </div>

      <form onSubmit={handleSubmitUpdate} className="space-y-4">
        {/* Transporter Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Transporter ID *
            </label>
            <input
              type="text"
              required
              value={locationData.transporter_id}
              onChange={(e) => setLocationData(prev => ({ ...prev, transporter_id: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Your transporter ID"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Transporter Name *
            </label>
            <input
              type="text"
              required
              value={locationData.transporter_name}
              onChange={(e) => setLocationData(prev => ({ ...prev, transporter_name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Your company name"
            />
          </div>
        </div>

        {/* Location Info */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Current Location *
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              required
              value={locationData.current_location}
              onChange={(e) => setLocationData(prev => ({ ...prev, current_location: e.target.value }))}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="City, State, Country"
            />
            <button
              type="button"
              onClick={getCurrentLocation}
              disabled={loading}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 flex items-center"
            >
              <MapPin className="w-4 h-4 mr-1" />
              GPS
            </button>
          </div>
        </div>

        {/* Coordinates */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Latitude
            </label>
            <input
              type="number"
              step="any"
              value={locationData.coordinates.latitude}
              onChange={(e) => setLocationData(prev => ({ 
                ...prev, 
                coordinates: { ...prev.coordinates, latitude: e.target.value }
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="0.000000"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Longitude
            </label>
            <input
              type="number"
              step="any"
              value={locationData.coordinates.longitude}
              onChange={(e) => setLocationData(prev => ({ 
                ...prev, 
                coordinates: { ...prev.coordinates, longitude: e.target.value }
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="0.000000"
            />
          </div>
        </div>

        {/* Status and Delivery */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status *
            </label>
            <select
              required
              value={locationData.status}
              onChange={(e) => setLocationData(prev => ({ ...prev, status: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <option value="in_transit">In Transit</option>
              <option value="at_hub">At Hub</option>
              <option value="out_for_delivery">Out for Delivery</option>
              <option value="delivered">Delivered</option>
              <option value="delayed">Delayed</option>
              <option value="returned">Returned</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Estimated Delivery
            </label>
            <input
              type="datetime-local"
              value={locationData.estimated_delivery}
              onChange={(e) => setLocationData(prev => ({ ...prev, estimated_delivery: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Notes
          </label>
          <textarea
            value={locationData.notes}
            onChange={(e) => setLocationData(prev => ({ ...prev, notes: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            rows="3"
            placeholder="Additional notes about the shipment..."
          />
        </div>

        {/* Proof Image */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Proof Image
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          {proofImage && (
            <div className="mt-2 text-sm text-green-600">
              ✅ {proofImage.file.name} selected
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="pt-4">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Updating Location...
              </div>
            ) : (
              <div className="flex items-center">
                <Save className="w-4 h-4 mr-2" />
                Update Location & Push to IPFS
              </div>
            )}
          </button>
        </div>
      </form>

      <div className="mt-6 bg-blue-50 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">🔄 Update Process:</h4>
        <div className="text-sm text-blue-700 space-y-1">
          <div>1. Downloads current product metadata from IPFS</div>
          <div>2. Adds your location update to shipping history</div>
          <div>3. Uploads updated metadata to IPFS</div>
          <div>4. Returns new CID for blockchain update</div>
        </div>
      </div>
    </div>
  );
};

export default TransporterLocationUpdate;