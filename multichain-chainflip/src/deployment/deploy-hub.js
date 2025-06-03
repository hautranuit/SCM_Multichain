const { ethers, network } = require("hardhat");

async function main() {
    console.log("🌐 Deploying EnhancedPolygonPoSHub contract...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    // Fix for ethers v6: Use provider to get balance
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Account balance:", ethers.formatEther(balance), "ETH");

    // Deploy EnhancedPolygonPoSHub
    const EnhancedHub = await ethers.getContractFactory("EnhancedPolygonPoSHub");
    const enhancedHub = await EnhancedHub.deploy(
        deployer.address // initialOwner
    );

    // Fix for ethers v6: Use waitForDeployment instead of deployed
    await enhancedHub.waitForDeployment();

    // Fix for ethers v6: Use getAddress() method
    const contractAddress = await enhancedHub.getAddress();
    console.log("✅ EnhancedPolygonPoSHub deployed to:", contractAddress);
    
    // Fix for ethers v6: Use deploymentTransaction() method
    const deployTx = enhancedHub.deploymentTransaction();
    console.log("📋 Transaction hash:", deployTx?.hash || "N/A");

    // Verify deployment
    console.log("\n🔍 Verifying deployment...");
    const name = await enhancedHub.name();
    const symbol = await enhancedHub.symbol();
    console.log("Contract name:", name);
    console.log("Contract symbol:", symbol);

    // Get FL metrics
    const flMetrics = await enhancedHub.getFLAggregationMetrics();
    console.log("Total FL models:", flMetrics.totalModels.toString());

    // Setup initial configuration
    console.log("\n⚙️  Setting up initial configuration...");

    // Register L2 chain contracts (placeholders for now)
    const MANUFACTURER_CHAIN_ID = 2001;
    const TRANSPORTER_CHAIN_ID = 2002;
    const BUYER_CHAIN_ID = 2003;

    // These will be updated after L2 contracts are deployed
    const placeholderAddress = "0x0000000000000000000000000000000000000000";

    console.log("📝 Note: L2 contract addresses need to be registered after deployment");
    console.log("Use registerChainContract() with actual deployed addresses");

    // Fund the contract (Fix for ethers v6: Use parseEther directly)
    const fundingAmount = ethers.parseEther("2.0"); // 2 ETH
    const fundTx = await deployer.sendTransaction({
        to: contractAddress,
        value: fundingAmount
    });
    await fundTx.wait();
    console.log("💰 Funded hub contract with 2 ETH");

    console.log("\n📝 Deployment Summary:");
    console.log("=".repeat(50));
    console.log("Contract Address:", contractAddress);
    console.log("Deployer:", deployer.address);
    console.log("Network:", network.name);
    console.log("Chain ID:", network.config.chainId);
    console.log("Contract Name:", name);
    console.log("Contract Symbol:", symbol);
    console.log("Total FL Models:", flMetrics.totalModels.toString());
    console.log("Gas Used:", deployTx?.gasLimit?.toString() || "N/A");
    console.log("=".repeat(50));

    // Save deployment info
    const deploymentInfo = {
        network: network.name,
        chainId: network.config.chainId,
        contractAddress: contractAddress,
        deployer: deployer.address,
        transactionHash: deployTx?.hash || "N/A",
        blockNumber: deployTx?.blockNumber || "N/A",
        timestamp: new Date().toISOString(),
        contractName: name,
        contractSymbol: symbol,
        totalFLModels: flMetrics.totalModels.toString(),
        chainIds: {
            MANUFACTURER_CHAIN_ID: MANUFACTURER_CHAIN_ID,
            TRANSPORTER_CHAIN_ID: TRANSPORTER_CHAIN_ID,
            BUYER_CHAIN_ID: BUYER_CHAIN_ID
        },
        flModels: [
            "anomaly_detection",
            "counterfeit_detection", 
            "quality_prediction",
            "route_optimization",
            "fraud_detection"
        ]
    };

    console.log("\n💾 Saving deployment info to deployment-hub.json");
    const fs = require('fs');
    fs.writeFileSync('deployment-hub.json', JSON.stringify(deploymentInfo, null, 2));

    console.log("\n📋 Next Steps:");
    console.log("1. Deploy L2 contracts with this hub address as HUB_CONTRACT_ADDRESS");
    console.log("2. Register L2 contracts with hub using registerChainContract()");
    console.log("3. Register participants using registerParticipant()");
    console.log("4. Fund L2 contracts for incentive mechanisms");

    return contractAddress;
}

main()
    .then((address) => {
        console.log(`\n🎉 EnhancedPolygonPoSHub successfully deployed at: ${address}`);
        console.log(`\n💡 Set this as HUB_CONTRACT_ADDRESS environment variable: ${address}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });