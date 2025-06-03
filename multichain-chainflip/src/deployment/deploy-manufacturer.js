const { ethers, network } = require("hardhat");

async function main() {
    console.log("🚀 Deploying ManufacturerChain contract...");
    
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

    // Deploy ManufacturerChain
    const ManufacturerChain = await ethers.getContractFactory("ManufacturerChain");
    const manufacturerChain = await ManufacturerChain.deploy(
        deployer.address, // initialAdmin
        hubContractAddress // hubContract
    );

    // Fix for ethers v6: Use waitForDeployment instead of deployed
    await manufacturerChain.waitForDeployment();

    // Fix for ethers v6: Use getAddress() method
    const contractAddress = await manufacturerChain.getAddress();
    console.log("✅ ManufacturerChain deployed to:", contractAddress);
    
    // Fix for ethers v6: Use deploymentTransaction() method
    const deployTx = manufacturerChain.deploymentTransaction();
    console.log("📋 Transaction hash:", deployTx?.hash || "N/A");

    // Verify deployment
    console.log("\n🔍 Verifying deployment...");
    const name = await manufacturerChain.name();
    const symbol = await manufacturerChain.symbol();
    console.log("Contract name:", name);
    console.log("Contract symbol:", symbol);

    // Setup initial roles and permissions
    console.log("\n⚙️  Setting up initial configuration...");
    
    // Grant manufacturer role to deployer for testing
    const MANUFACTURER_ROLE = await manufacturerChain.MANUFACTURER_ROLE();
    const QUALITY_INSPECTOR_ROLE = await manufacturerChain.QUALITY_INSPECTOR_ROLE();
    
    if (!await manufacturerChain.hasRole(MANUFACTURER_ROLE, deployer.address)) {
        const tx1 = await manufacturerChain.grantRole(MANUFACTURER_ROLE, deployer.address);
        await tx1.wait();
        console.log("✅ Granted MANUFACTURER_ROLE to deployer");
    }
    
    if (!await manufacturerChain.hasRole(QUALITY_INSPECTOR_ROLE, deployer.address)) {
        const tx2 = await manufacturerChain.grantRole(QUALITY_INSPECTOR_ROLE, deployer.address);
        await tx2.wait();
        console.log("✅ Granted QUALITY_INSPECTOR_ROLE to deployer");
    }

    // Fund the contract for incentives (Fix for ethers v6: Use parseEther directly)
    const fundingAmount = ethers.parseEther("1.0"); // 1 ETH
    const fundTx = await deployer.sendTransaction({
        to: contractAddress,
        value: fundingAmount
    });
    await fundTx.wait();
    console.log("💰 Funded contract with 1 ETH for incentives");

    console.log("\n📝 Deployment Summary:");
    console.log("=".repeat(50));
    console.log("Contract Address:", contractAddress);
    console.log("Deployer:", deployer.address);
    console.log("Hub Contract:", hubContractAddress);
    console.log("Network:", network.name);
    console.log("Chain ID:", network.config.chainId);
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
        roles: {
            DEFAULT_ADMIN_ROLE: await manufacturerChain.DEFAULT_ADMIN_ROLE(),
            MANUFACTURER_ROLE: MANUFACTURER_ROLE,
            QUALITY_INSPECTOR_ROLE: QUALITY_INSPECTOR_ROLE,
            HUB_COORDINATOR_ROLE: await manufacturerChain.HUB_COORDINATOR_ROLE()
        }
    };

    console.log("\n💾 Saving deployment info to deployment-manufacturer.json");
    const fs = require('fs');
    fs.writeFileSync('deployment-manufacturer.json', JSON.stringify(deploymentInfo, null, 2));

    return contractAddress;
}

main()
    .then((address) => {
        console.log(`\n🎉 ManufacturerChain successfully deployed at: ${address}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
