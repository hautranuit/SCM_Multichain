// Set Peer Connections for ChainFLIP Messenger V2 Contracts
// This script establishes peer connections between ChainFLIP Messenger contracts
// across all 4 testnets for proper LayerZero V2 messaging

const { ethers } = require("hardhat");

// ChainFLIP Messenger V2 Contract addresses (✅ DEPLOYED)
const MESSENGER_CONTRACTS = {
    "baseSepolia": "0xf333Ee4fD3D249AB7C38441a10C5848aE83a7Fbb",      // ✅ DEPLOYED
    "optimismSepolia": "0x31B2caa2F6E713B66d854fEd5770971a87C5f11C",  // ✅ DEPLOYED
    "arbitrumSepolia": "0xD9EB50e5F977210AA3C5A46B9918003e640A3032",  // ✅ DEPLOYED
    "amoy": "0x96922C50cB3dB61BA7663dc32d9d1796eE9E8fF4"             // ✅ DEPLOYED
};

// LayerZero V2 EIDs
const LAYERZERO_EIDS = {
    "baseSepolia": 40245,
    "optimismSepolia": 40232,
    "arbitrumSepolia": 40231,
    "amoy": 40267
};

// Messenger ABI - only the functions we need
const MESSENGER_ABI = [
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
        "inputs": [
            {"name": "_eid", "type": "uint32"}
        ],
        "name": "peers",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
];

async function main() {
    console.log("🔗 Setting LayerZero V2 Peers on ChainFLIP Messenger V2 Contracts");
    console.log("✨ Peer connections for cross-chain CID messaging");
    
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
    
    // Get current network Messenger contract
    const currentMessengerAddress = MESSENGER_CONTRACTS[currentNetwork];
    if (!currentMessengerAddress || currentMessengerAddress === "0x0000000000000000000000000000000000000000") {
        throw new Error(`No Messenger contract configured for network: ${currentNetwork}`);
    }
    
    console.log(`   Messenger Contract: ${currentMessengerAddress}`);
    
    // Initialize Messenger contract
    const messengerContract = new ethers.Contract(currentMessengerAddress, MESSENGER_ABI, deployer);
    
    try {
        const owner = await messengerContract.owner();
        console.log(`   ✅ Connected to Messenger contract`);
        console.log(`   👑 Contract Owner: ${owner}`);
        
        if (owner.toLowerCase() !== deployerAddress.toLowerCase()) {
            console.log(`   ⚠️ Warning: Deployer is not contract owner`);
        }
    } catch (error) {
        console.log(`   ❌ Failed to connect to Messenger contract: ${error.message}`);
        return;
    }
    
    console.log(`\n🔗 Setting peer connections on Messenger contract...`);
    
    // Set peer for each other network
    for (const [networkName, messengerAddress] of Object.entries(MESSENGER_CONTRACTS)) {
        if (networkName === currentNetwork) continue; // Skip self
        
        if (messengerAddress === "0x0000000000000000000000000000000000000000") {
            console.log(`   ⚠️ Skipping ${networkName}: Contract not deployed yet`);
            continue;
        }
        
        const targetEid = LAYERZERO_EIDS[networkName];
        console.log(`\n   🎯 Setting peer for ${networkName}:`);
        console.log(`   EID: ${targetEid}`);
        console.log(`   Messenger Address: ${messengerAddress}`);
        
        // Convert address to bytes32 (LayerZero V2 format)
        const peerBytes32 = ethers.utils.hexZeroPad(messengerAddress, 32);
        console.log(`   Peer (bytes32): ${peerBytes32}`);
        
        try {
            // Set the peer
            const tx = await messengerContract.setPeer(targetEid, peerBytes32);
            console.log(`   📤 Transaction sent: ${tx.hash}`);
            
            const receipt = await tx.wait();
            console.log(`   ✅ Peer set for ${networkName} (Gas used: ${receipt.gasUsed})`);
        } catch (error) {
            console.log(`   ❌ Failed to set peer for ${networkName}: ${error.message}`);
        }
    }
    
    console.log(`\n🔍 Verifying peer connections...`);
    
    // Verify all peer connections
    for (const [networkName, messengerAddress] of Object.entries(MESSENGER_CONTRACTS)) {
        if (networkName === currentNetwork) continue; // Skip self
        
        if (messengerAddress === "0x0000000000000000000000000000000000000000") {
            continue; // Skip undeployed
        }
        
        const targetEid = LAYERZERO_EIDS[networkName];
        
        try {
            const setPeer = await messengerContract.peers(targetEid);
            const expectedPeer = ethers.utils.hexZeroPad(messengerAddress, 32);
            
            if (setPeer === expectedPeer) {
                console.log(`   ✅ ${networkName} (EID ${targetEid}): Peer verified`);
            } else {
                console.log(`   ❌ ${networkName} (EID ${targetEid}): Peer mismatch`);
                console.log(`      Expected: ${expectedPeer}`);
                console.log(`      Got: ${setPeer}`);
            }
        } catch (error) {
            console.log(`   ⚠️ ${networkName} (EID ${targetEid}): Verification failed - ${error.message}`);
        }
    }
    
    console.log(`\n✅ Peer connection setup complete for ${currentNetwork}!`);
    console.log(`\n🎯 Next Steps:`);
    console.log(`   1. Update MESSENGER_CONTRACTS addresses in this script with actual deployed addresses`);
    console.log(`   2. Run this script on each network after all contracts are deployed`);
    console.log(`   3. Update Python backend service with new contract addresses`);
    console.log(`   4. Test cross-chain CID messaging functionality`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(`❌ Peer setup failed: ${error.message}`);
        process.exit(1);
    });
