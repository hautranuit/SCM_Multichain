#!/usr/bin/env node

/*
 * W3Storage Upload Script for Python Backend
 * This Node.js script handles IPFS uploads using w3up client
 */

// Add immediate debugging to verify script loads
console.error('🔄 W3Storage script loading...');
console.error('📋 Node.js version:', process.version);
console.error('📁 Script path:', import.meta.url);
console.error('🔧 Arguments:', process.argv);

import fs from 'fs';
import path from 'path';

console.error('✅ Basic imports successful');

// Import w3up client modules dynamically
async function loadW3StorageModules() {
    try {
        console.error('🔄 Loading W3Storage modules...');
        
        const w3upClient = await import('@web3-storage/w3up-client');
        console.error('✅ w3up-client loaded');
        
        const w3upStores = await import('@web3-storage/w3up-client/stores/memory');
        console.error('✅ w3up-client/stores/memory loaded');
        
        const w3upProof = await import('@web3-storage/w3up-client/proof');
        console.error('✅ w3up-client/proof loaded');
        
        const w3upSigner = await import('@web3-storage/w3up-client/principal/ed25519');
        console.error('✅ w3up-client/principal/ed25519 loaded');
        
        const webStdFile = await import('@web-std/file');
        console.error('✅ @web-std/file loaded');
        
        return {
            Client: w3upClient.create,
            StoreMemory: w3upStores.StoreMemory,
            Proof: w3upProof,
            Signer: w3upSigner.Signer,
            Blob: webStdFile.Blob,
            File: webStdFile.File
        };
    } catch (error) {
        console.error('❌ Error importing w3up modules:', error.message);
        console.error('Please run: npm install @web3-storage/w3up-client @web-std/file');
        throw error;
    }
}

async function initW3Storage() {
    console.error('🔧 Initializing W3Storage...');
    
    const modules = await loadW3StorageModules();
    const { Client, StoreMemory, Proof, Signer } = modules;
    
    // Read credentials from files or environment variables
    let W3UP_KEY, W3UP_PROOF;
    
    // Check for credential files first (more reliable for special characters)
    if (process.env.W3STORAGE_TOKEN_FILE && process.env.W3STORAGE_PROOF_FILE) {
        console.error('🔍 Reading credentials from files...');
        try {
            W3UP_KEY = fs.readFileSync(process.env.W3STORAGE_TOKEN_FILE, 'utf8').trim();
            W3UP_PROOF = fs.readFileSync(process.env.W3STORAGE_PROOF_FILE, 'utf8').trim();
            console.error('✅ Credentials loaded from files');
        } catch (fileError) {
            console.error('❌ Failed to read credential files:', fileError.message);
            throw new Error(`Failed to read credential files: ${fileError.message}`);
        }
    } else {
        // Fallback to environment variables
        console.error('🔍 Reading credentials from environment variables...');
        W3UP_KEY = process.env.W3STORAGE_TOKEN;
        W3UP_PROOF = process.env.W3STORAGE_PROOF;
    }
    
    console.error(`🔑 Token present: ${W3UP_KEY ? 'YES' : 'NO'}`);
    console.error(`🔏 Proof present: ${W3UP_PROOF ? 'YES' : 'NO'}`);
    
    if (!W3UP_KEY || !W3UP_PROOF) {
        throw new Error('Missing W3STORAGE_TOKEN or W3STORAGE_PROOF');
    }
    
    // Validate credentials format before parsing
    console.error('🔍 Validating credential formats...');
    
    if (W3UP_KEY.length < 50) {
        throw new Error(`W3STORAGE_TOKEN appears too short (${W3UP_KEY.length} chars). Expected longer token.`);
    }
    
    if (W3UP_PROOF.length < 100) {
        throw new Error(`W3STORAGE_PROOF appears too short (${W3UP_PROOF.length} chars). Expected longer proof.`);
    }
    
    // Check for common corruption patterns
    if (W3UP_PROOF.includes('…') || W3UP_PROOF.includes('...')) {
        throw new Error('W3STORAGE_PROOF appears to be truncated (contains ellipsis). Please get the complete proof.');
    }
    
    console.error('🔐 Parsing credentials...');
    
    let principal;
    try {
        principal = Signer.parse(W3UP_KEY);
        console.error('✅ W3STORAGE_TOKEN parsed successfully');
    } catch (tokenError) {
        throw new Error(`Failed to parse W3STORAGE_TOKEN: ${tokenError.message}. Please regenerate your token.`);
    }
    
    const store = new StoreMemory();
    
    console.error('🌐 Creating W3Storage client...');
    const client = await Client({ principal, store });
    
    console.error('📋 Parsing proof...');
    let proof;
    try {
        proof = await Proof.parse(W3UP_PROOF);
        console.error('✅ W3STORAGE_PROOF parsed successfully');
    } catch (proofError) {
        console.error('❌ W3STORAGE_PROOF parsing failed');
        console.error(`🔍 Proof length: ${W3UP_PROOF.length} characters`);
        console.error(`🔍 Proof preview: ${W3UP_PROOF.substring(0, 100)}...`);
        console.error(`🔍 Proof ending: ...${W3UP_PROOF.substring(W3UP_PROOF.length - 100)}`);
        throw new Error(`Failed to parse W3STORAGE_PROOF: ${proofError.message}. Error details: ${proofError.stack}`);
    }
    
    try {
        console.error('🔗 Adding space...');
        const space = await client.addSpace(proof);
        await client.setCurrentSpace(space.did());
        console.error('✅ W3Storage client initialized and space set');
    } catch (err) {
        if (err.message.includes('space already registered')) {
            console.error('⚠️ W3Storage space already registered. Setting current space.');
            const spaces = await client.spaces();
            if (spaces.length > 0) {
                await client.setCurrentSpace(spaces[0].did());
                console.error(`✅ W3Storage current space set to: ${spaces[0].did()}`);
            } else {
                throw new Error('❌ Space already registered, but no spaces found');
            }
        } else {
            throw err;
        }
    }
    
    return client;
}

