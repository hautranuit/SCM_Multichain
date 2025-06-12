// Official LayerZero V2 OFT Peer Connection Setup
// Configure peer connections between deployed OFT contracts

const { ethers } = require("hardhat");

// Contract addresses (UPDATED WITH NEW DEPLOYED ADDRESSES - V2 WITH DEPOSIT/WITHDRAW)
const DEPLOYED_CONTRACTS = {
    optimismSepolia: "0x25409B7ee450493248fD003A759304FF7f748c53",
    arbitrumSepolia: "0x75d2E18211390A8f2bdA96BB4Bd2D45ba77d5baD",
    amoy: "0x9f57e36F79aD26421A6aE29AC0f2AD67430d8608",
    cardona: "0x47FaF4084F4F69b705A6f947f020B59AA1993FD9"
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
    console.log("✨ NEW CONTRACTS WITH DEPOSIT/WITHDRAW FUNCTIONALITY");
    
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
    let oft;
    try {
        const RealChainFlipOFT = await ethers.getContractFactory("RealChainFlipOFT");
        oft = RealChainFlipOFT.attach(currentContractAddress);
        console.log(`   ✅ Connected to RealChainFlipOFT contract`);
    } catch (error) {
        console.log(`❌ Contract factory 'RealChainFlipOFT' not found: ${error.message}`);
        console.log("Make sure your contract is compiled: npx hardhat compile");
        return;
    }
    
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
    
    console.log("\n✨ NEW FEATURES AVAILABLE:");
    console.log("   • Users can deposit ETH → get cfWETH tokens");
    console.log("   • Users can withdraw cfWETH → get ETH back");
    console.log("   • No more minting restrictions!");
    console.log("   • True decentralized ETH bridging");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
