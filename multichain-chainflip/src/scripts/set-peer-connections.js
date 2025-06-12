// Official LayerZero V2 OFT Peer Connection Setup
// Configure peer connections between deployed OFT contracts

const { ethers } = require("hardhat");

// Contract addresses (UPDATE AFTER DEPLOYMENT)
const DEPLOYED_CONTRACTS = {
    optimismSepolia: "", // Fill after deployment
    arbitrumSepolia: "", // Fill after deployment  
    amoy: "",            // Fill after deployment
    cardona: ""          // Fill after deployment
};

// Official LayerZero V2 Endpoint IDs
const LAYERZERO_EIDS = {
    optimismSepolia: 40232,
    arbitrumSepolia: 40231,
    amoy: 40267,
    cardona: 40158
};

// Convert address to bytes32 (for LayerZero peer setting)
function addressToBytes32(address) {
    return ethers.zeroPadValue(address.toLowerCase(), 32);
}

async function main() {
    console.log("🔗 Setting up Official LayerZero V2 OFT Peer Connections...");
    
    const [deployer] = await ethers.getSigners();
    const currentNetwork = hre.network.name;
    
    console.log(`\n📊 Current Network: ${currentNetwork}`);
    console.log(`   Deployer: ${deployer.address}`);
    
    // Get current contract address
    const currentContractAddress = DEPLOYED_CONTRACTS[currentNetwork];
    if (!currentContractAddress) {
        console.log(`❌ No contract address configured for ${currentNetwork}`);
        console.log("Please update DEPLOYED_CONTRACTS with your deployed addresses");
        return;
    }
    
    console.log(`   Current Contract: ${currentContractAddress}`);
    
    // Get contract instance
    const ChainFlipOFT = await ethers.getContractFactory("ChainFlipOFT");
    const oft = ChainFlipOFT.attach(currentContractAddress);
    
    // Set peers for all other networks
    console.log("\n🔗 Setting peer connections...");
    
    for (const [networkName, contractAddress] of Object.entries(DEPLOYED_CONTRACTS)) {
        if (networkName === currentNetwork || !contractAddress) {
            continue; // Skip current network and empty addresses
        }
        
        const peerEid = LAYERZERO_EIDS[networkName];
        const peerBytes32 = addressToBytes32(contractAddress);
        
        console.log(`\n📡 Setting peer: ${networkName}`);
        console.log(`   EID: ${peerEid}`);
        console.log(`   Address: ${contractAddress}`);
        console.log(`   Bytes32: ${peerBytes32}`);
        
        try {
            // Check if peer is already set
            const currentPeer = await oft.peers(peerEid);
            const isAlreadySet = currentPeer !== "0x0000000000000000000000000000000000000000000000000000000000000000";
            
            if (isAlreadySet) {
                console.log(`   ✅ Peer already set for ${networkName}`);
                continue;
            }
            
            // Set the peer
            const tx = await oft.setPeer(peerEid, peerBytes32);
            console.log(`   📤 Transaction sent: ${tx.hash}`);
            
            const receipt = await tx.wait();
            console.log(`   ✅ Peer set successfully! Gas used: ${receipt.gasUsed.toString()}`);
            
        } catch (error) {
            console.log(`   ❌ Failed to set peer for ${networkName}: ${error.message}`);
        }
    }
    
    // Verify all peer connections
    console.log("\n🔍 Verifying peer connections...");
    for (const [networkName, contractAddress] of Object.entries(DEPLOYED_CONTRACTS)) {
        if (networkName === currentNetwork || !contractAddress) {
            continue;
        }
        
        const peerEid = LAYERZERO_EIDS[networkName];
        const expectedPeerBytes32 = addressToBytes32(contractAddress);
        
        try {
            const actualPeer = await oft.peers(peerEid);
            const isCorrect = actualPeer.toLowerCase() === expectedPeerBytes32.toLowerCase();
            
            console.log(`   ${isCorrect ? '✅' : '❌'} ${networkName} (EID ${peerEid}): ${isCorrect ? 'CORRECT' : 'MISMATCH'}`);
            if (!isCorrect) {
                console.log(`      Expected: ${expectedPeerBytes32}`);
                console.log(`      Actual:   ${actualPeer}`);
            }
        } catch (error) {
            console.log(`   ❌ ${networkName}: Verification failed - ${error.message}`);
        }
    }
    
    console.log("\n🎯 Peer Setup Complete!");
    console.log("Next: Run this script on other networks to set bidirectional connections");
    
    console.log("\n🔗 Commands to run on other networks:");
    Object.keys(DEPLOYED_CONTRACTS).forEach(network => {
        if (network !== currentNetwork) {
            console.log(`   npx hardhat run scripts/set-peer-connections.js --network ${network}`);
        }
    });
    
    console.log("\n⚠️ Important: Update DEPLOYED_CONTRACTS with actual deployed addresses before running!");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });