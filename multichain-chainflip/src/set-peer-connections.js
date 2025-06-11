const { ethers } = require("hardhat");

// FINAL LayerZero OFT Contract Addresses (ALL FIXED CONTRACTS WITH QUOTESEND)
const CONTRACTS = {
  optimismSepolia: "0x1A3F3924662aaa4f5122cD2B2EDff614Cf1d6eb0",  // ✅ FINAL FIXED 
  arbitrumSepolia: "0x35F63413FC7d0BE3f3e5f819BDd32b867A92d966",  // ✅ FINAL FIXED
  polygonAmoy: "0x7793D6Af377548082833E341Fb93681B531C656B",      // ✅ FINAL FIXED
  zkevmCardona: "0x736A068c7d2124D21026d86ee9F23F0A2d1dA5A4"       // ✅ FINAL FIXED
};

// LayerZero Endpoint IDs (V1 compatible for zkevmCardona)
const EIDS = {
  optimismSepolia: 40232,
  arbitrumSepolia: 40231,
  polygonAmoy: 40313,
  zkevmCardona: 30158  // FIXED: Use V1 compatible EID (changed from 40158)
};

// Convert address to bytes32 (for LayerZero peer setting)
function addressToBytes32(address) {
  return ethers.zeroPadValue(address.toLowerCase(), 32);
}

async function setPeerConnections() {
  console.log("🔗 Setting up LayerZero OFT Peer Connections (FIXED CONTRACTS)...");
  console.log("📋 Contract Addresses:");
  Object.entries(CONTRACTS).forEach(([chain, address]) => {
    console.log(`   ${chain}: ${address}`);
  });

  // Get current network
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  console.log(`\n🌐 Current Network: ${network.name} (${chainId})`);
  
  // Determine current chain and contract
  let currentChain;
  let currentContract;
  
  if (chainId === 11155420) {
    currentChain = "optimismSepolia";
    currentContract = CONTRACTS.optimismSepolia;
  } else if (chainId === 421614) {
    currentChain = "arbitrumSepolia";
    currentContract = CONTRACTS.arbitrumSepolia;
  } else if (chainId === 80002) {
    currentChain = "polygonAmoy";
    currentContract = CONTRACTS.polygonAmoy;
  } else if (chainId === 2442) {
    currentChain = "zkevmCardona";
    currentContract = CONTRACTS.zkevmCardona;
  } else {
    console.error("❌ Unsupported network for peer connections");
    return;
  }

  console.log(`📍 Setting peers for: ${currentChain} (${currentContract})`);

  // Get contract instance
  const [deployer] = await ethers.getSigners();
  const abi = [
    {
      "inputs": [{"name": "_eid", "type": "uint32"}, {"name": "_peer", "type": "bytes32"}],
      "name": "setPeer",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ];
  
  const oftContract = new ethers.Contract(currentContract, abi, deployer);

  // Set peers to all other chains
  const peerConnections = [];
  
  Object.entries(CONTRACTS).forEach(([chainName, contractAddress]) => {
    if (chainName !== currentChain) {
      const eid = EIDS[chainName];
      const peerBytes32 = addressToBytes32(contractAddress);
      peerConnections.push({ chainName, eid, contractAddress, peerBytes32 });
    }
  });

  console.log(`\n🔄 Setting ${peerConnections.length} peer connections...\n`);

  for (const peer of peerConnections) {
    try {
      console.log(`⏳ Setting peer: ${peer.chainName} (EID: ${peer.eid})`);
      console.log(`   Contract: ${peer.contractAddress}`);
      console.log(`   Bytes32: ${peer.peerBytes32}`);
      
      const tx = await oftContract.setPeer(peer.eid, peer.peerBytes32);
      console.log(`   📤 Transaction sent: ${tx.hash}`);
      
      const receipt = await tx.wait();
      if (receipt.status === 1) {
        console.log(`   ✅ Peer set successfully!\n`);
      } else {
        console.log(`   ❌ Transaction failed!\n`);
      }
    } catch (error) {
      console.error(`   ❌ Error setting peer for ${peer.chainName}: ${error.message}\n`);
    }
  }

  console.log("🎉 Peer connection setup complete!");
  console.log("\n📋 Summary:");
  console.log(`✅ ${currentChain} is now connected to all other chains`);
  console.log("🔄 Run this script on each chain to complete full mesh connectivity");
}

async function main() {
  try {
    await setPeerConnections();
  } catch (error) {
    console.error("❌ Peer connection setup failed:", error);
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });