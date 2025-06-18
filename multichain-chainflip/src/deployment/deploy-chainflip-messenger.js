const { ethers } = require("hardhat");

// LayerZero V2 Endpoint (same for all testnets!)
const LAYERZERO_V2_ENDPOINT = "0x6EDCE65403992e310A62460808c4b910D972f10f";

async function main() {
    console.log("🚀 Deploying ChainFLIPMessenger contracts...");
    
    const [deployer] = await ethers.getSigners();
    const network = await ethers.provider.getNetwork();
    const chainId = network.chainId;
    
    console.log(`📍 Network: ${network.name} (Chain ID: ${chainId})`);
    console.log(`👤 Deployer: ${deployer.address}`);
    console.log(`💰 Balance: ${ethers.utils.formatEther(await deployer.getBalance())} ETH`);
    
    // Get network name for current chain
    let networkName;
    
    switch (chainId.toString()) {
        case "84532": // Base Sepolia
            networkName = "baseSepolia";
            break;
        case "80002": // Polygon Amoy
            networkName = "polygonAmoy";
            break;
        case "11155420": // Optimism Sepolia
            networkName = "optimismSepolia";
            break;
        case "421614": // Arbitrum Sepolia
            networkName = "arbitrumSepolia";
            break;
        default:
            throw new Error(`Unsupported network with chain ID: ${chainId}`);
    }
    
    console.log(`🌐 LayerZero V2 Endpoint: ${LAYERZERO_V2_ENDPOINT}`);
    console.log(`📡 Network: ${networkName}`);
    
    // Deploy ChainFLIPMessenger
    console.log("\n📦 Deploying ChainFLIPMessenger...");
    const ChainFLIPMessenger = await ethers.getContractFactory("ChainFLIPMessenger");
    const messenger = await ChainFLIPMessenger.deploy(
        LAYERZERO_V2_ENDPOINT, // LayerZero V2 endpoint
        deployer.address       // Owner/delegate
    );
    await messenger.deployed();
    
    console.log(`✅ ChainFLIPMessenger deployed to: ${messenger.address}`);
    console.log(`📋 Transaction hash: ${messenger.deployTransaction.hash}`);
    
    // Wait for confirmations
    console.log("⏳ Waiting for confirmations...");
    await messenger.deployTransaction.wait(5);
    
    // Verify deployment
    console.log("\n🔍 Verifying deployment...");
    try {
        const supportedChains = await messenger.getSupportedChains();
        console.log(`📡 Supported destination chains: ${supportedChains.join(", ")}`);
        console.log(`👑 Contract owner: ${await messenger.owner()}`);
        console.log(`🔗 LayerZero endpoint: ${await messenger.endpoint()}`);
    } catch (error) {
        console.log(`⚠️ Verification failed: ${error.message}`);
    }
    
    // Save deployment info
    const deploymentInfo = {
        network: networkName,
        chainId: chainId.toString(),
        contractAddress: messenger.address,
        layerZeroEndpoint: LAYERZERO_V2_ENDPOINT,
        deployerAddress: deployer.address,
        transactionHash: messenger.deployTransaction.hash,
        blockNumber: messenger.deployTransaction.blockNumber,
        timestamp: new Date().toISOString()
    };
    
    const fs = require('fs');
    const path = require('path');
    const deploymentsDir = path.join(__dirname, '../deployments');
    
    if (!fs.existsSync(deploymentsDir)) {
        fs.mkdirSync(deploymentsDir, { recursive: true });
    }
    
    const deploymentFile = path.join(deploymentsDir, `chainflip-messenger-${networkName}-${chainId}.json`);
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
    
    console.log(`\n💾 Deployment info saved to: ${deploymentFile}`);
    
    console.log("\n🎉 ChainFLIPMessenger deployment completed!");
    console.log("\n📋 Next steps:");
    console.log("1. Deploy on all 4 chains (Base, Polygon, Optimism, Arbitrum)");
    console.log("2. Set trusted peers between all chains (LayerZero V2 uses setPeer)");
    console.log("3. Test cross-chain messaging");
    console.log("\n🔗 Contract address to save:");
    console.log(`${networkName}: "${messenger.address}"`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });