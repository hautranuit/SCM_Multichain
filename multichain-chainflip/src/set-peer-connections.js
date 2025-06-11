const { ethers } = require("hardhat");

// LayerZero V2 Endpoint IDs (eid) - Updated 2025
const LAYERZERO_V2_EIDS = {
  80002: 40313,   // Polygon Amoy
  421614: 40231,  // Arbitrum Sepolia
  11155420: 40232, // Optimism Sepolia
  2442: 40158     // zkEVM Cardona
};

// Deployed OFT Contract Addresses
const DEPLOYED_OFT_ADDRESSES = {
  80002: "0x2edF34BA32BC489BcbF313A98037b8c423f83000",   // Polygon Amoy
  421614: "0x9767D45C02Bf58842d723a1E1D8340a22748f6B8",  // Arbitrum Sepolia
  11155420: "0xf77FAB8A727ac0d6810881841Ad1274bacA306c9", // Optimism Sepolia
  2442: "0xc8DEf94605917074A3990D4c78cf52C556C47E28"    // zkEVM Cardona
};

async function setPeerConnections() {
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  console.log("🔗 Setting up LayerZero OFT Peer Connections...");
  console.log("Network:", network.name);
  console.log("Chain ID:", chainId);
  console.log("Deployer:", deployer.address);
  
  // Get current chain's contract address
  const currentContractAddress = DEPLOYED_OFT_ADDRESSES[chainId];
  if (!currentContractAddress) {
    console.log("❌ Contract not deployed on this chain");
    return;
  }
  
  console.log("📋 Current OFT Contract:", currentContractAddress);
  
  try {
    // Get contract instance
    const WETHOFT = await ethers.getContractFactory("WETHOFT");
    const wethOFT = WETHOFT.attach(currentContractAddress);
    
    // Set peers for all other chains
    for (const [otherChainId, otherContractAddress] of Object.entries(DEPLOYED_OFT_ADDRESSES)) {
      if (Number(otherChainId) !== chainId) {
        const otherEid = LAYERZERO_V2_EIDS[otherChainId];
        
        console.log(`\n🔗 Setting peer for Chain ID ${otherChainId} (EID: ${otherEid})`);
        console.log(`   Contract: ${otherContractAddress}`);
        
        // Convert contract address to bytes32
        const peerBytes32 = ethers.zeroPadValue(otherContractAddress, 32);
        
        try {
          // Check if peer is already set
          const currentPeer = await wethOFT.peers(otherEid);
          if (currentPeer === peerBytes32) {
            console.log(`   ✅ Peer already set correctly`);
            continue;
          }
          
          // Set the peer
          const tx = await wethOFT.setPeer(otherEid, peerBytes32);
          console.log(`   📤 Transaction sent: ${tx.hash}`);
          
          const receipt = await tx.wait();
          console.log(`   ✅ Peer set successfully! Gas used: ${receipt.gasUsed}`);
          
        } catch (error) {
          console.log(`   ❌ Failed to set peer: ${error.message}`);
        }
      }
    }
    
    console.log("\n🎉 Peer connection setup complete!");
    console.log("\n📋 Verification:");
    
    // Verify all peer connections
    for (const [otherChainId, otherContractAddress] of Object.entries(DEPLOYED_OFT_ADDRESSES)) {
      if (Number(otherChainId) !== chainId) {
        const otherEid = LAYERZERO_V2_EIDS[otherChainId];
        try {
          const peerAddress = await wethOFT.peers(otherEid);
          const expectedBytes32 = ethers.zeroPadValue(otherContractAddress, 32);
          
          if (peerAddress === expectedBytes32) {
            console.log(`   ✅ Chain ${otherChainId} (EID: ${otherEid}): Connected`);
          } else {
            console.log(`   ❌ Chain ${otherChainId} (EID: ${otherEid}): Not connected`);
          }
        } catch (error) {
          console.log(`   ❌ Chain ${otherChainId} (EID: ${otherEid}): Error checking - ${error.message}`);
        }
      }
    }
    
  } catch (error) {
    console.error("❌ Failed to set peer connections:", error);
  }
}

async function main() {
  await setPeerConnections();
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
