/**
 * Standalone QR Code Generator (Enhanced from original project)
 * Can be used independently or as part of the IPFS service
 */

import QRCode from 'qrcode';
import crypto from 'crypto';
import Jimp from 'jimp';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config();

class ChainFLIPQRGenerator {
    constructor() {
        this.aesKey = Buffer.from(process.env.AES_SECRET_KEY, 'hex');
        this.hmacKey = Buffer.from(process.env.HMAC_SECRET_KEY, 'hex');
    }

    // Enhanced encryption with version and integrity checks
    encrypt(data) {
        const timestamp = Date.now();
        const nonce = crypto.randomBytes(12);
        const iv = crypto.randomBytes(16);
        
        const payload = {
            data: data,
            timestamp: timestamp,
            version: '2.0',
            nonce: nonce.toString('hex')
        };
        
        const cipher = crypto.createCipherGCM('aes-256-gcm', this.aesKey, iv);
        
        let encrypted = cipher.update(JSON.stringify(payload), 'utf8', 'hex');
        encrypted += cipher.final('hex');
        
        const authTag = cipher.getAuthTag();
        
        const encryptedData = {
            iv: iv.toString('hex'),
            data: encrypted,
            authTag: authTag.toString('hex'),
            timestamp: timestamp
        };
        
        // Generate HMAC for additional integrity
        const hmac = crypto.createHmac('sha256', this.hmacKey);
        hmac.update(JSON.stringify(encryptedData));
        
        return {
            encrypted: encryptedData,
            signature: hmac.digest('hex'),
            version: '2.0'
        };
    }

    // Enhanced decryption with verification
    decrypt(encryptedObj) {
        try {
            // Verify HMAC signature
            const hmac = crypto.createHmac('sha256', this.hmacKey);
            hmac.update(JSON.stringify(encryptedObj.encrypted));
            const expectedSignature = hmac.digest('hex');
            
            if (expectedSignature !== encryptedObj.signature) {
                throw new Error('Data integrity verification failed');
            }
            
            const { iv, data, authTag } = encryptedObj.encrypted;
            
            const decipher = crypto.createDecipherGCM('aes-256-gcm', this.aesKey, Buffer.from(iv, 'hex'));
            decipher.setAuthTag(Buffer.from(authTag, 'hex'));
            
            let decrypted = decipher.update(data, 'hex', 'utf8');
            decrypted += decipher.final('utf8');
            
            const payload = JSON.parse(decrypted);
            
            // Verify timestamp (prevent replay attacks - 24 hour window)
            const now = Date.now();
            const age = now - payload.timestamp;
            const maxAge = 24 * 60 * 60 * 1000; // 24 hours
            
            if (age > maxAge) {
                throw new Error('QR code has expired');
            }
            
            return payload.data;
            
        } catch (error) {
            throw new Error(`Decryption failed: ${error.message}`);
        }
    }

    // Generate QR hash for verification
    generateQRHash(data) {
        const hash = crypto.createHash('sha256');
        hash.update(JSON.stringify(data) + Date.now());
        return hash.digest('hex');
    }

    // Generate dynamic QR code with encryption
    async generateDynamicQR(productData, options = {}) {
        try {
            const qrHash = this.generateQRHash(productData);
            
            // Add metadata to product data
            const enhancedData = {
                ...productData,
                qrId: qrHash,
                generatedAt: new Date().toISOString(),
                expiresAt: new Date(Date.now() + (options.validityHours || 24) * 60 * 60 * 1000).toISOString(),
                chainId: options.chainId || 80002,
                contractAddress: options.contractAddress
            };
            
            // Encrypt the data
            const encryptedData = this.encrypt(enhancedData);
            
            // QR code options
            const qrOptions = {
                errorCorrectionLevel: 'H',
                type: 'image/png',
                quality: 0.92,
                margin: 2,
                color: {
                    dark: options.darkColor || '#1a365d',
                    light: options.lightColor || '#ffffff'
                },
                width: options.size || 400,
                ...options.qrOptions
            };
            
            // Generate QR code
            const qrCodeData = {
                type: 'chainflip',
                version: '2.0',
                payload: encryptedData
            };
            
            const qrCodeBuffer = await QRCode.toBuffer(
                JSON.stringify(qrCodeData), 
                qrOptions
            );
            
            // Add logo or branding if requested
            let finalQRBuffer = qrCodeBuffer;
            if (options.addLogo && options.logoPath) {
                finalQRBuffer = await this.addLogoToQR(qrCodeBuffer, options.logoPath);
            }
            
            return {
                qrCodeBuffer: finalQRBuffer,
                qrHash: qrHash,
                encryptedData: encryptedData,
                metadata: {
                    productId: productData.productId,
                    generatedAt: enhancedData.generatedAt,
                    expiresAt: enhancedData.expiresAt,
                    size: qrOptions.width,
                    format: 'PNG'
                }
            };
            
        } catch (error) {
            throw new Error(`QR generation failed: ${error.message}`);
        }
    }

    // Add logo to QR code
    async addLogoToQR(qrBuffer, logoPath) {
        try {
            const qrImage = await Jimp.read(qrBuffer);
            const logo = await Jimp.read(logoPath);
            
            // Resize logo to be 20% of QR code size
            const logoSize = qrImage.getWidth() * 0.2;
            logo.resize(logoSize, logoSize);
            
            // Calculate center position
            const x = (qrImage.getWidth() - logoSize) / 2;
            const y = (qrImage.getHeight() - logoSize) / 2;
            
            // Composite logo onto QR code
            qrImage.composite(logo, x, y);
            
            return await qrImage.getBufferAsync(Jimp.MIME_PNG);
            
        } catch (error) {
            console.warn('Failed to add logo to QR code:', error.message);
            return qrBuffer; // Return original QR if logo addition fails
        }
    }

    // Batch QR generation for multiple products
    async generateBatchQR(products, options = {}) {
        const results = [];
        
        for (const product of products) {
            try {
                const qrResult = await this.generateDynamicQR(product, options);
                results.push({
                    success: true,
                    productId: product.productId,
                    ...qrResult
                });
            } catch (error) {
                results.push({
                    success: false,
                    productId: product.productId,
                    error: error.message
                });
            }
        }
        
        return results;
    }

    // Save QR code to file
    async saveQRToFile(qrBuffer, filename, outputDir = './qr_codes') {
        try {
            // Ensure output directory exists
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }
            
            const filepath = path.join(outputDir, filename);
            fs.writeFileSync(filepath, qrBuffer);
            
            return filepath;
        } catch (error) {
            throw new Error(`Failed to save QR code: ${error.message}`);
        }
    }
}

// CLI usage
async function main() {
    if (process.argv.length < 3) {
        console.log('Usage: node qr-generator.js <command> [options]');
        console.log('Commands:');
        console.log('  generate - Generate a single QR code');
        console.log('  batch    - Generate QR codes for multiple products');
        console.log('  decrypt  - Decrypt QR code data');
        process.exit(1);
    }

    const generator = new ChainFLIPQRGenerator();
    const command = process.argv[2];

    try {
        switch (command) {
            case 'generate':
                // Example product data
                const productData = {
                    productId: 'PROD-001',
                    name: 'Sample Product',
                    manufacturer: '0x742d35Cc6235C3F23fE82fcDc533C09B7B6a8C0d',
                    batchNumber: 'BATCH-001',
                    manufacturingDate: new Date().toISOString()
                };
                
                const result = await generator.generateDynamicQR(productData, {
                    size: 400,
                    validityHours: 72
                });
                
                const filename = `qr_${productData.productId}_${Date.now()}.png`;
                const filepath = await generator.saveQRToFile(result.qrCodeBuffer, filename);
                
                console.log('✅ QR Code generated successfully!');
                console.log(`📁 Saved to: ${filepath}`);
                console.log(`🔒 QR Hash: ${result.qrHash}`);
                break;
                
            case 'decrypt':
                console.log('Decrypt functionality - provide encrypted data as JSON');
                break;
                
            default:
                console.log('Unknown command:', command);
        }
    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    }
}

// Run CLI if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export default ChainFLIPQRGenerator;
