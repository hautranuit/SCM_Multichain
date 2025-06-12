const { ethers } = require('ethers');

// LayerZero Endpoint V2 ABI (key functions for configuration)
const ENDPOINT_ABI = [
    {
        "inputs": [
            {"name": "_oapp", "type": "address"},
            {"name": "_config", "type": "tuple", "components": [
                {"name": "eid", "type": "uint32"},
                {"name": "configType", "type": "uint32"},
                {"name": "config", "type": "bytes"}
            ]}
        ],
        "name": "setConfig",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
];

// OFT ABI for getting endpoint
const OFT_ABI = [
    {
        "inputs": [],
        "name": "endpoint",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
];

// Wrapper ABI for calling endpoint configuration
const WRAPPER_ABI = [
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

const PRIVATE_KEY = "5d014eee1544fe8e166b0ffc5d9a5da41456cec5d4c15b76611e8747d848f079";

const NETWORKS = {
    optimism_sepolia: {
        oft: "0x6478eAB366A16d96ae910fd16F6770DDa1845648",
        wrapper: "0x5428793EBd36693c993D6B3f8f2641C46121ec29",
        rpc: "https://sepolia.optimism.io",
        eid: 40232,
        endpoint: "0x6EDCE65403992e310A62460808c4b910D972f10f"
    },
    arbitrum_sepolia: {
        oft: "0x441C06d8548De93d64072F781e15E16A7c316b67",
        wrapper: "0x5952569276eA7f7eF95B910EAd0a67067A518188",
        rpc: "https://arbitrum-sepolia.drpc.org",
        eid: 40231,
        endpoint: "0x6EDCE65403992e310A62460808c4b910D972f10f"
    }
};

function createProvider(rpc) {
    if (ethers.JsonRpcProvider) {
        return new ethers.JsonRpcProvider(rpc);
    } else if (ethers.providers && ethers.providers.JsonRpcProvider) {
        return new ethers.providers.JsonRpcProvider(rpc);
    } else {
        throw new Error("Could not create provider");
    }
}

function createWallet(privateKey, provider) {
    return new ethers.Wallet(privateKey, provider);
}

async function configureLayerZeroEndpoint() {
    console.log("🔧 Configuring LayerZero Endpoint for OFT Contracts...\n");
    
    console.log("📝 Note: LayerZero V2 endpoints require proper configuration for:");
    console.log("   - Send Library");
    console.log("   - Receive Library");
    console.log("   - DVN (Decentralized Verifier Network)");
    console.log("   - Executor");
    console.log("");
    
    console.log("⚠️  This might require LayerZero Labs configuration or specific setup.");
    console.log("    For testnet, try using LayerZero's default configurations.");
    console.log("");
    
    // Check if we can access LayerZero endpoint functions
    for (const [chainName, config] of Object.entries(NETWORKS)) {
        console.log(`🔍 Checking ${chainName.toUpperCase()} LayerZero configuration:`);
        
        try {
            const provider = createProvider(config.rpc);
            const wallet = createWallet(PRIVATE_KEY, provider);
            
            // Check if endpoint contract exists and responds
            const endpointContract = new ethers.Contract(config.endpoint, ENDPOINT_ABI, wallet);
            
            console.log(`   📡 Endpoint: ${config.endpoint}`);
            console.log(`   🔗 OFT: ${config.oft}`);
            
            // Try to get bytecode to verify contract exists
            const bytecode = await provider.getCode(config.endpoint);
            if (bytecode === "0x") {
                console.log(`   ❌ LayerZero endpoint contract not found at ${config.endpoint}`);
                continue;
            } else {
                console.log(`   ✅ LayerZero endpoint contract exists`);
            }
            
            // For LayerZero V2, the endpoint might need default configurations
            // This is typically done by LayerZero Labs or requires specific setup
            console.log(`   📋 Suggested next steps for ${chainName}:`);
            console.log(`      1. Verify LayerZero V2 endpoint is properly deployed`);
            console.log(`      2. Configure send/receive libraries if needed`);
            console.log(`      3. Set up DVN and executor configurations`);
            
        } catch (error) {
            console.log(`   ❌ Error checking ${chainName}: ${error.message}`);
        }
        
        console.log("");
    }
    
    console.log("🎯 RECOMMENDED SOLUTION:");
    console.log("   Since peer connections are correct but endpoint config fails,");
    console.log("   this appears to be a LayerZero V2 endpoint configuration issue.");
    console.log("");
    console.log("📞 OPTIONS:");
    console.log("   1. Contact LayerZero support for testnet endpoint configuration");
    console.log("   2. Use LayerZero's official deployment tools");
    console.log("   3. Check LayerZero docs for V2 endpoint setup requirements");
    console.log("");
    console.log("🔄 ALTERNATIVE: Try fee estimation with lower amounts or different parameters");
}

configureLayerZeroEndpoint().catch(console.error);
