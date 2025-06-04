const { ethers, network } = require("hardhat");

async function main() {
    console.log("🚛 Deploying TransporterChain contract (Simplified)...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Account balance:", ethers.formatEther(balance), "ETH");

    // Hub contract address
    const hubContractAddress = process.env.HUB_CONTRACT_ADDRESS || "0x0000000000000000000000000000000000000000";
    
    if (hubContractAddress === "0x0000000000000000000000000000000000000000") {
        console.warn("⚠️  Warning: Hub contract address not set. Using zero address.");
    }

    // Deploy TransporterChain
    console.log("\n🚀 Deploying contract...");
    const TransporterChain = await ethers.getContractFactory("TransporterChain");
    const transporterChain = await TransporterChain.deploy(
        deployer.address, // initialAdmin
        hubContractAddress // hubContract
    );

    await transporterChain.waitForDeployment();

    const contractAddress = await transporterChain.getAddress();
    console.log("✅ TransporterChain deployed to:", contractAddress);
    
    const deployTx = transporterChain.deploymentTransaction();
    console.log("📋 Transaction hash:", deployTx?.hash || "N/A");

    // Basic verification
    console.log("\n🔍 Verifying deployment...");
    const consensusThreshold = await transporterChain.consensusThreshold();
    console.log("Consensus threshold:", consensusThreshold.toString() + "%");

    console.log("\n📝 Deployment Summary:");
    console.log("=".repeat(50));
    console.log("Contract Address:", contractAddress);
    console.log("Deployer:", deployer.address);
    console.log("Hub Contract:", hubContractAddress);
    console.log("Network:", network.name);
    console.log("Chain ID:", network.config.chainId);
    console.log("Consensus Threshold:", consensusThreshold.toString() + "%");
    console.log("=".repeat(50));

    // Save deployment info
    const deploymentInfo = {
        network: network.name,
        chainId: network.config.chainId,
        contractAddress: contractAddress,
        deployer: deployer.address,
        hubContract: hubContractAddress,
        transactionHash: deployTx?.hash || "N/A",
        blockNumber: deployTx?.blockNumber || "N/A",
        timestamp: new Date().toISOString(),
        consensusThreshold: consensusThreshold.toString(),
        deploymentType: "simplified"
    };

    console.log("\n💾 Saving deployment info to deployment-transporter.json");
    const fs = require('fs');
    fs.writeFileSync('deployment-transporter.json', JSON.stringify(deploymentInfo, null, 2));

    return contractAddress;
}

main()
    .then((address) => {
        console.log(`\n🎉 TransporterChain successfully deployed at: ${address}`);
        console.log("💡 Note: Additional setup (roles, funding) can be done separately if needed.");
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
