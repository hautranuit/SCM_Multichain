/**
 * Debug ChainFLIP Messenger Contract
 * Check ownership and setPeer function availability
 */

const { ethers } = require("hardhat");

// Contract addresses from environment
const MESSENGER_ADDRESSES = {
    baseSepolia: process.env.DIRECT_MESSENGER_BASE_SEPOLIA,
    optimismSepolia: process.env.DIRECT_MESSENGER_OP_SEPOLIA,
    arbitrumSepolia: process.env.DIRECT_MESSENGER_ARBITRUM_SEPOLIA,
    amoy: process.env.DIRECT_MESSENGER_POLYGON_AMOY
};

// Extended ABI with OApp functions
const MESSENGER_ABI = [
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "_eid", "type": "uint32"}
        ],
        "name": "peers",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "_eid", "type": "uint32"},
            {"name": "_peer", "type": "bytes32"}
        ],
        "name": "setPeer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "endpoint",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
];

async function main() {
    console.log("🔍 Debugging ChainFLIP Messenger Contract...");
    
    const [deployer] = await ethers.getSigners();
    const deployerAddress = await deployer.getAddress();
    
    // Detect current network
    const network = await ethers.provider.getNetwork();
    const chainId = Number(network.chainId);
    
    let currentNetwork;
    if (chainId === 84532) currentNetwork = "baseSepolia";
    else if (chainId === 11155420) currentNetwork = "optimismSepolia";
    else if (chainId === 421614) currentNetwork = "arbitrumSepolia";
    else if (chainId === 80002) currentNetwork = "amoy";
    else throw new Error(`❌ Unsupported network. Chain ID: ${chainId}`);
    
    console.log(`\n🌐 Current Network: ${currentNetwork} (Chain ID: ${chainId})`);
    console.log(`🔑 Deployer: ${deployerAddress}`);
    
    const messengerAddress = MESSENGER_ADDRESSES[currentNetwork];
    if (!messengerAddress) {
        throw new Error(`No messenger contract configured for ${currentNetwork}`);
    }
    
    console.log(`📄 Messenger Contract: ${messengerAddress}`);
    
    // Initialize contract
    const messengerContract = new ethers.Contract(messengerAddress, MESSENGER_ABI, deployer);
    
    try {
        console.log("\n📋 Contract Information:");
        
        // Check owner
        const owner = await messengerContract.owner();
        console.log(`   👑 Owner: ${owner}`);
        console.log(`   🔒 Deployer is owner: ${owner.toLowerCase() === deployerAddress.toLowerCase()}`);
        
        // Check endpoint
        try {
            const endpoint = await messengerContract.endpoint();
            console.log(`   🌐 LayerZero Endpoint: ${endpoint}`);
        } catch (e) {
            console.log(`   ⚠️ Could not get endpoint: ${e.message}`);
        }
        
        // Check existing peers
        console.log("\n🔗 Current Peer Connections:");
        const eids = [40245, 40232, 40231, 40267]; // Base, OP, Arbitrum, Polygon
        const eidNames = ["Base Sepolia", "OP Sepolia", "Arbitrum Sepolia", "Polygon Amoy"];
        
        for (let i = 0; i < eids.length; i++) {
            try {
                const peer = await messengerContract.peers(eids[i]);
                const isEmpty = peer === "0x0000000000000000000000000000000000000000000000000000000000000000";
                console.log(`   EID ${eids[i]} (${eidNames[i]}): ${isEmpty ? "NOT SET" : peer}`);
            } catch (e) {
                console.log(`   EID ${eids[i]} (${eidNames[i]}): ERROR - ${e.message}`);
            }
        }
        
        // Test setPeer function availability (dry run)
        console.log("\n🧪 Testing setPeer Function:");
        try {
            // Try to estimate gas for setPeer call (without actually sending)
            const testPeer = ethers.utils.hexZeroPad("0x1234567890abcdef1234567890abcdef12345678", 32);
            const gasEstimate = await messengerContract.estimateGas.setPeer(40232, testPeer);
            console.log(`   ✅ setPeer function available (Gas estimate: ${gasEstimate})`);
        } catch (e) {
            console.log(`   ❌ setPeer function error: ${e.message}`);
            
            // Additional debug info
            if (e.message.includes("Ownable")) {
                console.log(`   🔍 Ownership issue detected`);
            } else if (e.message.includes("setPeer")) {
                console.log(`   🔍 Function exists but call failed`);
            } else {
                console.log(`   🔍 Unknown error type`);
            }
        }
        
    } catch (error) {
        console.log(`❌ Contract interaction failed: ${error.message}`);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(`❌ Debug failed: ${error.message}`);
        process.exit(1);
    });