async function uploadToIPFS(data, filename = 'metadata.json') {
    try {
        console.error('📦 Starting uploadToIPFS function...');
        
        const modules = await loadW3StorageModules();
        const { Blob, File } = modules;
        
        console.error('🔧 Getting W3Storage client...');
        const client = await initW3Storage();
        
        console.error('📄 Creating file...');
        let blob;
        let file;
        
        // Check if data is JSON or binary file path
        if (typeof data === 'string' && fs.existsSync(data)) {
            // It's a file path - upload the binary file
            console.error(`📁 Reading binary file: ${data}`);
            const fileBuffer = fs.readFileSync(data);
            
            // Detect MIME type based on file extension
            const ext = path.extname(filename).toLowerCase();
            let mimeType = 'application/octet-stream';
            
            const mimeTypes = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.mp4': 'video/mp4',
                '.webm': 'video/webm',
                '.avi': 'video/avi',
                '.mov': 'video/quicktime',
                '.json': 'application/json'
            };
            
            mimeType = mimeTypes[ext] || 'application/octet-stream';
            console.error(`📄 File type: ${mimeType}, size: ${fileBuffer.length} bytes`);
            
            blob = new Blob([fileBuffer], { type: mimeType });
            file = new File([blob], filename, { type: mimeType });
        } else {
            // It's JSON data
            console.error('📄 Creating JSON blob...');
            blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            file = new File([blob], filename);
        }
        
        console.error('🚀 Uploading file to W3Storage...');
        const cid = await client.uploadFile(file);
        console.error(`✅ File uploaded successfully. CID: ${cid.toString()}`);
        
        return {
            success: true,
            cid: cid.toString(),
            gateway_url: `https://w3s.link/ipfs/${cid.toString()}`
        };
        
    } catch (error) {
        console.error('❌ Upload failed:', error.message);
        console.error('❌ Error stack:', error.stack);
        return {
            success: false,
            error: error.message
        };
    }
}

