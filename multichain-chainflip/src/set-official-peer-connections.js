const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

// OFFICIAL LayerZero V2 OFT Contract Addresses (TO BE UPDATED AFTER DEPLOYMENT)
// These will be populated with addresses from the official deployment
let OFFICIAL_CONTRACTS = {
  optimism_sepolia: "",   // Will be updated after deployment
  arbitrum_sepolia: "",   // Will be updated after deployment  
  polygon_pos: "",        // Will be updated after deployment
  zkevm_cardona: ""       // Will be updated after deployment
};

// Official LayerZero V2 Endpoint IDs (June 2025)
const OFFICIAL_EIDS = {
  optimism_sepolia: 40232,
  arbitrum_sepolia: 40231,
  polygon_pos: 40313,
  zkevm_cardona: 40158  // CORRECTED as per handoff document
};

// Chain ID to network name mapping
const CHAIN_ID_TO_NETWORK = {
  11155420: "optimism_sepolia",
  421614: "arbitrum_sepolia", 
  80002: "polygon_pos",
  2442: "zkevm_cardona"
};

// Network name to hardhat network mapping
const NETWORK_TO_HARDHAT = {
  optimism_sepolia: "optimismSepolia",
  arbitrum_sepolia: "arbitrumSepolia",
  polygon_pos: "amoy", 
  zkevm_cardona: "cardona"
};

// Convert address to bytes32 (for LayerZero peer setting)
function addressToBytes32(address) {
  return ethers.zeroPadValue(address.toLowerCase(), 32);
}

// Load deployed contract addresses from deployment files
function loadOfficialContractAddresses() {
  const deploymentDir = path.join(__dirname, "deployments");
  
  if (!fs.existsSync(deploymentDir)) {
    console.log("⚠️ No deployments directory found. Deploy contracts first.");
    return false;
  }
  
  console.log("📁 Loading official contract addresses from deployment files...");
  
  let loadedCount = 0;
  
  // Look for official deployment files
  const deploymentFiles = fs.readdirSync(deploymentDir)
    .filter(file => file.startsWith('official-layerzero-oft-') && file.endsWith('.json'));
  
  deploymentFiles.forEach(file => {
    try {
      const filePath = path.join(deploymentDir, file);
      const deploymentData = JSON.parse(fs.readFileSync(filePath, 'utf8'));
      
      const networkKey = deploymentData.network.networkKey;
      const contractAddress = deploymentData.contracts.wethOFT.address;
      
      if (OFFICIAL_CONTRACTS.hasOwnProperty(networkKey)) {
        OFFICIAL_CONTRACTS[networkKey] = contractAddress;
        loadedCount++;
        console.log(`   ✅ ${networkKey}: ${contractAddress}`);
      }
    } catch (error) {
      console.log(`   ⚠️ Error loading ${file}: ${error.message}`);
    }
  });
  
  console.log(`📋 Loaded ${loadedCount} official contract addresses`);
  
  // Check if we have addresses for all chains
  const missingChains = Object.entries(OFFICIAL_CONTRACTS)
    .filter(([chain, address]) => !address)
    .map(([chain]) => chain);
  
  if (missingChains.length > 0) {
    console.log("⚠️ Missing contract addresses for chains:", missingChains);
    console.log("🔧 Deploy official contracts on these chains first:");
    missingChains.forEach(chain => {
      const hardhatNetwork = NETWORK_TO_HARDHAT[chain];
      console.log(`   npx hardhat run deployment/deploy-official-layerzero-oft.js --network ${hardhatNetwork}`);
    });
    return false;
  }
  
  return true;
}

