const { ethers } = require("hardhat");
const fs = require('fs');
const path = require('path');

// Contract addresses - DEPLOYED ADDRESSES UPDATED
const CHAINFLIP_MESSENGER_ADDRESSES = {
    baseSepolia: "0xDbc80005e688df0b2E1486D6619A7Cdf3b10C714", // Update after deployment
    polygonAmoy: "0x225FD1670d94304b737A05412fbCE7a39224D1B1", // Update after deployment
    optimismSepolia: "0x69b862c5091fE37e6f1dD47CDC40c69916586e61", // Update after deployment
    arbitrumSepolia: "0xf42BB61B03697608104F12D8C009ad387b4750cB" // Update after deployment
};

// LayerZero V2 Endpoint IDs
const LAYERZERO_V2_EIDS = {
    baseSepolia: 40245,
    polygonAmoy: 40267,
    optimismSepolia: 40232,
    arbitrumSepolia: 40231
};

async function main() {
    console.log("🔗 Configuring ChainFLIP Messenger Trusted Peers (LayerZero V2)...");
    
    const [deployer] = await ethers.getSigners();
    const network = await ethers.provider.getNetwork();
    const chainId = network.chainId;
    
    console.log(`📍 Current Network: Chain ID ${chainId}`);
    console.log(`👤 Deployer: ${deployer.address}`);
    
    // Determine current network
    let currentNetworkName;
    let currentContractAddress;
    
    switch (chainId.toString()) {
        case "84532":
            currentNetworkName = "baseSepolia";
            break;
        case "80002":
            currentNetworkName = "polygonAmoy";
            break;
        case "11155420":
            currentNetworkName = "optimismSepolia";
            break;
        case "421614":
            currentNetworkName = "arbitrumSepolia";
            break;
        default:
            throw new Error(`Unsupported network: ${chainId}`);
    }
    
    currentContractAddress = CHAINFLIP_MESSENGER_ADDRESSES[currentNetworkName];
    
    if (currentContractAddress === "0x0000000000000000000000000000000000000000") {
        throw new Error(`Please update the contract address for ${currentNetworkName} in this script`);
    }
    
    console.log(`🏠 Current Network: ${currentNetworkName}`);
    console.log(`📄 Contract Address: ${currentContractAddress}`);
    
    // Get contract instance
    const ChainFLIPMessenger = await ethers.getContractFactory("ChainFLIPMessenger");
    const messenger = ChainFLIPMessenger.attach(currentContractAddress);
    
    // Verify contract owner
    const owner = await messenger.owner();
    if (owner.toLowerCase() !== deployer.address.toLowerCase()) {
        throw new Error(`Only contract owner can set peers. Owner: ${owner}, Deployer: ${deployer.address}`);
    }
    
    console.log("✅ Contract owner verified");
    
    // Configure peers for other chains
    const remoteNetworks = Object.keys(CHAINFLIP_MESSENGER_ADDRESSES).filter(net => net !== currentNetworkName);
    
    console.log(`\n🔧 Setting trusted peers for ${remoteNetworks.length} chains...`);
    
    for (const remoteNetwork of remoteNetworks) {
        const remoteAddress = CHAINFLIP_MESSENGER_ADDRESSES[remoteNetwork];
        const remoteEid = LAYERZERO_V2_EIDS[remoteNetwork];
        
        if (remoteAddress === "0x0000000000000000000000000000000000000000") {
            console.log(`⚠️ Skipping ${remoteNetwork} - contract address not set`);
            continue;
        }
        
        console.log(`\n📡 Setting peer for ${remoteNetwork}:`);
        console.log(`   Remote EID: ${remoteEid}`);
        console.log(`   Remote Address: ${remoteAddress}`);
        
        try {
            // LayerZero V2 uses setPeer instead of setTrustedRemote
            // Convert address to bytes32 format
            const peerBytes32 = ethers.utils.hexZeroPad(remoteAddress, 32);
            
            const tx = await messenger.setPeer(remoteEid, peerBytes32);
            console.log(`   📋 Transaction: ${tx.hash}`);
            
            await tx.wait();
            console.log(`   ✅ Peer set successfully`);
            
        } catch (error) {
            console.log(`   ❌ Failed to set peer: ${error.message}`);
        }
    }
    
    console.log("\n🎉 Peer configuration completed!");
    console.log("\n📋 Next steps:");
    console.log("1. Repeat this process on all 4 chains");
    console.log("2. Test cross-chain messaging");
    console.log("3. Verify peers are bidirectional");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Configuration failed:", error);
        process.exit(1);
    });