// CLI interface
async function main() {
    try {
        console.error('🚀 W3Storage upload script starting...');
        
        // Read JSON data from stdin or file
        const args = process.argv.slice(2);
        let jsonData;
        let filename = 'metadata.json';
        
        console.error(`📋 Arguments received: ${args.length}`);
        
        if (args.length >= 1) {
            // Read from file
            const inputFile = args[0];
            if (args[1]) filename = args[1];
            
            console.error(`📁 Input: ${inputFile}, Output filename: ${filename}`);
            
            if (!fs.existsSync(inputFile)) {
                throw new Error(`Input file not found: ${inputFile}`);
            }
            
            // Check if it's a binary file or JSON file
            const ext = path.extname(inputFile).toLowerCase();
            if (ext === '.json') {
                // JSON file - parse and upload
                const fileContent = fs.readFileSync(inputFile, 'utf8');
                jsonData = JSON.parse(fileContent);
                console.error(`✅ JSON data loaded, size: ${JSON.stringify(jsonData).length} bytes`);
            } else {
                // Binary file - pass file path to upload function
                console.error(`✅ Binary file detected: ${ext}`);
                jsonData = inputFile; // Pass file path instead of parsed content
            }
        } else {
            console.error('📥 Reading from stdin...');
            // Read from stdin
            let input = '';
            for await (const chunk of process.stdin) {
                input += chunk;
            }
            
            if (!input.trim()) {
                throw new Error('No input data provided');
            }
            
            jsonData = JSON.parse(input);
            console.error(`✅ JSON data loaded from stdin, size: ${input.length} bytes`);
        }
        
        console.error('🌐 Starting upload process...');
        const result = await uploadToIPFS(jsonData, filename);
        
        console.error(`📤 Upload result: ${result.success ? 'SUCCESS' : 'FAILED'}`);
        
        // Only output the JSON result to stdout
        console.log(JSON.stringify(result, null, 2));
        
        process.exit(result.success ? 0 : 1);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        console.error('❌ Stack:', error.stack);
        
        // Provide specific guidance based on error type
        if (error.message.includes('W3STORAGE_PROOF') || error.message.includes('Unexpected end of data')) {
            console.error('');
            console.error('🚨 W3STORAGE CREDENTIALS ISSUE DETECTED:');
            console.error('');
            console.error('Your W3Storage credentials appear to be corrupted or incomplete.');
            console.error('');
            console.error('To fix this issue:');
            console.error('1. Go to https://console.web3.storage/');
            console.error('2. Generate new API credentials');
            console.error('3. Copy the COMPLETE token and proof (no truncation)');
            console.error('4. Update your .env file with the new credentials');
            console.error('5. Restart your backend server');
            console.error('');
            console.error('⚠️  Make sure to copy the ENTIRE proof string - it should be very long!');
            console.error('');
        } else if (error.message.includes('network') || error.message.includes('ENOTFOUND')) {
            console.error('');
            console.error('🌐 NETWORK ISSUE DETECTED:');
            console.error('');
            console.error('Unable to connect to W3Storage servers.');
            console.error('Please check your internet connection and try again.');
            console.error('');
        }
        
        // Output error JSON to stdout for Python to parse
        console.log(JSON.stringify({
            success: false,
            error: error.message,
            error_type: error.message.includes('W3STORAGE_PROOF') ? 'credentials' : 
                       error.message.includes('network') ? 'network' : 'unknown'
        }));
        process.exit(1);
    }
}

// Run main function if this file is executed directly
console.error('🔍 Checking if this is the main script...');
console.error('📁 import.meta.url:', import.meta.url);
console.error('📁 process.argv[1]:', process.argv[1]);

const scriptPath = new URL(import.meta.url).pathname;
const argv1 = process.argv[1];

console.error('🔍 scriptPath:', scriptPath);
console.error('🔍 argv1:', argv1);

// Handle Windows path compatibility - multiple approaches
const normalizedArgv1 = argv1.replace(/\\/g, '/');
const normalizedScriptPath = scriptPath.startsWith('/') ? scriptPath.substring(1) : scriptPath;

console.error('🔍 normalizedArgv1:', normalizedArgv1);
console.error('🔍 normalizedScriptPath:', normalizedScriptPath);

const isMainScript = (
    argv1 === scriptPath ||
    normalizedArgv1 === scriptPath ||
    argv1 === normalizedScriptPath ||
    normalizedArgv1 === normalizedScriptPath ||
    normalizedArgv1.endsWith(normalizedScriptPath) ||
    scriptPath.endsWith(argv1.replace(/\\/g, '/'))
);

console.error('🔍 isMainScript:', isMainScript);

if (isMainScript) {
    console.error('🚀 W3Storage upload script is starting as main module...');
    main().catch(error => {
        console.error('❌ Fatal error in main:', error.message);
        console.error('❌ Stack:', error.stack);
        console.log(JSON.stringify({
            success: false,
            error: error.message
        }));
        process.exit(1);
    });
} else {
    console.error('⚠️ Script not recognized as main module, skipping execution');
    console.error('💡 This might be imported as a module');
}