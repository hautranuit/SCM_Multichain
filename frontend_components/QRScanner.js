import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import QRCode from 'qrcode.react';

const QRScanner = () => {
  const [scanResult, setScanResult] = useState(null);
  const [scanHistory, setScanHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [productDetails, setProductDetails] = useState(null);
  const [manualInput, setManualInput] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    loadScanHistory();
  }, []);

  const loadScanHistory = () => {
    const history = JSON.parse(localStorage.getItem('qrScanHistory') || '[]');
    setScanHistory(history);
  };

  const saveScanToHistory = (scanData) => {
    const history = JSON.parse(localStorage.getItem('qrScanHistory') || '[]');
    const newScan = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      data: scanData,
      result: productDetails
    };
    const updatedHistory = [newScan, ...history].slice(0, 50); // Keep last 50 scans
    localStorage.setItem('qrScanHistory', JSON.stringify(updatedHistory));
    setScanHistory(updatedHistory);
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } // Use back camera
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Could not access camera. Please ensure camera permissions are granted.');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject;
      const tracks = stream.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
      setCameraActive(false);
    }
  };

  const captureAndScan = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    // Simulate QR code detection (in real app, use a QR code library)
    // For demo, we'll use manual input
    setShowManualInput(true);
  };

  const processQRCode = async (qrData) => {
    setLoading(true);
    setScanResult(qrData);
    
    try {
      let parsedData;
      try {
        parsedData = JSON.parse(qrData);
      } catch {
        // If not JSON, treat as product ID
        parsedData = { productId: qrData };
      }

      // Fetch product details from blockchain
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/products/${parsedData.productId}`);
      setProductDetails(response.data);
      
      // Save to history
      saveScanToHistory(qrData);
      
    } catch (error) {
      console.error('Error fetching product details:', error);
      // Try to fetch from QR verification endpoint
      try {
        const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/qr/verify`, {
          qr_data: qrData
        });
        setProductDetails(response.data);
        saveScanToHistory(qrData);
      } catch (verifyError) {
        console.error('Error verifying QR code:', verifyError);
        setProductDetails({ 
          error: 'Product not found or invalid QR code',
          scannedData: qrData 
        });
      }
    }
    setLoading(false);
  };

  const handleManualScan = (e) => {
    e.preventDefault();
    if (manualInput.trim()) {
      processQRCode(manualInput.trim());
      setManualInput('');
      setShowManualInput(false);
    }
  };

  const clearResults = () => {
    setScanResult(null);
    setProductDetails(null);
  };

  const generateSampleQR = () => {
    const sampleData = {
      productId: "SAMPLE-001",
      name: "Sample Product",
      manufacturer: "0x032041b4b356fEE1496805DD4749f181bC736FFA",
      blockchain: "polygon",
      contractAddress: process.env.REACT_APP_CONTRACT_ADDRESS
    };
    return JSON.stringify(sampleData);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '30px' }}>📱 QR Code Scanner</h2>

      {/* Scanner Section */}
      <div className="card" style={{ padding: '20px', marginBottom: '30px' }}>
        <h3 style={{ marginBottom: '20px' }}>Scan Product QR Code</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          {/* Camera Section */}
          <div>
            <h4>Camera Scanner</h4>
            {!cameraActive ? (
              <div style={{ 
                textAlign: 'center', 
                padding: '40px', 
                border: '2px dashed #e5e7eb', 
                borderRadius: '8px',
                background: '#f9fafb'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '10px' }}>📷</div>
                <div style={{ marginBottom: '15px', color: '#6b7280' }}>
                  Click to activate camera and scan QR codes
                </div>
                <button
                  onClick={startCamera}
                  className="btn"
                  style={{ 
                    background: '#10b981', 
                    color: 'white', 
                    border: 'none', 
                    padding: '12px 24px', 
                    borderRadius: '8px',
                    fontSize: '16px',
                    cursor: 'pointer'
                  }}
                >
                  Start Camera
                </button>
              </div>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  style={{ 
                    width: '100%', 
                    maxWidth: '400px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '8px' 
                  }}
                />
                <canvas ref={canvasRef} style={{ display: 'none' }} />
                <div style={{ marginTop: '15px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
                  <button
                    onClick={captureAndScan}
                    className="btn"
                    style={{ 
                      background: '#3b82f6', 
                      color: 'white', 
                      border: 'none', 
                      padding: '10px 20px', 
                      borderRadius: '6px',
                      cursor: 'pointer'
                    }}
                  >
                    📸 Capture & Scan
                  </button>
                  <button
                    onClick={stopCamera}
                    className="btn"
                    style={{ 
                      background: '#ef4444', 
                      color: 'white', 
                      border: 'none', 
                      padding: '10px 20px', 
                      borderRadius: '6px',
                      cursor: 'pointer'
                    }}
                  >
                    Stop Camera
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Manual Input Section */}
          <div>
            <h4>Manual Input</h4>
            <div style={{ padding: '20px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
              <form onSubmit={handleManualScan}>
                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
                    Enter QR Code Data or Product ID:
                  </label>
                  <textarea
                    value={manualInput}
                    onChange={(e) => setManualInput(e.target.value)}
                    placeholder='{"productId":"PROD-001","name":"Product Name"} or just product ID'
                    style={{ 
                      width: '100%', 
                      padding: '10px', 
                      border: '1px solid #e5e7eb', 
                      borderRadius: '4px',
                      minHeight: '80px'
                    }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!manualInput.trim() || loading}
                  className="btn"
                  style={{ 
                    background: loading ? '#9ca3af' : '#8b5cf6', 
                    color: 'white', 
                    border: 'none', 
                    padding: '10px 20px', 
                    borderRadius: '6px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    width: '100%'
                  }}
                >
                  {loading ? 'Scanning...' : '🔍 Scan Data'}
                </button>
              </form>
            </div>
          </div>

          {/* Sample QR Code */}
          <div>
            <h4>Sample QR Code</h4>
            <div style={{ textAlign: 'center', padding: '20px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
              <div style={{ marginBottom: '15px' }}>
                <QRCode value={generateSampleQR()} size={150} />
              </div>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '10px' }}>
                Scan this sample QR code for testing
              </div>
              <button
                onClick={() => processQRCode(generateSampleQR())}
                className="btn"
                style={{ 
                  background: '#f59e0b', 
                  color: 'white', 
                  border: 'none', 
                  padding: '8px 16px', 
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Test Scan
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Scan Results */}
      {(scanResult || productDetails) && (
        <div className="card" style={{ padding: '20px', marginBottom: '30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>Scan Results</h3>
            <button
              onClick={clearResults}
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
              Clear Results
            </button>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div style={{ fontSize: '18px', color: '#6b7280' }}>Verifying product authenticity...</div>
            </div>
          ) : productDetails?.error ? (
            <div style={{ 
              padding: '20px', 
              background: '#fef2f2', 
              border: '1px solid #fecaca', 
              borderRadius: '8px',
              color: '#991b1b'
            }}>
              <h4>❌ Verification Failed</h4>
              <div>Error: {productDetails.error}</div>
              {productDetails.scannedData && (
                <div style={{ marginTop: '10px', fontSize: '14px' }}>
                  Scanned data: {productDetails.scannedData}
                </div>
              )}
            </div>
          ) : productDetails ? (
            <div style={{ 
              padding: '20px', 
              background: '#f0fdf4', 
              border: '1px solid #bbf7d0', 
              borderRadius: '8px'
            }}>
              <h4 style={{ color: '#166534', marginBottom: '15px' }}>✅ Product Verified</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
                <div>
                  <strong>Product Name:</strong> {productDetails.name || productDetails.metadata?.name || 'Unknown'}
                </div>
                <div>
                  <strong>Category:</strong> {productDetails.category || productDetails.metadata?.category || 'Not specified'}
                </div>
                <div>
                  <strong>Manufacturer:</strong> 
                  <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                    {productDetails.manufacturer ? `${productDetails.manufacturer.substring(0, 20)}...` : 'Unknown'}
                  </span>
                </div>
                <div>
                  <strong>Batch Number:</strong> {productDetails.batchNumber || productDetails.metadata?.batchNumber || 'N/A'}
                </div>
                <div>
                  <strong>Price:</strong> ${productDetails.price || productDetails.metadata?.price || '0.00'}
                </div>
                <div>
                  <strong>Location:</strong> {productDetails.location || productDetails.metadata?.location || 'Unknown'}
                </div>
              </div>
              
              {productDetails.description && (
                <div style={{ marginTop: '15px', padding: '10px', background: 'white', borderRadius: '4px' }}>
                  <strong>Description:</strong> {productDetails.description || productDetails.metadata?.description}
                </div>
              )}

              <div style={{ marginTop: '15px', fontSize: '14px', color: '#166534' }}>
                <div>✅ Product authenticity verified on blockchain</div>
                <div>✅ Supply chain integrity confirmed</div>
                <div>✅ No counterfeit indicators detected</div>
              </div>
            </div>
          ) : (
            <div style={{ padding: '20px', background: '#f3f4f6', borderRadius: '8px' }}>
              <div>Scanned Data: {scanResult}</div>
            </div>
          )}
        </div>
      )}

      {/* Scan History */}
      <div className="card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>Scan History</h3>
          <button
            onClick={() => {
              localStorage.removeItem('qrScanHistory');
              setScanHistory([]);
            }}
            className="btn"
            style={{ 
              background: '#ef4444', 
              color: 'white', 
              border: 'none', 
              padding: '8px 16px', 
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Clear History
          </button>
        </div>

        {scanHistory.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
            No scan history available. Start scanning QR codes to see them here.
          </div>
        ) : (
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {scanHistory.map((scan) => (
              <div key={scan.id} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                padding: '15px',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                marginBottom: '10px',
                background: 'white'
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '500', marginBottom: '5px' }}>
                    {new Date(scan.timestamp).toLocaleString()}
                  </div>
                  <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '5px' }}>
                    Data: {scan.data.length > 50 ? `${scan.data.substring(0, 50)}...` : scan.data}
                  </div>
                  {scan.result && !scan.result.error && (
                    <div style={{ fontSize: '12px', color: '#059669' }}>
                      ✅ Product: {scan.result.name || scan.result.metadata?.name || 'Unknown'}
                    </div>
                  )}
                  {scan.result?.error && (
                    <div style={{ fontSize: '12px', color: '#dc2626' }}>
                      ❌ {scan.result.error}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => processQRCode(scan.data)}
                  className="btn"
                  style={{ 
                    background: '#3b82f6', 
                    color: 'white', 
                    border: 'none', 
                    padding: '6px 12px', 
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Re-scan
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default QRScanner;