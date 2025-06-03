const { ethers, network } = require("hardhat");

async function main() {
    console.log("🚛 Deploying TransporterChain contract...");
    
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

    // Deploy TransporterChain
    const TransporterChain = await ethers.getContractFactory("TransporterChain");
    const transporterChain = await TransporterChain.deploy(
        deployer.address, // initialAdmin
        hubContractAddress // hubContract
    );

    // Fix for ethers v6: Use waitForDeployment instead of deployed
    await transporterChain.waitForDeployment();

    // Fix for ethers v6: Use getAddress() method
    const contractAddress = await transporterChain.getAddress();
    console.log("✅ TransporterChain deployed to:", contractAddress);
    
    // Fix for ethers v6: Use deploymentTransaction() method
    const deployTx = transporterChain.deploymentTransaction();
    console.log("📋 Transaction hash:", deployTx?.hash || "N/A");

    // Verify deployment
    console.log("\n🔍 Verifying deployment...");
    const consensusThreshold = await transporterChain.consensusThreshold();
    console.log("Consensus threshold:", consensusThreshold.toString() + "%");

    // Setup initial roles and permissions
    console.log("\n⚙️  Setting up initial configuration...");
    
    // Grant transporter role to deployer for testing
    const TRANSPORTER_ROLE = await transporterChain.TRANSPORTER_ROLE();
    const VALIDATOR_ROLE = await transporterChain.VALIDATOR_ROLE();
    
    if (!await transporterChain.hasRole(TRANSPORTER_ROLE, deployer.address)) {
        const tx1 = await transporterChain.grantRole(TRANSPORTER_ROLE, deployer.address);
        await tx1.wait();
        console.log("✅ Granted TRANSPORTER_ROLE to deployer");
    }
    
    if (!await transporterChain.hasRole(VALIDATOR_ROLE, deployer.address)) {
        const tx2 = await transporterChain.grantRole(VALIDATOR_ROLE, deployer.address);
        await tx2.wait();
        console.log("✅ Granted VALIDATOR_ROLE to deployer");
    }

    // Register deployer as a transport node
    const registerTx = await transporterChain.registerTransportNode(
        deployer.address,
        "primary",
        "Default Location"
    );
    await registerTx.wait();
    console.log("🚛 Registered deployer as transport node");

    // Fund the contract for incentives (Fix for ethers v6: Use parseEther directly)
    const fundingAmount = ethers.parseEther("2.0"); // 2 ETH
    const fundTx = await deployer.sendTransaction({
        to: contractAddress,
        value: fundingAmount
    });
    await fundTx.wait();
    console.log("💰 Funded contract with 2 ETH for incentives");

    console.log("\n📝 Deployment Summary:");
    console.log("=".repeat(50));
    console.log("Contract Address:", contractAddress);
    console.log("Deployer:", deployer.address);
    console.log("Hub Contract:", hubContractAddress);
    console.log("Network:", network.name);
    console.log("Chain ID:", network.config.chainId);
    console.log("Consensus Threshold:", consensusThreshold.toString() + "%");
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
        consensusThreshold: consensusThreshold.toString(),
        roles: {
            DEFAULT_ADMIN_ROLE: await transporterChain.DEFAULT_ADMIN_ROLE(),
            TRANSPORTER_ROLE: TRANSPORTER_ROLE,
            VALIDATOR_ROLE: VALIDATOR_ROLE,
            HUB_COORDINATOR_ROLE: await transporterChain.HUB_COORDINATOR_ROLE()
        }
    };

    console.log("\n💾 Saving deployment info to deployment-transporter.json");
    const fs = require('fs');
    fs.writeFileSync('deployment-transporter.json', JSON.stringify(deploymentInfo, null, 2));

    return contractAddress;
}

main()
    .then((address) => {
        console.log(`\n🎉 TransporterChain successfully deployed at: ${address}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
