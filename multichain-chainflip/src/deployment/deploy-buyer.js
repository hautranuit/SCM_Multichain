const { ethers, network } = require("hardhat");

async function main() {
    console.log("🛒 Deploying BuyerChain contract (Simplified)...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Account balance:", ethers.formatEther(balance), "ETH");

    // Hub contract address
    const hubContractAddress = process.env.HUB_CONTRACT_ADDRESS || "0x0000000000000000000000000000000000000000";
    
    if (hubContractAddress === "0x0000000000000000000000000000000000000000") {
        console.warn("⚠️  Warning: Hub contract address not set. Using zero address.");
    }

    // Deploy BuyerChain
    console.log("\n🚀 Deploying contract...");
    const BuyerChain = await ethers.getContractFactory("BuyerChain");
    const buyerChain = await BuyerChain.deploy(
        deployer.address, // initialAdmin
        hubContractAddress // hubContract
    );

    await buyerChain.waitForDeployment();

    const contractAddress = await buyerChain.getAddress();
    console.log("✅ BuyerChain deployed to:", contractAddress);
    
    const deployTx = buyerChain.deploymentTransaction();
    console.log("📋 Transaction hash:", deployTx?.hash || "N/A");

    // Basic verification
    console.log("\n🔍 Verifying deployment...");
    const disputeFee = await buyerChain.disputeResolutionFee();
    const confirmationPeriod = await buyerChain.confirmationPeriod();
    console.log("Dispute resolution fee:", ethers.formatEther(disputeFee), "ETH");
    console.log("Confirmation period:", confirmationPeriod.toString(), "seconds");

    console.log("\n📝 Deployment Summary:");
    console.log("=".repeat(50));
    console.log("Contract Address:", contractAddress);
    console.log("Deployer:", deployer.address);
    console.log("Hub Contract:", hubContractAddress);
    console.log("Network:", network.name);
    console.log("Chain ID:", network.config.chainId);
    console.log("Dispute Fee:", ethers.formatEther(disputeFee), "ETH");
    console.log("Confirmation Period:", confirmationPeriod.toString(), "seconds");
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
        disputeResolutionFee: ethers.formatEther(disputeFee),
        confirmationPeriod: confirmationPeriod.toString(),
        deploymentType: "simplified"
    };

    console.log("\n💾 Saving deployment info to deployment-buyer.json");
    const fs = require('fs');
    fs.writeFileSync('deployment-buyer.json', JSON.stringify(deploymentInfo, null, 2));

    return contractAddress;
}

main()
    .then((address) => {
        console.log(`\n🎉 BuyerChain successfully deployed at: ${address}`);
        console.log("💡 Note: Additional setup (roles, funding) can be done separately if needed.");
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
