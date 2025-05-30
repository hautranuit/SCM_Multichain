import React, { useState, useRef } from 'react';
import { useNotification } from '../contexts/NotificationContext';

export const QRScanner = () => {
  const { showSuccess, showError, showWarning } = useNotification();
  
  const [scanResult, setScanResult] = useState(null);
  const [decryptedData, setDecryptedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showGenerator, setShowGenerator] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setLoading(true);
      
      // In a real implementation, you would:
      // 1. Read the QR code from the image using a QR reader library
      // 2. Parse the JSON data from the QR code
      // 3. Send it to the backend for decryption
      
      // For demo purposes, we'll simulate this process
      showWarning('QR scanning simulation - upload a QR code image');
      
      const reader = new FileReader();
      reader.onload = async (e) => {
        // Simulate QR code reading and processing
        const mockQRData = {
          type: 'chainflip',
          version: '2.0',
          payload: {
            encrypted: {
              iv: 'mock_iv',
              data: 'mock_encrypted_data',
              authTag: 'mock_auth_tag',
              timestamp: Date.now()
            },
            signature: 'mock_signature',
            version: '2.0'
          }
        };
        
        setScanResult(mockQRData);
        
        // Try to decrypt
        await decryptQRData(mockQRData.payload);
      };
      
      reader.readAsDataURL(file);
      
    } catch (error) {
      console.error('QR scanning error:', error);
      showError('Failed to scan QR code');
    } finally {
      setLoading(false);
    }
  };

  const decryptQRData = async (encryptedPayload) => {
    try {
      setLoading(true);
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/ipfs/qr/decrypt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          encryptedData: encryptedPayload
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setDecryptedData(result.data);
        showSuccess('QR code decrypted successfully!');
      } else {
        showError('Failed to decrypt QR code - may be invalid or expired');
      }
      
    } catch (error) {
      console.error('Decryption error:', error);
      showError('Failed to decrypt QR code');
    } finally {
      setLoading(false);
    }
  };

  const generateSampleQR = async () => {
    try {
      setLoading(true);
      
      const sampleData = {
        productId: 'DEMO-001',
        name: 'Sample Product',
        manufacturer: '0x742d35Cc6235C3F23fE82fcDc533C09B7B6a8C0d',
        batchNumber: 'BATCH-001',
        manufacturingDate: new Date().toISOString(),
        location: 'Manufacturing Plant A'
      };
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/ipfs/qr/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: sampleData,
          options: {
            size: 400,
            validityHours: 24
          }
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        showSuccess('Sample QR code generated successfully!');
        
        // Display the generated QR
        setScanResult({
          type: 'generated',
          qrCodeUrl: result.qrCodeUrl,
          metadata: result
        });
        
      } else {
        showError('Failed to generate QR code');
      }
      
    } catch (error) {
      console.error('QR generation error:', error);
      showError('Failed to generate QR code');
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setScanResult(null);
    setDecryptedData(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">QR Scanner</h1>
          <p className="text-gray-600">Scan and verify product QR codes</p>
        </div>
        
        <button 
          onClick={() => setShowGenerator(!showGenerator)}
          className="btn-secondary"
        >
          {showGenerator ? '📱 Scanner' : '🔧 Generator'}
        </button>
      </div>

      {showGenerator ? (
        /* QR Generator */
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">🔧 QR Code Generator</h3>
          </div>
          
          <div className="text-center py-8">
            <div className="text-6xl mb-4">📱</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Generate Sample QR Code</h3>
            <p className="text-gray-600 mb-6">Create a sample encrypted QR code for testing</p>
            
            <button 
              onClick={generateSampleQR}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="loading-spinner w-4 h-4"></div>
                  <span>Generating...</span>
                </div>
              ) : (
                '🔧 Generate Sample QR'
              )}
            </button>
          </div>
        </div>
      ) : (
        /* QR Scanner */
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">📱 Scan QR Code</h3>
          </div>
          
          <div className="text-center py-8">
            <div className="text-6xl mb-4">📷</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Upload QR Code Image</h3>
            <p className="text-gray-600 mb-6">Select a QR code image to scan and decrypt</p>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
            
            <div className="flex justify-center space-x-4">
              <button 
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="btn-primary"
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="loading-spinner w-4 h-4"></div>
                    <span>Processing...</span>
                  </div>
                ) : (
                  '📂 Upload QR Image'
                )}
              </button>
              
              {scanResult && (
                <button 
                  onClick={clearResults}
                  className="btn-secondary"
                >
                  🗑️ Clear
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Scan Results */}
      {scanResult && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* QR Code Display */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">
                {scanResult.type === 'generated' ? '🔧 Generated QR Code' : '📱 Scanned QR Code'}
              </h3>
            </div>
            
            <div className="text-center py-6">
              {scanResult.qrCodeUrl ? (
                <div className="qr-code-container inline-block">
                  <img 
                    src={scanResult.qrCodeUrl} 
                    alt="QR Code" 
                    className="max-w-full h-auto"
                  />
                </div>
              ) : (
                <div className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg p-8">
                  <div className="text-4xl mb-2">📱</div>
                  <p className="text-gray-600">QR Code Data Detected</p>
                </div>
              )}
            </div>
            
            {scanResult.metadata && (
              <div className="mt-4 text-sm text-gray-600">
                <div><strong>Hash:</strong> {scanResult.metadata.qrHash?.slice(0, 16)}...</div>
                <div><strong>Generated:</strong> {new Date(scanResult.metadata.timestamp).toLocaleString()}</div>
              </div>
            )}
          </div>

          {/* Decrypted Data */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">🔓 Decrypted Data</h3>
            </div>
            
            {decryptedData ? (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex">
                    <span className="text-green-600 text-xl mr-3">✅</span>
                    <div>
                      <h4 className="text-sm font-medium text-green-800">
                        QR Code Verified
                      </h4>
                      <p className="mt-1 text-sm text-green-700">
                        Product data successfully decrypted and verified.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Product Information</h4>
                  <div className="space-y-2 text-sm">
                    {Object.entries(decryptedData).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-600 capitalize">{key.replace(/([A-Z])/g, ' $1')}:</span>
                        <span className="font-medium text-gray-900">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <button className="btn-primary text-sm flex-1">
                    🔍 Analyze Product
                  </button>
                  <button className="btn-secondary text-sm flex-1">
                    📋 View History
                  </button>
                </div>
              </div>
            ) : scanResult ? (
              <div className="text-center py-8">
                <div className="loading-spinner mx-auto mb-4"></div>
                <p className="text-gray-600">Decrypting QR code data...</p>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">🔒</div>
                <p>Scan a QR code to view decrypted data</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">📋 How to Use</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4">
            <div className="text-3xl mb-3">📱</div>
            <h4 className="font-semibold text-gray-900 mb-2">1. Scan QR Code</h4>
            <p className="text-sm text-gray-600">
              Upload an image containing a ChainFLIP QR code from your device
            </p>
          </div>
          
          <div className="text-center p-4">
            <div className="text-3xl mb-3">🔓</div>
            <h4 className="font-semibold text-gray-900 mb-2">2. Decrypt Data</h4>
            <p className="text-sm text-gray-600">
              The system automatically decrypts and verifies the product data
            </p>
          </div>
          
          <div className="text-center p-4">
            <div className="text-3xl mb-3">✅</div>
            <h4 className="font-semibold text-gray-900 mb-2">3. Verify Authenticity</h4>
            <p className="text-sm text-gray-600">
              View product details and run additional security analysis
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
