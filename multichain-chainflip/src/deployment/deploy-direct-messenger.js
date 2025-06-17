const hre = require("hardhat");

/**
 * Deploy DirectLayerZeroMessenger on all 4 chains with correct LayerZero V2 endpoints
 */

const LAYERZERO_ENDPOINTS = {
  base_sepolia: "0x6EDCE65403992e310A62460808c4b910D972f10f",
  op_sepolia: "0x6EDCE65403992e310A62460808c4b910D972f10f",   
  arbitrum_sepolia: "0x6EDCE65403992e310A62460808c4b910D972f10f",
  polygon_amoy: "0x6EDCE65403992e310A62460808c4b910D972f10f"
};

const DEPLOYER_ADDRESS = "0x032041b4b356fEE1496805DD4749f181bC736FFA";

async function main() {
  const network = hre.network.name;
  console.log(`🚀 Deploying DirectLayerZeroMessenger on ${network}...`);
  
  let lzEndpoint;
  let chainInfo;
  
  switch (network) {
    case "baseSepolia":
      lzEndpoint = LAYERZERO_ENDPOINTS.base_sepolia;
      chainInfo = { name: "Base Sepolia", eid: 40245, chainId: 84532 };
      break;
    case "optimismSepolia":
      lzEndpoint = LAYERZERO_ENDPOINTS.op_sepolia;
      chainInfo = { name: "OP Sepolia", eid: 40232, chainId: 11155420 };
      break;
    case "arbitrumSepolia":
      lzEndpoint = LAYERZERO_ENDPOINTS.arbitrum_sepolia;
      chainInfo = { name: "Arbitrum Sepolia", eid: 40231, chainId: 421614 };
      break;
    case "polygonAmoy":
      lzEndpoint = LAYERZERO_ENDPOINTS.polygon_amoy;
      chainInfo = { name: "Polygon Amoy", eid: 40267, chainId: 80002 };
      break;
    default:
      throw new Error(`❌ Unsupported network: ${network}`);
  }
  
  console.log(`📍 Chain: ${chainInfo.name}`);
  console.log(`🔗 LayerZero Endpoint: ${lzEndpoint}`);
  console.log(`🆔 LayerZero EID: ${chainInfo.eid}`);
  
  const DirectLayerZeroMessenger = await hre.ethers.getContractFactory("DirectLayerZeroMessenger");
  
  console.log("⏳ Deploying contract...");
  const messenger = await DirectLayerZeroMessenger.deploy(
    lzEndpoint,
    DEPLOYER_ADDRESS
  );
  
  await messenger.deployed();
  
  console.log(`✅ DirectLayerZeroMessenger deployed at: ${messenger.address}`);
  console.log(`🔗 Transaction hash: ${messenger.deployTransaction.hash}`);
  
  const deploymentInfo = {
    network: network,
    chainName: chainInfo.name,
    layerZeroEid: chainInfo.eid,
    chainId: chainInfo.chainId,
    contractAddress: messenger.address,
    layerZeroEndpoint: lzEndpoint,
    deployer: DEPLOYER_ADDRESS,
    deploymentHash: messenger.deployTransaction.hash,
    timestamp: new Date().toISOString()
  };
  
  console.log("\n📝 Deployment Summary:");
  console.log(JSON.stringify(deploymentInfo, null, 2));
  
  return deploymentInfo;
}

if (require.main === module) {
  main()
    .then((deploymentInfo) => {
      console.log(`\n🎉 Deployment completed successfully on ${deploymentInfo.chainName}!`);
      process.exit(0);
    })
    .catch((error) => {
      console.error("❌ Deployment failed:", error);
      process.exit(1);
    });
}

module.exports = main;
