const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

// LayerZero V2 Endpoint addresses for testnets (2025)
const LAYERZERO_V2_ENDPOINTS = {
  80002: "0x6Fcb97553D41516Cb228ac03FdC8B9a0a9df04A1", // Polygon Amoy
  421614: "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3", // Arbitrum Sepolia
  11155420: "0x55370E0fBB5f5b8dAeD978BA1c075a499eB107B8", // Optimism Sepolia
  2442: "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3" // zkEVM Cardona (estimated)
};

// WETH contract addresses on each chain
const WETH_ADDRESSES = {
  80002: "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889", // Polygon Amoy
  421614: "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73", // Arbitrum Sepolia
  11155420: "0x4200000000000000000000000000000000000006", // Optimism Sepolia
  2442: "0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9" // zkEVM Cardona
};

// LayerZero V2 Endpoint IDs (eid)
const LAYERZERO_V2_EIDS = {
  80002: 40267,   // Polygon Amoy
  421614: 40231,  // Arbitrum Sepolia
  11155420: 40232, // Optimism Sepolia
  2442: 40158     // zkEVM Cardona (estimated)
};

async function main() {
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  console.log("🚀 Deploying LayerZero WETH OFT Contracts...");
  console.log("Network:", network.name);
  console.log("Chain ID:", chainId);
  console.log("Deployer:", deployer.address);
  console.log("Balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");
  
  // Check if chain is supported
  if (!LAYERZERO_V2_ENDPOINTS[chainId]) {
    console.log("❌ Unsupported chain for LayerZero V2 deployment");
    return;
  }
  
  const layerzeroEndpoint = LAYERZERO_V2_ENDPOINTS[chainId];
  const wethAddress = WETH_ADDRESSES[chainId];
  const eid = LAYERZERO_V2_EIDS[chainId];
  
  console.log("🔗 LayerZero V2 Endpoint:", layerzeroEndpoint);
  console.log("💰 WETH Address:", wethAddress);
  console.log("🆔 LayerZero EID:", eid);
  
  try {
    // Deploy WETH OFT contract
    console.log("\n📦 Deploying WETH OFT...");
    
    const WETHOFT = await ethers.getContractFactory("WETHOFT");
    const wethOFT = await WETHOFT.deploy(
      "ChainFLIP WETH",           // Name
      "cfWETH",                   // Symbol
      layerzeroEndpoint,          // LayerZero V2 endpoint
      wethAddress,                // WETH contract address
      deployer.address            // Delegate (owner)
    );
    
    await wethOFT.waitForDeployment();
    const wethOFTAddress = await wethOFT.getAddress();
    
    console.log("✅ WETH OFT deployed:", wethOFTAddress);
    
    // Verify the deployment
    console.log("\n🔍 Verifying deployment...");
    const wethToken = await wethOFT.wethToken();
    const lzEndpoint = await wethOFT.endpoint();
    const owner = await wethOFT.owner();
    
    console.log("📋 Contract verification:");
    console.log("   WETH Token:", wethToken);
    console.log("   LZ Endpoint:", lzEndpoint);
    console.log("   Owner:", owner);
    console.log("   Name:", await wethOFT.name());
    console.log("   Symbol:", await wethOFT.symbol());
    
    // Save deployment information
    const deploymentInfo = {
      network: network.name,
      chainId: chainId,
      deployer: deployer.address,
      deployedAt: new Date().toISOString(),
      contracts: {
        wethOFT: wethOFTAddress
      },
      configuration: {
        layerzeroEndpoint: layerzeroEndpoint,
        layerzeroEid: eid,
        wethAddress: wethAddress,
        name: "ChainFLIP WETH",
        symbol: "cfWETH"
      },
      bridgeType: "LayerZero OFT V2",
      gasUsed: "TBD"
    };
    
    // Save to deployment file
    const deploymentDir = path.join(__dirname, "../deployments");
    if (!fs.existsSync(deploymentDir)) {
      fs.mkdirSync(deploymentDir, { recursive: true });
    }
    
    const deploymentFile = path.join(deploymentDir, `weth-oft-${network.name}-${chainId}.json`);
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
    
    console.log("\n🎉 WETH OFT Deployment Complete!");
    console.log("📁 Deployment info saved to:", deploymentFile);
    console.log("\n📋 Deployed Contract:");
    console.log(`   WETH OFT: ${wethOFTAddress}`);
    
    // Instructions for next steps
    console.log("\n🔗 Next Steps:");
    console.log("1. Deploy WETH OFT on all target chains");
    console.log("2. Set peer addresses between all OFT contracts:");
    console.log(`   setPeer(${eid}, "${wethOFTAddress}")`);
    console.log("3. Update backend configuration with OFT addresses");
    console.log("4. Test cross-chain transfers");
    
    // Generate peer setting commands for convenience
    console.log("\n📝 Peer Setting Commands (run after all deployments):");
    Object.entries(LAYERZERO_V2_EIDS).forEach(([otherChainId, otherEid]) => {
      if (Number(otherChainId) !== chainId) {
        console.log(`   // For ${otherChainId}:`);
        console.log(`   await wethOFT.setPeer(${otherEid}, "0x<OTHER_CHAIN_OFT_ADDRESS>");`);
      }
    });
    
    // Configuration for backend
    console.log("\n⚙️ Backend Configuration Update:");
    console.log(`Add to layerzero_oft_bridge_service.py:`);
    console.log(`"${network.name.toLowerCase().replace(' ', '_')}": {`);
    console.log(`    "address": "${wethOFTAddress}",`);
    console.log(`    "layerzero_eid": ${eid},`);
    console.log(`    // ... other config`);
    console.log(`},`);
    
  } catch (error) {
    console.error("❌ WETH OFT deployment failed:", error);
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
