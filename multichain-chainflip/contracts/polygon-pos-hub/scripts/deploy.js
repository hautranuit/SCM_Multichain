const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 Deploying ChainFLIP Polygon PoS Hub Contract...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    // Get account balance
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Account balance:", ethers.formatEther(balance), "MATIC");
    
    // Deploy the contract
    const PolygonPoSHub = await ethers.getContractFactory("PolygonPoSHub");
    
    console.log("Deploying PolygonPoSHub...");
    const hub = await PolygonPoSHub.deploy(deployer.address);
    
    await hub.waitForDeployment();
    const contractAddress = await hub.getAddress();
    
    console.log("✅ PolygonPoSHub deployed to:", contractAddress);
    console.log("📋 Deployment Summary:");
    console.log("- Contract: PolygonPoSHub");
    console.log("- Address:", contractAddress);
    console.log("- Owner:", deployer.address);
    console.log("- Network:", hre.network.name);
    console.log("- Chain ID:", (await ethers.provider.getNetwork()).chainId);
    
    // Verify the deployment
    try {
        const name = await hub.name();
        const symbol = await hub.symbol();
        const owner = await hub.owner();
        
        console.log("\n🔍 Contract Verification:");
        console.log("- Name:", name);
        console.log("- Symbol:", symbol);
        console.log("- Owner:", owner);
        
        console.log("\n✅ Contract deployed and verified successfully!");
        
        // Save deployment info
        const deploymentInfo = {
            contractName: "PolygonPoSHub",
            contractAddress: contractAddress,
            deployer: deployer.address,
            network: hre.network.name,
            chainId: (await ethers.provider.getNetwork()).chainId.toString(),
            timestamp: new Date().toISOString(),
            transactionHash: hub.deploymentTransaction()?.hash
        };
        
        console.log("\n📄 Deployment Info:", JSON.stringify(deploymentInfo, null, 2));
        
    } catch (error) {
        console.error("❌ Contract verification failed:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
