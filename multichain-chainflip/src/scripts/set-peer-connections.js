// LayerZero V2 OFT Peer Connection Setup for Separated Architecture
// Configure peer connections between ChainFlipOFT contracts (for cross-chain transfers)
// ETHWrapper contracts handle deposit/withdraw on each chain

const { ethers } = require("hardhat");

// ChainFlipOFT Contract addresses (For LayerZero cross-chain transfers)
const OFT_CONTRACTS = {
    optimismSepolia: "0x2c97B9855D7096348aeAdc3e67f93B93828f91b3",
    arbitrumSepolia: "0xd14651Bc6DFb5B3bf42027A715F37C47C061239c", 
    amoy: "0xCC2d10e405096f40ea658C493625f15bE22A942F"
    // cardona: Will be replaced with a better supported network
};

// ETHWrapper Contract addresses (For ETH deposit/withdraw)
const WRAPPER_CONTRACTS = {
    optimismSepolia: "0x2AeF441a83347b9370511437D475bc028745FC5F",
    arbitrumSepolia: "0x42F6D4BFD27330865C7F32De63301a27b6dD65FC",
    amoy: "0x9E4B5C5EcD7f80064c7061Ef6871078702E2DC56"
    // cardona: Will be replaced with a better supported network
};

// Official LayerZero V2 Endpoint IDs (Cardona removed due to poor support)
const LAYERZERO_EIDS = {
    optimismSepolia: 40232,
    arbitrumSepolia: 40231,
    amoy: 40267
    // cardona: 40158 - Removed due to LayerZero V2 compatibility issues
};

// Convert address to bytes32 (for LayerZero peer setting) - Ethers v5 compatible
function addressToBytes32(address) {
    return ethers.utils.hexZeroPad(address.toLowerCase(), 32);
}

async function main() {
    console.log("🔗 Setting up LayerZero V2 Peer Connections for Separated Architecture...");
    console.log("✨ ChainFlipOFT (LayerZero) + ETHWrapper (Deposit/Withdraw)");
    
    const [deployer] = await ethers.getSigners();
    const currentNetwork = hre.network.name;
    
    console.log(`\n📊 Current Network: ${currentNetwork}`);
    console.log(`   Deployer: ${deployer.address}`);
    
    // Get current OFT contract address (for LayerZero peer connections)
    const currentOftAddress = OFT_CONTRACTS[currentNetwork];
    const currentWrapperAddress = WRAPPER_CONTRACTS[currentNetwork];
    
    if (!currentOftAddress) {
        console.log(`❌ No OFT contract address configured for ${currentNetwork}`);
        console.log("Please update OFT_CONTRACTS with your deployed addresses");
        return;
    }
    
    console.log(`   ChainFlipOFT: ${currentOftAddress}`);
    console.log(`   ETHWrapper: ${currentWrapperAddress}`);
    
    // Get OFT contract instance for peer connections
    let oft;
    try {
        const ChainFlipOFT = await ethers.getContractFactory("ChainFlipOFT");
        oft = ChainFlipOFT.attach(currentOftAddress);
        console.log(`   ✅ Connected to ChainFlipOFT contract`);
    } catch (error) {
        console.log(`❌ Contract factory 'ChainFlipOFT' not found: ${error.message}`);
        console.log("Make sure your contract is compiled: npx hardhat compile");
        return;
    }
    
    // Set peers for all other networks
    console.log("\n🔗 Setting peer connections...");
    
    for (const [networkName, contractAddress] of Object.entries(OFT_CONTRACTS)) {
        if (networkName === currentNetwork || !contractAddress) {
            continue; // Skip current network and empty addresses
        }
        
        const peerEid = LAYERZERO_EIDS[networkName];
        const peerBytes32 = addressToBytes32(contractAddress);
        
        console.log(`\n📡 Setting peer: ${networkName}`);
        console.log(`   EID: ${peerEid}`);
        console.log(`   OFT Address: ${contractAddress}`);
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
    for (const [networkName, contractAddress] of Object.entries(OFT_CONTRACTS)) {
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
    Object.keys(OFT_CONTRACTS).forEach(network => {
        if (network !== currentNetwork) {
            console.log(`   npx hardhat run scripts/set-peer-connections.js --network ${network}`);
        }
    });
    
    console.log("\n✨ SEPARATED ARCHITECTURE FEATURES:");
    console.log("   • ChainFlipOFT: Cross-chain transfers via LayerZero V2");
    console.log("   • ETHWrapper: Deposit ETH → get cfWETH tokens");
    console.log("   • ETHWrapper: Withdraw cfWETH → get ETH back");
    console.log("   • Clean architecture with separated concerns");
    console.log("   • True decentralized ETH bridging across 3 networks");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
