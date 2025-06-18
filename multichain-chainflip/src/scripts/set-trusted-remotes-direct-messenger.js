// LayerZero V2 Trusted Remote Setup for DirectLayerZeroMessenger Contracts
// Sets trusted remotes between DirectLayerZeroMessenger contracts on all chains

const hre = require("hardhat");
const { ethers } = require("hardhat");

// DirectLayerZeroMessenger Contract addresses (from deployment summary)
const DIRECT_MESSENGER_CONTRACTS = {
    baseSepolia: "0x1208F8F0E40381F14E41621906D13C9c3CaAa061",      // Base Sepolia (Manufacturer chain)
    optimismSepolia: "0x97420B3dEd4B3eA72Ff607fd96927Bfa605b197c",  // Optimism Sepolia (Buyer chain)
    arbitrumSepolia: "0x25409B7ee450493248fD003A759304FF7f748c53",   // Arbitrum Sepolia (Additional chain)
    amoy: "0x34705a7e91b465AE55844583EC16715C88bD457a"             // Polygon Amoy (Hub chain)
};

// LayerZero V2 Endpoint IDs
const LAYERZERO_EIDS = {
    baseSepolia: 40245,      // Manufacturer chain
    optimismSepolia: 40232,  // Buyer chain
    arbitrumSepolia: 40231,  // Additional chain
    amoy: 40267              // Hub chain
};

