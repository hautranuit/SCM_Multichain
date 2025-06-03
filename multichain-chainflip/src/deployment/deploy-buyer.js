const { ethers, network } = require("hardhat");

async function main() {
    console.log("🛒 Deploying BuyerChain contract...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    // Fix for ethers v6: Use provider to get balance
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Account balance:", ethers.formatEther(balance), "ETH");

    // Hub contract address (needs to be deployed first)
    const hubContractAddress = process.env.HUB_CONTRACT_ADDRESS || "0x0000000000000000000000000000000000000000";
    
    if (hubContractAddress === "0x0000000000000000000000000000000000000000") {
        console.warn("⚠️  Warning: Hub contract address not set. Using zero address.");
    }

    // Deploy BuyerChain
    const BuyerChain = await ethers.getContractFactory("BuyerChain");
    const buyerChain = await BuyerChain.deploy(
        deployer.address, // initialAdmin
        hubContractAddress // hubContract
    );

    // Fix for ethers v6: Use waitForDeployment instead of deployed
    await buyerChain.waitForDeployment();

    // Fix for ethers v6: Use getAddress() method
    const contractAddress = await buyerChain.getAddress();
    console.log("✅ BuyerChain deployed to:", contractAddress);
    
    // Fix for ethers v6: Use deploymentTransaction() method
    const deployTx = buyerChain.deploymentTransaction();
    console.log("📋 Transaction hash:", deployTx?.hash || "N/A");

    // Verify deployment
    console.log("\n🔍 Verifying deployment...");
    const disputeFee = await buyerChain.disputeResolutionFee();
    const confirmationPeriod = await buyerChain.confirmationPeriod();
    console.log("Dispute resolution fee:", ethers.formatEther(disputeFee), "ETH");
    console.log("Confirmation period:", confirmationPeriod.toString(), "seconds");

    // Setup initial roles and permissions
    console.log("\n⚙️  Setting up initial configuration...");
    
    // Grant buyer and seller roles to deployer for testing
    const BUYER_ROLE = await buyerChain.BUYER_ROLE();
    const SELLER_ROLE = await buyerChain.SELLER_ROLE();
    const ARBITRATOR_ROLE = await buyerChain.ARBITRATOR_ROLE();
    
    if (!await buyerChain.hasRole(BUYER_ROLE, deployer.address)) {
        const tx1 = await buyerChain.grantRole(BUYER_ROLE, deployer.address);
        await tx1.wait();
        console.log("✅ Granted BUYER_ROLE to deployer");
    }
    
    if (!await buyerChain.hasRole(SELLER_ROLE, deployer.address)) {
        const tx2 = await buyerChain.grantRole(SELLER_ROLE, deployer.address);
        await tx2.wait();
        console.log("✅ Granted SELLER_ROLE to deployer");
    }

    // Register deployer as an arbitrator
    const registerArbitratorTx = await buyerChain.registerArbitrator(deployer.address);
    await registerArbitratorTx.wait();
    console.log("⚖️  Registered deployer as arbitrator");

    // Fund the contract for payments and incentives (Fix for ethers v6: Use parseEther directly)
    const fundingAmount = ethers.parseEther("5.0"); // 5 ETH
    const fundTx = await deployer.sendTransaction({
        to: contractAddress,
        value: fundingAmount
    });
    await fundTx.wait();
    console.log("💰 Funded contract with 5 ETH for payments and incentives");

    console.log("\n📝 Deployment Summary:");
    console.log("=".repeat(50));
    console.log("Contract Address:", contractAddress);
    console.log("Deployer:", deployer.address);
    console.log("Hub Contract:", hubContractAddress);
    console.log("Network:", network.name);
    console.log("Chain ID:", network.config.chainId);
    console.log("Dispute Fee:", ethers.formatEther(disputeFee), "ETH");
    console.log("Confirmation Period:", confirmationPeriod.toString(), "seconds");
    console.log("Gas Used:", deployTx?.gasLimit?.toString() || "N/A");
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
        roles: {
            DEFAULT_ADMIN_ROLE: await buyerChain.DEFAULT_ADMIN_ROLE(),
            BUYER_ROLE: BUYER_ROLE,
            SELLER_ROLE: SELLER_ROLE,
            ARBITRATOR_ROLE: ARBITRATOR_ROLE,
            HUB_COORDINATOR_ROLE: await buyerChain.HUB_COORDINATOR_ROLE()
        }
    };

    console.log("\n💾 Saving deployment info to deployment-buyer.json");
    const fs = require('fs');
    fs.writeFileSync('deployment-buyer.json', JSON.stringify(deploymentInfo, null, 2));

    return contractAddress;
}

main()
    .then((address) => {
        console.log(`\n🎉 BuyerChain successfully deployed at: ${address}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
