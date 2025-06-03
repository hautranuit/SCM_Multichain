const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

// LayerZero Endpoint addresses for testnets
const LAYERZERO_ENDPOINTS = {
  80002: "0x6Fcb97553D41516Cb228ac03FdC8B9a0a9df04A1", // Polygon Amoy
  421614: "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3", // Arbitrum Sepolia
  11155420: "0x55370E0fBB5f5b8dAeD978BA1c075a499eB107B8" // Optimism Sepolia
};

// FxPortal contracts for Polygon ecosystem
const FX_PORTAL_ADDRESSES = {
  80002: {
    fxStateSender: "0x4CdF39285D7Ca8eB3f090fDA0C069ba5F4145B37", // Polygon Amoy FxStateSender
    checkpointManager: "0x2890bA17EfE978480615e330ecB65333b880928e"
  },
  2442: {
    fxChild: "0xCf73231F28B7331BBe3124B907840A94851f9f11" // zkEVM Cardona FxChild
  }
};

async function main() {
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  console.log("🌉 Deploying Bridge Infrastructure...");
  console.log("Network:", network.name);
  console.log("Chain ID:", chainId);
  console.log("Deployer:", deployer.address);
  console.log("Balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");
  
  const deployedContracts = {};
  
  try {
    // Deploy appropriate bridges based on chain
    if (chainId === 80002) {
      // Polygon Amoy Hub - Deploy both LayerZero and FxPortal for coordination
      console.log("\n🏭 Deploying Hub Bridge Infrastructure on Polygon Amoy...");
      
      // Deploy LayerZero Config
      const LayerZeroConfig = await ethers.getContractFactory("LayerZeroConfig");
      const layerZeroConfig = await LayerZeroConfig.deploy(
        LAYERZERO_ENDPOINTS[chainId],
        deployer.address
      );
      await layerZeroConfig.waitForDeployment();
      deployedContracts.layerZeroConfig = await layerZeroConfig.getAddress();
      console.log("✅ LayerZero Config deployed:", deployedContracts.layerZeroConfig);
      
      // Deploy FxPortal Bridge
      const FxPortalBridge = await ethers.getContractFactory("FxPortalBridge");
      const fxPortalBridge = await FxPortalBridge.deploy(
        FX_PORTAL_ADDRESSES[chainId].fxStateSender,
        deployer.address
      );
      await fxPortalBridge.waitForDeployment();
      deployedContracts.fxPortalBridge = await fxPortalBridge.getAddress();
      console.log("✅ FxPortal Bridge deployed:", deployedContracts.fxPortalBridge);
      
      // Deploy Cross Chain Messenger
      const CrossChainMessenger = await ethers.getContractFactory("CrossChainMessenger");
      const crossChainMessenger = await CrossChainMessenger.deploy(deployer.address);
      await crossChainMessenger.waitForDeployment();
      deployedContracts.crossChainMessenger = await crossChainMessenger.getAddress();
      console.log("✅ Cross Chain Messenger deployed:", deployedContracts.crossChainMessenger);
      
      // Configure the messenger with bridge contracts
      await crossChainMessenger.setBridgeContracts(
        deployedContracts.layerZeroConfig,
        deployedContracts.fxPortalBridge
      );
      console.log("✅ Bridge contracts configured in messenger");
      
    } else if (chainId === 2442) {
      // zkEVM Cardona Manufacturer - Deploy FxPortal Child
      console.log("\n🚀 Deploying Manufacturer Bridge Infrastructure on zkEVM Cardona...");
      
      // Deploy FxPortal Bridge (Child side)
      const FxPortalBridge = await ethers.getContractFactory("FxPortalBridge");
      const fxPortalBridge = await FxPortalBridge.deploy(
        ethers.ZeroAddress, // No FxStateSender on child chain
        deployer.address
      );
      await fxPortalBridge.waitForDeployment();
      deployedContracts.fxPortalBridge = await fxPortalBridge.getAddress();
      console.log("✅ FxPortal Bridge (Child) deployed:", deployedContracts.fxPortalBridge);
      
    } else if (chainId === 421614) {
      // Arbitrum Sepolia Transporter - Deploy LayerZero
      console.log("\n🚛 Deploying Transporter Bridge Infrastructure on Arbitrum Sepolia...");
      
      // Deploy LayerZero Config
      const LayerZeroConfig = await ethers.getContractFactory("LayerZeroConfig");
      const layerZeroConfig = await LayerZeroConfig.deploy(
        LAYERZERO_ENDPOINTS[chainId],
        deployer.address
      );
      await layerZeroConfig.waitForDeployment();
      deployedContracts.layerZeroConfig = await layerZeroConfig.getAddress();
      console.log("✅ LayerZero Config deployed:", deployedContracts.layerZeroConfig);
      
    } else if (chainId === 11155420) {
      // Optimism Sepolia Buyer - Deploy LayerZero
      console.log("\n🛒 Deploying Buyer Bridge Infrastructure on Optimism Sepolia...");
      
      // Deploy LayerZero Config
      const LayerZeroConfig = await ethers.getContractFactory("LayerZeroConfig");
      const layerZeroConfig = await LayerZeroConfig.deploy(
        LAYERZERO_ENDPOINTS[chainId],
        deployer.address
      );
      await layerZeroConfig.waitForDeployment();
      deployedContracts.layerZeroConfig = await layerZeroConfig.getAddress();
      console.log("✅ LayerZero Config deployed:", deployedContracts.layerZeroConfig);
      
    } else {
      console.log("❌ Unsupported chain for bridge deployment");
      return;
    }
    
    // Save deployment information
    const deploymentInfo = {
      network: network.name,
      chainId: chainId,
      deployer: deployer.address,
      deployedAt: new Date().toISOString(),
      contracts: deployedContracts,
      bridgeType: chainId === 2442 ? "FxPortal" : "LayerZero",
      gasUsed: "TBD" // Would need to track gas usage
    };
    
    // Save to deployment file
    const deploymentDir = path.join(__dirname, "../deployments");
    if (!fs.existsSync(deploymentDir)) {
      fs.mkdirSync(deploymentDir, { recursive: true });
    }
    
    const deploymentFile = path.join(deploymentDir, `bridges-${network.name}-${chainId}.json`);
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
    
    console.log("\n🎉 Bridge Deployment Complete!");
    console.log("📁 Deployment info saved to:", deploymentFile);
    console.log("\n📋 Deployed Contracts:");
    Object.entries(deployedContracts).forEach(([name, address]) => {
      console.log(`   ${name}: ${address}`);
    });
    
    // Next steps instructions
    console.log("\n🔗 Next Steps:");
    if (chainId === 80002) {
      console.log("1. Deploy bridges on all L2 chains");
      console.log("2. Configure trusted remotes between chains");
      console.log("3. Update Hub contract with bridge addresses");
      console.log("4. Test cross-chain messaging");
    } else {
      console.log("1. Configure trusted remote with Hub (Polygon Amoy)");
      console.log("2. Update L2 contract with bridge address");
      console.log("3. Test bridge communication");
    }
    
  } catch (error) {
    console.error("❌ Bridge deployment failed:", error);
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