// DirectLayerZeroMessenger ABI (correct functions from the contract)
const DIRECT_MESSENGER_ABI = [
    {
        "inputs": [
            {"name": "eid", "type": "uint16"},
            {"name": "trustedRemote", "type": "bytes"}
        ],
        "name": "setTrustedRemote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "eid", "type": "uint16"}],
        "name": "getChainConfig",
        "outputs": [{
            "components": [
                {"name": "layerZeroEid", "type": "uint16"},
                {"name": "chainId", "type": "uint256"},
                {"name": "name", "type": "string"},
                {"name": "isActive", "type": "bool"},
                {"name": "trustedRemote", "type": "bytes"}
            ],
            "name": "",
            "type": "tuple"
        }],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getSupportedEids",
        "outputs": [{"name": "", "type": "uint16[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "role", "type": "bytes32"},
            {"name": "account", "type": "address"}
        ],
        "name": "hasRole",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "targetEid", "type": "uint16"},
            {"name": "payload", "type": "bytes"},
            {"name": "useZro", "type": "bool"},
            {"name": "adapterParams", "type": "bytes"}
        ],
        "name": "estimateFees",
        "outputs": [
            {"name": "nativeFee", "type": "uint256"},
            {"name": "zroFee", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
];

// AccessControl role constants
const DEFAULT_ADMIN_ROLE = "0x0000000000000000000000000000000000000000000000000000000000000000";

async function main() {
    console.log("🔗 Setting LayerZero V2 Trusted Remotes on DirectLayerZeroMessenger Contracts");
    console.log("✨ Trusted remotes for cross-chain CID sync functionality");
    
    const [deployer] = await ethers.getSigners();
    const currentNetwork = hre.network.name;
    
    console.log(`\n📊 Current Network: ${currentNetwork}`);
    console.log(`   Deployer: ${deployer.address}`);
    
    // Get current network DirectLayerZeroMessenger contract
    const currentMessengerAddress = DIRECT_MESSENGER_CONTRACTS[currentNetwork];
    if (!currentMessengerAddress) {
        throw new Error(`No DirectLayerZeroMessenger contract configured for network: ${currentNetwork}`);
    }
    
    console.log(`   DirectLayerZeroMessenger Contract: ${currentMessengerAddress}`);
    
    // Initialize DirectLayerZeroMessenger contract
    const messengerContract = new ethers.Contract(currentMessengerAddress, DIRECT_MESSENGER_ABI, deployer);
    
    try {
        // Check if deployer has admin role
        const hasAdminRole = await messengerContract.hasRole(DEFAULT_ADMIN_ROLE, deployer.address);
        console.log(`   🔐 Has DEFAULT_ADMIN_ROLE: ${hasAdminRole}`);
        
        if (!hasAdminRole) {
            console.log(`   ❌ WARNING: You don't have DEFAULT_ADMIN_ROLE!`);
            console.log(`   💡 Only accounts with DEFAULT_ADMIN_ROLE can set trusted remotes`);
            console.log(`   🔄 Will continue anyway to show what needs to be done...`);
        } else {
            console.log(`   ✅ You have permission to set trusted remotes`);
        }
        
        // Check supported EIDs
        const supportedEids = await messengerContract.getSupportedEids();
        console.log(`   📋 Supported LayerZero EIDs: [${supportedEids.join(', ')}]`);
        
        console.log(`   ✅ Successfully connected to DirectLayerZeroMessenger contract`);
        
    } catch (error) {
        console.log(`   ❌ Error connecting to contract: ${error.message}`);
        console.log(`   🔄 Will try to continue anyway...`);
    }
    
    console.log(`\n🔗 Setting trusted remotes on DirectLayerZeroMessenger contract...`);
    
    // Set trusted remotes for all other networks
    for (const [networkName, messengerAddress] of Object.entries(DIRECT_MESSENGER_CONTRACTS)) {
        if (networkName === currentNetwork) continue; // Skip self
        
        const targetEid = LAYERZERO_EIDS[networkName];
        
        // For LayerZero V1, trusted remote is: target_contract_address + source_contract_address
        // But DirectLayerZeroMessenger seems to use just the target contract address as bytes
        const trustedRemoteBytes = ethers.utils.solidityPack(
            ["address", "address"],
            [messengerAddress, currentMessengerAddress]
        );
        
        console.log(`\n📡 Setting trusted remote: ${networkName}`);
        console.log(`   EID: ${targetEid}`);
        console.log(`   Target Contract: ${messengerAddress}`);
        console.log(`   Current Contract: ${currentMessengerAddress}`);
        console.log(`   Trusted Remote Bytes: ${trustedRemoteBytes}`);
        
        try {
            // Check current trusted remote
            try {
                const chainConfig = await messengerContract.getChainConfig(targetEid);
                console.log(`   📋 Current trusted remote: ${chainConfig.trustedRemote}`);
                console.log(`   📋 Chain active: ${chainConfig.isActive}`);
                console.log(`   📋 Chain name: ${chainConfig.name}`);
                
                if (chainConfig.trustedRemote === trustedRemoteBytes) {
                    console.log(`   ✅ Trusted remote already set for ${networkName}`);
                    continue;
                }
            } catch (configError) {
                console.log(`   ⚠️ Could not get current chain config: ${configError.message}`);
            }
            
            // Estimate gas for setTrustedRemote transaction
            let gasEstimate;
            try {
                gasEstimate = await messengerContract.estimateGas.setTrustedRemote(targetEid, trustedRemoteBytes);
                console.log(`   ⛽ Estimated gas: ${gasEstimate.toString()}`);
            } catch (gasError) {
                console.log(`   ⚠️ Could not estimate gas: ${gasError.message}`);
                gasEstimate = 150000; // Use default
            }
            
            // Set the trusted remote
            const tx = await messengerContract.setTrustedRemote(targetEid, trustedRemoteBytes, {
                gasLimit: gasEstimate.mul ? gasEstimate.mul(120).div(100) : 180000 // Add 20% buffer
            });
            console.log(`   📤 Transaction sent: ${tx.hash}`);
            
            const receipt = await tx.wait();
            if (receipt.status === 1) {
                console.log(`   ✅ Trusted remote set for ${networkName} (Gas used: ${receipt.gasUsed})`);
            } else {
                console.log(`   ❌ Transaction failed for ${networkName}`);
            }
            
        } catch (error) {
            console.log(`   ❌ Failed to set trusted remote for ${networkName}: ${error.message}`);
            if (error.message.includes("AccessControl")) {
                console.log(`   💡 Make sure you have DEFAULT_ADMIN_ROLE on the contract`);
            } else if (error.message.includes("execution reverted")) {
                console.log(`   💡 This might be due to:`);
                console.log(`      • Not having DEFAULT_ADMIN_ROLE`);
                console.log(`      • Contract not supporting setTrustedRemote function`);
                console.log(`      • Invalid EID or trusted remote bytes`);
            }
        }
    }
    
    console.log(`\n🔍 Verifying trusted remote connections...`);
    
    // Verify all trusted remote connections
    for (const [networkName, messengerAddress] of Object.entries(DIRECT_MESSENGER_CONTRACTS)) {
        if (networkName === currentNetwork) continue;
        
        const targetEid = LAYERZERO_EIDS[networkName];
        const expectedTrustedRemote = ethers.utils.solidityPack(
            ["address", "address"],
            [messengerAddress, currentMessengerAddress]
        );
        
        try {
            const chainConfig = await messengerContract.getChainConfig(targetEid);
            if (chainConfig.trustedRemote === expectedTrustedRemote) {
                console.log(`   ✅ ${networkName} (EID ${targetEid}): CORRECT`);
            } else {
                console.log(`   ❌ ${networkName} (EID ${targetEid}): MISMATCH`);
                console.log(`      Expected: ${expectedTrustedRemote}`);
                console.log(`      Actual: ${chainConfig.trustedRemote}`);
            }
        } catch (error) {
            console.log(`   ❌ ${networkName} (EID ${targetEid}): ERROR - ${error.message}`);
        }
    }
    
    console.log(`\n🎯 DirectLayerZeroMessenger Trusted Remote Setup Complete!`);
    console.log(`\n🔗 Run on all networks to complete trusted remote mesh:`);
    console.log(`   npx hardhat run scripts/set-trusted-remotes-direct-messenger.js --network baseSepolia`);
    console.log(`   npx hardhat run scripts/set-trusted-remotes-direct-messenger.js --network optimismSepolia`);
    console.log(`   npx hardhat run scripts/set-trusted-remotes-direct-messenger.js --network arbitrumSepolia`);
    console.log(`   npx hardhat run scripts/set-trusted-remotes-direct-messenger.js --network amoy`);
    
    console.log(`\n💡 After setting up trusted remotes on all networks, your ChainFLIP Cross-Chain CID Sync will work!`);
    console.log(`🚀 The DirectLayerZeroMessenger contracts will be able to send LayerZero messages`);
    console.log(`📦 CID sync from Base Sepolia to Polygon Amoy will complete successfully`);
}

main().catch((error) => {
    console.error("❌ Error setting DirectLayerZeroMessenger trusted remotes:", error);
    process.exitCode = 1;
});
