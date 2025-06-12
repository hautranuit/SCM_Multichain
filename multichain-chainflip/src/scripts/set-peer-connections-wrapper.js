// LayerZero V2 Peer Connection Setup via ETHWrapper
// Works with separated architecture where wrapper owns the OFT contract

const hre = require("hardhat");
const { ethers } = require("hardhat");

// ETHWrapper Contract addresses (these own the OFT contracts)
const WRAPPER_CONTRACTS = {
    optimismSepolia: "0x5428793EBd36693c993D6B3f8f2641C46121ec29",
    arbitrumSepolia: "0x5952569276eA7f7eF95B910EAd0a67067A518188",
    amoy: "0xA471c665263928021AF5aa7852724b6f757005e1"
};

// ChainFlipOFT Contract addresses (owned by wrappers above)
const OFT_CONTRACTS = {
    optimismSepolia: "0x6478eAB366A16d96ae910fd16F6770DDa1845648",
    arbitrumSepolia: "0x441C06d8548De93d64072F781e15E16A7c316b67", 
    amoy: "0x865F1Dac1d8E17f492FFce578095b49f3D604ad4"
};

// LayerZero V2 Endpoint IDs
const LAYERZERO_EIDS = {
    optimismSepolia: 40232,
    arbitrumSepolia: 40231,
    amoy: 40267
};

// Convert address to bytes32 (for LayerZero peer setting)
function addressToBytes32(address) {
    return ethers.utils.hexZeroPad(address.toLowerCase(), 32);
}

async function main() {
    console.log("🔗 Setting LayerZero V2 Peers via ETHWrapper (Separated Architecture)");
    console.log("✨ Using wrapper contract to manage OFT peers");
    
    const [deployer] = await ethers.getSigners();
    const currentNetwork = hre.network.name;
    
    console.log(`\n📊 Current Network: ${currentNetwork}`);
    console.log(`   Deployer: ${deployer.address}`);
    
    // Get current wrapper address
    const currentWrapperAddress = WRAPPER_CONTRACTS[currentNetwork];
    const currentOftAddress = OFT_CONTRACTS[currentNetwork];
    
    if (!currentWrapperAddress || !currentOftAddress) {
        console.log(`❌ No contracts configured for ${currentNetwork}`);
        return;
    }
    
    console.log(`   ETHWrapper: ${currentWrapperAddress}`);
    console.log(`   ChainFlipOFT: ${currentOftAddress}`);
    
    // Get wrapper contract instance
    let wrapper;
    try {
        const ETHWrapper = await ethers.getContractFactory("ETHWrapper");
        wrapper = ETHWrapper.attach(currentWrapperAddress);
        console.log(`   ✅ Connected to ETHWrapper contract`);
    } catch (error) {
        console.log(`❌ Contract connection failed: ${error.message}`);
        console.log("Make sure contracts are compiled: npx hardhat compile");
        return;
    }
    
    // Set peers for all other networks
    console.log("\n🔗 Setting peer connections via wrapper...");
    
    for (const [networkName, oftAddress] of Object.entries(OFT_CONTRACTS)) {
        if (networkName === currentNetwork) {
            continue; // Skip current network
        }
        
        const peerEid = LAYERZERO_EIDS[networkName];
        const peerBytes32 = addressToBytes32(oftAddress);
        
        console.log(`\n📡 Setting peer: ${networkName}`);
        console.log(`   EID: ${peerEid}`);
        console.log(`   OFT Address: ${oftAddress}`);
        console.log(`   Bytes32: ${peerBytes32}`);
        
        try {
            // Check if peer is already set
            const currentPeer = await wrapper.getPeer(peerEid);
            const isAlreadySet = currentPeer !== "0x0000000000000000000000000000000000000000000000000000000000000000";
            
            if (isAlreadySet) {
                console.log(`   ✅ Peer already set for ${networkName}`);
                continue;
            }
            
            // Set the peer via wrapper
            const tx = await wrapper.setPeer(peerEid, peerBytes32, {
                gasLimit: 300000
            });
            console.log(`   📤 Transaction sent: ${tx.hash}`);
            
            const receipt = await tx.wait();
            if (receipt.status === 1) {
                console.log(`   ✅ Peer set successfully! Gas used: ${receipt.gasUsed.toString()}`);
            } else {
                console.log(`   ❌ Transaction failed`);
            }
            
        } catch (error) {
            console.log(`   ❌ Failed to set peer for ${networkName}: ${error.message}`);
        }
    }
    
    // Verify all peer connections
    console.log("\n🔍 Verifying peer connections...");
    for (const [networkName, oftAddress] of Object.entries(OFT_CONTRACTS)) {
        if (networkName === currentNetwork) {
            continue;
        }
        
        const peerEid = LAYERZERO_EIDS[networkName];
        const expectedPeerBytes32 = addressToBytes32(oftAddress);
        
        try {
            const actualPeer = await wrapper.getPeer(peerEid);
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
    console.log("\n🔗 Run on other networks:");
    Object.keys(WRAPPER_CONTRACTS).forEach(network => {
        if (network !== currentNetwork) {
            console.log(`   npx hardhat run scripts/set-peer-connections-wrapper.js --network ${network}`);
        }
    });
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });