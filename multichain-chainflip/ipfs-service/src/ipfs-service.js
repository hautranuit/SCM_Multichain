/**
 * Enhanced IPFS Service for ChainFLIP Multi-Chain
 * Integrates original w3storage functionality with QR code generation and encryption
 */

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import * as Client from '@web3-storage/w3up-client';
import { StoreMemory } from '@web3-storage/w3up-client/stores/memory';
import * as Proof from '@web3-storage/w3up-client/proof';
import { Signer } from '@web3-storage/w3up-client/principal/ed25519';
import { Blob, File } from '@web-std/file';
import QRCode from 'qrcode';
import crypto from 'crypto';
import Jimp from 'jimp';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8002;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Global IPFS client
let ipfsClient;

// Encryption utilities (from original project)
class EncryptionUtils {
    constructor() {
        this.aesKey = Buffer.from(process.env.AES_SECRET_KEY, 'hex');
        this.hmacKey = Buffer.from(process.env.HMAC_SECRET_KEY, 'hex');
    }

    encrypt(data) {
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipher('aes-256-cbc', this.aesKey);
        cipher.setAutoPadding(true);
        
        let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
        encrypted += cipher.final('hex');
        
        const encryptedData = iv.toString('hex') + ':' + encrypted;
        
        // Generate HMAC for integrity
        const hmac = crypto.createHmac('sha256', this.hmacKey);
        hmac.update(encryptedData);
        const signature = hmac.digest('hex');
        
        return {
            data: encryptedData,
            signature: signature
        };
    }

    decrypt(encryptedObj) {
        // Verify HMAC
        const hmac = crypto.createHmac('sha256', this.hmacKey);
        hmac.update(encryptedObj.data);
        const expectedSignature = hmac.digest('hex');
        
        if (expectedSignature !== encryptedObj.signature) {
            throw new Error('Data integrity check failed');
        }
        
        const parts = encryptedObj.data.split(':');
        const iv = Buffer.from(parts[0], 'hex');
        const encrypted = parts[1];
        
        const decipher = crypto.createDecipher('aes-256-cbc', this.aesKey);
        decipher.setAutoPadding(true);
        
        let decrypted = decipher.update(encrypted, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        
        return JSON.parse(decrypted);
    }

    generateQRHash(data) {
        const hash = crypto.createHash('sha256');
        hash.update(JSON.stringify(data));
        return hash.digest('hex');
    }
}

const encryption = new EncryptionUtils();

// Initialize Web3.Storage client
async function initWeb3Storage() {
    try {
        const principal = Signer.parse(process.env.W3STORAGE_TOKEN);
        const store = new StoreMemory();
        const client = await Client.create({ principal, store });
        const proof = await Proof.parse(process.env.W3STORAGE_PROOF);
        
        try {
            const space = await client.addSpace(proof);
            await client.setCurrentSpace(space.did());
            console.log('✅ Web3.Storage client initialized');
        } catch (err) {
            if (err.message.includes('space already registered')) {
                const spaces = await client.spaces();
                if (spaces.length > 0) {
                    await client.setCurrentSpace(spaces[0].did());
                    console.log('✅ Web3.Storage space set');
                }
            } else {
                throw err;
            }
        }
        
        return client;
    } catch (error) {
        console.error('❌ Failed to initialize Web3.Storage:', error);
        throw error;
    }
}

// Upload data to IPFS
async function uploadToIPFS(data, filename = 'data.json') {
    try {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const file = new File([blob], filename);
        const cid = await ipfsClient.uploadFile(file);
        return cid.toString();
    } catch (error) {
        console.error('❌ IPFS upload error:', error);
        throw error;
    }
}

// Upload file buffer to IPFS
async function uploadFileToIPFS(buffer, filename, mimeType) {
    try {
        const blob = new Blob([buffer], { type: mimeType });
        const file = new File([blob], filename);
        const cid = await ipfsClient.uploadFile(file);
        return cid.toString();
    } catch (error) {
        console.error('❌ IPFS file upload error:', error);
        throw error;
    }
}

// Generate QR code with encryption
async function generateEncryptedQR(data, options = {}) {
    try {
        // Encrypt the data
        const encryptedData = encryption.encrypt(data);
        
        // Generate QR hash for verification
        const qrHash = encryption.generateQRHash(data);
        
        // Create QR code data structure
        const qrData = {
            encrypted: encryptedData,
            timestamp: Date.now(),
            version: '2.0',
            productId: data.productId || 'unknown'
        };
        
        // Generate QR code image
        const qrCodeOptions = {
            errorCorrectionLevel: 'M',
            type: 'image/png',
            quality: 0.92,
            margin: 1,
            color: {
                dark: '#000000',
                light: '#FFFFFF'
            },
            width: options.size || 300,
            ...options.qrOptions
        };
        
        const qrCodeBuffer = await QRCode.toBuffer(JSON.stringify(qrData), qrCodeOptions);
        
        // Upload QR code to IPFS
        const qrImageCid = await uploadFileToIPFS(
            qrCodeBuffer,
            `qr_${data.productId || Date.now()}.png`,
            'image/png'
        );
        
        // Upload encrypted data to IPFS
        const dataCid = await uploadToIPFS(
            encryptedData,
            `encrypted_data_${data.productId || Date.now()}.json`
        );
        
        return {
            qrCodeCid: qrImageCid,
            encryptedDataCid: dataCid,
            qrHash: qrHash,
            timestamp: qrData.timestamp,
            qrCodeUrl: `${process.env.IPFS_GATEWAY}${qrImageCid}`,
            encryptedDataUrl: `${process.env.IPFS_GATEWAY}${dataCid}`
        };
        
    } catch (error) {
        console.error('❌ QR generation error:', error);
        throw error;
    }
}

// API Routes

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'ChainFLIP IPFS Service',
        timestamp: new Date().toISOString()
    });
});

