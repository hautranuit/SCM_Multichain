// LayerZero V2 Peer Connection Setup on Fresh OFT Contracts (UPDATED)
// Sets peer connections directly on ChainFlipOFT contracts with direct deployer ownership

const hre = require("hardhat");
const { ethers } = require("hardhat");

// ChainFlipOFT Contract addresses (UPDATED - Fresh deployments with direct deployer ownership)
const OFT_CONTRACTS = {
    optimismSepolia: "0x76D43CEC28775032A7EC8895ad178c660246c8Ec",     // ✅ Fresh deployment - owned by deployer
    arbitrumSepolia: "0x47FaF4084F4F69b705A6f947f020B59AA1993FD9",     // ✅ Fresh deployment - owned by deployer  
    amoy: "0x36DDc43D2FfA30588CcAC8C2979b69225c292a73",              // ✅ Fresh deployment - owned by deployer
    baseSepolia: "0xdAd142646292A550008B44D968764c52eF1C3f67"          // ✅ Original - working perfectly
};

// LayerZero Endpoint IDs for V2
const LAYERZERO_EIDS = {
    optimismSepolia: 40232,
    arbitrumSepolia: 40231,
    amoy: 40267,
    baseSepolia: 40245
};

// OFT ABI - only the functions we need
const OFT_ABI = [
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
        "inputs": [{"name": "_eid", "type": "uint32"}],
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
    console.log("🔗 Setting LayerZero V2 Peers on OFT Contracts (CORRECTED)");
    console.log("✨ Peer connections set directly on ChainFlipOFT contracts");
    
    const [deployer] = await ethers.getSigners();
    const currentNetwork = hre.network.name;
    
    console.log(`\n📊 Current Network: ${currentNetwork}`);
    console.log(`   Deployer: ${deployer.address}`);
    
    // Get current network OFT contract
    const currentOftAddress = OFT_CONTRACTS[currentNetwork];
    if (!currentOftAddress) {
        throw new Error(`No OFT contract configured for network: ${currentNetwork}`);
    }
    
    console.log(`   OFT Contract: ${currentOftAddress}`);
    
    // Initialize OFT contract
    const oftContract = new ethers.Contract(currentOftAddress, OFT_ABI, deployer);
    
    try {
        const owner = await oftContract.owner();
        console.log(`   Contract Owner: ${owner}`);
        console.log(`   ✅ Connected to OFT contract`);
    } catch (error) {
        console.log(`   ❌ Failed to connect to OFT contract: ${error.message}`);
        return;
    }
    
    console.log(`\n🔗 Setting peer connections on OFT contract...`);
    
    // Set peers for all other networks
    for (const [networkName, oftAddress] of Object.entries(OFT_CONTRACTS)) {
        if (networkName === currentNetwork) continue; // Skip self
        
        const targetEid = LAYERZERO_EIDS[networkName];
        const peerBytes32 = ethers.utils.hexZeroPad(oftAddress.toLowerCase(), 32);
        
        console.log(`\n📡 Setting peer: ${networkName}`);
        console.log(`   EID: ${targetEid}`);
        console.log(`   OFT Address: ${oftAddress}`);
        console.log(`   Bytes32: ${peerBytes32}`);
        
        try {
            // Check if peer is already set
            const existingPeer = await oftContract.peers(targetEid);
            if (existingPeer === peerBytes32) {
                console.log(`   ✅ Peer already set for ${networkName}`);
                continue;
            }
            
            // Set the peer
            const tx = await oftContract.setPeer(targetEid, peerBytes32);
            console.log(`   📤 Transaction sent: ${tx.hash}`);
            
            const receipt = await tx.wait();
            console.log(`   ✅ Peer set for ${networkName} (Gas used: ${receipt.gasUsed})`);
            
        } catch (error) {
            console.log(`   ❌ Failed to set peer for ${networkName}: ${error.message}`);
        }
    }
    
    console.log(`\n🔍 Verifying peer connections...`);
    
    // Verify all peer connections
    for (const [networkName, oftAddress] of Object.entries(OFT_CONTRACTS)) {
        if (networkName === currentNetwork) continue;
        
        const targetEid = LAYERZERO_EIDS[networkName];
        const expectedPeer = ethers.utils.hexZeroPad(oftAddress.toLowerCase(), 32);
        
        try {
            const actualPeer = await oftContract.peers(targetEid);
            if (actualPeer === expectedPeer) {
                console.log(`   ✅ ${networkName} (EID ${targetEid}): CORRECT`);
            } else {
                console.log(`   ❌ ${networkName} (EID ${targetEid}): MISMATCH`);
                console.log(`      Expected: ${expectedPeer}`);
                console.log(`      Actual: ${actualPeer}`);
            }
        } catch (error) {
            console.log(`   ❌ ${networkName} (EID ${targetEid}): ERROR - ${error.message}`);
        }
    }
    
    console.log(`\n🎯 Peer Setup Complete!`);
    console.log(`\n🔗 Run on other networks:`);
    console.log(`   npx hardhat run scripts/set-peer-connections-oft.js --network optimismSepolia`);
    console.log(`   npx hardhat run scripts/set-peer-connections-oft.js --network arbitrumSepolia`);
    console.log(`   npx hardhat run scripts/set-peer-connections-oft.js --network amoy`);
    console.log(`   npx hardhat run scripts/set-peer-connections-oft.js --network baseSepolia`);
}

main().catch((error) => {
    console.error("❌ Error setting peer connections:", error);
    process.exitCode = 1;
});
