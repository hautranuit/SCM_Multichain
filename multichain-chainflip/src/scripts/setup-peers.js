/**
 * ChainFLIP Cross-Chain NFT Bridge - LayerZero Peer Setup
 * 
 * This script sets up LayerZero peer connections between DirectLayerZeroMessenger contracts
 * on all supported networks for cross-chain NFT transfers.
 * 
 * Note: This script operates on DirectLayerZeroMessenger contracts (NOT the NFT contracts).
 * The NFT contracts are regular ERC721 without LayerZero functionality.
 * 
 * Usage:
 *   npx hardhat run scripts/setup-peers.js --network baseSepolia
 *   npx hardhat run scripts/setup-peers.js --network optimismSepolia
 *   npx hardhat run scripts/setup-peers.js --network arbitrumSepolia
 *   npx hardhat run scripts/setup-peers.js --network amoy
 */

/**
 * ChainFLIP Cross-Chain NFT Bridge - LayerZero Peer Setup
 * 
 * This script sets up LayerZero peer connections between DirectLayerZeroMessenger contracts
 * on all supported networks for cross-chain NFT transfers.
 * 
 * Note: This script operates on DirectLayerZeroMessenger contracts (NOT the NFT contracts).
 * The NFT contracts are regular ERC721 without LayerZero functionality.
 * 
 * Usage:
 *   npx hardhat run scripts/setup-peers.js --network baseSepolia
 *   npx hardhat run scripts/setup-peers.js --network optimismSepolia
 *   npx hardhat run scripts/setup-peers.js --network arbitrumSepolia
 *   npx hardhat run scripts/setup-peers.js --network amoy
 */

const { ethers } = require("hardhat");
const fs = require('fs');
const path = require('path');

// LayerZero Endpoint IDs for each network
const LAYER_ZERO_EIDS = {
    baseSepolia: 40245,
    optimismSepolia: 40232,
    arbitrumSepolia: 40231,
    amoy: 40267
};

// Network configurations - Updated to use DirectLayerZeroMessenger contracts
const NETWORKS = {
    baseSepolia: {
        name: "Base Sepolia",
        chainId: 84532,
        envKey: "DIRECT_MESSENGER_BASE_SEPOLIA",
        lzEid: LAYER_ZERO_EIDS.baseSepolia
    },
    optimismSepolia: {
        name: "OP Sepolia", 
        chainId: 11155420,
        envKey: "DIRECT_MESSENGER_OP_SEPOLIA",
        lzEid: LAYER_ZERO_EIDS.optimismSepolia
    },
    arbitrumSepolia: {
        name: "Arbitrum Sepolia",
        chainId: 421614,
        envKey: "DIRECT_MESSENGER_ARBITRUM_SEPOLIA",
        lzEid: LAYER_ZERO_EIDS.arbitrumSepolia
    },
    amoy: {
        name: "Polygon Amoy",
        chainId: 80002,
        envKey: "DIRECT_MESSENGER_POLYGON_AMOY",
        lzEid: LAYER_ZERO_EIDS.amoy
    }
};

// Simple ABI for setPeer function
const SET_PEER_ABI = [
    {
        "inputs": [
            {"name": "_eid", "type": "uint32"},
            {"name": "_peer", "type": "bytes32"}
        ],
        "name": "setPeer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
];

async function setPeerForNetwork(networkName, contractAddress) {
    console.log(`Setting up peer connections for ${NETWORKS[networkName].name}...`);
    
    const [deployer] = await ethers.getSigners();
    console.log("Using account:", deployer.address);
    
    // Get contract instance
    const contract = await ethers.getContractAt(SET_PEER_ABI, contractAddress);
    
    // Set peers for all other networks
    for (const [peerNetwork, peerConfig] of Object.entries(NETWORKS)) {
        if (peerNetwork === networkName) {
            continue; // Skip self
        }
        
        const peerContractAddress = process.env[peerConfig.envKey];
        if (!peerContractAddress) {
            console.log(`No contract address found for ${peerConfig.name}`);
            continue;
        }
        
        try {
            // Convert contract address to bytes32 for LayerZero
            const peerBytes32 = ethers.utils.hexZeroPad(peerContractAddress, 32);
            
            console.log(`Setting peer for ${peerConfig.name}:`);
            console.log(`   EID: ${peerConfig.lzEid}`);
            console.log(`   Peer Address: ${peerContractAddress}`);
            
            // Call setPeer function
            const tx = await contract.setPeer(peerConfig.lzEid, peerBytes32, {
                gasLimit: 200000
            });
            
            console.log(`Transaction sent: ${tx.hash}`);
            await tx.wait();
            console.log(`Peer set successfully for ${peerConfig.name}`);
            
        } catch (error) {
            console.error(`Failed to set peer for ${peerConfig.name}:`, error.message);
        }
    }
}

async function main() {
    console.log("Setting up LayerZero peer connections for ChainFLIP DirectLayerZeroMessenger contracts...");
    console.log("Note: Using Messenger contracts (NOT NFT contracts) for LayerZero functionality");
    
    // Display network information
    for (const [networkName, config] of Object.entries(NETWORKS)) {
        const contractAddress = process.env[config.envKey];
        console.log(`${config.name}: ${contractAddress || 'NOT_DEPLOYED'} (EID: ${config.lzEid})`);
    }
    
    // Check current network and set peers
    const networkName = network.name;
    const currentNetworkConfig = NETWORKS[networkName];
    
    if (!currentNetworkConfig) {
        throw new Error(`Unsupported network: ${networkName}`);
    }
    
    const contractAddress = process.env[currentNetworkConfig.envKey];
    if (!contractAddress) {
        throw new Error(`No contract address found for ${currentNetworkConfig.name}`);
    }
    
    console.log(`Current network: ${currentNetworkConfig.name}`);
    console.log(`Contract address: ${contractAddress}`);
    
    await setPeerForNetwork(networkName, contractAddress);
    
    console.log(`Peer connections setup completed for ${currentNetworkConfig.name}!`);
}

module.exports = { main, setPeerForNetwork };

if (require.main === module) {
    main()
        .then(() => {
            console.log("Peer setup completed!");
            process.exit(0);
        })
        .catch((error) => {
            console.error("Peer setup failed:", error);
            process.exit(1);
        });
}