async function setOfficialPeerConnections() {
  console.log("🔗 === SETTING UP OFFICIAL LAYERZERO V2 PEER CONNECTIONS ===");
  console.log("📅 Date: June 2025");
  console.log("🔧 Purpose: Configure official LayerZero V2 OFT peer connections");
  
  // Load official contract addresses
  if (!loadOfficialContractAddresses()) {
    console.log("❌ Cannot proceed without all contract addresses. Deploy all contracts first.");
    return;
  }
  
  console.log("\n📋 === OFFICIAL CONTRACT ADDRESSES ===");
  Object.entries(OFFICIAL_CONTRACTS).forEach(([chain, address]) => {
    console.log(`   ${chain}: ${address}`);
  });

  // Get current network
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  console.log(`\n🌐 Current Network: ${network.name} (${chainId})`);
  
  // Determine current chain and contract
  const currentNetworkKey = CHAIN_ID_TO_NETWORK[chainId];
  
  if (!currentNetworkKey) {
    console.error("❌ Unsupported network for official peer connections");
    console.log("✅ Supported networks:", Object.keys(CHAIN_ID_TO_NETWORK));
    return;
  }
  
  const currentContract = OFFICIAL_CONTRACTS[currentNetworkKey];
  
  if (!currentContract) {
    console.error(`❌ No official contract deployed on ${currentNetworkKey}`);
    console.log(`🔧 Deploy first: npx hardhat run deployment/deploy-official-layerzero-oft.js --network ${network.name}`);
    return;
  }

  console.log(`📍 Setting official peers for: ${currentNetworkKey}`);
  console.log(`📍 Contract Address: ${currentContract}`);

  // Get contract instance with official LayerZero V2 OFT ABI
  const [deployer] = await ethers.getSigners();
  console.log(`👤 Using deployer: ${deployer.address}`);
  
  // Official LayerZero V2 OFT setPeer function
  const officialOFTAbi = [
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
  
  const oftContract = new ethers.Contract(currentContract, officialOFTAbi, deployer);

  // Verify contract ownership
  try {
    const contractOwner = await oftContract.owner();
    console.log(`🔐 Contract Owner: ${contractOwner}`);
    console.log(`👤 Deployer Address: ${deployer.address}`);
    
    if (contractOwner.toLowerCase() !== deployer.address.toLowerCase()) {
      console.log("⚠️ Warning: Deployer is not the contract owner. Peer setting may fail.");
    } else {
      console.log("✅ Deployer is contract owner - can set peers");
    }
  } catch (error) {
    console.log("⚠️ Could not verify contract ownership:", error.message);
  }

  // Set peers to all other chains
  const peerConnections = [];
  
  Object.entries(OFFICIAL_CONTRACTS).forEach(([chainName, contractAddress]) => {
    if (chainName !== currentNetworkKey && contractAddress) {
      const eid = OFFICIAL_EIDS[chainName];
      const peerBytes32 = addressToBytes32(contractAddress);
      peerConnections.push({ chainName, eid, contractAddress, peerBytes32 });
    }
  });

  console.log(`\n🔄 === SETTING ${peerConnections.length} OFFICIAL PEER CONNECTIONS ===\n`);

  let successCount = 0;
  let failureCount = 0;

  for (const peer of peerConnections) {
    try {
      console.log(`⏳ Setting official peer: ${peer.chainName} (EID: ${peer.eid})`);
      console.log(`   📍 Contract: ${peer.contractAddress}`);
      console.log(`   🔗 Bytes32: ${peer.peerBytes32}`);
      
      // Check if peer is already set
      try {
        const existingPeer = await oftContract.peers(peer.eid);
        if (existingPeer === peer.peerBytes32) {
          console.log(`   ✅ Peer already set correctly - skipping\n`);
          successCount++;
          continue;
        } else if (existingPeer !== ethers.ZeroHash) {
          console.log(`   🔄 Updating existing peer: ${existingPeer} → ${peer.peerBytes32}`);
        }
      } catch (error) {
        console.log(`   ⚠️ Could not check existing peer: ${error.message}`);
      }
      
      // Set the peer
      const tx = await oftContract.setPeer(peer.eid, peer.peerBytes32);
      console.log(`   📤 Transaction sent: ${tx.hash}`);
      
      const receipt = await tx.wait();
      if (receipt.status === 1) {
        console.log(`   ✅ Official peer set successfully!`);
        console.log(`   ⛽ Gas used: ${receipt.gasUsed.toString()}\n`);
        successCount++;
      } else {
        console.log(`   ❌ Transaction failed - Receipt status: ${receipt.status}\n`);
        failureCount++;
      }
    } catch (error) {
      console.error(`   ❌ Error setting official peer for ${peer.chainName}: ${error.message}\n`);
      failureCount++;
    }
  }

  console.log("🎉 === OFFICIAL PEER CONNECTION SETUP COMPLETE ===");
  console.log(`✅ Successful connections: ${successCount}`);
  console.log(`❌ Failed connections: ${failureCount}`);
  console.log(`📋 ${currentNetworkKey} is now connected to ${successCount} other chains`);
  
  if (failureCount === 0) {
    console.log("🌟 ALL PEER CONNECTIONS SET SUCCESSFULLY!");
  } else {
    console.log("⚠️ Some peer connections failed. Check errors above.");
  }
  
  console.log("\n🔄 === NEXT STEPS ===");
  console.log("1. Run this script on ALL other chains to complete full mesh connectivity:");
  
  Object.entries(NETWORK_TO_HARDHAT).forEach(([networkKey, hardhatNetwork]) => {
    if (networkKey !== currentNetworkKey) {
      console.log(`   npx hardhat run set-official-peer-connections.js --network ${hardhatNetwork}`);
    }
  });
  
  console.log("2. Update backend configuration with official contract addresses");
  console.log("3. Test LayerZero OFT transfers (should fix '0x3ee5aeb5' error)");
  
  // Verification summary
  console.log("\n📋 === VERIFICATION CHECKLIST ===");
  console.log(`✅ Contract deployed with official LayerZero V2 interface: ${currentContract}`);
  console.log(`✅ Peer connections set: ${successCount}/${peerConnections.length}`);
  console.log(`✅ Ready for cross-chain transfers: ${failureCount === 0 ? 'YES' : 'NO'}`);
}

async function main() {
  try {
    await setOfficialPeerConnections();
  } catch (error) {
    console.error("❌ === OFFICIAL PEER CONNECTION SETUP FAILED ===");
    console.error("Error:", error);
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });