import React, { useState } from 'react';
import axios from 'axios';
import { QrCode, Camera, Upload, Eye, Truck, ShoppingBag } from 'lucide-react';
import TransporterLocationUpdate from './TransporterLocationUpdate';
import BuyerProductView from './BuyerProductView';
import { useAuth } from '../contexts/AuthContext';

const QRScanner = () => {
  const { userRole } = useAuth();
  const [scannedData, setScannedData] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeMode, setActiveMode] = useState(null); // 'transporter' or 'buyer'
  const [qrFile, setQrFile] = useState(null);

  const handleQRFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setQrFile(file);
      // In a real implementation, you would decode the QR from the image
      // For now, we'll simulate with the text input
      alert('QR image uploaded. Please also paste the QR data in the text field for this demo.');
    }
  };

  const handleScanQR = async () => {
    if (!scannedData.trim()) {
      alert('Please enter QR code data');
      return;
    }

    if (!activeMode) {
      alert('Please select whether you are a Transporter or Buyer');
      return;
    }

    setLoading(true);
    try {
      // Call backend to decrypt QR and get product info
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/ipfs/qr/scan-and-decrypt`,
        {
          encrypted_qr_data: scannedData,
          user_type: activeMode
        }
      );

      if (response.data.success) {
        setScanResult(response.data);
        
        // Show initial scan result
        if (activeMode === 'transporter') {
          alert(`✅ QR Scanned Successfully!\n\nProduct ID: ${response.data.product_id}\nYou can now update the location for this product.`);
        } else if (activeMode === 'buyer') {
          alert(`✅ QR Scanned Successfully!\n\nProduct ID: ${response.data.product_id}\nLoading product information and shipping history...`);
        }
      }

    } catch (error) {
      console.error('QR scan error:', error);
      alert(`❌ QR Scan Failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationUpdate = (updateResult) => {
    alert(`✅ Location Updated Successfully!\n\nThe new IPFS CID (${updateResult.new_cid}) should now be saved to the blockchain for permanent tracking.`);
    // Reset for next scan
    setScannedData('');
    setScanResult(null);
  };

  const handleReceiptConfirmation = (confirmResult) => {
    alert(`✅ Receipt Confirmed!\n\nDelivery has been marked as complete. The final IPFS CID (${confirmResult.new_cid}) contains the complete product journey.`);
    // Reset for next scan
    setScannedData('');
    setScanResult(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
            <QrCode className="w-8 h-8 mr-3 text-blue-600" />
            QR Code Scanner
          </h1>
          <p className="text-gray-600">
            Scan QR codes to update product location (Transporter) or view product information (Buyer)
          </p>
        </div>

        {!scanResult && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            {/* User Type Selection */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">I am a:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => setActiveMode('transporter')}
                  className={`p-4 border-2 rounded-lg transition-colors ${
                    activeMode === 'transporter'
                      ? 'border-green-500 bg-green-50 text-green-800'
                      : 'border-gray-200 hover:border-green-300'
                  }`}
                >
                  <div className="flex items-center justify-center mb-2">
                    <Truck className="w-8 h-8" />
                  </div>
                  <div className="font-semibold">Transporter</div>
                  <div className="text-sm mt-1">Update product location and shipping status</div>
                </button>
                
                <button
                  onClick={() => setActiveMode('buyer')}
                  className={`p-4 border-2 rounded-lg transition-colors ${
                    activeMode === 'buyer'
                      ? 'border-blue-500 bg-blue-50 text-blue-800'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <div className="flex items-center justify-center mb-2">
                    <ShoppingBag className="w-8 h-8" />
                  </div>
                  <div className="font-semibold">Buyer</div>
                  <div className="text-sm mt-1">View product info and confirm receipt</div>
                </button>
              </div>
            </div>

            {/* QR Code Input */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  QR Code Data
                </label>
                <div className="flex gap-2">
                  <textarea
                    value={scannedData}
                    onChange={(e) => setScannedData(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="4"
                    placeholder="Paste QR code data here or upload QR image..."
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <label className="flex-1 bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer hover:border-gray-400 transition-colors">
                  <Upload className="w-6 h-6 mx-auto mb-2 text-gray-400" />
                  <span className="text-sm text-gray-600">Upload QR Image</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleQRFileUpload}
                    className="hidden"
                  />
                </label>
                
                <button
                  onClick={handleScanQR}
                  disabled={loading || !activeMode}
                  className="bg-blue-600 text-white px-6 py-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  ) : (
                    <Camera className="w-5 h-5 mr-2" />
                  )}
                  {loading ? 'Processing...' : 'Process QR'}
                </button>
              </div>

              {qrFile && (
                <div className="text-sm text-green-600">
                  ✅ QR image uploaded: {qrFile.name}
                </div>
              )}
            </div>

            {/* Instructions */}
            <div className="mt-6 bg-blue-50 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">📱 How to Use:</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <div>1. Select whether you are a Transporter or Buyer</div>
                <div>2. Scan QR code with your phone camera and paste the data, or upload QR image</div>
                <div>3. Click "Process QR" to decrypt and access product information</div>
                <div>4. Follow the workflow for your role (update location or confirm receipt)</div>
              </div>
            </div>
          </div>
        )}

        {/* Scan Results and Actions */}
        {scanResult && activeMode === 'transporter' && (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="text-green-900 font-semibold mb-2">🚛 Transporter Mode</h3>
              <div className="text-green-700 text-sm">
                <div><strong>Product ID:</strong> {scanResult.product_id}</div>
                <div><strong>Current Metadata CID:</strong> {scanResult.current_metadata_cid}</div>
                <div><strong>Permissions:</strong> {scanResult.permissions?.join(', ')}</div>
              </div>
            </div>
            
            <TransporterLocationUpdate
              productId={scanResult.product_id}
              currentCid={scanResult.current_metadata_cid}
              onUpdate={handleLocationUpdate}
            />
            
            <div className="text-center">
              <button
                onClick={() => {
                  setScannedData('');
                  setScanResult(null);
                }}
                className="text-blue-600 hover:text-blue-800 underline"
              >
                ← Scan Another QR Code
              </button>
            </div>
          </div>
        )}

        {scanResult && activeMode === 'buyer' && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-blue-900 font-semibold mb-2">🛒 Buyer Mode</h3>
              <div className="text-blue-700 text-sm">
                <div><strong>Product ID:</strong> {scanResult.product_id}</div>
                <div><strong>Current Metadata CID:</strong> {scanResult.current_metadata_cid}</div>
                <div><strong>Permissions:</strong> {scanResult.permissions?.join(', ')}</div>
              </div>
            </div>
            
            <BuyerProductView
              productCid={scanResult.current_metadata_cid}
              onConfirmReceipt={handleReceiptConfirmation}
            />
            
            <div className="text-center">
              <button
                onClick={() => {
                  setScannedData('');
                  setScanResult(null);
                }}
                className="text-blue-600 hover:text-blue-800 underline"
              >
                ← Scan Another QR Code
              </button>
            </div>
          </div>
        )}

        {/* Demo Data */}
        <div className="mt-8 bg-gray-100 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">🧪 Demo QR Data (for testing):</h4>
          <div className="text-sm text-gray-700 space-y-2">
            <div>
              <strong>Sample QR:</strong> 
              <code className="ml-2 bg-white px-2 py-1 rounded text-xs">
                {`{"product_id":"PROD-001","metadata_cid":"bafkreiqr..","timestamp":"${new Date().toISOString()}","encrypted":true}`}
              </code>
            </div>
            <div className="text-xs text-gray-500">
              Note: In production, QR codes would contain encrypted data that gets decrypted by the backend.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QRScanner;