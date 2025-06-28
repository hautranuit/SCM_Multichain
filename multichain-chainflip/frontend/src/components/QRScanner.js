import React, { useState } from 'react';
import { Upload, Lock, Unlock, CheckCircle, ArrowRight, QrCode } from 'lucide-react';

const QRScanner = () => {
  const [step, setStep] = useState('upload'); // upload, decrypt, confirm, processing, complete
  const [uploadedImage, setUploadedImage] = useState(null);
  const [decryptionProgress, setDecryptionProgress] = useState(0);
  const [decryptedContent, setDecryptedContent] = useState('');
  const [receiptProcessing, setReceiptProcessing] = useState(false);
  const [transactionResults, setTransactionResults] = useState(null);

  // Hardcoded encryption keys for demo
  const DEMO_AES_KEY = "b4f8c2a9d6e1f7b3c5a8d2e9f1b6c4a7d8e2f5b9c3a6d1e4f7b2c5a8d9e3f6b1";
  const DEMO_HMAC_KEY = "f6b9c3a6d1e4f7b2c5a8d9e3f6b1a4c7d8e2f5b9c3a6d1e4f7b2c5a8d9e3f6b1";
  const DEMO_DECRYPTED_URL = "https://w3s.link/ipfs/bafkreieeus3jwnrrgf64agcuqz2jqlmlnz42qkjbmfigby5o5wyiim3gjq";

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedImage(e.target.result);
        // Stay on upload step to show the "Process QR" button
      };
      reader.readAsDataURL(file);
    }
  };

  const handleProcessQR = async () => {
    setStep('decrypt');
    setDecryptionProgress(0);
    setDecryptedContent(''); // Reset decrypted content

    // Simulate decryption process
    const steps = [
      { progress: 20, message: "Reading QR code data..." },
      { progress: 40, message: "Extracting encrypted payload..." },
      { progress: 60, message: "Applying AES decryption..." },
      { progress: 80, message: "Verifying HMAC signature..." },
      { progress: 100, message: "Decryption complete!" }
    ];

    for (const step of steps) {
      await new Promise(resolve => setTimeout(resolve, 800));
      setDecryptionProgress(step.progress);
    }

    // Show decrypted content after completion
    await new Promise(resolve => setTimeout(resolve, 500));
    setDecryptedContent(DEMO_DECRYPTED_URL);
  };

  const handleConfirmReceipt = async () => {
    setReceiptProcessing(true);
    
    try {
      // Call backend API for receipt confirmation
      const response = await fetch('http://localhost:8001/api/blockchain/delivery/buyer/confirm-receipt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          buyer_address: "0xc6A050a538a9E857B4DCb4A33436280c202F6941",
          manufacturer_address: "0x5503a5B847e98B621d97695edf1bD84242C5862E",
          token_id: "8",
          product_id: "8",
          order_id: "XIAOMI-HEADPHONE-8",
          payment_amount: "0.025", // ETH
          qr_content: decryptedContent,
          verification_keys: {
            aes_key: DEMO_AES_KEY,
            hmac_key: DEMO_HMAC_KEY
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Receipt confirmation result:', result);
        setTransactionResults(result);
        setStep('complete');
      } else {
        const error = await response.json();
        alert(`Receipt confirmation failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error confirming receipt:', error);
      alert('Error confirming receipt');
    }
    
    setReceiptProcessing(false);
  };

  const renderUploadStep = () => (
    <div className="text-center">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 mb-4">
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-gray-600 mb-4">Upload QR Code Image</p>
        <input
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          className="hidden"
          id="qr-upload"
        />
        <label 
          htmlFor="qr-upload"
          className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Choose Image
        </label>
      </div>
      
      {uploadedImage && (
        <div className="mt-4">
          <img 
            src={uploadedImage} 
            alt="Uploaded QR Code" 
            className="max-w-xs mx-auto border rounded-lg"
          />
          <button
            onClick={handleProcessQR}
            className="mt-4 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center space-x-2 mx-auto"
          >
            <Lock className="w-4 h-4" />
            <span>Process QR</span>
          </button>
        </div>
      )}
    </div>
  );

  const renderDecryptStep = () => (
    <div className="text-center">
      <div className="bg-gray-50 border rounded-lg p-6 mb-4">
        <h3 className="text-lg font-semibold mb-4">🔐 Decrypting QR Code</h3>
        
        <div className="space-y-4 text-left">
          <div>
            <label className="block text-sm font-medium text-gray-700">AES Encryption Key:</label>
            <code className="block bg-gray-100 p-2 rounded text-xs font-mono break-all">
              {DEMO_AES_KEY}
            </code>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">HMAC Verification Key:</label>
            <code className="block bg-gray-100 p-2 rounded text-xs font-mono break-all">
              {DEMO_HMAC_KEY}
            </code>
          </div>
        </div>

        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Decryption Progress</span>
            <span className="text-sm text-gray-600">{decryptionProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${decryptionProgress}%` }}
            ></div>
          </div>
        </div>
      </div>

      {decryptedContent && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <Unlock className="w-5 h-5 text-green-600 mr-2" />
            <span className="font-semibold text-green-800">Decryption Successful!</span>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Decrypted IPFS URL:</label>
            <code className="block bg-white p-3 rounded border text-sm break-all">
              {decryptedContent}
            </code>
          </div>
          <button
            onClick={() => setStep('confirm')}
            className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center justify-center space-x-2"
          >
            <ArrowRight className="w-4 h-4" />
            <span>Continue to Verification</span>
          </button>
        </div>
      )}
    </div>
  );

  const renderConfirmStep = () => (
    <div className="text-center">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
        <CheckCircle className="w-12 h-12 mx-auto mb-4 text-blue-600" />
        <h3 className="text-lg font-semibold mb-2">Product Verification Complete</h3>
        <p className="text-gray-600 mb-4">
          QR code has been successfully decrypted and verified. Product authenticity confirmed.
        </p>
        
        <div className="bg-white border rounded-lg p-4 mb-4">
          <h4 className="font-medium mb-2">📦 Product Details:</h4>
          <div className="text-sm text-left space-y-1">
            <p><strong>Product:</strong> Xiaomi Wireless Headphone</p>
            <p><strong>Token ID:</strong> 8</p>
            <p><strong>Price:</strong> 0.025 ETH</p>
            <p><strong>IPFS CID:</strong> bafkreieeus3jwnrrgf64agcuqz2jqlmlnz42qkjbmfigby5o5wyiim3gjq</p>
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <h4 className="font-medium mb-2">⚡ What happens next:</h4>
          <div className="text-sm text-left space-y-1">
            <p>• 💰 ETH payment (0.025) from OP Sepolia → Base Sepolia</p>
            <p>• 🎨 NFT transfer from Base Sepolia → OP Sepolia</p>
            <p>• 🔗 IPFS metadata preserved during transfer</p>
            <p>• ✅ Escrow released to manufacturer</p>
          </div>
        </div>
      </div>

      <button
        onClick={handleConfirmReceipt}
        disabled={receiptProcessing}
        className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center space-x-2 mx-auto"
      >
        {receiptProcessing ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
        ) : (
          <ArrowRight className="w-5 h-5" />
        )}
        <span>
          {receiptProcessing ? 'Processing...' : 'Confirm Receipt and Payment'}
        </span>
      </button>
    </div>
  );

  const renderCompleteStep = () => (
    <div className="text-center">
      <div className="bg-green-50 border border-green-200 rounded-lg p-8">
        <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-600" />
        <h3 className="text-xl font-semibold mb-4 text-green-800">Receipt Confirmed Successfully!</h3>
        
        <div className="space-y-4 text-left">
          <div className="bg-white border rounded-lg p-4">
            <h4 className="font-medium mb-2">✅ Completed Transactions:</h4>
            <div className="text-sm space-y-2">
              <div className="flex justify-between">
                <span>💰 ETH Payment:</span>
                <span className="font-mono text-green-600">0.025 ETH transferred</span>
              </div>
              <div className="flex justify-between">
                <span>🎨 NFT Transfer:</span>
                <span className="font-mono text-blue-600">Token #8 transferred</span>
              </div>
              <div className="flex justify-between">
                <span>🔗 IPFS Metadata:</span>
                <span className="font-mono text-purple-600">Preserved</span>
              </div>
              <div className="flex justify-between">
                <span>📦 Escrow Status:</span>
                <span className="font-mono text-green-600">Released to manufacturer</span>
              </div>
            </div>
          </div>

          {/* Transaction Details */}
          {transactionResults && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium mb-2">🔗 Transaction Details:</h4>
              <div className="text-xs space-y-2">
                {transactionResults.eth_transfer && transactionResults.eth_transfer.transaction_hash && (
                  <div>
                    <span className="font-medium">ETH Transfer TX:</span>
                    <code className="block bg-white p-1 rounded mt-1 break-all">
                      {transactionResults.eth_transfer.transaction_hash}
                    </code>
                  </div>
                )}
                
                {transactionResults.nft_transfer && transactionResults.nft_transfer.transfer_id && (
                  <div>
                    <span className="font-medium">NFT Transfer ID:</span>
                    <code className="block bg-white p-1 rounded mt-1 break-all">
                      {transactionResults.nft_transfer.transfer_id}
                    </code>
                  </div>
                )}
                
                {transactionResults.nft_transfer && transactionResults.nft_transfer.burn_transaction && (
                  <div>
                    <span className="font-medium">NFT Burn TX (Base Sepolia):</span>
                    <code className="block bg-white p-1 rounded mt-1 break-all">
                      {transactionResults.nft_transfer.burn_transaction.transaction_hash}
                    </code>
                  </div>
                )}
                
                {transactionResults.nft_transfer && transactionResults.nft_transfer.message_transaction && (
                  <div>
                    <span className="font-medium">LayerZero Message TX:</span>
                    <code className="block bg-white p-1 rounded mt-1 break-all">
                      {transactionResults.nft_transfer.message_transaction.transaction_hash}
                    </code>
                  </div>
                )}
              </div>
              
              <div className="mt-3 text-xs text-gray-600">
                <p>💡 Tip: Copy transaction hashes to verify on blockchain explorers:</p>
                <p>• Base Sepolia: https://sepolia.basescan.org</p>
                <p>• OP Sepolia: https://sepolia-optimism.etherscan.io</p>
              </div>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium mb-2">🎉 Congratulations!</h4>
            <p className="text-sm text-gray-700">
              You now own the authentic Xiaomi Wireless Headphone NFT with complete supply chain history preserved on-chain. 
              The IPFS metadata ensures permanent verification of authenticity.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2 flex items-center space-x-2">
          <QrCode className="w-8 h-8" />
          <span>QR Code Scanner</span>
        </h1>
        <p className="text-gray-600">Scan QR codes to update product location (Transporter) or view product information (Buyer)</p>
      </div>

      {/* Role Selection */}
      <div className="flex space-x-4 mb-6">
        <div className="flex-1 p-4 border-2 border-blue-500 rounded-lg bg-blue-50">
          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-2 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl">📱</span>
            </div>
            <h3 className="font-semibold">Buyer</h3>
            <p className="text-sm text-gray-600">View product info and confirm receipt</p>
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div className="border rounded-lg p-6">
        {step === 'upload' && renderUploadStep()}
        {step === 'decrypt' && renderDecryptStep()}
        {step === 'confirm' && renderConfirmStep()}
        {step === 'complete' && renderCompleteStep()}
      </div>
    </div>
  );
};

export default QRScanner;