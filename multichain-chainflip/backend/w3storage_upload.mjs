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
    
    const W3UP_KEY = process.env.W3STORAGE_TOKEN;
    const W3UP_PROOF = process.env.W3STORAGE_PROOF;
    
    console.error(`🔑 Token present: ${W3UP_KEY ? 'YES' : 'NO'}`);
    console.error(`🔏 Proof present: ${W3UP_PROOF ? 'YES' : 'NO'}`);
    
    if (!W3UP_KEY || !W3UP_PROOF) {
        throw new Error('Missing W3STORAGE_TOKEN or W3STORAGE_PROOF environment variables');
    }
    
    console.error('🔐 Parsing credentials...');
    const principal = Signer.parse(W3UP_KEY);
    const store = new StoreMemory();
    
    console.error('🌐 Creating W3Storage client...');
    const client = await Client({ principal, store });
    
    console.error('📋 Parsing proof...');
    const proof = await Proof.parse(W3UP_PROOF);
    
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

async function uploadToIPFS(jsonData, filename = 'metadata.json') {
    try {
        console.error('📦 Starting uploadToIPFS function...');
        
        const modules = await loadW3StorageModules();
        const { Blob, File } = modules;
        
        console.error('🔧 Getting W3Storage client...');
        const client = await initW3Storage();
        
        console.error('📄 Creating file blob...');
        const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
        const file = new File([blob], filename);
        
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
            
            console.error(`📁 Reading from file: ${inputFile}`);
            
            if (!fs.existsSync(inputFile)) {
                throw new Error(`Input file not found: ${inputFile}`);
            }
            
            const fileContent = fs.readFileSync(inputFile, 'utf8');
            jsonData = JSON.parse(fileContent);
            console.error(`✅ JSON data loaded, size: ${JSON.stringify(jsonData).length} bytes`);
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
        // Output error JSON to stdout for Python to parse
        console.log(JSON.stringify({
            success: false,
            error: error.message
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