// Upload data to IPFS
app.post('/upload', async (req, res) => {
    try {
        const { data, filename } = req.body;
        
        if (!data) {
            return res.status(400).json({ error: 'Data is required' });
        }
        
        const cid = await uploadToIPFS(data, filename);
        
        res.json({
            success: true,
            cid: cid,
            ipfsUrl: `${process.env.IPFS_GATEWAY}${cid}`,
            filename: filename || 'data.json'
        });
        
    } catch (error) {
        console.error('Upload error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Upload file to IPFS
app.post('/upload-file', async (req, res) => {
    try {
        const { fileData, filename, mimeType } = req.body;
        
        if (!fileData || !filename) {
            return res.status(400).json({ error: 'File data and filename are required' });
        }
        
        // Convert base64 to buffer if needed
        let buffer;
        if (typeof fileData === 'string') {
            // Assume base64 encoded
            const base64Data = fileData.replace(/^data:[^;]+;base64,/, '');
            buffer = Buffer.from(base64Data, 'base64');
        } else {
            buffer = Buffer.from(fileData);
        }
        
        const cid = await uploadFileToIPFS(buffer, filename, mimeType || 'application/octet-stream');
        
        res.json({
            success: true,
            cid: cid,
            ipfsUrl: `${process.env.IPFS_GATEWAY}${cid}`,
            filename: filename
        });
        
    } catch (error) {
        console.error('File upload error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Generate encrypted QR code
app.post('/qr/generate', async (req, res) => {
    try {
        const { data, options } = req.body;
        
        if (!data) {
            return res.status(400).json({ error: 'Data is required for QR generation' });
        }
        
        const result = await generateEncryptedQR(data, options);
        
        res.json({
            success: true,
            ...result
        });
        
    } catch (error) {
        console.error('QR generation error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Decrypt QR data
app.post('/qr/decrypt', async (req, res) => {
    try {
        const { encryptedData } = req.body;
        
        if (!encryptedData) {
            return res.status(400).json({ error: 'Encrypted data is required' });
        }
        
        const decryptedData = encryption.decrypt(encryptedData);
        
        res.json({
            success: true,
            data: decryptedData
        });
        
    } catch (error) {
        console.error('Decryption error:', error);
        res.status(400).json({ error: 'Failed to decrypt data: ' + error.message });
    }
});

// Get content from IPFS
app.get('/ipfs/:cid', async (req, res) => {
    try {
        const { cid } = req.params;
        const url = `${process.env.IPFS_GATEWAY}${cid}`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch from IPFS: ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            res.json(data);
        } else {
            const buffer = await response.arrayBuffer();
            res.set('Content-Type', contentType || 'application/octet-stream');
            res.send(Buffer.from(buffer));
        }
        
    } catch (error) {
        console.error('IPFS fetch error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Product metadata creation (from original system)
app.post('/product/metadata', async (req, res) => {
    try {
        const { 
            productId, 
            rfidData, 
            images = [], 
            videos = [], 
            historyLog = [] 
        } = req.body;
        
        if (!productId || !rfidData) {
            return res.status(400).json({ error: 'Product ID and RFID data are required' });
        }
        
        const metadata = {
            productId,
            rfid: rfidData,
            images,
            videos,
            historyLog: [
                ...historyLog,
                {
                    timestamp: new Date().toISOString(),
                    event: 'Metadata Created',
                    actor: 'IPFS Service',
                    details: 'Product metadata uploaded to IPFS'
                }
            ],
            createdAt: new Date().toISOString(),
            version: '2.0'
        };
        
        const cid = await uploadToIPFS(metadata, `product_${productId}_metadata.json`);
        
        res.json({
            success: true,
            cid: cid,
            ipfsUrl: `${process.env.IPFS_GATEWAY}${cid}`,
            metadata: metadata
        });
        
    } catch (error) {
        console.error('Metadata creation error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Update product history
app.post('/product/:productId/history', async (req, res) => {
    try {
        const { productId } = req.params;
        const { currentCid, newHistoryEntry } = req.body;
        
        if (!currentCid || !newHistoryEntry) {
            return res.status(400).json({ error: 'Current CID and new history entry are required' });
        }
        
        // Fetch current metadata
        const currentUrl = `${process.env.IPFS_GATEWAY}${currentCid}`;
        const response = await fetch(currentUrl);
        
        if (!response.ok) {
            throw new Error('Failed to fetch current metadata');
        }
        
        const currentMetadata = await response.json();
        
        // Add new history entry
        const updatedMetadata = {
            ...currentMetadata,
            historyLog: [
                ...(currentMetadata.historyLog || []),
                {
                    ...newHistoryEntry,
                    timestamp: new Date().toISOString()
                }
            ],
            lastUpdated: new Date().toISOString()
        };
        
        const newCid = await uploadToIPFS(
            updatedMetadata, 
            `product_${productId}_history_${Date.now()}.json`
        );
        
        res.json({
            success: true,
            newCid: newCid,
            ipfsUrl: `${process.env.IPFS_GATEWAY}${newCid}`,
            metadata: updatedMetadata
        });
        
    } catch (error) {
        console.error('History update error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Initialize service
async function initService() {
    try {
        console.log('🚀 Initializing ChainFLIP IPFS Service...');
        
        // Initialize Web3.Storage client
        ipfsClient = await initWeb3Storage();
        
        // Start server
        app.listen(PORT, () => {
            console.log(`✅ ChainFLIP IPFS Service running on port ${PORT}`);
            console.log(`📡 Health check: http://localhost:${PORT}/health`);
        });
        
    } catch (error) {
        console.error('❌ Service initialization failed:', error);
        process.exit(1);
    }
}

// Start the service
initService();

export default app;
