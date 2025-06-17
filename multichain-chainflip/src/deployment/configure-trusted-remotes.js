const hre = require("hardhat");

/**
 * Configure trusted remotes between DirectLayerZeroMessenger contracts
 * Run this after deploying to all 4 chains
 */

// Replace these with actual deployed contract addresses
const CONTRACT_ADDRESSES = {
  baseSepolia: "0x1208F8F0E40381F14E41621906D13C9c3CaAa061",
  optimismSepolia: "0x97420B3dEd4B3eA72Ff607fd96927Bfa605b197c", 
  arbitrumSepolia: "0x25409B7ee450493248fD003A759304FF7f748c53",
  amoy: "0x34705a7e91b465AE55844583EC16715C88bD457a"
};

const EID_MAPPING = {
  baseSepolia: 40245,
  optimismSepolia: 40232,
  arbitrumSepolia: 40231,
  amoy: 40267
};

async function main() {
  const network = hre.network.name;
  console.log(`🔗 Configuring trusted remotes for ${network}...`);
  
  const contractAddress = CONTRACT_ADDRESSES[network];
  if (!contractAddress || contractAddress.includes("[")) {
    throw new Error(`❌ Please update CONTRACT_ADDRESSES with actual deployed addresses`);
  }
  
  const DirectLayerZeroMessenger = await hre.ethers.getContractFactory("DirectLayerZeroMessenger");
  const messenger = await DirectLayerZeroMessenger.attach(contractAddress);
  
  // Configure trusted remotes for all other chains
  for (const [chainName, remoteAddress] of Object.entries(CONTRACT_ADDRESSES)) {
    if (chainName === network) continue; // Skip current chain
    
    const remoteEid = EID_MAPPING[chainName];
    const trustedRemote = hre.ethers.utils.solidityPack(
      ["address", "address"],
      [remoteAddress, contractAddress]
    );
    
    console.log(`⏳ Setting trusted remote for ${chainName} (EID: ${remoteEid})...`);
    
    try {
      const tx = await messenger.setTrustedRemote(remoteEid, trustedRemote);
      await tx.wait();
      console.log(`✅ Trusted remote set for ${chainName}: ${tx.hash}`);
    } catch (error) {
      console.error(`❌ Failed to set trusted remote for ${chainName}:`, error.message);
    }
  }
  
  console.log(`🎉 Trusted remote configuration completed for ${network}!`);
}

if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error("❌ Configuration failed:", error);
      process.exit(1);
    });
}

module.exports = main;
