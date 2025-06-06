#!/usr/bin/env node

/*
 * W3Storage Upload Script for Python Backend
 * This Node.js script handles IPFS uploads using w3up client
 */

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

// Import w3up client modules
let Client, StoreMemory, Proof, Signer, Blob, File;

try {
    ({ create: Client, StoreMemory } = createRequire(import.meta.url)('@web3-storage/w3up-client'));
    ({ StoreMemory } = createRequire(import.meta.url)('@web3-storage/w3up-client/stores/memory'));
    Proof = createRequire(import.meta.url)('@web3-storage/w3up-client/proof');
    ({ Signer } = createRequire(import.meta.url)('@web3-storage/w3up-client/principal/ed25519'));
    ({ Blob, File } = createRequire(import.meta.url)('@web-std/file'));
} catch (error) {
    console.error('Error importing w3up modules:', error.message);
    console.error('Please run: npm install @web3-storage/w3up-client @web-std/file');
    process.exit(1);
}

async function initW3Storage() {
    const W3UP_KEY = process.env.W3STORAGE_TOKEN;
    const W3UP_PROOF = process.env.W3STORAGE_PROOF;
    
    if (!W3UP_KEY || !W3UP_PROOF) {
        throw new Error('Missing W3STORAGE_TOKEN or W3STORAGE_PROOF environment variables');
    }
    
    const principal = Signer.parse(W3UP_KEY);
    const store = new StoreMemory();
    const client = await Client({ principal, store });
    const proof = await Proof.parse(W3UP_PROOF);
    
    try {
        const space = await client.addSpace(proof);
        await client.setCurrentSpace(space.did());
        console.log('✅ W3Storage client initialized and space set');
    } catch (err) {
        if (err.message.includes('space already registered')) {
            console.warn('⚠️ W3Storage space already registered. Setting current space.');
            const spaces = await client.spaces();
            if (spaces.length > 0) {
                await client.setCurrentSpace(spaces[0].did());
                console.log(`✅ W3Storage current space set to: ${spaces[0].did()}`);
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
        const client = await initW3Storage();
        
        const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
        const file = new File([blob], filename);
        
        const cid = await client.uploadFile(file);
        console.log(`✅ File uploaded successfully. CID: ${cid.toString()}`);
        
        return {
            success: true,
            cid: cid.toString(),
            gateway_url: `https://w3s.link/ipfs/${cid.toString()}`
        };
        
    } catch (error) {
        console.error('❌ Upload failed:', error.message);
        return {
            success: false,
            error: error.message
        };
    }
}

// CLI interface
async function main() {
    try {
        // Read JSON data from stdin or file
        const args = process.argv.slice(2);
        let jsonData;
        let filename = 'metadata.json';
        
        if (args.length >= 1) {
            // Read from file
            const inputFile = args[0];
            if (args[1]) filename = args[1];
            
            if (!fs.existsSync(inputFile)) {
                throw new Error(`Input file not found: ${inputFile}`);
            }
            
            const fileContent = fs.readFileSync(inputFile, 'utf8');
            jsonData = JSON.parse(fileContent);
        } else {
            // Read from stdin
            let input = '';
            for await (const chunk of process.stdin) {
                input += chunk;
            }
            
            if (!input.trim()) {
                throw new Error('No input data provided');
            }
            
            jsonData = JSON.parse(input);
        }
        
        const result = await uploadToIPFS(jsonData, filename);
        console.log(JSON.stringify(result, null, 2));
        
        process.exit(result.success ? 0 : 1);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        console.log(JSON.stringify({
            success: false,
            error: error.message
        }));
        process.exit(1);
    }
}

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}